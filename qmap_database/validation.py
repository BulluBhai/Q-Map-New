"""Validation checks V-* and quarantine routing (document 02 v1.6, section 7).

Severity decides what happens: ERROR quarantines the row (or holds the file),
WARNING stores the row, possibly flagged, and opens an issue, INFO is recorded
only. Nothing is repaired, filled or adjusted (D-11); G-03 and G-04 are
applied exactly as the Owner approved them.
"""

# --- Imports -----------------------------------------------------------------
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

from . import session_rules as sr
from . import standardise as std

# --- Constants ---------------------------------------------------------------
REASON_INVALID_OHLC = "INVALID_OHLC"
REASON_BAD_PRICE = "BAD_PRICE"
REASON_OFF_TICK_SYNTHETIC = "OFF_TICK_SYNTHETIC"
REASON_BAD_VOLUME = "BAD_VOLUME"
REASON_OUTSIDE_SESSION = "OUTSIDE_SESSION"

SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"

# G-03 (Owner-approved): every day-to-day open or close move beyond this
# percentage blocks continuity-dependent calculations until the Owner
# verifies that occurrence.
LARGE_MOVE_PERCENT = 15.0
# Implementation note (documented choice, to ChatGPT with the M1a evidence):
# a close move beyond this percentage is represented as LEVEL_BREAK_UNVERIFIED
# (a possible rebase, DQ-15) rather than LARGE_GAP_UNVERIFIED. Both block
# continuity identically under G-03; only the flag name differs.
LEVEL_BREAK_PERCENT = 50.0

# V-PX-04: three or more consecutive candles with an identical close-to-close
# step and frozen High/Low are a fill heuristic - flagged, never quarantined.
MIN_CONSTANT_STEP_RUN = 3

_PRICE_TOLERANCE = 1e-6


# --- Issue structure -----------------------------------------------------------
@dataclass
class IssueRecord:
    check_code: str
    severity: str
    description: str
    evidence: str = ""
    ts_from: object = None
    ts_to: object = None
    affects_continuity: bool = False


# --- Helpers ------------------------------------------------------------------
def _invalid_ohlc_mask(frame):
    """High must be at or above O, C and L; Low at or below O, C and H."""
    high_bad = (frame["high"] < frame["open"]) | (frame["high"] < frame["close"]) \
        | (frame["high"] < frame["low"])
    low_bad = (frame["low"] > frame["open"]) | (frame["low"] > frame["close"]) \
        | (frame["low"] > frame["high"])
    return high_bad | low_bad


def _bad_price_mask(frame):
    """Prices must be positive and finite (V-PX-02)."""
    mask = pd.Series(False, index=frame.index)
    for column in ("open", "high", "low", "close"):
        values = frame[column]
        mask |= ~values.apply(lambda v: isinstance(v, float) and math.isfinite(v)
                              and v > 0)
    return mask


def _off_tick_mask(prices, tick):
    """A price is off-tick when it is not a whole multiple of the tick."""
    remainder = (prices / tick).round() * tick - prices
    return remainder.abs() > _PRICE_TOLERANCE


def _applicable_tick_rule(tick_rules, day):
    """Return the TICK_SIZE rule covering a date, or None. A rule without
    effective dates applies to every date."""
    for rule in tick_rules or []:
        start = rule.get("effective_from")
        end = rule.get("effective_to")
        if (start is None or day >= start) and (end is None or day <= end):
            return rule
    return None


def _compress_minutes_to_ranges(minutes):
    """Turn a sorted list of datetime values into 'HH:MM-HH:MM' range text."""
    if not minutes:
        return ""
    ranges = []
    run_start = prev = minutes[0]
    for current in minutes[1:]:
        if current - prev != timedelta(minutes=1):
            ranges.append((run_start, prev))
            run_start = current
        prev = current
    ranges.append((run_start, prev))
    return ";".join("%s-%s" % (a.strftime("%H:%M"), b.strftime("%H:%M"))
                    for a, b in ranges)


def _quarantine(frame, mask, reason, store):
    taken = frame.loc[mask].copy()
    if len(taken) == 0:
        return frame, store
    taken["reason_code"] = reason
    keep = [c for c in ("ts", "trade_date", "open", "high", "low", "close",
                        "volume", "volume_invalid_text", "source_row",
                        "reason_code")
            if c in taken.columns]
    if len(store) == 0:
        # Concatenating onto an empty store is deprecated in pandas and could
        # change result dtypes; start the store from the taken rows instead.
        store = taken[keep].reset_index(drop=True)
    else:
        store = pd.concat([store, taken[keep]], ignore_index=True)
    return frame.loc[~mask].copy(), store


