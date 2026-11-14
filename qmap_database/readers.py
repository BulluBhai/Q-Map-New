"""Source-file readers R1 to R4 (document 02 v1.6, section 6.1).

A file is matched to a reader by its structure, never by trusting its name.
Each reader parses one inspected source format into a raw pandas frame with
standard column names. Readers decide nothing about validity beyond the
file-level checks assigned to them (V-FILE-01, V-SCH-01, V-TS-01 and the
1-minute resolution test TC-26); row-level validation happens later.

Readers never write files.
"""

# --- Imports -----------------------------------------------------------------
import hashlib
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from .errors import FileImportError

# --- Constants ---------------------------------------------------------------
READER_R1 = "R1"  # master-style 1-minute Parquet
READER_R2 = "R2"  # vendor 1-minute CSV with header, ISO 8601 +05:30
READER_R3 = "R3"  # headerless daily text, 6 or 7 fields
READER_R4 = "R4"  # daily Parquet

REQUIRED_PRICE_COLUMNS = ("open", "high", "low", "close")
IST_OFFSET_TEXT = "+05:30"

# TC-26 resolution test: a file counts as 1-minute data only when the most
# common within-day timestamp step is exactly one minute, over at least this
# many within-day gaps. Missing minutes make some gaps larger but never change
# the most common step, so genuine 1-minute files are never rejected for gaps.
MIN_WITHIN_DAY_GAPS = 30
ONE_MINUTE_SECONDS = 60.0

# A day inside an accepted 1-minute file is suspect when it has at least this
# many records and its own most common step is 2 minutes or more (section 6.1
# rule 6): kept unchanged, reported as RESOLUTION_SUSPECT.
MIN_RECORDS_FOR_DAY_RESOLUTION = 10


# --- Result structure ---------------------------------------------------------
@dataclass
class ReaderResult:
    """What a reader hands to standardisation."""
    reader_id: str
    is_intraday: bool
    frame: pd.DataFrame            # intraday: ts/open/high/low/close/volume/source_row
                                   # daily: trade_date/open/high/low/close/volume/source_row
    ignored_columns: list = field(default_factory=list)   # V-SCH-02 INFO
    resolution_suspect_days: list = field(default_factory=list)  # dates
    notes: list = field(default_factory=list)


# --- Helpers ------------------------------------------------------------------
def sha256_of_file(path):
    """Return the SHA-256 hex digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_column(columns, wanted):
    """Find a column by name without regard to letter case; None if absent."""
    lowered = {str(name).lower(): name for name in columns}
    return lowered.get(wanted.lower())


def _require_price_columns(columns, file_name):
    """Map the required OHLC columns case-insensitively or fail the file."""
    mapping = {}
    for wanted in REQUIRED_PRICE_COLUMNS:
        actual = _find_column(columns, wanted)
        if actual is None:
            raise FileImportError(
                "%s is missing the required column '%s'. "
                "The file was not imported." % (file_name, wanted),
                check_code="V-SCH-01")
        mapping[wanted] = actual
    return mapping


def _to_nullable_volume(series):
    """Convert a volume column to nullable Int64 without inventing values."""
    if series is None:
        return None
    try:
        return series.astype("Int64")
    except (TypeError, ValueError):
        # Fractional or textual volumes cannot be whole numbers; let the
        # row-level V-VOL-01 check see them by keeping the raw values.
        numeric = pd.to_numeric(series, errors="coerce")
        whole = numeric.dropna() % 1 == 0
        if whole.all():
            return numeric.astype("Int64")
        raise FileImportError(
            "volume column contains non-numeric or fractional values",
            check_code="V-FILE-01")


def most_common_within_day_step_seconds(ts_values):
    """Return (most common within-day step in seconds, within-day gap count).

    Gaps across days are ignored, so overnight breaks, holidays, CAS jumps and
    missing minutes do not influence the result (TC-26). Seconds are used so
    the comparison does not depend on the frame's timestamp resolution."""
    ordered = ts_values.sort_values()
    diffs = ordered.diff()
    same_day = ordered.dt.normalize() == ordered.dt.normalize().shift()
    within = diffs[same_day.fillna(False)]
    within = within.dropna()
    if len(within) == 0:
        return None, 0
    counts = Counter(within.dt.total_seconds())
    step, _ = counts.most_common(1)[0]
    return step, len(within)


