"""Q-MAP stock-universe inventory (G-01; document 09 v1.6, sections 3 and 8).

Exploratory and READ-ONLY. It is not a Q-MAP module and never touches the
Q-MAP database. It reads every file in the chosen stock folder (and its
subfolders) and writes exactly one Excel workbook:
    Q-MAP_Universe_Inventory_<dd_mmm_yy_hhmmss>.xlsx

How to run: open this file in IDLE or Thonny and press F5. Choose the stock
folder, choose where to save the workbook, press Run.

Packages: pandas, pyarrow, openpyxl (no DuckDB). Nothing is repaired, filled,
selected or merged; duplicate-source conflicts (G-16) and +/-15% moves (G-03)
are only reported for the Owner's review.
"""

# --- Imports -----------------------------------------------------------------
import hashlib
import math
import os
import platform
import queue
import re
import statistics
import sys
import threading
import time
import traceback
from collections import Counter, defaultdict
from datetime import date, datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Constants ---------------------------------------------------------------
SCRIPT_VERSION = "1.0.0"
WINDOW_TITLE = "Q-MAP Universe Inventory (read-only)"

SUPPORTED_EXTENSIONS = (".txt", ".csv", ".parquet")
LARGE_MOVE_PCT = 15.0           # V-PX-05 / G-03
PLACEHOLDER_RUN = 20            # identical consecutive volumes
EMA_BARS = 800                  # D-EMA-08
LONG_HISTORY_BARS = 2500        # pilot rule 6.1 item 4
TICK = 0.05                     # reported only, never used to judge validity
FINGERPRINT_RECHECK_SAMPLE = 20
MEDIAN_VOLUME_ROWS = 250        # pilot group A rule

FORMAT_TXT7 = "TXT7"
FORMAT_TXT6 = "TXT6"
FORMAT_TXT_MIXED = "TXT_MIXED_6_7"
FORMAT_CSV = "CSV_HEADER"
FORMAT_PARQUET = "PARQUET_DAILY"
FORMAT_OTHER = "OTHER"
FORMAT_UNREADABLE = "UNREADABLE"
FORMAT_UNSUPPORTED = "UNSUPPORTED_TYPE"
FORMAT_EMPTY = "EMPTY"

DATE_FMT_EXCEL = "dd-mmm-yy"
POLL_MS = 100


# --- Helpers: identity ---------------------------------------------------------
def suffix_now(now=None):
    return (now or datetime.now()).strftime("%d_%b_%y_%H%M%S")


def human_date(value):
    return value.strftime("%d-%b-%y") if value else ""


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symbol_from_name(file_name):
    """F-01: exact stem for text/CSV; for Parquet the stem before the first
    '_' that is followed by 'daily' (e.g. 'INFY_daily 02Jan98-...')."""
    stem, ext = os.path.splitext(file_name)
    if ext.lower() == ".parquet":
        match = re.match(r"^(.*?)_daily", stem, flags=re.IGNORECASE)
        if match and match.group(1):
            return match.group(1)
    return stem


def file_safe(symbol):
    """02 section 3.2: every character outside A-Z and 0-9 becomes '_'."""
    return re.sub(r"[^A-Z0-9]", "_", symbol.upper())


# --- Helpers: parsing into a common row list -----------------------------------
class ParsedFile:
    """Rows as parallel lists: date, open, high, low, close, volume(raw),
    field7 (or None); plus structural facts."""

    def __init__(self):
        self.dates = []
        self.prices = []          # (o, h, l, c) floats or None for bad text
        self.volumes = []         # raw text/number or None
        self.field7 = []          # raw or None
        self.fmt = None
        self.header = False
        self.line_endings = ""
        self.bom = False
        self.encoding_errors = 0
        self.parse_errors = 0
        self.first_parse_error = ""
        self.non_numeric = Counter()  # field -> count
        self.null_values = Counter()


def _to_float(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _parse_date_text(text):
    text = text.strip()
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)),
                    int(match.group(3)))
    except ValueError:
        return None


def parse_text_file(path):
    """Headerless daily text, 6 or 7 fields per line (reader R3 layout)."""
    parsed = ParsedFile()
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        parsed.bom = True
        raw = raw[3:]
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    parsed.line_endings = ("CRLF" if crlf and not lf else
                           "LF" if lf and not crlf else
                           "MIXED" if crlf and lf else "NONE")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        parsed.encoding_errors = text.count("�")
    counts = Counter()
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        fields = line.split(",")
        day = _parse_date_text(fields[0]) if fields else None
        if day is None and line_no == 1 and not parsed.dates:
            parsed.header = True
            continue
        if len(fields) not in (6, 7) or day is None:
            parsed.parse_errors += 1
            if not parsed.first_parse_error:
                parsed.first_parse_error = (
                    "line %d: %d fields%s" % (line_no, len(fields),
                                               "" if day else ", bad date"))
            continue
        counts[len(fields)] += 1
        _append_row(parsed, day, fields[1:5], fields[5],
                    fields[6] if len(fields) == 7 else None)
    if counts[6] and counts[7]:
        parsed.fmt = FORMAT_TXT_MIXED
    elif counts[7]:
        parsed.fmt = FORMAT_TXT7
    elif counts[6]:
        parsed.fmt = FORMAT_TXT6
    return parsed


def _append_row(parsed, day, price_texts, volume, field7):
    prices = []
    for name, value in zip(("open", "high", "low", "close"), price_texts):
        if value is None or (isinstance(value, str) and not value.strip()):
            parsed.null_values[name] += 1
            prices.append(None)
            continue
        number = _to_float(value)
        if number is None:
            parsed.non_numeric[name] += 1
        prices.append(number)
    parsed.dates.append(day)
    parsed.prices.append(tuple(prices))
    parsed.volumes.append(volume)
    parsed.field7.append(field7)


