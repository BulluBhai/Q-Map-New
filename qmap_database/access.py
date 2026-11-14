"""QMapData - the single public, read-only data-access interface
(document 03 v1.2, Part A; interface 1.1 plus the ChatGPT rulings of
12 Nov 26: S-1 to S-6 and T-DA-12, per the Consolidated Handover section 7.5).

This module is the only door into the Q-MAP Database. Callers see function
names, parameters, the bars columns, the meta keys, warning codes and
exceptions - never folders, file names, generations or SQL. Data problems are
answers (status, warnings, notes, issues), not crashes; caller mistakes and
system problems raise the QMapDataError family.

Exactly ten functions are public. Nothing here writes anything, and nothing
here ever triggers maintenance.
"""

# --- Imports -----------------------------------------------------------------
import difflib
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import pandas as pd
import pyarrow.parquet as pq

from . import aggregation as agg
from . import session_rules as sr
from .catalogue import Catalogue
from .errors import (DatabaseUnavailableError, DataIntegrityError,
                     InvalidRequestError, UnknownInstrumentError,
                     UnsupportedTimeframeError)

# --- Constants ---------------------------------------------------------------
INTRADAY_TIMEFRAMES = {"1m": 1, "3m": 3, "5m": 5, "10m": 10, "15m": 15,
                       "30m": 30, "60m": 60}
PERIOD_TIMEFRAMES = ("1D", "1W", "1MO")
ALL_FIELDS = ("open", "high", "low", "close", "volume")

TS_MEANING = "interval_start_ist_wallclock"
TIMEZONE = "Asia/Kolkata"

# Warning codes (03 section A6). Any warning makes the status PARTIAL.
W_RANGE_TRUNCATED_START = "RANGE_TRUNCATED_START"
W_RANGE_TRUNCATED_END = "RANGE_TRUNCATED_END"
W_INCOMPLETE_BARS = "INCOMPLETE_BARS"
W_FORMING_BAR = "FORMING_BAR"
W_VOLUME_PARTIAL = "VOLUME_PARTIAL"
W_VOLUME_UNAVAILABLE = "VOLUME_UNAVAILABLE"
W_FLAGGED_ROWS_INCLUDED = "FLAGGED_ROWS_INCLUDED"
W_CONTINUITY_ISSUE = "CONTINUITY_ISSUE_IN_RANGE"
W_UNRECOGNISED_SESSION = "UNRECOGNISED_SESSION_IN_RANGE"
W_HELD_REVISION = "HELD_REVISION_EXISTS"
W_NO_DATA = "NO_DATA_IN_RANGE"

# Note codes: informational, never change the status (03 section A6).
N_COMPLETENESS_PROVISIONAL = "COMPLETENESS_PROVISIONAL"
N_CANDIDATE_SESSIONS = "CANDIDATE_SESSIONS_IN_RANGE"
N_DAILY_VOLUME_EXCLUDES_AUCTION = "DAILY_VOLUME_EXCLUDES_AUCTION"

# S-4a availability reason codes (additive; interface 1.1 + rulings).
R_REQUIRED_FIELD_UNAVAILABLE = "REQUIRED_FIELD_UNAVAILABLE"
R_REQUIRED_FIELD_PARTIAL = "REQUIRED_FIELD_PARTIAL"
R_MISSING_DAY = "MISSING_DAY"
R_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"

# S-6: exactly these data-quality flags raise FLAGGED_ROWS_INCLUDED, wherever
# they appear on returned rows. CAS_CANDIDATE and VOLUME_EXCLUDES_AUCTION are
# covered by notes instead and never trigger it.
TRIGGER_FLAGS = {"SUSPECT_FILL", "OFF_TICK_RULE_UNVERIFIED",
                 "SESSION_UNCONFIRMED", "LARGE_GAP_UNVERIFIED",
                 "LEVEL_BREAK_UNVERIFIED", "VOLUME_SEMANTICS_UNVERIFIED"}


# --- Return structures ----------------------------------------------------------
@dataclass(frozen=True)
class BarResult:
    bars: pd.DataFrame
    meta: dict
    status: str                 # "OK" | "PARTIAL" | "EMPTY"


@dataclass(frozen=True)
class DataRequirement:
    instrument_id: str
    timeframe: str
    start: object = None
    end: object = None
    required_fields: tuple = ("open", "high", "low", "close")
    optional_fields: tuple = ("volume",)
    min_bars: int = 1
    require_complete_bars: bool = False
    exclude_flagged: bool = False
    latest_n: int = None


@dataclass(frozen=True)
class AvailabilityReport:
    status: str                 # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    reasons: list = field(default_factory=list)
    available_start: object = None
    available_end: object = None
    estimated_bars: int = 0
    missing_fields: tuple = ()
    continuity_issues: list = field(default_factory=list)