def _check_one_minute_resolution(frame, file_name):
    """Apply the TC-26 resolution test; return RESOLUTION_SUSPECT day list."""
    step, gap_count = most_common_within_day_step_seconds(frame["ts"])
    if gap_count < MIN_WITHIN_DAY_GAPS or step is None:
        raise FileImportError(
            "%s: cannot establish 1-minute resolution (only %d within-day "
            "time steps found). The file was not imported."
            % (file_name, gap_count), check_code="V-FILE-01")
    if step != ONE_MINUTE_SECONDS:
        minutes = step / ONE_MINUTE_SECONDS
        minutes_text = ("%d" % minutes) if minutes == int(minutes) else ("%.2f" % minutes)
        raise FileImportError(
            "%s: most common time step is %s minutes; 1-minute data required. "
            "The file was not imported." % (file_name, minutes_text),
            check_code="V-FILE-01")

    # Per-day check: a coarser day inside an accepted file is kept unchanged
    # but reported, never resampled or deleted (section 6.1 rule 6).
    suspect_days = []
    for day, day_ts in frame["ts"].groupby(frame["ts"].dt.date):
        if len(day_ts) < MIN_RECORDS_FOR_DAY_RESOLUTION:
            continue
        diffs = day_ts.sort_values().diff().dropna()
        if len(diffs) == 0:
            continue
        day_step, _ = Counter(diffs.dt.total_seconds()).most_common(1)[0]
        if day_step >= 2 * ONE_MINUTE_SECONDS:
            suspect_days.append(day)
    return suspect_days


def _parse_iso_date(text, file_name, line_no):
    """Parse a strict YYYY-MM-DD date; two-digit years are ambiguous for
    history reaching 1998 and are refused."""
    parts = text.split("-")
    if len(parts) != 3 or len(parts[0]) != 4:
        raise FileImportError(
            "%s line %d: '%s' is not a YYYY-MM-DD date. "
            "The file was not imported." % (file_name, line_no, text),
            check_code="V-TS-01")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as exc:
        raise FileImportError(
            "%s line %d: invalid date '%s' (%s). The file was not imported."
            % (file_name, line_no, text, exc), check_code="V-TS-01")


# --- Reader R1: master-style 1-minute Parquet ----------------------------------
def _read_r1_r4_parquet(path):
    """Shared Parquet reading for R1 and R4; returns (frame, ignored, name)."""
    file_name = os.path.basename(path)
    try:
        raw = pd.read_parquet(path)
    except Exception as exc:
        raise FileImportError(
            "%s is incomplete or damaged and could not be read (%s). "
            "The file was not imported." % (file_name, exc),
            check_code="V-FILE-01")

    time_col = _find_column(raw.columns, "datetime")
    if time_col is None:
        raise FileImportError(
            "%s has no 'datetime' timestamp column. The file was not imported."
            % file_name, check_code="V-SCH-01")
    price_map = _require_price_columns(raw.columns, file_name)
    volume_col = _find_column(raw.columns, "volume")

    used = {time_col, volume_col} | set(price_map.values())
    ignored = [str(c) for c in raw.columns if c not in used]

    ts = pd.to_datetime(raw[time_col])
    if ts.isna().any():
        raise FileImportError(
            "%s contains an unparseable timestamp. The file was not imported."
            % file_name, check_code="V-TS-01")
    if ts.dt.tz is not None:
        # An explicit offset is checked and removed; wall-clock values stay IST.
        offsets = ts.dt.strftime("%z").unique()
        if any(off not in ("+0530",) for off in offsets):
            raise FileImportError(
                "%s: time offset %s is not IST (+05:30). The file was not "
                "imported." % (file_name, offsets[0]), check_code="V-TS-01")
        ts = ts.dt.tz_localize(None)

    frame = pd.DataFrame({
        "ts": ts.astype("datetime64[us]"),
        "open": raw[price_map["open"]].astype("float64"),
        "high": raw[price_map["high"]].astype("float64"),
        "low": raw[price_map["low"]].astype("float64"),
        "close": raw[price_map["close"]].astype("float64"),
    })
    frame["volume"] = (_to_nullable_volume(raw[volume_col])
                       if volume_col is not None else pd.array([None] * len(raw),
                                                               dtype="Int64"))
    frame["source_row"] = range(1, len(frame) + 1)
    return frame, ignored, file_name


