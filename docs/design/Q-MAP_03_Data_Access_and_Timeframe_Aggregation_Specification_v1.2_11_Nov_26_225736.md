# Q-MAP — Data Access Interface and Timeframe Aggregation Specification

**Package document 03 | Version 1.2 | 11-Nov-26 | Status: Proposed — consistency corrections from the Claude 2 follow-up review; pending ChatGPT review and Project Owner approval**

| Field | Value |
|---|---|
| Covers | The single data-access interface used by the Analytical Engine and other programs; timeframe aggregation rules for intraday and daily data; on-demand vs stored timeframes |
| Depends on | Document 02 v1.1 (canonical records, generations, catalogue); Deliverable 1 v1.2 (session and volume findings); decisions D-03 to D-11 |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed sections | Reason (review item) |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | §A5, §A6 | New meta keys (`completeness_basis`, `session_summary`); informational `notes` separated from status-affecting warnings; new codes for unrecognised sessions and auction volume (A3, A4, B5) |
| 1.1 | §A7 Examples 2 and 3 | Expected responses updated for provisional completeness and candidate sessions |
| 1.1 | §B3, §B4, §B5 | Sessions taken from confirmed or candidate status; unrecognised days aggregated under a provisional regular expectation; special-session anchoring only after confirmation (A3) |
| 1.1 | §B7 | Daily volume = continuous-session candle volume only; auction-record volumes excluded and reported, pending verification (A4) |
| 1.1 | §B9 | Off-tick handling per verified or unverified tick rule (A6) |
| 1.1 | §B10 | Benchmark corrected and fully specified; v1.0 discrepancy explained with evidence (A5) |
| 1.1 | §B11.5 | Manually checked daily-volume example added (A4) |
| 1.2 | §A4, §A5 (`DataRequirement`) | `latest_n` added to `DataRequirement`, and the mapping from a requirement to `get_bars` stated. v1.1 had no way for a scanner to pass `latest_n` through `context.fetch(requirement)`, although the EMA proposal needs it (interface gap found in review). Interface version 1.0 → **1.1** (additive; no existing parameter changes). |
| 1.2 | §A6 | `RANGE_TRUNCATED_END` defined precisely for `latest_n` requests (needed for stale-data handling) |
| 1.2 | §B3 | Evidence counts corrected for weekend sessions (document 02 v1.2 §6.2): 383 candidate REGULAR NIFTY days; weekend sessions listed as unrecognised until confirmed |

Unchanged in v1.1: §A1–§A4, §A8, §B1, §B2, §B6, §B8.

Unchanged in v1.2: §A1–§A3, §A7, Part B except §B3. §A8 changes only its interface-version number.

---

## Part A — Data-access interface (F-20)

### A1. Purpose in plain English

The data-access interface is the **only door** into the Q-MAP Database. A program asks for data in simple terms, for example "NIFTY, 15-minute bars, 01-Sep-26 to 30-Sep-26". It receives:

- the bars,
- a short report on how complete and trustworthy those bars are.

The program never needs to know about Parquet folders, file names or DuckDB.

**Design rules (Approved — blueprint):**
- The interface is small and stable.
- It is read-only.
- It never triggers maintenance or rebuilding.
- Timestamps and their timezone meaning are always explicit.
- Unavailable or incomplete data is reported clearly; it is never hidden and never fabricated.

**Not built (Approved — scope):** no web service, no server, no remote API. It is an ordinary Python module that a program imports.

### A2. Location and opening

```python
from qmap_database.access import QMapData

db = QMapData(data_root=r"D:\QMAP_DATA")    # opens the catalogue read-only
...
db.close()                                   # or use:  with QMapData(...) as db:
```

`data_root` normally comes from the Q-MAP settings file, so that the user picks the folder only once.

### A3. Functions

| # | Function | Purpose | Returns |
|---|---|---|---|
| 1 | `list_datasets()` | Which datasets exist | DataFrame |
| 2 | `list_instruments(dataset_id=None, instrument_type=None, active_only=True)` | Which instruments exist, with ranges and status | DataFrame |
| 3 | `describe_instrument(instrument_id)` | Everything known about one instrument: fields, timeframes, coverage, quality, issues summary, session patterns | dict |
| 4 | `supported_timeframes(instrument_id)` | Which timeframe codes can be requested | list of str |
| 5 | `check_availability(requirement)` | Can a request be satisfied? Answers without loading the bars. | `AvailabilityReport` |
| 6 | `get_bars(instrument_id, timeframe, start=None, end=None, *, fields=None, latest_n=None, include_auction_records=True, exclude_flagged=False)` | Retrieve bars (1-minute or aggregated) | `BarResult` |
| 7 | `get_trading_calendar(start, end)` | Trading days, holidays and special sessions, with verification status | DataFrame |
| 8 | `get_day_profiles(instrument_id, start, end)` | Per-day intraday completeness and session pattern | DataFrame |
| 9 | `get_issues(instrument_id=None, start=None, end=None, min_severity="WARNING", status="OPEN")` | Known data problems | DataFrame |
| 10 | `close()` | Release the catalogue | — |