# --- Helpers ----------------------------------------------------------------------
def _parse_moment(value, name):
    """Accept date, datetime, pandas Timestamp or 'YYYY-MM-DD' text; return
    (datetime, was_date_only). Interpreted as IST."""
    if value is None:
        return None, False
    if isinstance(value, str):
        try:
            parsed = pd.Timestamp(value)
        except ValueError:
            raise InvalidRequestError(
                "%s '%s' is not a date. Use YYYY-MM-DD." % (name, value))
        date_only = len(value.strip()) <= 10
        return parsed.to_pydatetime(), date_only
    if isinstance(value, pd.Timestamp):
        moment = value.to_pydatetime()
        return moment, moment.time() == time(0, 0)
    if isinstance(value, datetime):
        return value, value.time() == time(0, 0)
    if isinstance(value, date):
        return datetime.combine(value, time(0, 0)), True
    raise InvalidRequestError("%s has unsupported type %s"
                              % (name, type(value).__name__))


def _flags_of(text):
    return set(text.split(";")) if isinstance(text, str) and text else set()


# --- Main logic ---------------------------------------------------------------------
class QMapData:
    """Read-only access to the Q-MAP database. The catalogue connection stays
    open from construction to close(), so every request in one analysis run
    sees the same active generations (02 section 9.5)."""

    def __init__(self, data_root):
        self._data_root = os.path.abspath(data_root)
        catalogue_path = os.path.join(self._data_root, "catalogue",
                                      "qmap_catalogue.duckdb")
        if not os.path.exists(catalogue_path):
            raise DatabaseUnavailableError(
                "No Q-MAP catalogue was found under %s. Choose the data root "
                "folder you loaded with the Data Manager." % self._data_root)
        # Catalogue() raises DatabaseUnavailableError itself when the Data
        # Manager holds the write lock.
        self._catalogue = Catalogue(catalogue_path, read_only=True)
        self._records_cache = {}
        self._windows_cache = {}
        self._calendar_cache = None
        self._closed = False

    # -- lifecycle ------------------------------------------------------------------
    def close(self):
        if not self._closed:
            self._catalogue.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def _require_open(self):
        if self._closed:
            raise DatabaseUnavailableError("This QMapData handle is closed.")

    # -- public function 1 ------------------------------------------------------------
    def list_datasets(self):
        self._require_open()
        return self._catalogue.con.execute(
            "SELECT dataset_id, name, data_kind, base_timeframe, timezone, "
            "status FROM dataset ORDER BY dataset_id").df()

    # -- public function 2 ------------------------------------------------------------
    def list_instruments(self, dataset_id=None, instrument_type=None,
                         active_only=True):
        self._require_open()
        if dataset_id is not None:
            known = [row[0] for row in self._catalogue.con.execute(
                "SELECT dataset_id FROM dataset ORDER BY dataset_id"
            ).fetchall()]
            if dataset_id not in known:
                # S-3: the message names the bad value and the known datasets.
                raise InvalidRequestError(
                    "Dataset '%s' is not in the Q-MAP catalogue. Known "
                    "datasets: %s." % (dataset_id, ", ".join(known)))
        query = ("SELECT i.instrument_id, i.dataset_id, i.instrument_type, "
                 "c.first_ts, c.last_ts, c.row_count, c.quality_status, "
                 "c.completeness_status, c.volume_first_date AS "
                 "volume_available_from, c.volume_last_date AS "
                 "volume_available_to FROM instrument i LEFT JOIN coverage c "
                 "ON c.instrument_id = i.instrument_id WHERE 1=1")
        params = []
        if dataset_id is not None:
            query += " AND i.dataset_id = ?"
            params.append(dataset_id)
        if instrument_type is not None:
            query += " AND i.instrument_type = ?"
            params.append(instrument_type)
        if active_only:
            query += " AND i.active"
        query += " ORDER BY i.instrument_id"
        return self._catalogue.con.execute(query, params).df()

    # -- public function 3 ------------------------------------------------------------
    def describe_instrument(self, instrument_id):
        self._require_open()
        instrument = self._instrument(instrument_id)
        coverage = self._catalogue.con.execute(
            "SELECT * FROM coverage WHERE instrument_id = ?",
            [instrument["instrument_id"]]).df()
        fields = self._catalogue.con.execute(
            "SELECT field_name, data_type, nullable, meaning FROM "
            "field_definition WHERE dataset_id = ?",
            [instrument["dataset_id"]]).df()
        issue_counts = dict(self._catalogue.con.execute(
            "SELECT severity, count(*) FROM data_issue WHERE instrument_id "
            "= ? AND status = 'OPEN' GROUP BY severity",
            [instrument["instrument_id"]]).fetchall())
        rules = self._catalogue.con.execute(
            "SELECT rule_type, value, effective_from, effective_to, "
            "verified, source FROM instrument_rule WHERE instrument_id = ?",
            [instrument["instrument_id"]]).df()
        return {
            "instrument_id": instrument["instrument_id"],
            "dataset_id": instrument["dataset_id"],
            "instrument_type": instrument["instrument_type"],
            "timeframes": self.supported_timeframes(
                instrument["instrument_id"]),
            "fields": fields,
            "coverage": coverage,
            "open_issue_counts": issue_counts,
            "session_rules": rules,
        }

    # -- public function 4 ------------------------------------------------------------
    def supported_timeframes(self, instrument_id):
        self._require_open()
        instrument = self._instrument(instrument_id)
        if self._is_intraday(instrument):
            return list(INTRADAY_TIMEFRAMES) + list(PERIOD_TIMEFRAMES)
        return list(PERIOD_TIMEFRAMES)

    # -- public function 5 ------------------------------------------------------------
    def check_availability(self, requirement):
        self._require_open()
        instrument = self._instrument(requirement.instrument_id)
        self._check_timeframe(instrument, requirement.timeframe)
        all_requested = tuple(requirement.required_fields) \
            + tuple(requirement.optional_fields)
        self._check_fields(all_requested)

        result = self._build_bars(
            instrument, requirement.timeframe, requirement.start,
            requirement.end, fields=all_requested,
            latest_n=requirement.latest_n, include_auction_records=False,
            exclude_flagged=requirement.exclude_flagged,
            count_complete_only=requirement.require_complete_bars)
        bars = result["bars"]
        candle_bars = bars[~bars["record_type"].isin(
            [agg.RECORD_AUCTION_PHASE, agg.RECORD_CLOSING_AUCTION])]

        reasons = []
        status_rank = {"AVAILABLE": 0, "PARTIAL": 1, "UNAVAILABLE": 2}
        status = "AVAILABLE"

        def worsen(new_status, code, message):
            nonlocal status
            reasons.append({"code": code, "message": message})
            if status_rank[new_status] > status_rank[status]:
                status = new_status

        for code, message in result["truncation_warnings"]:
            worsen("PARTIAL", code, message)

        # S-4 / S-4a: required-field availability, evaluated over the window's
        # underlying records. An empty range is not a missing field.
        missing_fields = []
        if len(result["window_records"]) > 0:
            presence = result["field_presence"]
            for field_name in requirement.required_fields:
                state = presence.get(field_name, "all")
                if state == "none":
                    missing_fields.append(field_name)
                    code = (W_VOLUME_UNAVAILABLE if field_name == "volume"
                            else R_REQUIRED_FIELD_UNAVAILABLE)
                    worsen("UNAVAILABLE", code,
                           "Required field '%s' is absent throughout the "
                           "range." % field_name)
                elif state == "some":
                    missing_fields.append(field_name)
                    code = (W_VOLUME_PARTIAL if field_name == "volume"
                            else R_REQUIRED_FIELD_PARTIAL)
                    worsen("PARTIAL", code,
                           "Required field '%s' is absent for part of the "
                           "range (%s)." % (field_name,
                                            result["field_detail"].get(
                                                field_name, "")))

        for issue in result["missing_day_issues"]:
            worsen("PARTIAL", R_MISSING_DAY, issue)
        continuity = result["continuity_issues"]
        if continuity:
            worsen("PARTIAL", W_CONTINUITY_ISSUE,
                   "%d continuity-blocking issue(s) lie inside the range."
                   % len(continuity))

        usable = (int(candle_bars["is_complete"].sum())
                  if requirement.require_complete_bars else len(candle_bars))
        if usable < requirement.min_bars:
            worsen("UNAVAILABLE", R_INSUFFICIENT_HISTORY,
                   "Only %d usable bar(s); the requirement needs %d."
                   % (usable, requirement.min_bars))

        return AvailabilityReport(
            status=status, reasons=reasons,
            available_start=result["available_start"],
            available_end=result["available_end"],
            estimated_bars=len(candle_bars),
            missing_fields=tuple(missing_fields),
            continuity_issues=continuity)

    # -- public function 6 ------------------------------------------------------------
    def get_bars(self, instrument_id, timeframe, start=None, end=None, *,
                 fields=None, latest_n=None, include_auction_records=True,
                 exclude_flagged=False):
        self._require_open()
        instrument = self._instrument(instrument_id)
        self._check_timeframe(instrument, timeframe)
        requested_fields = tuple(fields) if fields else ALL_FIELDS
        self._check_fields(requested_fields)
        if latest_n is not None and latest_n < 1:
            raise InvalidRequestError("latest_n must be 1 or more, not %r."
                                      % latest_n)

        result = self._build_bars(instrument, timeframe, start, end,
                                  fields=requested_fields, latest_n=latest_n,
                                  include_auction_records=
                                  include_auction_records,
                                  exclude_flagged=exclude_flagged)
        bars = result["bars"].copy()

        warnings = [{"code": code, "message": message}
                    for code, message in result["truncation_warnings"]]
        notes = []

        candle_bars = bars[~bars["record_type"].isin(
            [agg.RECORD_AUCTION_PHASE, agg.RECORD_CLOSING_AUCTION])]
        if len(bars) == 0:
            warnings.append({"code": W_NO_DATA,
                             "message": "No data exists in the requested "
                                        "range."})
        if (~candle_bars["is_complete"].astype(bool)).any():
            warnings.append({"code": W_INCOMPLETE_BARS,
                             "message": "%d bar(s) are incomplete; missing "
                                        "source minutes are never filled."
                                        % int((~candle_bars["is_complete"]
                                               .astype(bool)).sum())})
        if candle_bars["is_forming"].astype(bool).any():
            warnings.append({"code": W_FORMING_BAR,
                             "message": "The last bar is still forming."})

        # S-5: volume warnings from the underlying CANDLE records only, and
        # only when volume was requested.
        if "volume" in requested_fields and len(result["window_records"]) > 0:
            state = result["field_presence"].get("volume", "all")
            if state == "none":
                warnings.append({"code": W_VOLUME_UNAVAILABLE,
                                 "message": "Volume for %s is not available "
                                            "in this range (%s)."
                                            % (instrument["instrument_id"],
                                               result["field_detail"].get(
                                                   "volume", ""))})
            elif state == "some":
                warnings.append({"code": W_VOLUME_PARTIAL,
                                 "message": "Volume is available for only "
                                            "part of the range (%s)."
                                            % result["field_detail"].get(
                                                "volume", "")})

        # S-6: FLAGGED_ROWS_INCLUDED from the returned rows' quality flags.
        returned_flags = set()
        for text in bars["quality_flags"]:
            returned_flags |= _flags_of(text)
        if returned_flags & TRIGGER_FLAGS:
            warnings.append({"code": W_FLAGGED_ROWS_INCLUDED,
                             "message": "Returned rows carry data-quality "
                                        "flags: %s."
                                        % ", ".join(sorted(returned_flags
                                                           & TRIGGER_FLAGS))})
        if result["continuity_issues"]:
            warnings.append({"code": W_CONTINUITY_ISSUE,
                             "message": "%d issue(s) blocking continuity lie "
                                        "inside the range (G-03); see "
                                        "meta['issues']."
                                        % len(result["continuity_issues"])})
        session_summary = result["session_summary"]
        if session_summary.get(sr.STATUS_UNRECOGNISED):
            warnings.append({"code": W_UNRECOGNISED_SESSION,
                             "message": "%d day(s) in the range have an "
                                        "unrecognised session shape: "
                                        "boundaries uncertain, possible "
                                        "missing data."
                                        % session_summary[
                                            sr.STATUS_UNRECOGNISED]})
        if result["held_revision"]:
            warnings.append({"code": W_HELD_REVISION,
                             "message": "A source revision awaits the "
                                        "Owner's review; this is the active, "
                                        "unrevised data."})

        if result["completeness_basis"] != "OFFICIAL_CALENDAR":
            notes.append(N_COMPLETENESS_PROVISIONAL)
        if session_summary.get(sr.STATUS_CANDIDATE):
            notes.append(N_CANDIDATE_SESSIONS)
        if result["daily_volume_excludes_auction"]:
            notes.append(N_DAILY_VOLUME_EXCLUDES_AUCTION)

        # Field selection: only the requested value columns are returned.
        for column in ALL_FIELDS:
            if column not in requested_fields and column in bars.columns:
                bars = bars.drop(columns=[column])

        status = ("EMPTY" if len(bars) == 0
                  else "PARTIAL" if warnings else "OK")
        meta = {
            "instrument_id": instrument["instrument_id"],
            "dataset_id": instrument["dataset_id"],
            "timeframe": timeframe,
            "timezone": TIMEZONE,
            "ts_meaning": TS_MEANING,
            "requested_start": result["requested_start"],
            "requested_end": result["requested_end"],
            "returned_first_ts": (bars["ts"].iloc[0] if len(bars) else None),
            "returned_last_ts": (bars["ts"].iloc[-1] if len(bars) else None),
            "bar_count": len(bars),
            "incomplete_bar_count": int((~candle_bars["is_complete"]
                                         .astype(bool)).sum()),
            "forming_bar_count": int(candle_bars["is_forming"]
                                     .astype(bool).sum()),
            "volume_available_from": result["volume_available_from"],
            "volume_available_to": result["volume_available_to"],
            "quality_status": result["quality_status"],
            "completeness_status": result["completeness_status"],
            "completeness_basis": result["completeness_basis"],
            "session_summary": session_summary,
            "notes": notes,
            "data_version": result["data_version"],
            "warnings": warnings,
            "issues": result["issues_in_range"],
        }
        return BarResult(bars=bars.reset_index(drop=True), meta=meta,
                         status=status)

    # -- public function 7 ------------------------------------------------------------
    def get_trading_calendar(self, start, end):
        self._require_open()
        start_dt, _ = _parse_moment(start, "start")
        end_dt, _ = _parse_moment(end, "end")
        if start_dt is None or end_dt is None:
            raise InvalidRequestError("get_trading_calendar needs both start "
                                      "and end.")
        if start_dt > end_dt:
            raise InvalidRequestError("Start %s is after end %s."
                                      % (start_dt.date(), end_dt.date()))
        calendar = self._calendar()
        rows = []
        current = start_dt.date()
        while current <= end_dt.date():
            entry = calendar.get(current)
            if entry is not None:
                day_type, source, verified = entry
            elif current.weekday() < 5:
                day_type, source, verified = "TRADING", "DERIVED_FROM_DATA", \
                    False
            else:
                day_type, source, verified = "WEEKEND", "DERIVED_FROM_DATA", \
                    False
            rows.append({"trade_date": current, "day_type": day_type,
                         "source": source, "verified": verified})
            current += timedelta(days=1)
        return pd.DataFrame(rows)

    # -- public function 8 ------------------------------------------------------------
    def get_day_profiles(self, instrument_id, start, end):
        self._require_open()
        instrument = self._instrument(instrument_id)
        start_dt, _ = _parse_moment(start, "start")
        end_dt, _ = _parse_moment(end, "end")
        if start_dt is not None and end_dt is not None \
                and start_dt > end_dt:
            raise InvalidRequestError("Start %s is after end %s."
                                      % (start_dt.date(), end_dt.date()))
        query = ("SELECT * FROM day_profile WHERE instrument_id = ?")
        params = [instrument["instrument_id"]]
        if start_dt is not None:
            query += " AND trade_date >= ?"
            params.append(start_dt.date())
        if end_dt is not None:
            query += " AND trade_date <= ?"
            params.append(end_dt.date())
        query += " ORDER BY trade_date"
        return self._catalogue.con.execute(query, params).df()

    # -- public function 9 ------------------------------------------------------------
    def get_issues(self, instrument_id=None, start=None, end=None,
                   min_severity="WARNING", status="OPEN"):
        self._require_open()
        if instrument_id is not None:
            instrument_id = self._instrument(instrument_id)["instrument_id"]
        rows = self._catalogue.get_issues(instrument_id=instrument_id,
                                          min_severity=min_severity,
                                          status=status)
        frame = pd.DataFrame(rows, columns=[
            "issue_id", "dataset_id", "instrument_id", "ts_from", "ts_to",
            "check_code", "severity", "description", "evidence",
            "affects_continuity", "status", "user_note"])
        start_dt, _ = _parse_moment(start, "start")
        end_dt, end_date_only = _parse_moment(end, "end")
        if end_dt is not None and end_date_only:
            end_dt = end_dt + timedelta(days=1) - timedelta(microseconds=1)
        if start_dt is not None:
            frame = frame[(frame["ts_to"].isna())
                          | (frame["ts_to"] >= start_dt)]
        if end_dt is not None:
            frame = frame[(frame["ts_from"].isna())
                          | (frame["ts_from"] <= end_dt)]
        return frame.reset_index(drop=True)

    # -- public function 10 is close(), defined above -----------------------------------

    # ==================================================================================
    # Internal machinery - may change freely without affecting callers (A8).
    # ==================================================================================
    def _instrument(self, instrument_id):
        wanted = str(instrument_id).upper()
        for instrument in self._catalogue.instruments():
            if instrument["instrument_id"] == wanted:
                return instrument
        known = [i["instrument_id"] for i in self._catalogue.instruments()]
        suggestions = difflib.get_close_matches(wanted, known, n=1)
        hint = (" Did you mean '%s'?" % suggestions[0]) if suggestions else ""
        raise UnknownInstrumentError(
            "Instrument '%s' is not in the Q-MAP catalogue.%s"
            % (instrument_id, hint))

    def _is_intraday(self, instrument):
        dataset = self._catalogue.dataset(instrument["dataset_id"])
        return dataset["data_kind"] == "intraday_ohlcv"

    def _check_timeframe(self, instrument, timeframe):
        allowed = (list(INTRADAY_TIMEFRAMES) + list(PERIOD_TIMEFRAMES)
                   if self._is_intraday(instrument)
                   else list(PERIOD_TIMEFRAMES))
        if timeframe not in allowed:
            kind = ("1-minute" if self._is_intraday(instrument) else "daily")
            raise UnsupportedTimeframeError(
                "Timeframe '%s' is not available for %s (%s data). "
                "Available: %s." % (timeframe, instrument["instrument_id"],
                                    kind, ", ".join(allowed)))

    @staticmethod
    def _check_fields(fields):
        for field_name in fields:
            if field_name not in ALL_FIELDS:
                raise InvalidRequestError(
                    "Field '%s' is not available. Available fields: %s."
                    % (field_name, ", ".join(ALL_FIELDS)))

    def _records(self, instrument):
        """All canonical rows of the active generation, resolved through the
        catalogue pointer and verified against it (read once per handle)."""
        key = (instrument["instrument_id"], instrument["active_generation"])
        if key in self._records_cache:
            return self._records_cache[key]
        if instrument["active_generation"] is None:
            raise DatabaseUnavailableError(
                "%s has no loaded data yet. Run the Data Manager's Initial "
                "load first." % instrument["instrument_id"])
        file_rows = self._catalogue.con.execute(
            "SELECT relative_path, row_count FROM data_file WHERE "
            "instrument_id = ? AND generation = ? ORDER BY relative_path",
            [instrument["instrument_id"],
             instrument["active_generation"]]).fetchall()
        frames = []
        for relative_path, expected_rows in file_rows:
            full_path = os.path.join(self._data_root,
                                     relative_path.replace("/", os.sep))
            if not os.path.exists(full_path):
                raise DataIntegrityError(
                    "%s does not match the catalogue (file missing). Run "
                    "'Check integrity' in the Data Manager." % relative_path)
            if pq.read_metadata(full_path).num_rows != expected_rows:
                raise DataIntegrityError(
                    "%s does not match the catalogue (row count differs). "
                    "Run 'Check integrity' in the Data Manager."
                    % relative_path)
            frames.append(pd.read_parquet(full_path))
        records = pd.concat(frames, ignore_index=True)
        key_column = "ts" if self._is_intraday(instrument) else "trade_date"
        records = records.sort_values(key_column).reset_index(drop=True)
        self._records_cache[key] = records
        return records

    def _day_windows(self, instrument):
        """DayWindow per stored day, from the recorded day profiles plus the
        Owner's confirmations - never from the observed records alone."""
        key = (instrument["instrument_id"], instrument["active_generation"])
        if key in self._windows_cache:
            return self._windows_cache[key]
        confirmations = self._catalogue.session_confirmations(
            instrument["instrument_id"])
        rows = self._catalogue.con.execute(
            "SELECT trade_date, session_status, session_type, "
            "expected_candles FROM day_profile WHERE instrument_id = ?",
            [instrument["instrument_id"]]).fetchall()
        windows = {}
        for trade_date, status, session_type, expected in rows:
            confirmation = confirmations.get(trade_date)
            window_open = (confirmation.session_open
                           if confirmation is not None
                           and confirmation.session_open is not None
                           else sr.SESSION_OPEN)
            windows[trade_date] = agg.DayWindow(
                trade_date, window_open, int(expected), status,
                session_type,
                is_cas=session_type in (sr.TYPE_CAS, sr.TYPE_SPECIAL_CAS))
        self._windows_cache[key] = windows
        return windows

    def _calendar(self):
        if self._calendar_cache is None:
            self._calendar_cache = {
                row[0]: (row[1], row[5], row[6])
                for row in self._catalogue.calendar_entries()}
        return self._calendar_cache

    def _weekday_trading_days_between(self, first, last):
        """Trading days for the RANGE_TRUNCATED_END staleness test: weekdays
        not marked HOLIDAY. A weekend special session does not make data
        'stale' (T-DA-15: a request ending on the weekend after the last
        trading day raises nothing). Weekdays beyond the calendar's known
        range count as trading days, so the warning errs towards being shown."""
        calendar = self._calendar()
        count = 0
        current = first
        while current <= last:
            if current.weekday() < 5:
                entry = calendar.get(current)
                if (entry[0] if entry else None) != "HOLIDAY":
                    count += 1
            current += timedelta(days=1)
        return count

    def _trading_days_between(self, first, last):
        """Expected trading days in a week or month: weekdays not marked
        HOLIDAY, plus weekend days marked SPECIAL."""
        calendar = self._calendar()
        count = 0
        current = first
        while current <= last:
            entry = calendar.get(current)
            day_type = entry[0] if entry else None
            if current.weekday() < 5:
                if day_type != "HOLIDAY":
                    count += 1
            elif day_type == "SPECIAL":
                count += 1
            current += timedelta(days=1)
        return count

    def _build_bars(self, instrument, timeframe, start, end, fields,
                    latest_n=None, include_auction_records=True,
                    exclude_flagged=False, count_complete_only=False):
        """Shared bar construction for get_bars and check_availability."""
        intraday = self._is_intraday(instrument)
        records = self._records(instrument)
        key_column = "ts" if intraday else "trade_date"

        start_dt, _ = _parse_moment(start, "start")
        end_dt, end_date_only = _parse_moment(end, "end")
        if end_dt is not None and end_date_only:
            # A date-only end covers the whole day (A4).
            end_dt = end_dt + timedelta(days=1) - timedelta(microseconds=1)
        if start_dt is not None and end_dt is not None and start_dt > end_dt:
            raise InvalidRequestError(
                "Start %s is after end %s." % (start_dt.strftime("%d-%b-%y"),
                                               end_dt.strftime("%d-%b-%y")))
        if latest_n is not None:
            start_dt = None   # latest_n: start is ignored (A4)

        coverage = self._catalogue.con.execute(
            "SELECT first_ts, last_ts, volume_first_date, volume_last_date, "
            "quality_status, completeness_status, completeness_basis, "
            "last_import_id FROM coverage WHERE instrument_id = ?",
            [instrument["instrument_id"]]).fetchone()
        (first_ts, last_ts, volume_from, volume_to, quality_status,
         completeness_status, completeness_basis, last_import_id) = coverage

        requested_start = start_dt or first_ts
        requested_end = end_dt or last_ts

        # Slice whole days for intraday so bars are always built from the
        # complete session, then filtered afterwards.
        if intraday:
            day_values = records["ts"].dt.date
            mask = pd.Series(True, index=records.index)
            if start_dt is not None:
                mask &= day_values >= start_dt.date()
            if end_dt is not None:
                mask &= day_values <= end_dt.date()
            window_records = records[mask]
        else:
            mask = pd.Series(True, index=records.index)
            if start_dt is not None:
                mask &= pd.to_datetime(records["trade_date"]) >= \
                    pd.Timestamp(start_dt.date())
            if end_dt is not None:
                mask &= pd.to_datetime(records["trade_date"]) <= \
                    pd.Timestamp(end_dt.date())
            window_records = records[mask]

        if intraday:
            windows = self._day_windows(instrument)
            latest_day = records["ts"].max().date()
            latest_window = windows.get(latest_day)
            latest_day_records = records[records["ts"].dt.date == latest_day]
            latest_closed = (agg.day_is_closed(latest_day_records,
                                               latest_window)
                             if latest_window else True)
            # Unrecognised days whose provisional expectation is not met force
            # every bar incomplete (S-1 / B5).
            adjusted_windows = windows
            if timeframe in INTRADAY_TIMEFRAMES:
                bars = agg.aggregate_intraday(
                    window_records, adjusted_windows,
                    INTRADAY_TIMEFRAMES[timeframe],
                    include_auction_records=include_auction_records,
                    exclude_flagged=exclude_flagged,
                    latest_stored_day=latest_day,
                    latest_day_closed=latest_closed)
                bars = self._force_unrecognised_incomplete(
                    bars, window_records, windows)
            else:
                daily = agg.daily_bars_from_intraday(
                    records, windows, exclude_flagged=exclude_flagged,
                    latest_stored_day=latest_day,
                    latest_day_closed=latest_closed)
                bars = self._period_bars(daily, timeframe, records, latest_day)
                bars = self._slice_bars(bars, start_dt, end_dt)
        else:
            daily = agg.daily_bars_from_daily(records)
            bars = self._period_bars(daily, timeframe, records, None)
            bars = self._slice_bars(bars, start_dt, end_dt)

        if intraday and timeframe in INTRADAY_TIMEFRAMES:
            bars = self._slice_bars(bars, start_dt, end_dt)

        if latest_n is not None:
            if count_complete_only:
                keep = bars[bars["is_complete"].astype(bool)].tail(latest_n)
                bars = bars[bars.index.isin(keep.index)]
            else:
                bars = bars.tail(latest_n)
        bars = bars.reset_index(drop=True)

        # Truncation warnings (A6, with the v1.2 precision for the end).
        truncation = []
        # Truncation compares dates: a date-only start on the first available
        # date is not a truncated request (DA-23).
        if start_dt is not None and first_ts is not None \
                and start_dt.date() < first_ts.date():
            truncation.append((W_RANGE_TRUNCATED_START,
                               "Data begins %s; the request started %s."
                               % (first_ts.strftime("%d-%b-%y"),
                                  start_dt.strftime("%d-%b-%y"))))
        if end_dt is not None and last_ts is not None \
                and end_dt.date() > last_ts.date():
            between = self._weekday_trading_days_between(
                last_ts.date() + timedelta(days=1), end_dt.date())
            if between > 0:
                truncation.append((W_RANGE_TRUNCATED_END,
                                   "Data ends %s; the request extends to %s "
                                   "(%d trading day(s) later)."
                                   % (last_ts.strftime("%d-%b-%y"),
                                      end_dt.strftime("%d-%b-%y"), between)))

        # S-5 field presence over the underlying records of the result window.
        field_presence, field_detail = self._field_presence(
            window_records, intraday, bars, latest_n)

        # Issues overlapping the range.
        range_start = (bars["ts"].iloc[0] if len(bars)
                       else (start_dt or requested_start))
        range_end = end_dt or requested_end
        issues_in_range = self._issues_in_range(
            instrument["instrument_id"], range_start, range_end)
        continuity = [issue for issue in issues_in_range
                      if issue["affects_continuity"]]
        missing_days = [issue["description"] for issue in issues_in_range
                        if issue["check_code"] == "V-CAL-02"]
        held = bool(self._catalogue.con.execute(
            "SELECT count(*) FROM data_issue WHERE instrument_id = ? AND "
            "check_code = 'V-REV-01' AND status = 'OPEN'",
            [instrument["instrument_id"]]).fetchone()[0])

        session_summary = {sr.STATUS_CONFIRMED_OFFICIAL: 0,
                           sr.STATUS_CONFIRMED_BY_OWNER: 0,
                           sr.STATUS_CANDIDATE: 0, sr.STATUS_UNRECOGNISED: 0}
        if intraday:
            for status_value, count in self._catalogue.con.execute(
                    "SELECT session_status, count(*) FROM day_profile WHERE "
                    "instrument_id = ? AND trade_date BETWEEN ? AND ? GROUP "
                    "BY session_status",
                    [instrument["instrument_id"],
                     (start_dt or first_ts).date()
                     if (start_dt or first_ts) else date(1900, 1, 1),
                     (end_dt or last_ts).date()
                     if (end_dt or last_ts) else date(2100, 1, 1)]).fetchall():
                session_summary[status_value] = int(count)

        daily_volume_excludes_auction = bool(
            timeframe in PERIOD_TIMEFRAMES and intraday and len(bars)
            and bars["quality_flags"].map(
                lambda text: agg.FLAG_VOLUME_EXCLUDES_AUCTION
                in _flags_of(text)).any())

        run_id = self._catalogue.con.execute(
            "SELECT coalesce(max(run_id), 0) FROM maintenance_run"
        ).fetchone()[0]
        data_version = "run_%06d/import_%06d" % (run_id, last_import_id or 0)

        return {
            "bars": bars,
            "window_records": window_records,
            "field_presence": field_presence,
            "field_detail": field_detail,
            "truncation_warnings": truncation,
            "issues_in_range": issues_in_range,
            "continuity_issues": continuity,
            "missing_day_issues": missing_days,
            "held_revision": held,
            "session_summary": session_summary,
            "daily_volume_excludes_auction": daily_volume_excludes_auction,
            "requested_start": requested_start,
            "requested_end": requested_end,
            "available_start": first_ts,
            "available_end": last_ts,
            "volume_available_from": volume_from,
            "volume_available_to": volume_to,
            "quality_status": quality_status,
            "completeness_status": completeness_status,
            "completeness_basis": completeness_basis,
            "data_version": data_version,
        }

    @staticmethod
    def _slice_bars(bars, start_dt, end_dt):
        if len(bars) == 0:
            return bars
        mask = pd.Series(True, index=bars.index)
        if start_dt is not None:
            mask &= bars["ts"] >= start_dt
        if end_dt is not None:
            mask &= bars["ts"] <= end_dt
        return bars[mask]

    def _period_bars(self, daily_bars, timeframe, records, latest_day):
        if timeframe == "1D":
            return daily_bars
        if len(daily_bars) == 0:
            return daily_bars
        last_date = daily_bars["ts"].max().date()
        return agg.aggregate_periods(daily_bars, timeframe,
                                     self._trading_days_between,
                                     last_stored_date=last_date)

    @staticmethod
    def _force_unrecognised_incomplete(bars, window_records, windows):
        """S-1 / B5: on an unrecognised day whose provisional expectation is
        not met, every bar of that day is incomplete."""
        if len(bars) == 0:
            return bars
        dates = window_records["ts"].dt.date
        for day, day_records in window_records.groupby(dates):
            window = windows.get(day)
            if window is None \
                    or window.session_status != sr.STATUS_UNRECOGNISED:
                continue
            candles = day_records[day_records["record_type"]
                                  == agg.RECORD_CANDLE]
            in_window = candles[(candles["ts"] >= window.open_dt)
                                & (candles["ts"] <= window.end_dt)]
            if len(in_window) < window.expected_minutes:
                day_mask = bars["ts"].dt.date == day
                bars.loc[day_mask, "is_complete"] = False
                bars.loc[day_mask, "volume_complete"] = False
        return bars

    @staticmethod
    def _field_presence(window_records, intraday, bars, latest_n):
        """S-5: per requested field, whether the underlying CANDLE records
        carry it throughout ('all'), partly ('some') or never ('none')."""
        presence, detail = {}, {}
        if intraday:
            candles = window_records[window_records["record_type"]
                                     == agg.RECORD_CANDLE]
        else:
            candles = window_records
        if latest_n is not None and len(bars):
            # Evaluate over the records behind the returned bars only.
            first_ts = bars["ts"].min()
            key = "ts" if intraday else None
            if intraday:
                candles = candles[candles["ts"] >= first_ts]
            else:
                candles = candles[pd.to_datetime(candles["trade_date"])
                                  >= first_ts]
        for field_name in ALL_FIELDS:
            if field_name not in candles.columns or len(candles) == 0:
                presence[field_name] = "all"
                continue
            values = candles[field_name]
            missing = int(values.isna().sum())
            if missing == 0:
                presence[field_name] = "all"
            elif missing == len(values):
                presence[field_name] = "none"
            else:
                presence[field_name] = "some"
                with_values = candles[values.notna()]
                without_values = candles[values.isna()]
                column = "ts" if intraday else "trade_date"
                detail[field_name] = ("absent %s to %s; present %s to %s"
                                      % (without_values[column].min(),
                                         without_values[column].max(),
                                         with_values[column].min(),
                                         with_values[column].max()))
        return presence, detail

    def _issues_in_range(self, instrument_id, range_start, range_end):
        start_ts = pd.Timestamp(range_start) if range_start is not None \
            else pd.Timestamp.min
        end_ts = pd.Timestamp(range_end) if range_end is not None \
            else pd.Timestamp.max
        rows = self._catalogue.con.execute(
            "SELECT issue_id, check_code, severity, ts_from, ts_to, "
            "affects_continuity, status, description FROM data_issue WHERE "
            "instrument_id = ? AND status IN ('OPEN', 'ACKNOWLEDGED') AND "
            "ts_from IS NOT NULL ORDER BY issue_id",
            [instrument_id]).fetchall()
        issues = []
        for (issue_id, check_code, severity, ts_from, ts_to,
             affects_continuity, status, description) in rows:
            if pd.Timestamp(ts_to or ts_from) < start_ts \
                    or pd.Timestamp(ts_from) > end_ts:
                continue
            issues.append({"issue_id": issue_id, "check_code": check_code,
                           "severity": severity, "ts_from": ts_from,
                           "ts_to": ts_to,
                           "affects_continuity": bool(affects_continuity),
                           "status": status, "description": description})
        return issues
