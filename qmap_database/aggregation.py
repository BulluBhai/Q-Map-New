"""Timeframe aggregation (document 03 v1.2, Part B).

One-minute data is the source of truth; aggregation is computed on request
and nothing is stored (TC-11). Only real data is aggregated: missing minutes
are never filled, an interval with no data produces no bar, and aggregation
never crosses a session. Auction records are never merged into intraday
candles (D-08) but are included in the daily bar (D-07, D-10); their volumes
are never added to daily volume (DQ-21, R-5).
"""

# --- Imports -----------------------------------------------------------------
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd

from .errors import DataIntegrityError

# --- Constants ---------------------------------------------------------------
RECORD_CANDLE = "CANDLE"
RECORD_AUCTION_PHASE = "AUCTION_PHASE"
RECORD_CLOSING_AUCTION = "CLOSING_AUCTION"

FLAG_VOLUME_EXCLUDES_AUCTION = "VOLUME_EXCLUDES_AUCTION"

BAR_COLUMNS = ["ts", "record_type", "open", "high", "low", "close", "volume",
               "expected_units", "present_units", "is_complete", "is_forming",
               "session_truncated", "volume_complete", "quality_flags",
               "source_ts"]


# --- Data structures ------------------------------------------------------------
@dataclass
class DayWindow:
    """The continuous-trading window aggregation uses for one day, derived
    from the day's recorded session status - never from the observed records
    alone (03 section B3)."""
    trade_date: date
    window_open: time          # first continuous-trading minute
    expected_minutes: int      # length of the continuous window
    session_status: str
    session_type: str          # may be None (unrecognised)
    is_cas: bool               # a CAS-type day: closing auction expected

    @property
    def open_dt(self):
        return datetime.combine(self.trade_date, self.window_open)

    @property
    def end_dt(self):
        """Start of the last expected candle."""
        return self.open_dt + timedelta(minutes=self.expected_minutes - 1)


# --- Helpers ---------------------------------------------------------------------
def _flags_to_set(text):
    return set(text.split(";")) if isinstance(text, str) and text else set()


def _union_flags(series):
    combined = set()
    for text in series:
        combined |= _flags_to_set(text)
    return ";".join(sorted(combined)) if combined else ""


def _assert_unique(keys, what):
    """Duplicate keys are impossible in canonical data (02 section 4); a
    duplicate here means corrupted storage, so reading stops."""
    if keys.duplicated().any():
        raise DataIntegrityError(
            "duplicate %s found in stored data. Run 'Check integrity' in the "
            "Data Manager." % what)


def _empty_bars():
    frame = pd.DataFrame(columns=BAR_COLUMNS)
    return frame


def _finish_bar_frame(rows):
    if not rows:
        return _empty_bars()
    frame = pd.DataFrame(rows, columns=BAR_COLUMNS)
    frame["volume"] = frame["volume"].astype("Int64")
    frame["expected_units"] = frame["expected_units"].astype("Int64")
    frame["present_units"] = frame["present_units"].astype("Int64")
    return frame.sort_values("ts").reset_index(drop=True)


def day_is_closed(day_records, window):
    """A day is closed when its last expected continuous candle or a closing
    auction is present (03 section B6)."""
    if (day_records["record_type"] == RECORD_CLOSING_AUCTION).any():
        return True
    return bool((day_records["ts"] == window.end_dt).any())