No other function is public. Anything else, such as SQL helpers or path building, is internal and may change freely.

### A4. Parameters

| Parameter | Required | Type and accepted values | Rule |
|---|---|---|---|
| `instrument_id` | Yes | str, e.g. `"NIFTY"`, `"CONCOR"` | Must exist in the catalogue. Case-insensitive on input; returned in upper case. |
| `timeframe` | Yes | `"1m"`, `"3m"`, `"5m"`, `"10m"`, `"15m"`, `"30m"`, `"60m"`, `"1D"`, `"1W"`, `"1MO"` | Intraday codes are allowed only for intraday datasets. Daily datasets support `1D`, `1W`, `1MO`. Other minute values are added only when an approved scanner needs them (TC-11). |
| `start`, `end` | No | `datetime.date`, `datetime.datetime`, pandas Timestamp, or `"YYYY-MM-DD"` text | Both ends inclusive. A date-only `end` includes the whole day. If omitted: the instrument's first or last available date. `start > end` raises an error. Interpreted as IST. |
| `fields` | No | Any of `"open"`, `"high"`, `"low"`, `"close"`, `"volume"` | Default: all five. Asking for `volume` where it does not exist returns the column filled with nulls plus a warning. It is not an error (D-03). |
| `latest_n` | No | int ≥ 1 | Return the last N bars ending at `end` (or at the latest data). `start` is then ignored. Useful for scanner look-backs. Bars counted are those returned (with `require_complete_bars` in a `DataRequirement`, only complete bars count towards N). |
| `include_auction_records` | No | bool, default True | Intraday timeframes only. Adds the `AUCTION_PHASE` and `CLOSING_AUCTION` records as separate rows (D-08). They are never merged into candles. |
| `exclude_flagged` | No | bool, default False | If True, source rows carrying a quality flag (e.g. `SUSPECT_FILL`) are treated as missing. |

### A5. Return structures

#### `BarResult`

```python
@dataclass(frozen=True)
class BarResult:
    bars: pandas.DataFrame   # the data (columns below)
    meta: dict               # what the data is and how good it is (keys below)
    status: str              # "OK" | "PARTIAL" | "EMPTY"
```

**`bars` columns — every timeframe:**

| Column | Type | Meaning |
|---|---|---|
| `ts` | datetime64 (naive) | IST wall-clock **start** of the interval. For `1D`/`1W`/`1MO`: 00:00 on the period's first trading date. |
| `record_type` | str | `CANDLE` (aggregated or 1-minute continuous trading), `AUCTION_PHASE`, `CLOSING_AUCTION`, or `DAY` / `WEEK` / `MONTH` for daily-and-above periods |
| `open`, `high`, `low`, `close` | float | |
| `volume` | Int64 (nullable) | Sum of available volume; null if none available |
| `expected_units` | Int64 | Minutes (intraday) or trading days (`1W`/`1MO`) expected in this interval, from the session rules and calendar. Null for auction rows. |
| `present_units` | Int64 | Minutes or trading days actually present |
| `is_complete` | bool | `present_units == expected_units` (plus, for a CAS daily bar, the closing auction is present) |
| `is_forming` | bool | The interval is still open — data has not yet arrived — as opposed to historically incomplete |
| `session_truncated` | bool | The interval is shorter than the nominal length because the session ended (e.g. the 15:15–15:30 hourly bar) |
| `volume_complete` | bool | Every present unit had volume |
| `quality_flags` | str | Union of the flags on the source rows (e.g. `SUSPECT_FILL`); empty if none |
| `source_ts` | datetime64 | Only on auction rows: the original source timestamp (D-09). Null otherwise. |

**`meta` keys:**

| Key | Example |
|---|---|
| `instrument_id`, `dataset_id`, `timeframe` | `"NIFTY"`, `"NSE_INDEX_1M"`, `"15m"` |
| `timezone` | `"Asia/Kolkata"` (always) |
| `ts_meaning` | `"interval_start_ist_wallclock"` (always) |
| `requested_start`, `requested_end` | As interpreted |
| `returned_first_ts`, `returned_last_ts`, `bar_count` | |
| `incomplete_bar_count`, `forming_bar_count` | |
| `volume_available_from`, `volume_available_to` | `"2026-08-17"`, `"2026-11-06"` |
| `quality_status`, `completeness_status` | From catalogue coverage |
| `completeness_basis` | `OFFICIAL_CALENDAR` or `PROVISIONAL_DERIVED_CALENDAR`. Provisional until the official NSE calendar is loaded for the dates concerned (review B5). |
| `session_summary` | Counts of days in range by session status, e.g. `{"CONFIRMED_OFFICIAL": 0, "CONFIRMED_BY_OWNER": 0, "CANDIDATE": 22, "UNRECOGNISED_SESSION_SHAPE": 0}` |
| `notes` | Informational items that do not change `status`: `COMPLETENESS_PROVISIONAL`, `CANDIDATE_SESSIONS_IN_RANGE`, `DAILY_VOLUME_EXCLUDES_AUCTION` |
| `data_version` | e.g. `"run_000034/import_000412"` — identifies exactly which stored data was used, for reproducibility |
| `warnings` | list of `{code, message}` (codes below) |
| `issues` | list of open catalogue issues overlapping the range: `{issue_id, check_code, severity, ts_from, ts_to, affects_continuity, status, description}` |