def _bad_volume_mask(frame):
    """V-VOL-01: volume that is non-numeric, fractional or negative is
    impossible. The reader marks such rows with the original text; a negative
    number arriving by another path is caught by the sign test. A genuinely
    missing volume is not an issue (V-VOL-02, D-03)."""
    mask = frame["volume"].notna() & (frame["volume"] < 0)
    if "volume_invalid_text" in frame.columns:
        mask = mask | frame["volume_invalid_text"].notna()
    return mask.fillna(False).astype(bool)


def _drop_reader_only_columns(frame):
    """The invalid-volume evidence column belongs to quarantine only."""
    return frame.drop(columns=["volume_invalid_text"], errors="ignore")


# --- Main logic: intraday row validation ------------------------------------------
def validate_intraday(standardised, instrument_id, tick_rules=None):
    """Apply the intraday V-PX, V-VOL and V-SES row checks.

    Mutates nothing in the input; returns (records, quarantine, issues)."""
    frame = standardised.records.copy()
    quarantine = standardised.quarantine.copy()
    issues = []

    # V-PX-01 and V-PX-02: impossible rows are quarantined.
    frame, quarantine = _quarantine(frame, _invalid_ohlc_mask(frame),
                                    REASON_INVALID_OHLC, quarantine)
    frame, quarantine = _quarantine(frame, _bad_price_mask(frame),
                                    REASON_BAD_PRICE, quarantine)

    # V-VOL-01: negative, fractional or non-numeric volume is impossible.
    volume_bad = _bad_volume_mask(frame)
    frame, quarantine = _quarantine(frame, volume_bad, REASON_BAD_VOLUME,
                                    quarantine)

    # V-PX-03: tick check, only where a TICK_SIZE rule covers the date.
    # Verified rule: off-tick rows are synthetic (D-11) and quarantined.
    # Unverified rule: flagged OFF_TICK_RULE_UNVERIFIED, never quarantined
    # (G-04, OD-05).
    if tick_rules:
        dates = frame["ts"].dt.date
        off_tick_flagged_dates = set()
        quarantine_idx = []
        for day in dates.unique():
            rule = _applicable_tick_rule(tick_rules, day)
            if rule is None:
                continue
            tick = float(rule["value"])
            day_mask = dates == day
            day_frame = frame.loc[day_mask]
            off = pd.Series(False, index=day_frame.index)
            for column in ("open", "high", "low", "close"):
                off |= _off_tick_mask(day_frame[column], tick)
            if not off.any():
                continue
            if rule.get("verified"):
                quarantine_idx.extend(day_frame.index[off])
            else:
                for idx in day_frame.index[off]:
                    frame.at[idx, "quality_flags"].add(std.FLAG_OFF_TICK)
                off_tick_flagged_dates.add(day)
        if quarantine_idx:
            mask = frame.index.isin(quarantine_idx)
            frame, quarantine = _quarantine(frame, pd.Series(mask, index=frame.index),
                                            REASON_OFF_TICK_SYNTHETIC, quarantine)
        if off_tick_flagged_dates:
            days_text = ", ".join(str(d) for d in sorted(off_tick_flagged_dates))
            issues.append(IssueRecord(
                "V-PX-03", SEVERITY_WARNING,
                "%s: off-tick prices on %d day(s) under an unverified tick "
                "rule; rows stored with %s"
                % (instrument_id, len(off_tick_flagged_dates), std.FLAG_OFF_TICK),
                evidence="days: %s" % days_text))

    # V-PX-04: constant-step runs with frozen High/Low on CANDLE rows.
    fill_days = _flag_constant_step_runs(frame)
    for day, run_count in sorted(fill_days.items()):
        issues.append(IssueRecord(
            "V-PX-04", SEVERITY_WARNING,
            "%s %s: %d constant-step candle run(s) with frozen High/Low; "
            "stored with %s (heuristic, never quarantined)"
            % (instrument_id, day, run_count, std.FLAG_SUSPECT_FILL)))

    # V-VOL-03: volume on an auction record is preserved exactly as supplied,
    # flagged, and excluded from daily volume (DQ-21). One INFO issue per
    # instrument.
    auction_mask = frame["record_type"].isin([std.RECORD_AUCTION_PHASE,
                                              std.RECORD_CLOSING_AUCTION])
    auction_volume = auction_mask & frame["volume"].notna()
    if auction_volume.any():
        for idx in frame.index[auction_volume]:
            frame.at[idx, "quality_flags"].add(std.FLAG_VOLUME_SEMANTICS)
        issues.append(IssueRecord(
            "V-VOL-03", SEVERITY_INFO,
            "%s: %d auction record(s) carry a volume whose meaning is not "
            "established; preserved exactly as supplied and excluded from "
            "daily volume" % (instrument_id, int(auction_volume.sum()))))

    # V-SES-03: a record outside a *confirmed* session is quarantined. On
    # candidate or unrecognised days nothing is quarantined.
    outside_idx = []
    dates = frame["ts"].dt.date
    for day, classification in standardised.day_classes.items():
        if classification.session_status not in (sr.STATUS_CONFIRMED_OFFICIAL,
                                                 sr.STATUS_CONFIRMED_BY_OWNER):
            continue
        day_mask = dates == day
        candle_mask = day_mask & (frame["record_type"] == std.RECORD_CANDLE)
        times = frame.loc[candle_mask, "ts"].dt.time
        bad = ((times < classification.session_open)
               | (times > classification.last_candle_time))
        outside_idx.extend(times.index[bad])
    if outside_idx:
        mask = pd.Series(frame.index.isin(outside_idx), index=frame.index)
        frame, quarantine = _quarantine(frame, mask, REASON_OUTSIDE_SESSION,
                                        quarantine)

    frame = frame.reset_index(drop=True)

    # Defensive unique-key check: duplicate keys are impossible in canonical
    # data (02 section 4.1); a violation here is a programming error.
    if frame["ts"].duplicated().any():
        raise AssertionError("duplicate (instrument, ts) key after "
                             "standardisation of %s" % instrument_id)
    return _drop_reader_only_columns(frame), quarantine, issues