def _frame_to_parsed(frame, parsed, time_col):
    """Fill a ParsedFile from a pandas frame with a date/time column."""
    import pandas as pd
    lower = {str(c).lower(): c for c in frame.columns}
    missing = [c for c in ("open", "high", "low", "close") if c not in lower]
    if missing:
        raise ValueError("missing column(s): %s" % ", ".join(missing))
    ts = pd.to_datetime(frame[time_col], errors="coerce")
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_localize(None)
    volume_col = lower.get("volume")
    columns = [frame[lower[c]].tolist() for c in ("open", "high", "low", "close")]
    volumes = frame[volume_col].tolist() if volume_col is not None else \
        [None] * len(frame)
    for idx, moment in enumerate(ts):
        if pd.isna(moment):
            parsed.parse_errors += 1
            if not parsed.first_parse_error:
                parsed.first_parse_error = "row %d: unparseable date" % (idx + 1)
            continue
        if moment.hour or moment.minute or moment.second:
            return False      # intraday data: not a daily file
        volume = volumes[idx]
        if volume is not None and isinstance(volume, float) and math.isnan(volume):
            volume = None
        _append_row(parsed, moment.date(),
                    [None if (isinstance(col[idx], float) and math.isnan(col[idx]))
                     else col[idx] for col in columns],
                    volume, None)
    return True


def parse_parquet_file(path):
    import pandas as pd
    parsed = ParsedFile()
    frame = pd.read_parquet(path)
    lower = {str(c).lower(): c for c in frame.columns}
    time_col = lower.get("datetime") or lower.get("date") or lower.get("time")
    if time_col is None:
        parsed.fmt = FORMAT_OTHER
        parsed.first_parse_error = "no datetime/date column"
        return parsed
    if not _frame_to_parsed(frame, parsed, time_col):
        parsed.fmt = FORMAT_OTHER
        parsed.first_parse_error = "intraday timestamps (not a daily file)"
        return parsed
    parsed.fmt = FORMAT_PARQUET
    return parsed


def parse_csv_file(path):
    import pandas as pd
    parsed = ParsedFile()
    with open(path, "rb") as handle:
        head = handle.read(4)
    parsed.bom = head.startswith(b"\xef\xbb\xbf")
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    parsed.header = True
    lower = {str(c).lower(): c for c in frame.columns}
    time_col = lower.get("date") or lower.get("datetime") or lower.get("time")
    if time_col is None:
        parsed.fmt = FORMAT_OTHER
        parsed.first_parse_error = "no date/time column in the header"
        return parsed
    # Strip an explicit +05:30 offset so the wall-clock date is kept.
    frame[time_col] = frame[time_col].astype(str).str.replace(
        r"[+-]\d{2}:\d{2}$", "", regex=True)
    if not _frame_to_parsed(frame, parsed, time_col):
        parsed.fmt = FORMAT_OTHER
        parsed.first_parse_error = "intraday timestamps (not a daily file)"
        return parsed
    parsed.fmt = FORMAT_CSV
    return parsed