#### `DataRequirement` and `AvailabilityReport`

```python
@dataclass(frozen=True)
class DataRequirement:
    instrument_id: str
    timeframe: str
    start: object = None                    # date / datetime / "YYYY-MM-DD"
    end: object = None
    required_fields: tuple = ("open", "high", "low", "close")
    optional_fields: tuple = ("volume",)
    min_bars: int = 1                       # minimum usable bars
    require_complete_bars: bool = False     # count only is_complete bars towards min_bars
    exclude_flagged: bool = False
    latest_n: int = None                    # v1.2: last N bars ending at `end`; start then ignored

@dataclass(frozen=True)
class AvailabilityReport:
    status: str               # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    reasons: list             # [{code, message}]
    available_start: object
    available_end: object
    estimated_bars: int
    missing_fields: tuple
    continuity_issues: list   # issues with affects_continuity = True inside the range
```

`DataRequirement` is defined in the database package because it describes a data request. The Analytical Engine imports it, so a scanner's declared needs and the database's answer use exactly the same vocabulary.

**From a requirement to `get_bars` (v1.2).** The engine's `context.fetch(requirement)` (document 04 §7.2) calls `get_bars` with exactly these arguments, so a scanner never needs any other route to data:

| `get_bars` argument | Taken from |
|---|---|
| `instrument_id`, `timeframe`, `start`, `end`, `latest_n`, `exclude_flagged` | The requirement fields of the same name |
| `fields` | `required_fields` + `optional_fields` |
| `include_auction_records` | The run option of the same name (document 04 §6) |

`check_availability` evaluates `min_bars` against the same window: with `latest_n`, the window is the last `latest_n` bars ending at `end`.

### A6. Status, warnings and errors

**Data problems are answers, not crashes.** They come back in `status`, `warnings`, `notes` and `issues`.

| `status` | Meaning |
|---|---|
| `OK` | Bars returned; no warnings. Notes may still be present. |
| `PARTIAL` | Bars returned, with at least one **warning** |
| `EMPTY` | No bars exist in the range (e.g. a holiday-only range). Not an exception. |

**Warnings** set `status = PARTIAL`, because they affect what the caller may safely conclude:

| Warning code | Raised when |
|---|---|
| `RANGE_TRUNCATED_START` / `RANGE_TRUNCATED_END` | Requested dates extend beyond available data. For `RANGE_TRUNCATED_END` (v1.2 precision): raised when the requested `end` is later than the instrument's last stored bar **and** at least one trading day (per `market_calendar`) lies between that bar and `end`. A request ending on a holiday or weekend after the last trading day does not raise it. Weekdays later than the calendar's last known date count as trading days for this test, so the warning errs towards being shown. The message names both dates, so a caller can see stale data. |
| `INCOMPLETE_BARS` | One or more bars have `is_complete = False` |
| `FORMING_BAR` | The last bar is still forming |
| `VOLUME_PARTIAL` / `VOLUME_UNAVAILABLE` | Volume requested but missing for part or all of the range |
| `FLAGGED_ROWS_INCLUDED` | Bars include source rows with quality flags (`SUSPECT_FILL`, `OFF_TICK_RULE_UNVERIFIED`, `SESSION_UNCONFIRMED`) |
| `CONTINUITY_ISSUE_IN_RANGE` | An issue with `affects_continuity = True` lies inside the range (e.g. Nifty IT 28-May-04) |
| `UNRECOGNISED_SESSION_IN_RANGE` | The range includes days with status `UNRECOGNISED_SESSION_SHAPE`: session boundaries uncertain, possible missing data (new in v1.1) |
| `HELD_REVISION_EXISTS` | The source has supplied a revision of this range that awaits owner review; the returned data is the active, unrevised data (new in v1.1) |
| `NO_DATA_IN_RANGE` | `status = EMPTY` |

**Notes** are informational and do not change `status`. They describe conditions that apply to nearly all data until reference information is supplied, so treating them as warnings would mark every response partial and drown real warnings.