def _flag_constant_step_runs(frame):
    """Flag SUSPECT_FILL on runs of >= 3 consecutive CANDLE rows whose closes
    move by one identical step while High and Low stay frozen. Returns
    {date: run_count}. Heuristic only: flags, never quarantines (OD-05)."""
    fill_days = {}
    candles = frame[frame["record_type"] == std.RECORD_CANDLE]
    for day, day_rows in candles.groupby(candles["ts"].dt.date):
        ordered = day_rows.sort_values("ts")
        closes = ordered["close"].to_numpy()
        highs = ordered["high"].to_numpy()
        lows = ordered["low"].to_numpy()
        indices = ordered.index.to_numpy()
        n = len(ordered)
        run_count = 0
        start = 0
        while start < n - 2:
            step = closes[start + 1] - closes[start]
            end = start + 1
            while (end + 1 < n
                   and abs((closes[end + 1] - closes[end]) - step) <= _PRICE_TOLERANCE
                   and highs[end + 1] == highs[start]
                   and lows[end + 1] == lows[start]):
                end += 1
            # The run start must share the frozen High/Low as well.
            if (end - start + 1 >= MIN_CONSTANT_STEP_RUN
                    and highs[start] == highs[start + 1]
                    and lows[start] == lows[start + 1]):
                for idx in indices[start:end + 1]:
                    frame.at[idx, "quality_flags"].add(std.FLAG_SUSPECT_FILL)
                run_count += 1
                start = end + 1
            else:
                start += 1
        if run_count:
            fill_days[day] = run_count
    return fill_days


# --- Main logic: daily row validation ---------------------------------------------
def validate_daily(standardised, instrument_id):
    """Apply the daily V-PX and V-VOL checks, including G-03 (V-PX-05)."""
    frame = standardised.records.copy()
    quarantine = standardised.quarantine.copy()
    issues = []

    frame, quarantine = _quarantine(frame, _invalid_ohlc_mask(frame),
                                    REASON_INVALID_OHLC, quarantine)
    frame, quarantine = _quarantine(frame, _bad_price_mask(frame),
                                    REASON_BAD_PRICE, quarantine)
    volume_bad = _bad_volume_mask(frame)
    frame, quarantine = _quarantine(frame, volume_bad, REASON_BAD_VOLUME,
                                    quarantine)
    frame = frame.sort_values("trade_date").reset_index(drop=True)

    # V-PX-05 (G-03, Owner-approved): every day-to-day open OR close move
    # beyond +/-15% is stored unchanged, flagged, and opens an issue with
    # affects_continuity = true. Only the Owner's VERIFIED_OK unblocks it.
    prev_close = frame["close"].shift(1)
    open_pct = (frame["open"] - prev_close) / prev_close * 100.0
    close_pct = (frame["close"] - prev_close) / prev_close * 100.0
    beyond = ((open_pct.abs() > LARGE_MOVE_PERCENT)
              | (close_pct.abs() > LARGE_MOVE_PERCENT)) & prev_close.notna()
    for idx in frame.index[beyond]:
        day = frame.at[idx, "trade_date"]
        o_pct, c_pct = float(open_pct.at[idx]), float(close_pct.at[idx])
        is_level_break = abs(c_pct) > LEVEL_BREAK_PERCENT
        flag = std.FLAG_LEVEL_BREAK if is_level_break else std.FLAG_LARGE_GAP
        frame.at[idx, "quality_flags"].add(flag)
        kind = ("level break (possible rebase)" if is_level_break
                else "large day-to-day move")
        issues.append(IssueRecord(
            "V-PX-05", SEVERITY_WARNING,
            "%s %s: %s beyond +/-15%%; stored unchanged with %s; blocks "
            "continuity-dependent calculations until the Owner verifies it "
            "(G-03)" % (instrument_id, day, kind, flag),
            evidence=("prev_close=%s open=%s close=%s open_change=%.2f%% "
                      "close_change=%.2f%%"
                      % (prev_close.at[idx], frame.at[idx, "open"],
                         frame.at[idx, "close"], o_pct, c_pct)),
            ts_from=datetime.combine(day, datetime.min.time()),
            ts_to=datetime.combine(day, datetime.min.time()),
            affects_continuity=True))

    if frame["trade_date"].duplicated().any():
        raise AssertionError("duplicate (instrument, trade_date) key after "
                             "standardisation of %s" % instrument_id)
    return _drop_reader_only_columns(frame), quarantine, issues