def read_r1(path):
    """R1: 1-minute Parquet, subject to the TC-26 resolution test."""
    frame, ignored, file_name = _read_r1_r4_parquet(path)
    suspect_days = _check_one_minute_resolution(frame, file_name)
    return ReaderResult(READER_R1, True, frame, ignored_columns=ignored,
                        resolution_suspect_days=suspect_days)


# --- Reader R2: vendor 1-minute CSV --------------------------------------------
def read_r2(path):
    """R2: vendor CSV with header; `time` in ISO 8601 with +05:30."""
    file_name = os.path.basename(path)
    try:
        raw = pd.read_csv(path, dtype=str)
    except Exception as exc:
        raise FileImportError(
            "%s is incomplete or damaged and could not be read (%s). "
            "The file was not imported." % (file_name, exc),
            check_code="V-FILE-01")

    time_col = _find_column(raw.columns, "time")
    if time_col is None:
        raise FileImportError(
            "%s has no 'time' column. The file was not imported." % file_name,
            check_code="V-SCH-01")
    price_map = _require_price_columns(raw.columns, file_name)
    volume_col = _find_column(raw.columns, "volume")
    used = {time_col, volume_col} | set(price_map.values())
    ignored = [str(c) for c in raw.columns if c not in used]

    times = raw[time_col].astype(str)
    # An explicit offset must be IST; any other offset fails the file (V-TS-01).
    has_offset = times.str.contains(r"[+-]\d{2}:\d{2}$", regex=True)
    if has_offset.any():
        offsets = times[has_offset].str[-6:]
        wrong = offsets[offsets != IST_OFFSET_TEXT]
        if len(wrong) > 0:
            raise FileImportError(
                "%s: time offset %s is not IST (%s). The file was not imported."
                % (file_name, wrong.iloc[0], IST_OFFSET_TEXT),
                check_code="V-TS-01")
        times = times.where(~has_offset, times.str[:-6])

    ts = pd.to_datetime(times, errors="coerce")
    if ts.isna().any():
        bad_row = int(ts[ts.isna()].index[0]) + 2  # +1 header, +1 one-based
        raise FileImportError(
            "%s line %d: timestamp could not be parsed. The file was not "
            "imported." % (file_name, bad_row), check_code="V-TS-01")

    try:
        frame = pd.DataFrame({
            "ts": ts.astype("datetime64[us]"),
            "open": raw[price_map["open"]].astype("float64"),
            "high": raw[price_map["high"]].astype("float64"),
            "low": raw[price_map["low"]].astype("float64"),
            "close": raw[price_map["close"]].astype("float64"),
        })
    except ValueError as exc:
        raise FileImportError(
            "%s contains a non-numeric price value (%s). The file was not "
            "imported." % (file_name, exc), check_code="V-FILE-01")
    if volume_col is not None:
        try:
            frame["volume"] = _to_nullable_volume(
                pd.to_numeric(raw[volume_col], errors="raise"))
        except (TypeError, ValueError) as exc:
            raise FileImportError(
                "%s contains a non-numeric volume value (%s). The file was "
                "not imported." % (file_name, exc), check_code="V-FILE-01")
    else:
        frame["volume"] = pd.array([None] * len(raw), dtype="Int64")
    frame["source_row"] = range(1, len(frame) + 1)

    suspect_days = _check_one_minute_resolution(frame, file_name)
    return ReaderResult(READER_R2, True, frame, ignored_columns=ignored,
                        resolution_suspect_days=suspect_days)