| Note code | Meaning |
|---|---|
| `COMPLETENESS_PROVISIONAL` | Completeness was measured against a derived, unverified calendar |
| `CANDIDATE_SESSIONS_IN_RANGE` | Range includes CAS or regular days whose session status is `CANDIDATE` (D-06 confirmation pending) |
| `DAILY_VOLUME_EXCLUDES_AUCTION` | Daily volume excludes auction-record volume whose meaning is unverified (§B7) |

**Caller mistakes and system problems raise clear exceptions.** Every exception message names the offending value and suggests a fix.

| Exception | Raised when | Example message |
|---|---|---|
| `UnknownInstrumentError` | Instrument not in catalogue | "Instrument 'NIFTI' is not in the Q-MAP catalogue. Did you mean 'NIFTY'?" |
| `UnsupportedTimeframeError` | Code not allowed for that dataset | "Timeframe '5m' is not available for CONCOR (daily data). Available: 1D, 1W, 1MO." |
| `InvalidRequestError` | Bad dates, unknown field, `start > end` | "Start 30-Sep-26 is after end 01-Sep-26." |
| `DatabaseUnavailableError` | Data root missing, catalogue missing, or locked by the Data Manager | "The Q-MAP database is being updated by the Data Manager. Please try again after the update finishes." |
| `DataIntegrityError` | A catalogue-registered file is missing, or its fingerprint or row count differs | "NIFTY_2026.parquet does not match the catalogue. Run 'Check integrity' in the Data Manager." |

All of these inherit from `QMapDataError`, so a caller can catch them with one statement.

### A7. Typical requests and expected responses

The values below come from the actual inspected data. Each example is also a test case in document 06.

**Example 1 — list instruments**

```python
db.list_instruments()
```

| instrument_id | dataset_id | first_date | last_date | quality_status | volume_available_from |
|---|---|---|---|---|---|
| BANKNIFTY | NSE_INDEX_1M | 17-Aug-26 | 11-Nov-26 | PASS_WITH_WARNINGS | 17-Aug-26 |
| CONCOR | NSE_EQ_DAILY | 26-Nov-98 | 06-Nov-26 | PASS_WITH_WARNINGS | 26-Nov-98 |
| INFY | NSE_EQ_DAILY | 02-Jan-98 | 06-Nov-26 | PASS_WITH_WARNINGS | 02-Jan-98 |
| NIFTY | NSE_INDEX_1M | 09-Jan-25 | 06-Nov-26 | PASS_WITH_WARNINGS | 17-Aug-26 |
| NIFTYIT | NSE_SECTOR_INDEX_DAILY | 25-Aug-03 | 06-Nov-26 | PASS_WITH_WARNINGS | 25-Aug-03 |

Every status shows `PASS_WITH_WARNINGS` because of known open items: unconfirmed CAS patterns, unverified gaps and missing candles.

**Example 2 — 5-minute bars, volume present**

```python
r = db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17")
```

First bar of `r.bars`:

| ts | record_type | open | high | low | close | volume | expected_units | present_units | is_complete |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 17-Aug-26 09:15 | CANDLE | 24,354.65 | 24,357.60 | 24,282.80 | 24,306.65 | 9,824,234 | 5 | 5 | True |

The last two rows of the day are the 15:10 bar (5 of 5 minutes), then `CLOSING_AUCTION` at 15:30 with O = H = L = C = 24,287.65 and `source_ts` 15:30. `r.status == "OK"`. `r.meta["notes"]` contains `COMPLETENESS_PROVISIONAL` and `CANDIDATE_SESSIONS_IN_RANGE` (until the official calendar is loaded and the CAS rule is confirmed). `r.meta["completeness_basis"] == "PROVISIONAL_DERIVED_CALENDAR"`.

**Example 3 — request with a gap**

```python
r = db.get_bars("BANKNIFTY", "5m", "2026-08-19", "2026-08-19")
```

The 13:25 bar is O 57,061.60, H 57,076.10, L 57,052.95, C 57,068.40, volume 291,326, `expected_units` 5, `present_units` 3, `is_complete` False. The 13:28 and 13:29 minutes are missing and are **not** filled.
- `r.status == "PARTIAL"`
- `r.meta["warnings"]` contains `INCOMPLETE_BARS`

**Example 4 — volume not available**

```python
r = db.get_bars("NIFTY", "1D", "2025-01-09", "2025-01-31", fields=["close", "volume"])
```

Bars are returned. `volume` is null on every row and `volume_complete` is False. Warning `VOLUME_UNAVAILABLE`: "Volume for NIFTY is available only from 17-Aug-26." Status `PARTIAL`. No exception.

**Example 5 — wrong timeframe for a daily stock**

```python
db.get_bars("CONCOR", "15m")
```