# --- Main logic: intraday N-minute bars (B4, B5, B6) ---------------------------------
def aggregate_intraday(records, day_windows, minutes,
                       include_auction_records=True, exclude_flagged=False,
                       latest_stored_day=None, latest_day_closed=True):
    """Build N-minute bars from canonical 1-minute records.

    `records`: canonical rows (ts, record_type, open..volume, quality_flags,
    source_ts) covering whole days. `day_windows`: {date: DayWindow}.
    `latest_stored_day` / `latest_day_closed` describe the instrument's last
    stored day, for the forming-bar rule."""
    _assert_unique(records["ts"], "(instrument, ts) key")
    rows = []
    dates = records["ts"].dt.date

    for day, day_records in records.groupby(dates):
        window = day_windows.get(day)
        if window is None:
            continue
        candles = day_records[day_records["record_type"] == RECORD_CANDLE]
        if exclude_flagged:
            # Flagged source rows are treated as missing (A4); never repaired.
            flagged = candles["quality_flags"].map(
                lambda text: bool(_flags_to_set(text)))
            candles = candles[~flagged]

        window_open = window.open_dt
        window_end = window.end_dt
        last_stored_minute = (day_records["ts"].max()
                              if len(day_records) else None)
        forming_day = (day == latest_stored_day and not latest_day_closed)

        if len(candles):
            offsets = ((candles["ts"] - window_open)
                       .dt.total_seconds() // 60).astype(int)
            buckets = offsets // minutes
            for bucket, bucket_rows in candles.groupby(buckets):
                bucket_rows = bucket_rows.sort_values("ts")
                interval_start = window_open + timedelta(
                    minutes=int(bucket) * minutes)
                interval_end_excl = interval_start + timedelta(minutes=minutes)
                # Expected units: minutes of the continuous window inside the
                # interval (B5); the last interval of a session may be shorter.
                overlap_start = max(interval_start, window_open)
                overlap_end = min(interval_end_excl,
                                  window_end + timedelta(minutes=1))
                expected = max(0, int((overlap_end - overlap_start)
                                      .total_seconds() // 60))
                present = len(bucket_rows)
                volumes = bucket_rows["volume"].dropna()
                volume = int(volumes.sum()) if len(volumes) else None
                is_complete = present == expected and expected > 0
                is_forming = (forming_day and last_stored_minute is not None
                              and not is_complete
                              and interval_end_excl > last_stored_minute)
                rows.append([
                    interval_start, RECORD_CANDLE,
                    float(bucket_rows["open"].iloc[0]),
                    float(bucket_rows["high"].max()),
                    float(bucket_rows["low"].min()),
                    float(bucket_rows["close"].iloc[-1]),
                    volume, expected, present, is_complete, is_forming,
                    expected < minutes and expected > 0,
                    bool(len(volumes) == present and is_complete),
                    _union_flags(bucket_rows["quality_flags"]), None])

        if include_auction_records:
            auctions = day_records[day_records["record_type"].isin(
                [RECORD_AUCTION_PHASE, RECORD_CLOSING_AUCTION])]
            for _, record in auctions.sort_values("ts").iterrows():
                volume = (int(record["volume"])
                          if pd.notna(record["volume"]) else None)
                rows.append([
                    record["ts"], record["record_type"], record["open"],
                    record["high"], record["low"], record["close"], volume,
                    None, None, True, False, False, True,
                    record["quality_flags"] or "", record["source_ts"]])
    return _finish_bar_frame(rows)


# --- Main logic: daily bars from 1-minute data (B7) -----------------------------------
def daily_bars_from_intraday(records, day_windows, exclude_flagged=False,
                             latest_stored_day=None, latest_day_closed=True):
    """One daily bar per stored day. High/Low cover candle AND auction records
    (D-07, D-10); close is the closing auction when present; volume sums
    CANDLE rows only, never the auction records (DQ-21; T-AGG-13)."""
    _assert_unique(records["ts"], "(instrument, ts) key")
    rows = []
    dates = records["ts"].dt.date
    for day, day_records in records.groupby(dates):
        window = day_windows.get(day)
        if window is None:
            continue
        candles = day_records[day_records["record_type"] == RECORD_CANDLE]
        if exclude_flagged:
            flagged = candles["quality_flags"].map(
                lambda text: bool(_flags_to_set(text)))
            candles = candles[~flagged]
        if len(candles) == 0 and len(day_records) == 0:
            continue
        auctions = day_records[day_records["record_type"].isin(
            [RECORD_AUCTION_PHASE, RECORD_CLOSING_AUCTION])]
        closing = day_records[day_records["record_type"]
                              == RECORD_CLOSING_AUCTION]
        price_rows = pd.concat([candles, auctions]) if len(auctions) \
            else candles
        if len(price_rows) == 0:
            continue
        candles = candles.sort_values("ts")
        open_value = (float(candles["open"].iloc[0]) if len(candles)
                      else float(price_rows.sort_values("ts")["open"].iloc[0]))
        close_value = (float(closing["close"].iloc[-1]) if len(closing)
                       else float(candles["close"].iloc[-1]) if len(candles)
                       else float(price_rows.sort_values("ts")["close"].iloc[-1]))
        volumes = candles["volume"].dropna()
        volume = int(volumes.sum()) if len(volumes) else None
        auction_volume_present = bool(auctions["volume"].notna().any())

        expected = window.expected_minutes
        present = len(candles)
        is_complete = (present == expected
                       and (not window.is_cas or len(closing) > 0))
        flags = set(_flags_to_set(_union_flags(price_rows["quality_flags"])))
        volume_complete = (len(volumes) == present and is_complete
                           and not auction_volume_present)
        if auction_volume_present:
            # The true daily total is uncertain while the auction-volume
            # meaning is unverified (V-09), so the bar says so explicitly.
            flags.add(FLAG_VOLUME_EXCLUDES_AUCTION)
        forming_day = (day == latest_stored_day and not latest_day_closed)
        rows.append([
            datetime.combine(day, time(0, 0)), "DAY", open_value,
            float(price_rows["high"].max()), float(price_rows["low"].min()),
            close_value, volume, expected, present, is_complete,
            forming_day and not is_complete, False, volume_complete,
            ";".join(sorted(flags)) if flags else "", None])
    return _finish_bar_frame(rows)


# --- Main logic: daily bars from stored daily data -------------------------------------
def daily_bars_from_daily(records):
    """Stored daily rows become DAY bars one for one. Nothing is known about
    intraday completeness, so each bar counts itself as its only unit."""
    _assert_unique(records["trade_date"], "(instrument, trade_date) key")
    rows = []
    for _, record in records.sort_values("trade_date").iterrows():
        volume = (int(record["volume"]) if pd.notna(record["volume"])
                  else None)
        rows.append([
            datetime.combine(record["trade_date"], time(0, 0)), "DAY",
            float(record["open"]), float(record["high"]),
            float(record["low"]), float(record["close"]), volume, 1, 1, True,
            False, False, volume is not None,
            record["quality_flags"] or "", None])
    return _finish_bar_frame(rows)


# --- Main logic: weekly and monthly bars (B8) --------------------------------------------
def _period_key(day, timeframe):
    if timeframe == "1W":
        return day - timedelta(days=day.weekday())      # Monday of the week
    return date(day.year, day.month, 1)                 # calendar month


def _period_last_day(period_start, timeframe):
    if timeframe == "1W":
        return period_start + timedelta(days=6)
    if period_start.month == 12:
        return date(period_start.year, 12, 31)
    return date(period_start.year, period_start.month + 1, 1) \
        - timedelta(days=1)


def aggregate_periods(daily_bars, timeframe, trading_days_fn,
                      last_stored_date=None):
    """Weekly (Monday-Sunday) and monthly (calendar month) bars from daily
    bars, labelled with the period's first trading date. `trading_days_fn`
    (period_start, period_end) -> expected trading-day count, from the
    calendar."""
    if len(daily_bars) == 0:
        return _empty_bars()
    rows = []
    days = daily_bars["ts"].dt.date
    for period_start, period_rows in daily_bars.groupby(
            days.map(lambda d: _period_key(d, timeframe))):
        period_rows = period_rows.sort_values("ts")
        period_end = _period_last_day(period_start, timeframe)
        expected = trading_days_fn(period_start, period_end)
        present = len(period_rows)
        volumes = period_rows["volume"].dropna()
        volume = int(volumes.sum()) if len(volumes) else None
        is_forming = (last_stored_date is not None
                      and period_end > last_stored_date)
        flags = _union_flags(period_rows["quality_flags"])
        rows.append([
            period_rows["ts"].iloc[0],                 # first trading date
            "WEEK" if timeframe == "1W" else "MONTH",
            float(period_rows["open"].iloc[0]),
            float(period_rows["high"].max()),
            float(period_rows["low"].min()),
            float(period_rows["close"].iloc[-1]),
            volume, expected, present,
            present == expected and not is_forming, is_forming, False,
            bool(len(volumes) == present
                 and period_rows["volume_complete"].all()),
            flags, None])
    return _finish_bar_frame(rows)