# --- Main logic: intraday completeness (day profiles) ------------------------------
def build_day_profiles(records, quarantine, day_classes, instrument_id):
    """Measure completeness per day against the classified expectation
    (document 02 section 8). Expectations come from the session status, never
    from the observed records alone. Returns (profile_rows, issues)."""
    issues = []
    profiles = []
    dates = records["ts"].dt.date
    quarantine_dates = (quarantine["ts"].dt.date if len(quarantine) else
                        pd.Series(dtype=object))

    for day in sorted(day_classes):
        classification = day_classes[day]
        day_mask = dates == day
        day_rows = records.loc[day_mask]
        candles = day_rows[day_rows["record_type"] == std.RECORD_CANDLE]
        window_start = datetime.combine(day, classification.session_open)
        window_end = datetime.combine(day, classification.last_candle_time)

        expected = sr.expected_minutes(classification)
        in_window = candles[(candles["ts"] >= window_start)
                            & (candles["ts"] <= window_end)]
        present = len(in_window)
        present_minutes = set(in_window["ts"].tolist())
        all_minutes = [window_start + timedelta(minutes=i)
                       for i in range(expected)]
        missing = [m for m in all_minutes if m not in present_minutes]
        missing_text = _compress_minutes_to_ranges(missing)

        has_phase = bool((day_rows["record_type"]
                          == std.RECORD_AUCTION_PHASE).any())
        has_closing = bool((day_rows["record_type"]
                            == std.RECORD_CLOSING_AUCTION).any())
        has_volume = bool(candles["volume"].notna().any())
        quarantined = int((quarantine_dates == day).sum()) if len(quarantine) else 0

        profiles.append({
            "instrument_id": instrument_id,
            "trade_date": day,
            "observed_shape": classification.observed_shape,
            "session_status": classification.session_status,
            "session_type": classification.session_type,
            "first_record": day_rows["source_ts"].min().time(),
            "last_continuous_candle": (in_window["ts"].max().time()
                                       if present else None),
            "expected_candles": expected,
            "expected_basis": classification.expected_basis,
            "present_candles": present,
            "missing_candles": len(missing),
            "missing_ranges": missing_text,
            "has_auction_phase": has_phase,
            "has_closing_auction": has_closing,
            "has_volume": has_volume,
            "quarantined_rows": quarantined,
        })

        # V-SES-01: unrecognised days ask the Owner a question; missing data
        # there is only "possible", because the session is unconfirmed.
        if classification.session_status == sr.STATUS_UNRECOGNISED:
            issues.append(IssueRecord(
                "V-SES-01", SEVERITY_WARNING,
                "%s %s: session shape not recognised (records %s-%s). "
                "Special session, or truncated data? Possible missing data: %s"
                % (instrument_id, day,
                   day_rows["source_ts"].min().strftime("%H:%M"),
                   day_rows["source_ts"].max().strftime("%H:%M"),
                   missing_text or "none"),
                ts_from=window_start, ts_to=window_end))
        elif classification.session_status == sr.STATUS_CANDIDATE \
                and classification.session_type == sr.TYPE_CAS:
            issues.append(IssueRecord(
                "V-SES-01", SEVERITY_INFO,
                "%s %s: CAS candidate awaiting confirmation" % (instrument_id,
                                                                day)))

        # V-SES-02: missing candles inside a recognised continuous session,
        # grouped into one issue per day.
        if missing and classification.session_status != sr.STATUS_UNRECOGNISED:
            issues.append(IssueRecord(
                "V-SES-02", SEVERITY_WARNING,
                "%s %s: %d missing candle(s) inside the session: %s"
                % (instrument_id, day, len(missing), missing_text),
                ts_from=window_start, ts_to=window_end))

    return profiles, issues