Raises `UnsupportedTimeframeError`: "Timeframe '15m' is not available for CONCOR (daily data). Available: 1D, 1W, 1MO."

**Example 6 — availability check before a scanner runs**

```python
db.check_availability(DataRequirement("NIFTYIT", "1D", "2003-01-01", "2005-12-31", min_bars=200))
```

| Field | Value |
|---|---|
| `status` | `PARTIAL` |
| `reasons` | `RANGE_TRUNCATED_START` — data begins 25-Aug-03; `CONTINUITY_ISSUE_IN_RANGE` — 28-May-04 level break (unverified); `MISSING_DAY` — 01-Jul-05 quarantined (invalid OHLC) |
| `available_start` | 25-Aug-03 |
| `continuity_issues` | Issue `LEVEL_BREAK_UNVERIFIED`, 28-May-04, `affects_continuity = True` |

**Example 7 — latest bars for a look-back**

```python
db.get_bars("CONCOR", "1D", latest_n=5, fields=["close"])
```

Closes for 02-Nov-26 to 06-Nov-26: 417.85, 419.15, 425.10, 440.85, 439.80.

### A8. What the interface hides, and what can change behind it

| Hidden from callers | Can change without affecting scanners |
|---|---|
| Folder layout, file names, partitioning | Yes |
| DuckDB SQL and the DuckDB version | Yes |
| Catalogue table structure | Yes (callers see DataFrames and dicts only) |
| Whether a timeframe is computed on demand or read from a cache | Yes (a P2 cache could be added invisibly) |

The **contract** is the function names, parameters, the `bars` columns, the `meta` keys, the warning codes and the exceptions. Changing any of these requires a version change and a review (interface version **1.1**; v1.1 added the optional `DataRequirement.latest_n` field and changed nothing else).

---

## Part B — Timeframe aggregation (F-21)

### B1. Principles

1. **One-minute data is the source of truth for intraday instruments.** It is preserved and never overwritten by aggregation (Approved — blueprint).
2. **Aggregation is computed on request** from the canonical data. Nothing is precomputed in P1 (B9).
3. **Only real data is aggregated.** Missing minutes are never filled. An interval with no data produces no bar. An interval with some data produces a bar marked incomplete.
4. **Aggregation never crosses a trading session** (Approved — blueprint).
5. **Auction records are never merged into intraday candles** (D-08). They **are** included in the daily bar (D-07, D-10).

### B2. Timestamp meaning and timezone

- Every timestamp is an IST (Asia/Kolkata) wall-clock value. The computer's timezone is never used.
- Every intraday timestamp marks the **start** of its interval. The evidence (Deliverable 1, section 5.2) is that regular days run from 09:15 to 15:29 in 375 one-minute candles. A 5-minute bar labelled 09:15 covers 09:15:00 to 09:19:59.
- Daily, weekly and monthly bars are labelled with the period's **first trading date** at 00:00. This matches the existing monthly file, where every month is labelled with its first trading day.

### B3. Sessions — confirmed, candidate or unrecognised

Aggregation uses the session status and type recorded for each day by the database (document 02 v1.1, §6.2). **The observed first and last records are never used as proof of official session times.**

| Day status and type | Continuous window used for aggregation | Auction records | Evidence |
|---|---|---|---|
| `REGULAR` (confirmed or candidate) | 09:15–15:29 (375) | None | 383 NIFTY weekdays (candidate; corrected in v1.2) |
| `CAS` (confirmed or candidate; from 03-Aug-26, CAS instruments) | 09:15–15:14 (360) | Optional `AUCTION_PHASE` at 15:15; `CLOSING_AUCTION` at 15:30 (`source_ts` keeps 15:28 / 15:29 / 15:30) | 67 NIFTY, 59 BANKNIFTY days (candidate) |
| `SPECIAL` / `SPECIAL_CAS` — **confirmed only** (official calendar or owner) | The confirmed session times | Closing print if confirmed. A special-session close time stays `SESSION_CLOSE_UNVERIFIED` until official reference data exists. | NIFTY 21-Oct-25 and BANKNIFTY 08-Nov-26 **after** confirmation |
| `UNRECOGNISED_SESSION_SHAPE` | **Provisional regular window** (09:15–15:29, or 09:15–15:14 under a CAS rule). Records outside it are still returned, as `CANDLE` with `SESSION_UNCONFIRMED`, in intervals anchored as in §B4. | None (no auction labels until confirmed) | NIFTY 21-Oct-25, 01-Feb-25 and 01-Feb-26 (weekend Budget sessions), and BANKNIFTY 08-Nov-26, **before** confirmation; any truncated file. Full-length weekend days meet the provisional window, so their bars are complete but carry `SESSION_UNCONFIRMED`. |

Holidays have no session and therefore no bars. A day with no data that the calendar says is a trading day is reported as `MISSING_DAY`. It is never filled.