# --- Helpers: per-file checks (F-03 to F-09) ---------------------------------------
def _volume_state(raw):
    """Return (int volume or None, problem) - problem in {None, 'blank',
    'non_numeric', 'negative', 'non_whole'}. Values are never changed."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, "blank"
    number = _to_float(raw)
    if number is None:
        return None, "non_numeric"
    if number < 0:
        return None, "negative"
    if number != int(number):
        return None, "non_whole"
    return int(number), None


def _field7_state(volume, raw7):
    if raw7 is None:
        return "ABSENT"
    f7 = _to_float(raw7)
    if f7 is None:
        return "NON_NUMERIC"
    if f7 == 0:
        return "ZERO"
    if volume is None:
        return "NO_VOLUME"
    if f7 == volume:
        return "EQUAL"
    return "LOWER" if f7 < volume else "HIGHER"


def _runs_text(dates, states, limit=12):
    """Compress consecutive identical states into 'STATE dd-mmm-yy..dd-mmm-yy'."""
    runs = []
    for day, state in zip(dates, states):
        if runs and runs[-1][0] == state:
            runs[-1][2] = day
        else:
            runs.append([state, day, day])
    parts = ["%s %s..%s" % (s, human_date(a), human_date(b)) for s, a, b in runs]
    if len(parts) > limit:
        parts = parts[:limit] + ["(+%d more periods)" % (len(parts) - limit)]
    return "; ".join(parts)


def analyse_rows(parsed):
    """Per-file record checks. Returns (facts dict, moves list, date list)."""
    rows = list(zip(parsed.dates, parsed.prices, parsed.volumes, parsed.field7))
    facts = {}
    unsorted = sum(1 for a, b in zip(parsed.dates, parsed.dates[1:]) if b < a)
    facts["unsorted_rows"] = unsorted

    # Duplicates: exact (same values) versus conflicting.
    by_date = defaultdict(list)
    for day, prices, volume, f7 in rows:
        by_date[day].append((prices, str(volume)))
    dup_exact = dup_conflict = 0
    for day, entries in by_date.items():
        if len(entries) > 1:
            if len(set(entries)) == 1:
                dup_exact += 1
            else:
                dup_conflict += 1
    facts["duplicate_dates_exact"] = dup_exact
    facts["duplicate_dates_conflicting"] = dup_conflict

    # One row per date for the time-series checks (first occurrence), sorted.
    seen = set()
    series = []
    for row in sorted(rows, key=lambda r: r[0]):
        if row[0] in seen:
            continue
        seen.add(row[0])
        series.append(row)
    dates = [r[0] for r in series]

    nonpositive = ohlc_bad = weekend = 0
    volume_problems = Counter()
    zero_volume = 0
    quarantinable_dates = set()
    closes = []
    opens = []
    volumes_int = []
    f7_states = []
    for day, prices, raw_volume, raw7 in series:
        o, h, l, c = prices
        bad_price = any(p is None or p <= 0 for p in prices)
        if any(p is not None and p <= 0 for p in prices):
            nonpositive += 1
        bad_ohlc = False
        if not any(p is None for p in prices):
            bad_ohlc = (h < max(o, c, l) - 1e-9) or (l > min(o, c, h) + 1e-9)
        if bad_ohlc:
            ohlc_bad += 1
        if day.weekday() >= 5:
            weekend += 1
        volume, problem = _volume_state(raw_volume)
        if problem and problem != "blank":
            volume_problems[problem] += 1
        if problem == "blank":
            volume_problems["blank"] += 1
        if volume == 0:
            zero_volume += 1
        if bad_price or bad_ohlc or (problem and problem != "blank"):
            quarantinable_dates.add(day)
        closes.append(c)
        opens.append(o)
        volumes_int.append(volume)
        f7_states.append(_field7_state(volume, raw7))
    facts.update({
        "non_positive_price_rows": nonpositive,
        "ohlc_violation_rows": ohlc_bad,
        "weekend_dates": weekend,
        "volume_blank": volume_problems["blank"],
        "volume_non_numeric": volume_problems["non_numeric"],
        "volume_negative": volume_problems["negative"],
        "volume_non_whole": volume_problems["non_whole"],
        "zero_volume_rows": zero_volume,
        "null_values": ", ".join("%s %d" % kv for kv in
                                 sorted(parsed.null_values.items())),
        "non_numeric_values": ", ".join("%s %d" % kv for kv in
                                        sorted(parsed.non_numeric.items())),
    })

    # F-05 field 7 periods.
    facts["field7_periods"] = (_runs_text(dates, f7_states)
                               if any(s != "ABSENT" for s in f7_states)
                               else "ABSENT throughout")

    # F-06 placeholder volume runs.
    runs = []
    current = 1
    for prev, cur in zip(volumes_int, volumes_int[1:]):
        if cur is not None and cur == prev:
            current += 1
        else:
            if current >= PLACEHOLDER_RUN:
                runs.append(current)
            current = 1
    if current >= PLACEHOLDER_RUN:
        runs.append(current)
    facts["placeholder_volume_runs"] = len(runs)
    facts["placeholder_longest_run"] = max(runs) if runs else 0

    # F-07 tick profile (reported only).
    by_year = defaultdict(lambda: [0, 0])
    last_off_tick = None
    for day, c in zip(dates, closes):
        if c is None:
            continue
        on_grid = abs(round(c / TICK) * TICK - c) <= 1e-6
        by_year[day.year][0] += 1
        by_year[day.year][1] += 1 if on_grid else 0
        if not on_grid:
            last_off_tick = day
    facts["on_tick_share_by_year"] = "; ".join(
        "%d:%.0f%%" % (year, 100.0 * on / total)
        for year, (total, on) in sorted(by_year.items()))
    facts["last_off_tick_date"] = last_off_tick

    # F-08 large moves.
    moves = []
    for i in range(1, len(series)):
        prev_close = closes[i - 1]
        if prev_close is None or prev_close <= 0:
            continue
        o, c = opens[i], closes[i]
        open_pct = (o - prev_close) / prev_close * 100.0 if o is not None else None
        close_pct = (c - prev_close) / prev_close * 100.0 if c is not None else None
        open_big = open_pct is not None and abs(open_pct) > LARGE_MOVE_PCT
        close_big = close_pct is not None and abs(close_pct) > LARGE_MOVE_PCT
        if close_big or open_big:
            moves.append({"date": dates[i], "prev_close": prev_close,
                          "open": o, "close": c, "open_pct": open_pct,
                          "close_pct": close_pct,
                          "type": "CLOSE_MOVE" if close_big else "OPEN_ONLY"})
    facts["large_moves_close"] = sum(1 for m in moves if m["type"] == "CLOSE_MOVE")
    facts["large_moves_open_only"] = sum(1 for m in moves if m["type"] == "OPEN_ONLY")

    # F-09 coverage.
    n = len(dates)
    facts["rows_unique_dates"] = n
    facts["first_date"] = dates[0] if dates else None
    facts["last_date"] = dates[-1] if dates else None
    facts["has_800_rows"] = n >= EMA_BARS
    facts["has_2500_rows"] = n >= LONG_HISTORY_BARS
    facts["date_of_800th_last_row"] = dates[-EMA_BARS] if n >= EMA_BARS else None
    facts["first_date_with_800_rows"] = dates[EMA_BARS - 1] if n >= EMA_BARS else None
    latest_window = set(dates[-EMA_BARS:])
    facts["latest800_ohlc_or_quarantinable"] = len(quarantinable_dates
                                                   & latest_window)
    facts["latest800_large_moves"] = sum(1 for m in moves
                                         if m["date"] in latest_window)
    recent_volumes = [v for v in volumes_int[-MEDIAN_VOLUME_ROWS:]
                      if v is not None]
    # Conventional median: the average of the two middle values when the
    # count is even (statistics.median, standard library).
    facts["median_volume_latest_250"] = (
        statistics.median(recent_volumes) if recent_volumes else None)
    facts["last_close"] = closes[-1] if closes else None
    return facts, moves, dates


# --- Main logic: the inventory ------------------------------------------------------
def list_files(folder):
    found = []
    for current, subfolders, names in os.walk(folder):
        subfolders.sort()
        for name in sorted(names):
            found.append(os.path.join(current, name))
    return found


def inspect_file(path, folder):
    """Return (record dict, moves, dates or None)."""
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    stat = os.stat(path)
    symbol = symbol_from_name(name)
    record = {
        "path": path, "relative_folder": os.path.relpath(os.path.dirname(path),
                                                         folder),
        "file_name": name, "extension": ext, "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "symbol": symbol, "file_safe_name": file_safe(symbol),
        "sha256": sha256_of(path), "format": None, "problem": "",
    }
    if ext not in SUPPORTED_EXTENSIONS:
        record["format"] = FORMAT_UNSUPPORTED
        record["problem"] = "not inspected (unsupported type)"
        return record, [], None
    if stat.st_size == 0:
        record["format"] = FORMAT_EMPTY
        record["problem"] = "empty file"
        return record, [], None
    try:
        if ext == ".txt":
            parsed = parse_text_file(path)
        elif ext == ".csv":
            parsed = parse_csv_file(path)
        else:
            parsed = parse_parquet_file(path)
    except Exception as exc:                     # reported, never hidden
        record["format"] = FORMAT_UNREADABLE
        record["problem"] = "%s: %s" % (type(exc).__name__, exc)
        return record, [], None
    record.update({"header_present": parsed.header,
                   "line_endings": parsed.line_endings, "bom": parsed.bom,
                   "encoding_errors": parsed.encoding_errors,
                   "parse_errors": parsed.parse_errors,
                   "first_parse_error": parsed.first_parse_error,
                   "rows_read": len(parsed.dates)})
    if parsed.fmt in (None, FORMAT_OTHER) or not parsed.dates:
        record["format"] = parsed.fmt or FORMAT_UNREADABLE
        record["problem"] = (parsed.first_parse_error
                             or "no readable data rows")
        return record, [], None
    record["format"] = parsed.fmt
    facts, moves, dates = analyse_rows(parsed)
    record.update(facts)
    for move in moves:
        move["symbol"] = symbol
        move["file_name"] = name
    return record, moves, dates


def build_calendar(file_dates, file_spans):
    """U-03: for every date, files with data and files alive."""
    with_data = Counter()
    for dates in file_dates.values():
        with_data.update(set(dates))
    all_dates = sorted(with_data)
    rows = []
    for day in all_dates:
        alive = sum(1 for first, last in file_spans.values()
                    if first <= day <= last)
        rows.append({"date": day, "files_with_data": with_data[day],
                     "files_alive": alive,
                     "share": with_data[day] / alive if alive else 0.0,
                     "weekend": day.weekday() >= 5})
    return rows


def find_absences(path, dates, calendar_rows, calendar_index, latest800):
    """F-10: calendar dates absent from this file between its own first and
    last date, grouped into consecutive calendar ranges. For review only."""
    own = set(dates)
    first, last = dates[0], dates[-1]
    start = calendar_index[first]
    end = calendar_index[last]
    ranges = []
    for pos in range(start, end + 1):
        row = calendar_rows[pos]
        if row["date"] in own:
            continue
        # files_alive includes this file and files_with_data excludes it (it
        # is absent here), so the OTHER alive files without data are
        # files_alive - files_with_data - 1.
        others_absent = row["files_alive"] - row["files_with_data"] - 1
        if ranges and ranges[-1]["end_pos"] == pos - 1:
            current = ranges[-1]
            current["end_pos"] = pos
            current["range_end"] = row["date"]
            current["days"] += 1
            current["min_share"] = min(current["min_share"], row["share"])
            current["max_others_absent"] = max(current["max_others_absent"],
                                               others_absent)
        else:
            ranges.append({"end_pos": pos, "range_start": row["date"],
                           "range_end": row["date"], "days": 1,
                           "min_share": row["share"],
                           "max_others_absent": others_absent})
    for item in ranges:
        item["in_latest_800"] = item["range_end"] >= latest800
        item.pop("end_pos")
    return ranges


def run_inventory(folder, out_path, report):
    """report(kind, payload) sends progress to the GUI queue."""
    started = time.time()
    paths = list_files(folder)
    total = len(paths)
    report("total", total)
    records, all_moves, file_dates = [], [], {}
    for index, path in enumerate(paths, start=1):
        report("file", (index, total, os.path.relpath(path, folder)))
        try:
            record, moves, dates = inspect_file(path, folder)
        except OSError as exc:
            record = {"path": path, "file_name": os.path.basename(path),
                      "relative_folder": os.path.relpath(os.path.dirname(path),
                                                         folder),
                      "extension": os.path.splitext(path)[1].lower(),
                      "symbol": symbol_from_name(os.path.basename(path)),
                      "format": FORMAT_UNREADABLE,
                      "problem": "could not open: %s" % exc, "sha256": ""}
            moves, dates = [], None
        records.append(record)
        all_moves.extend(moves)
        if dates:
            file_dates[path] = dates
        if record["problem"]:
            report("log", "PROBLEM %s: %s" % (record["file_name"],
                                             record["problem"]))
        report("counts", (sum(1 for r in records if not r["problem"]),
                          sum(1 for r in records if r["problem"])))

    report("stage", "Building the universe calendar...")
    spans = {p: (d[0], d[-1]) for p, d in file_dates.items()}
    calendar_rows = build_calendar(file_dates, spans)
    calendar_index = {row["date"]: i for i, row in enumerate(calendar_rows)}
    universe_latest = calendar_rows[-1]["date"] if calendar_rows else None

    report("stage", "Finding absences for review...")
    absences = []
    for record in records:
        dates = file_dates.get(record["path"])
        if not dates:
            continue
        latest800 = dates[-EMA_BARS] if len(dates) >= EMA_BARS else dates[0]
        ranges = find_absences(record["path"], dates, calendar_rows,
                               calendar_index, latest800)
        record["absence_ranges"] = len(ranges)
        record["absent_days"] = sum(r["days"] for r in ranges)
        record["absent_days_latest_800"] = sum(r["days"] for r in ranges
                                               if r["in_latest_800"])
        for item in ranges:
            item["symbol"] = record["symbol"]
            item["file_name"] = record["file_name"]
            absences.append(item)

    report("stage", "Grouping symbols and checking eligibility...")
    symbols = defaultdict(list)
    for record in records:
        if record["format"] not in (FORMAT_UNSUPPORTED,):
            symbols[record["symbol"].upper()].append(record)
    symbol_rows = []
    for symbol, group in sorted(symbols.items()):
        hashes = {r["sha256"] for r in group}
        status = ("SINGLE" if len(group) == 1 else
                  "IDENTICAL_DUPLICATES (G-16)" if len(hashes) == 1 else
                  "DIFFERING_FILES - CONFLICT FOR OWNER (G-16)")
        for r in group:
            r["symbol_file_count"] = len(group)
            r["symbol_status"] = status
        symbol_rows.append({
            "symbol": symbol, "file_count": len(group), "status": status,
            "files": " | ".join(
                "%s [%s, %s rows, %s..%s, %s]" % (
                    os.path.join(r["relative_folder"], r["file_name"]),
                    r.get("format"), r.get("rows_unique_dates", ""),
                    human_date(r.get("first_date")),
                    human_date(r.get("last_date")), r["sha256"][:12])
                for r in group)})

    safe_names = defaultdict(set)
    for symbol in symbols:
        safe_names[file_safe(symbol)].add(symbol)
    for record in records:
        if record["problem"]:
            continue
        record["eligible_1_readable"] = record["parse_errors"] == 0
        record["eligible_2_single_or_identical"] = \
            not record["symbol_status"].startswith("DIFFERING")
        record["eligible_3_current"] = record["last_date"] == universe_latest
        record["eligible_4_2500_rows"] = record["has_2500_rows"]
        record["eligible_5_clean_latest_800"] = (
            record["latest800_ohlc_or_quarantinable"] == 0)
        record["latest800_absences_for_review"] = record["absent_days_latest_800"]
        record["core_eligible_flags_all_true"] = all(
            record[k] for k in ("eligible_1_readable",
                                "eligible_2_single_or_identical",
                                "eligible_3_current", "eligible_4_2500_rows",
                                "eligible_5_clean_latest_800"))

    report("stage", "Re-checking source fingerprints...")
    inspected = [r for r in records if r.get("sha256")]
    step = max(1, len(inspected) // FINGERPRINT_RECHECK_SAMPLE)
    sample = inspected[::step][:FINGERPRINT_RECHECK_SAMPLE]
    changed = [r["file_name"] for r in sample
               if not os.path.exists(r["path"]) or sha256_of(r["path"]) != r["sha256"]]

    report("stage", "Writing the workbook...")
    summary = {
        "started": datetime.fromtimestamp(started), "folder": folder,
        "total": total, "records": records, "symbols": symbol_rows,
        "calendar": calendar_rows, "moves": all_moves, "absences": absences,
        "universe_latest": universe_latest, "safe_names": safe_names,
        "fingerprint_sample": len(sample), "fingerprint_changed": changed,
        "run_seconds": time.time() - started,
    }
    write_workbook(out_path, summary)
    return summary


# --- Main logic: workbook ----------------------------------------------------------------
FILE_COLUMNS = [
    "relative_folder", "file_name", "extension", "size_bytes", "modified",
    "sha256", "symbol", "file_safe_name", "symbol_file_count", "symbol_status",
    "format", "header_present", "line_endings", "bom", "encoding_errors",
    "parse_errors", "first_parse_error", "rows_read", "rows_unique_dates",
    "first_date", "last_date", "unsorted_rows", "duplicate_dates_exact",
    "duplicate_dates_conflicting", "null_values", "non_numeric_values",
    "non_positive_price_rows", "ohlc_violation_rows", "volume_blank",
    "volume_non_numeric", "volume_negative", "volume_non_whole",
    "zero_volume_rows", "weekend_dates", "field7_periods",
    "placeholder_volume_runs", "placeholder_longest_run",
    "on_tick_share_by_year", "last_off_tick_date", "large_moves_close",
    "large_moves_open_only", "has_800_rows", "has_2500_rows",
    "date_of_800th_last_row", "first_date_with_800_rows", "absence_ranges",
    "absent_days", "absent_days_latest_800",
]
ELIGIBILITY_COLUMNS = [
    "symbol", "file_name", "rows_unique_dates", "first_date", "last_date",
    "last_close", "median_volume_latest_250", "eligible_1_readable",
    "eligible_2_single_or_identical", "eligible_3_current",
    "eligible_4_2500_rows", "eligible_5_clean_latest_800",
    "latest800_absences_for_review", "latest800_large_moves",
    "core_eligible_flags_all_true",
]


def _write_sheet(wb, title, headers, rows):
    from openpyxl.styles import Font
    sheet = wb.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append([_cell_value(v) for v in row])
    for column_cells in sheet.iter_cols(min_row=2):
        for cell in column_cells:
            if isinstance(cell.value, (date, datetime)):
                cell.number_format = (DATE_FMT_EXCEL if not isinstance(
                    cell.value, datetime) or cell.value.time() == datetime.min.time()
                    else "dd-mmm-yy hh:mm:ss")
    sheet.freeze_panes = "A2"
    for index, header in enumerate(headers, start=1):
        letter = sheet.cell(row=1, column=index).column_letter
        sheet.column_dimensions[letter].width = min(max(len(str(header)) + 2, 10), 40)
    return sheet


def _cell_value(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_workbook(out_path, s):
    import openpyxl
    import pandas
    import pyarrow
    records = s["records"]
    good = [r for r in records if not r["problem"]]
    problems = [r for r in records if r["problem"]]
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    formats = Counter(r["format"] for r in records)
    buckets = Counter()
    for r in good:
        n = r["rows_unique_dates"]
        buckets["< 200" if n < 200 else "200-799" if n < 800 else
                "800-2,499" if n < 2500 else ">= 2,500"] += 1
    moves = s["moves"]
    unsupported = sum(1 for r in records if r["format"] == FORMAT_UNSUPPORTED)
    summary_rows = [
        ("Run date", s["started"].strftime("%d-%b-%y %H:%M:%S")),
        ("Folder inspected (with subfolders)", s["folder"]),
        ("Script version", SCRIPT_VERSION),
        ("Python", platform.python_version()),
        ("pandas / pyarrow / openpyxl", "%s / %s / %s" % (
            pandas.__version__, pyarrow.__version__, openpyxl.__version__)),
        ("Run time (seconds)", round(s["run_seconds"], 1)),
        ("U-01 Total files found", s["total"]),
        ("U-01 Files inspected successfully (Files sheet)", len(good)),
        ("U-01 Files on the Problems sheet", len(problems)),
        ("   of which unsupported type", unsupported),
        ("   of which unreadable / empty / other", len(problems) - unsupported),
        ("Check: Files + Problems = Total", "TRUE" if len(good) + len(problems)
         == s["total"] else "FALSE"),
        ("U-01 Distinct symbols", len(s["symbols"])),
        ("U-02 Symbols with byte-identical duplicates",
         sum(1 for r in s["symbols"] if r["status"].startswith("IDENTICAL"))),
        ("U-02 Symbols with differing files (Owner conflicts)",
         sum(1 for r in s["symbols"] if r["status"].startswith("DIFFERING"))),
        ("Universe latest date", human_date(s["universe_latest"])),
        ("U-04 Files ending before the universe latest date",
         sum(1 for r in good if r["last_date"] != s["universe_latest"])),
    ]
    for bucket in ("< 200", "200-799", "800-2,499", ">= 2,500"):
        summary_rows.append(("U-05 Files with %s rows" % bucket, buckets[bucket]))
    summary_rows += [
        ("Large moves: CLOSE_MOVE", sum(1 for m in moves if m["type"] == "CLOSE_MOVE")),
        ("Large moves: OPEN_ONLY", sum(1 for m in moves if m["type"] == "OPEN_ONLY")),
        ("Large moves: distinct dates", len({m["date"] for m in moves})),
        ("Files with OHLC violations", sum(1 for r in good if r["ohlc_violation_rows"])),
        ("Files with non-positive prices", sum(1 for r in good if r["non_positive_price_rows"])),
        ("Files with negative/non-whole/non-numeric volume", sum(
            1 for r in good if r["volume_negative"] or r["volume_non_whole"]
            or r["volume_non_numeric"])),
        ("Files with conflicting duplicate dates", sum(1 for r in good if r["duplicate_dates_conflicting"])),
        ("Files with placeholder-volume runs (>=20)", sum(1 for r in good if r["placeholder_volume_runs"])),
        ("Files with parse errors", sum(1 for r in good if r["parse_errors"])),
        ("U-08 Files with all core eligibility flags TRUE",
         sum(1 for r in good if r.get("core_eligible_flags_all_true"))),
        ("Fingerprint re-check sample size", s["fingerprint_sample"]),
        ("Fingerprint re-check result", "UNCHANGED" if not s["fingerprint_changed"]
         else "CHANGED: " + ", ".join(s["fingerprint_changed"])),
        ("Owner confirmation required", "Confirm the folder was the complete stock universe (doc 09 §8.6)"),
    ]
    for fmt, count in sorted(formats.items()):
        summary_rows.append(("Format %s" % fmt, count))
    _write_sheet(wb, "Summary", ["Item", "Value"], summary_rows)
    wb["Summary"].column_dimensions["A"].width = 52
    wb["Summary"].column_dimensions["B"].width = 70

    _write_sheet(wb, "Files", FILE_COLUMNS,
                 [[r.get(c) for c in FILE_COLUMNS] for r in good])
    _write_sheet(wb, "Symbols", ["symbol", "file_count", "status", "files"],
                 [[r["symbol"], r["file_count"], r["status"], r["files"]]
                  for r in s["symbols"]])
    variant_rows = []
    for fmt, count in sorted(formats.items()):
        examples = [r["file_name"] for r in records if r["format"] == fmt][:3]
        variant_rows.append([fmt, count, ", ".join(examples)])
    _write_sheet(wb, "Format_Variants", ["format", "files", "examples"],
                 variant_rows)
    _write_sheet(wb, "Problems",
                 ["relative_folder", "file_name", "extension", "format",
                  "problem", "size_bytes", "sha256"],
                 [[r.get("relative_folder"), r["file_name"], r.get("extension"),
                   r["format"], r["problem"], r.get("size_bytes"),
                   r.get("sha256")] for r in problems])
    _write_sheet(wb, "Universe_Calendar",
                 ["date", "weekday", "files_with_data", "files_alive",
                  "share_pct", "weekend"],
                 [[c["date"], c["date"].strftime("%a"), c["files_with_data"],
                   c["files_alive"], round(100.0 * c["share"], 2), c["weekend"]]
                  for c in s["calendar"]])
    _write_sheet(wb, "Large_Moves",
                 ["symbol", "file_name", "date", "prev_close", "open", "close",
                  "open_pct", "close_pct", "type"],
                 [[m["symbol"], m["file_name"], m["date"], m["prev_close"],
                   m["open"], m["close"],
                   None if m["open_pct"] is None else round(m["open_pct"], 2),
                   None if m["close_pct"] is None else round(m["close_pct"], 2),
                   m["type"]]
                  for m in sorted(moves, key=lambda m: (m["symbol"], m["date"]))])
    by_date = defaultdict(list)
    for m in moves:
        by_date[m["date"]].append(m)
    _write_sheet(wb, "Moves_By_Date",
                 ["date", "files", "close_moves", "open_only", "symbols"],
                 [[day, len(items),
                   sum(1 for m in items if m["type"] == "CLOSE_MOVE"),
                   sum(1 for m in items if m["type"] == "OPEN_ONLY"),
                   ", ".join(sorted({m["symbol"] for m in items}))[:2000]]
                  for day, items in sorted(by_date.items(),
                                           key=lambda kv: (-len(kv[1]), kv[0]))])
    _write_sheet(wb, "Absences_For_Review",
                 ["symbol", "file_name", "range_start", "range_end",
                  "calendar_days", "in_latest_800", "min_universe_share_pct",
                  "max_other_files_also_absent"],
                 [[a["symbol"], a["file_name"], a["range_start"], a["range_end"],
                   a["days"], a["in_latest_800"], round(100.0 * a["min_share"], 2),
                   a["max_others_absent"]] for a in s["absences"]])
    coverage_rows = []
    last_dates = Counter(r["last_date"] for r in good)
    for day, count in sorted(last_dates.items(), reverse=True)[:15]:
        coverage_rows.append(["U-04 last date", human_date(day), count, ""])
    for r in good:
        if r["last_date"] != s["universe_latest"]:
            coverage_rows.append(["U-04 ends early", r["symbol"],
                                  human_date(r["last_date"]), r["file_name"]])
    for bucket in ("< 200", "200-799", "800-2,499", ">= 2,500"):
        coverage_rows.append(["U-05 rows bucket", bucket, buckets[bucket], ""])
    for symbol in sorted(s["symbols"], key=lambda r: r["symbol"]):
        if re.search(r"[^A-Z0-9]", symbol["symbol"]):
            coverage_rows.append(["U-06 special characters", symbol["symbol"],
                                  file_safe(symbol["symbol"]), ""])
    for safe, originals in sorted(s["safe_names"].items()):
        if len(originals) > 1:
            coverage_rows.append(["U-06 file-safe collision", safe,
                                  ", ".join(sorted(originals)), ""])
    _write_sheet(wb, "Coverage", ["item", "key", "value", "detail"],
                 coverage_rows)
    _write_sheet(wb, "Pilot_Eligibility", ELIGIBILITY_COLUMNS,
                 [[r.get(c) for c in ELIGIBILITY_COLUMNS] for r in good])
    notes = [
        "Read-only exploratory inventory (document 09 v1.6, section 8). No source file was changed.",
        "Every file found appears in exactly one of Files or Problems (unsupported types are on Problems).",
        "Thresholds: +/-15% open or close vs previous close (V-PX-05, G-03); 20 identical consecutive volumes; 800 and 2,500 rows; 0.05 tick grid (reported only, TC-20).",
        "Symbol = exact file stem; Parquet: stem before '_daily'. File-safe name: characters outside A-Z/0-9 become '_'.",
        "G-16: only byte-identical files (same SHA-256) are duplicates; any difference is a conflict for the Owner. Nothing is selected or merged.",
        "Absences are 'for review', never defects (section 6.5); counted only between each file's own first and last date.",
        "Pilot_Eligibility holds flags only (section 6.1); it is not a selection. Absences in the latest 800 rows need review before item 5 is final.",
        "Large moves are listed for the Owner's G-03 verification; none is classified or unblocked here.",
        "Duplicate dates: checks use the first occurrence of each date; counts of exact and conflicting duplicates are on Files.",
    ]
    _write_sheet(wb, "Notes", ["note"], [[n] for n in notes])
    wb["Notes"].column_dimensions["A"].width = 140

    temp_path = out_path + ".partial"
    wb.save(temp_path)
    os.replace(temp_path, out_path)


# --- GUI -----------------------------------------------------------------------------
class ScrollFrame(tk.Frame):
    """Whole-window vertical scrolling so every control stays reachable."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self._window = self.canvas.create_window((0, 0), window=self.body,
                                                 anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._window, width=e.width))
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

    def destroy_canvas_first(self):
        try:
            self.canvas.destroy()
        except tk.TclError:
            pass


class InventoryApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("860x640")
        self._closing = False
        self._queue = queue.Queue()
        self._started = None
        self._total = 0
        self._done = 0
        self._scroll_frame = ScrollFrame(self)
        self._scroll_frame.pack(fill="both", expand=True)
        body = self._scroll_frame.body
        pad = {"padx": 6, "pady": 3}

        box = tk.LabelFrame(body, text="1. Input - stock-data folder "
                                       "(subfolders included)", padx=6, pady=4)
        box.pack(fill="x", **pad)
        self.folder_var = tk.StringVar()
        tk.Entry(box, textvariable=self.folder_var).pack(side="left", fill="x",
                                                         expand=True)
        tk.Button(box, text="Browse...", command=self._pick_folder).pack(
            side="left", padx=4)
        self.count_label = tk.Label(box, text="0 files", width=12)
        self.count_label.pack(side="left")

        box = tk.LabelFrame(body, text="2. Output - Excel workbook", padx=6,
                            pady=4)
        box.pack(fill="x", **pad)
        self.out_var = tk.StringVar()
        tk.Entry(box, textvariable=self.out_var).pack(side="left", fill="x",
                                                      expand=True)
        tk.Button(box, text="Save As...", command=self._pick_output).pack(
            side="left", padx=4)

        box = tk.LabelFrame(body, text="3. Options", padx=6, pady=4)
        box.pack(fill="x", **pad)
        tk.Label(box, anchor="w", justify="left",
                 text="Fixed thresholds (doc 09 §8.3): ±15% moves, 20 identical "
                      "volumes, 800 / 2,500 rows, 0.05 tick grid. Read-only: "
                      "source files are never changed.").pack(fill="x")

        self.run_button = tk.Button(body, text="Run inventory", width=20,
                                    command=self._start)
        self.run_button.pack(**pad)

        box = tk.LabelFrame(body, text="Progress / Status", padx=6, pady=4)
        box.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(box, mode="determinate")
        self.progress.pack(fill="x")
        self.status_label = tk.Label(box, text="Ready.", anchor="w")
        self.status_label.pack(fill="x")
        self.timing_label = tk.Label(box, text="", anchor="w")
        self.timing_label.pack(fill="x")
        self.counter_label = tk.Label(box, text="", anchor="w")
        self.counter_label.pack(fill="x")

        box = tk.LabelFrame(body, text="Live log", padx=6, pady=4)
        box.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(box, height=16, bg="black", fg="#d0d0d0",
                           font=("Consolas", 9))
        scroll = tk.Scrollbar(box, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(POLL_MS, self._poll)

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Choose the stock-data folder")
        if not folder:
            return
        self.folder_var.set(folder)
        self.count_label.config(text="%d files" % len(list_files(folder)))
        if not self.out_var.get():
            self.out_var.set(os.path.join(
                os.path.dirname(folder),
                "Q-MAP_Universe_Inventory_%s.xlsx" % suffix_now()))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Save the inventory workbook as", defaultextension=".xlsx",
            initialfile="Q-MAP_Universe_Inventory_%s.xlsx" % suffix_now(),
            filetypes=[("Excel workbook", "*.xlsx")])
        if path:
            self.out_var.set(path)

    def _start(self):
        folder = self.folder_var.get().strip()
        out_path = self.out_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror(WINDOW_TITLE, "Please choose an existing "
                                               "stock-data folder.")
            return
        if not out_path:
            messagebox.showerror(WINDOW_TITLE, "Please choose where to save "
                                               "the workbook.")
            return
        if os.path.abspath(out_path).startswith(os.path.abspath(folder) + os.sep):
            messagebox.showerror(WINDOW_TITLE, "Save the workbook outside the "
                                               "folder being inspected.")
            return
        self.run_button.config(state="disabled")
        self._started = time.time()
        self._done = 0
        self._append("Inventory started %s" % datetime.now().strftime(
            "%d-%b-%y %H:%M:%S"))
        threading.Thread(target=self._worker, args=(folder, out_path),
                         daemon=True).start()

    def _worker(self, folder, out_path):
        def report(kind, payload):
            self._queue.put((kind, payload))
        try:
            summary = run_inventory(folder, out_path, report)
            self._queue.put(("done", (out_path, summary)))
        except Exception:
            self._queue.put(("error", traceback.format_exc()))

    def _poll(self):
        if getattr(self, "_closing", False):
            return
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                self._handle(kind, payload)
        except queue.Empty:
            pass
        if self._started:
            elapsed = time.time() - self._started
            eta = ""
            if self._done and self._total and self._done < self._total:
                remaining = elapsed / self._done * (self._total - self._done)
                eta = "   ETA %s" % _clock(remaining)
            self.timing_label.config(text="Started %s   elapsed %s%s" % (
                datetime.fromtimestamp(self._started).strftime("%H:%M:%S"),
                _clock(elapsed), eta))
        self.after(POLL_MS, self._poll)

    def _handle(self, kind, payload):
        if kind == "total":
            self._total = payload
            self.progress.config(maximum=max(payload, 1))
            self._append("%d file(s) found" % payload)
        elif kind == "file":
            index, total, name = payload
            self._done = index
            self.progress.config(value=index)
            self.status_label.config(text="Reading %d of %d: %s"
                                     % (index, total, name))
        elif kind == "counts":
            self.counter_label.config(text="Inspected OK: %d   Problems: %d"
                                      % payload)
        elif kind == "stage":
            self.status_label.config(text=payload)
            self._append(payload)
        elif kind == "log":
            self._append(payload)
        elif kind == "done":
            out_path, summary = payload
            self._started = None
            self.run_button.config(state="normal")
            self.status_label.config(text="Finished. Workbook saved.")
            self._append("Saved: %s" % out_path)
            self._append("Run time %.1f s; fingerprint re-check: %s" % (
                summary["run_seconds"],
                "UNCHANGED" if not summary["fingerprint_changed"] else "CHANGED"))
        elif kind == "error":
            self._started = None
            self.run_button.config(state="normal")
            self.status_label.config(text="The inventory failed - see the log.",
                                     fg="red")
            self._append(payload)

    def _append(self, text):
        if getattr(self, "_closing", False):
            return
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def _on_closing(self):
        self._closing = True
        try:
            self._scroll_frame.destroy_canvas_first()
            self._scroll_frame.pack_forget()
            self._scroll_frame.destroy()
        except tk.TclError:
            pass
        self.withdraw()
        try:
            for callback in self.tk.call("after", "info"):
                try:
                    self.after_cancel(callback)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass


def _clock(seconds):
    seconds = int(seconds)
    return "%02d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


# --- Execution ------------------------------------------------------------------------
if __name__ == "__main__":
    InventoryApp().mainloop()