# --- Reader R3: headerless daily text -------------------------------------------
def read_r3(path):
    """R3: headerless daily text, `YYYY-MM-DD,O,H,L,C,Volume[,field7]`.

    Both 6- and 7-field lines are accepted in one file; field 7 is read and
    ignored (D-01, D-02). A line with any other field count fails the whole
    file, naming the line (V-FILE-01, message style of document 02 section 11).
    """
    file_name = os.path.basename(path)
    rows = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            raw_lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise FileImportError(
            "%s could not be read (%s). The file was not imported."
            % (file_name, exc), check_code="V-FILE-01")

    for line_no, line in enumerate(raw_lines, start=1):
        line = line.strip()
        if not line:
            continue
        fields = line.split(",")
        if len(fields) not in (6, 7):
            raise FileImportError(
                "%s could not be read: line %d has %d fields; expected 6 or 7. "
                "The file was not imported." % (file_name, line_no, len(fields)),
                check_code="V-FILE-01")
        trade_date = _parse_iso_date(fields[0], file_name, line_no)
        try:
            prices = [float(value) for value in fields[1:5]]
            volume = int(fields[5])
        except ValueError:
            raise FileImportError(
                "%s line %d: a price or volume value is not a number. "
                "The file was not imported." % (file_name, line_no),
                check_code="V-FILE-01")
        # Field 7 (fields[6]) is read and ignored per D-01/D-02.
        rows.append((trade_date, prices[0], prices[1], prices[2], prices[3],
                     volume, line_no))

    if not rows:
        raise FileImportError(
            "%s contains no data lines. The file was not imported." % file_name,
            check_code="V-FILE-01")

    frame = pd.DataFrame(rows, columns=["trade_date", "open", "high", "low",
                                        "close", "volume", "source_row"])
    frame["volume"] = frame["volume"].astype("Int64")
    seven_field_lines = sum(1 for line in raw_lines
                            if line.strip() and len(line.split(",")) == 7)
    notes = []
    if seven_field_lines:
        notes.append("field 7 present on %d lines; read and ignored (D-01)"
                     % seven_field_lines)
    return ReaderResult(READER_R3, False, frame, notes=notes)


# --- Reader R4: daily Parquet ----------------------------------------------------
def read_r4(path):
    """R4: daily Parquet with `datetime` at 00:00 plus OHLC and Volume."""
    frame, ignored, file_name = _read_r1_r4_parquet(path)
    not_midnight = frame["ts"] != frame["ts"].dt.normalize()
    if not_midnight.any():
        raise FileImportError(
            "%s: a daily file must carry time 00:00 on every row. "
            "The file was not imported." % file_name, check_code="V-TS-01")
    daily = pd.DataFrame({
        "trade_date": frame["ts"].dt.date,
        "open": frame["open"], "high": frame["high"],
        "low": frame["low"], "close": frame["close"],
        "volume": frame["volume"], "source_row": frame["source_row"],
    })
    return ReaderResult(READER_R4, False, daily, ignored_columns=ignored)


# --- Main logic: structural reader selection -------------------------------------
def detect_and_read(path, expect_intraday):
    """Choose the reader from the file's structure and read it.

    `expect_intraday` comes from the instrument's dataset (base timeframe):
    an intraday dataset requires 1-minute data (R1/R2), a daily dataset daily
    data (R3/R4). A mismatch is a file-level error, which is how a derived
    multi-minute file mapped to an intraday instrument is refused (T-FILE-06).
    """
    file_name = os.path.basename(path)
    extension = os.path.splitext(path)[1].lower()

    if extension == ".parquet":
        frame, ignored, _ = _read_r1_r4_parquet(path)
        all_midnight = bool((frame["ts"] == frame["ts"].dt.normalize()).all())
        if expect_intraday:
            if all_midnight and len(frame) > 0:
                raise FileImportError(
                    "%s carries daily timestamps (00:00); 1-minute data "
                    "required. The file was not imported." % file_name,
                    check_code="V-FILE-01")
            suspect_days = _check_one_minute_resolution(frame, file_name)
            return ReaderResult(READER_R1, True, frame, ignored_columns=ignored,
                                resolution_suspect_days=suspect_days)
        if not all_midnight:
            raise FileImportError(
                "%s carries intraday timestamps; daily data required for this "
                "instrument. The file was not imported." % file_name,
                check_code="V-FILE-01")
        return read_r4(path)

    if extension == ".csv":
        if not expect_intraday:
            raise FileImportError(
                "%s: the vendor CSV format holds 1-minute data, but this "
                "instrument's dataset is daily. The file was not imported."
                % file_name, check_code="V-FILE-01")
        return read_r2(path)

    if extension == ".txt":
        if expect_intraday:
            raise FileImportError(
                "%s: the daily text format cannot supply 1-minute data. "
                "The file was not imported." % file_name,
                check_code="V-FILE-01")
        return read_r3(path)

    raise FileImportError(
        "%s has an unsupported file type '%s'. Supported: .parquet, .csv, "
        ".txt. The file was not imported." % (file_name, extension),
        check_code="V-FILE-01")