### B4. Interval boundaries and alignment (TC-08)

- Intervals are **anchored at the session open of each day**. On a regular day, an N-minute interval k covers `[09:15 + k·N, 09:15 + (k+1)·N)`, clipped to the continuous window. **Confirmed** special sessions anchor at their confirmed open (e.g. Muhurat 13:45 once confirmed). **Unrecognised** days anchor at 09:15, the provisional regular open, never at the observed first record.
- This matches the existing derived files: 1-minute → 3-minute, 3-minute → 15-minute and 5-minute → 15-minute rebuilds all matched with zero differences (Deliverable 1, section 9.1).
- **Alternative not chosen:** clock-aligned hours (10:00, 11:00, …). These would split the first 45 minutes of trading oddly and would not match the existing files or common NSE charting practice.

**Resulting intervals:**

| Timeframe | REGULAR day | CAS day |
|---|---|---|
| 3m, 5m, 15m | 125 / 75 / 25 full intervals | 120 / 72 / 24 full intervals |
| 30m | 12 full (09:15–15:14) plus 15:15–15:29 (15 minutes, `session_truncated`) | 12 full (09:15–15:14) |
| 60m | 6 full (09:15–15:14) plus 15:15–15:29 (15 minutes, `session_truncated`) | 6 full |

On a CAS day there is **no** 15:15 interval: the continuous window ends at 15:14, so nothing is expected there and nothing is missing. The auction records follow as separate rows.

### B5. Building one intraday bar

For each interval, using only `CANDLE` records:

| Output | Rule |
|---|---|
| `open` | `open` of the earliest present candle |
| `high` | maximum `high` |
| `low` | minimum `low` |
| `close` | `close` of the latest present candle |
| `volume` | sum of non-null volumes; null if none present |
| `expected_units` | minutes of the continuous window inside the interval |
| `present_units` | candles present |
| `is_complete` | `present_units == expected_units`. Always False on `UNRECOGNISED_SESSION_SHAPE` days whose provisional expectation is not met, and the bar carries `SESSION_UNCONFIRMED`. |
| `session_truncated` | `expected_units < N` because the session ended |
| `volume_complete` | every present candle has volume **and** `is_complete` |
| `quality_flags` | union of the candles' flags |

**Missing candles.** The bar is built from the candles that exist, with `is_complete = False`. An interval with zero candles produces **no bar**; the missing interval is visible from the day profile.

*Why not fill?* A filled candle would invent prices that never traded. That is exactly what D-11 forbids.

### B6. Forming versus completed bars

A bar is **forming** when its interval has not finished receiving data. All three conditions must hold:

1. It is on the instrument's latest stored trading day.
2. That day is not closed: neither the session's last expected continuous candle nor a closing auction is present.
3. The interval's end lies after the last stored minute.

A forming bar always has `is_complete = False` and `is_forming = True`. A historically incomplete bar has `is_complete = False` and `is_forming = False`.

Q-MAP normally imports after the close, so forming bars are rare. They occur only if a part-day file is imported. The rule exists so that a forming bar is never mistaken for a completed one (Approved — blueprint).

### B7. Daily bars from 1-minute data (indices)

| Output | Rule |
|---|---|
| `open` | `open` of the first `CANDLE` of the day |
| `high` | maximum `high` over `CANDLE` **and** `AUCTION_PHASE` **and** `CLOSING_AUCTION` records (D-07, D-10, unchanged) |
| `low` | minimum `low` over the same records |
| `close` | `close` of the `CLOSING_AUCTION` record if present, otherwise the last `CANDLE` |
| `volume` | **Sum of non-null volumes of `CANDLE` records only** (continuous session). Auction-record volumes are **not** added (revised in v1.1; DQ-21). |
| `volume_complete` | False if any present candle lacks volume, **or** if any auction record of the day carries a non-null volume (its meaning is unverified, so the true daily total is uncertain). The bar then carries the flag `VOLUME_EXCLUDES_AUCTION`. |
| `is_complete` | all expected candles present; on CAS days also a `CLOSING_AUCTION` present |

**Why auction volumes are not added (review item A4; evidence in Deliverable 1 v1.2, §6.5).**
- In the BANKNIFTY source, the final-print volume exactly equals the 15:15 volume on 19 of 43 days, which suggests duplication.
- From 12-Oct-26 the final-print volume becomes millions, which suggests genuine auction quantity.
- The meaning is therefore not established, and summing could double count.
- The auction volumes stay intact on their own 1-minute records, so nothing is lost.

When the vendor's semantics are verified, the rule can be changed. It is recorded as verification item V-09.

**Checked against the actual data:**
- NIFTY 17-Aug-26 from 1-minute: O 24,354.65, H 24,360.10, L 24,226.95, C 24,287.65, V 218,297,189. The 15:30 auction has no volume, so `volume_complete` is True. Identical to the existing daily file.
- NIFTY 03-Aug-26: the auction price 24,774.30 becomes the daily High, against a traded High of 24,609.50, as decided in D-07.
- BANKNIFTY 18-Aug-26: see the manually checked example in §B11.5.

### B8. Weekly and monthly bars (TC-09)

- They are built from **daily** bars: the stored daily data for stocks and sector indices, or the daily bars of B7 for intraday indices.
- **Week** = Monday to Sunday, so weekend special sessions belong to their own week. **Month** = calendar month.
- Label = first trading date in the period. Rules: open first, high max, low min, close last, volume sum.
- `expected_units` = calendar trading days in the period. `present_units` = days present.
- `is_forming` = the period's last calendar day is after the instrument's last stored date.

### B9. Duplicates, holidays, synthetic data — summary

| Situation | Treatment in aggregation |
|---|---|
| Duplicate timestamps | Cannot exist in canonical data (unique key, document 02, section 4). As a defence, aggregation checks again and raises `DataIntegrityError` if one is found. |
| Holidays | No session, no bars, not counted as missing |
| Missing minutes | Bar marked incomplete (B5); never filled |
| Off-tick rows | Under a **verified** tick rule: quarantined at import, so they appear as missing minutes. Under an unverified or observed-only rule: stored with `OFF_TICK_RULE_UNVERIFIED`, included by default with the flag carried into the bar, and treated as missing with `exclude_flagged=True`. |
| `SUSPECT_FILL` rows (on-tick constant-step runs) | Included by default with the flag carried into the bar. With `exclude_flagged=True` they are treated as missing. |
| `AUCTION_PHASE` / `CLOSING_AUCTION` | Separate rows intraday; prices included in daily (B7); volumes excluded from daily volume (B7) |
| Unrecognised session days | Aggregated under the provisional regular window, with the `SESSION_UNCONFIRMED` flag and the `UNRECOGNISED_SESSION_IN_RANGE` warning (B3) |

### B10. Which timeframes are calculated and which are stored (TC-11, Proposed)

**Recommendation for P1: store only the 1-minute (and source daily) data. Calculate every other timeframe on request.**

**Evidence (exploratory benchmark, corrected in v1.1).**

This is an **initial performance experiment** on a repeated sample. It is **not** a verified full-universe benchmark and **not** a measurement on the Project Owner's PC. It shows only that on-demand aggregation is plausibly fast enough to try first. It is not proof of production performance.

| Item | Exact value |
|---|---|
| Script | `QMAP_Exploratory_Benchmark.py` (exploratory; included in the package) |
| Source | `Nifty_1min_09Jan25-06Nov26.parquet` (168,623 rows; 453 trading days; 09-Jan-25 to 06-Nov-26) |
| Record labelling | Flat final record of a day at 15:30 (67 CAS days) or 14:45 (Muhurat 21-Oct-25) → `CLOSING_AUCTION`; all others `CANDLE` (168,555 per copy) |
| Input construction | 6 copies; copy k shifted forward by k × 728 days (104 weeks). This preserves weekdays, and because the sample spans 666 days the copies **never overlap**. |
| Input rows | **1,011,738** (of which 1,011,330 `CANDLE`); **2,718** distinct trading days; **0** duplicate timestamps |
| Grouping rule | `CANDLE` records only. Per calendar day, anchor = that day's first candle; bucket = anchor + floor(minutes since anchor ÷ N) × N. Open = earliest candle's open, high = max, low = min, close = latest candle's close, volume = sum, present = count. (Simplification: the benchmark anchors every day at its first candle. Under §B4 an *unconfirmed* Muhurat day would anchor at 09:15 instead; this changes only the 60-minute count, by +1 bar per copy. It does not affect timing.) |
| Query | DuckDB SQL (in the script): CTE `c` (candles) → CTE `o` (per-day anchor) → CTE `b` (bucket) → `GROUP BY bucket` |
| Environment | Linux container; 1 virtual CPU (Intel Xeon 2.10 GHz); about 3 GB RAM; Python 3.12.3; DuckDB 2.0.0; pandas 3.0.6 |
| Timing method | `time.perf_counter()` around query execution **plus** transfer of the result to pandas; 5 repetitions per timeframe; three independent script runs (ranges of the medians shown) |

| Operation | Output bars | Per single copy | Expected per copy | Median time (5 runs) |
|---|---:|---:|---:|---:|
| 5-minute | **202,266** | 33,711 | 385×75 + 67×72 + 12 = **33,711** ✓ | 0.24–0.28 s |
| 15-minute | **67,422** | 11,237 | 385×25 + 67×24 + 4 = **11,237** ✓ | 0.18–0.23 s |
| 60-minute | **18,588** | 3,098 | 385×7 + 67×6 + 1 = **3,098** ✓ | 0.16–0.17 s |
| Read one calendar year (2025, copy 0 only) | 90,811 rows | — | — | 0.04 s |

**Why v1.0 reported 144,484 five-minute bars.**
- v1.0 shifted the copies by whole **calendar years** (`DateOffset(years=k)`), while the sample spans about 1.83 years, so adjacent copies **overlapped in time**.
- Re-running that construction gives 1,011,738 rows but only **720,808 distinct timestamps (290,930 duplicates)** and 1,928 distinct days. Overlapping minutes fell into the same buckets, so fewer bars were produced.
- The year shift also moved trading days onto different weekdays, and v1.0 bucketed the auction prints together with candles.

The v1.0 figures are withdrawn and replaced by the table above.

**What the result does and does not show.** Aggregating a little over 1 million 1-minute rows, roughly a decade of one index, took about a quarter of a second on a single slow virtual CPU. Validation on the owner's PC and on the real data volume is an M2 acceptance activity (document 06 v1.1). No production-performance claim is made.

| Option | Advantages | Disadvantages |
|---|---|---|
| **On demand (recommended)** | One source of truth; nothing to keep in sync; a correction to 1-minute data is reflected immediately; no extra storage; no maintenance step | A little computation per request |
| Store common timeframes | Instant reads | Every revision or new import must regenerate stored timeframes; a risk of stale or mismatched data; more files and catalogue entries; the blueprint warns against precomputing every timeframe |

**Trigger for reconsidering (P2, F-17).** Add a cache **only** if measured scanner runs on real hardware exceed either of these:
- 5 seconds per instrument for data retrieval, or
- 2 minutes for a full-universe run.

Any cache must then sit behind the interface (A8) and be cleared whenever the underlying data changes.

### B11. Worked aggregation examples (actual data)

These are the "manually verifiable" anchors. Their test-case forms are in document 06.

**B11.1 — 1-minute → 5-minute (NIFTY 09-Jan-25, 09:15 interval)**

| Minute | Open | High | Low | Close |
|---|---:|---:|---:|---:|
| 09:15 | 23,674.75 | 23,689.50 | 23,607.75 | 23,643.70 |
| 09:16 | 23,642.75 | 23,642.75 | 23,631.20 | 23,638.70 |
| 09:17 | 23,639.15 | 23,639.15 | 23,630.50 | 23,638.70 |
| 09:18 | 23,638.35 | 23,638.35 | 23,618.65 | 23,620.90 |
| 09:19 | 23,621.75 | 23,625.00 | 23,614.35 | 23,618.20 |
| **5-min bar** | **23,674.75** (first open) | **23,689.50** (max) | **23,607.75** (min) | **23,618.20** (last close) |

Volume is null, because volume is unavailable before 17-Aug-26. The bar is identical to the existing 5-minute file.

**B11.2 — Interval with missing minutes (BANKNIFTY 19-Aug-26, 13:25 interval):** three candles present (13:25, 13:26, 13:27). O 57,061.60, H 57,076.10, L 57,052.95, C 57,068.40. Volume 174,660 + 114,180 + 2,486 = 291,326. `expected_units` 5, `present_units` 3, `is_complete` False.

**B11.3 — CAS day, 15-minute (NIFTY 17-Aug-26):**
- *15:00 interval* (15:00–15:14, 15 candles): O 24,337.70, H 24,360.10, L 24,330.70, C 24,341.90, V 23,634,943, complete.
- *No 15:15 interval.*
- *Separate row:* `CLOSING_AUCTION` 15:30, O = H = L = C = 24,287.65.

**B11.4 — Truncated hourly interval (NIFTY 31-Jul-25, regular day, 15:15 interval):** 15 candles (15:15–15:29). O 24,762.30, H 24,766.60, L 24,747.55, C 24,765.60. `expected_units` 15, `present_units` 15, `is_complete` True, `session_truncated` True.

**B11.5 — Daily bar including an auction-phase record (BANKNIFTY 18-Aug-26):** O 57,331.10, H 57,584.70, L 57,217.60. C 57,262.40, which is the closing auction (source time 15:29, stored at 15:30). The 15:15 auction-phase record (57,314.55 to 57,308.15) lies inside the range here, so it does not alter High or Low on this day.

*Volume (manually checked, v1.1):*

| Component | Volume |
|---|---:|
| Sum of 360 continuous candles, 09:15–15:14 | **123,512,346** |
| 15:15 auction-phase record | 19,993 (kept on its own record; not added) |
| Final print (15:29 → 15:30) | 19,993 (identical: possible duplicate; not added) |
| **Daily `volume` returned** | **123,512,346**, with `volume_complete` False and flag `VOLUME_EXCLUDES_AUCTION` |
| For comparison: if both auction values were added | 123,552,332, which would double-count if the 19,993 is a repeated figure |

*End of document 03, v1.2.*
