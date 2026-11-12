# Q-MAP — Consolidated Claude 1 Implementation Handover

**Version 1.0 | 12 Nov 26 | Prepared by Claude 2 (final groundwork close-out) | For Claude 1, with ChatGPT as reviewer**

> **What this document is.** It is the single entry point for implementing Gate 0, M1a, M1b and M2.
>
> - **It does not replace the Owner-approved Design Package v1.10.** It brings together, in one place, three sets of material on top of v1.10:
>   - the final ChatGPT technical rulings;
>   - the Owner's later instructions;
>   - Claude 2's final verification package (v1.2).
> - **Corrections to v1.10 text** are listed in Annex A, each with its status. Where Annex A says a v1.10 statement is outdated, follow Annex A. Report anything else that conflicts; do not resolve it silently.
>
> **Status of approvals:**
> - **Design Package v1.10 is approved by the Project Owner.**
> - **Starting production implementation requires the Owner's explicit authorisation to Claude 1** (see §0, item Q-3).
> - The technical Gate 0 checks are pending.
> - No Q-MAP code exists. No Q-MAP test has been executed.

---

## 0. Status, authority and the first steps

| Item | Status |
|---|---|
| Owner approval of Design Package v1.10 | **Completed** |
| Owner authorisation for Claude 1 to begin production implementation | **Pending — Owner (Q-3).** An earlier Claude 2 chat handover recorded GATE-0 as "approved; Claude 1 authorised for Gate 0, M1a, M1b and M2". The close-out assignment lists a separate authorisation as still to come. **Do not write production code until the Owner confirms it to you.** |
| Gate 0 — technical (pins and T-ENV-01) | **Pending — Claude 1, then the Owner** |
| M1a, M1b, M2 | Not started; specified; tests and expected results prepared |
| M1c, M3, M4, M5 | Blocked by the Owner decisions in §13 |

**Authority, when documents disagree:**
1. Human-Readable Blueprint v1.0.
2. Technical Blueprint v1.0.
3. Owner decisions, including Owner instructions relayed through ChatGPT (Annex A).
4. ChatGPT technical rulings S-1 to S-6 and T-DA-12 (§7.5).
5. Design Package v1.10.
6. This handover and the Verification Package v1.2, which interpret items 1–5 and must not contradict them.

**First steps once authorised:**
1. Read §1 to §4.
2. Set up the repository as in §4.
3. Complete Gate 0 (§9.1).
4. Start M1a.

**Approved order of work:** M1a → M1b → M2 → M1c → M3 → M4 → M5, with M6 after M3. OD-10 (M2 before M1b) is **not** adopted.

---

## 1. Document map (use these exact versions)

| Purpose | Document |
|---|---|
| Scope and intent | Human-Readable Blueprint v1.0; Technical Blueprint v1.0 |
| Package index (fingerprints) | 00 Master Index v1.10 |
| What the data looks like | 01 Data Inventory and Quality Report v1.4; 01a workbook v1.1 |
| Storage, catalogue, import, validation, maintenance, backup | 02 v1.6 |
| Data-access interface and aggregation | 03 v1.2 (interface 1.1) **plus the rulings in §7.5** |
| Engine and scanner contract (M3 onwards) | 04 v1.3 |
| Combined scoring and output (M5 onwards) | 05 v1.1 |
| Test catalogue | 06 v1.5 **plus T-MNT-17 and the DA cases** of the Verification Package v1.2 |
| Decisions, contradictions, future ideas | 07 v1.6 |
| Original implementation handover | 08 v1.7 (corrected by Annex A) |
| Stock universe and pilot (M1c) | 09 v1.6 |
| EMA scanner (M3) | 10 v1.7; evidence 13 v1.2 |
| Readiness checklist | 11 v1.7 (corrected by Annex A) |
| Owner decisions | 12 v1.5 (corrected by Annex A) |
| Reference results, expected results and evidence specification | Independent Verification Package v1.2 and Reference Results workbook v1.2 |

Version numbers cited *inside* the v1.10 documents (e.g. "02 v1.3", "07 v1.1") are the versions current when each passage was written. **Always read the version listed above.**

---

## 2. Approved architecture and scope

**Two independent components:**

| Component | Contents | Rule |
|---|---|---|
| **Q-MAP Database** (`qmap_database`) | Parquet storage; a DuckDB catalogue file; readers; standardisation; validation; maintenance with generations; one read-only public interface `QMapData` | It is the only door to the data |
| **Q-MAP Analytical Engine** (`qmap_engine`, `qmap_scanners`) | Scanner contract, runner, scoring and output | It never reads storage files directly. It uses `QMapData` through `context.fetch(requirement)` |

**Approved requirements** (08 §2, R-01 to R-18):
- Local, offline, single-user Windows operation.
- Parquet for data and DuckDB for querying. No SQLite and no second metadata store.
- A simple catalogue.
- Validation that reports problems, never silently.
- No fabricated fields.
- Incremental maintenance. A scanner run never triggers a rebuild, and initial load is separate from maintenance.
- Historical revisions are always held for the Owner (OD-04).
- One stable interface.
- Aggregation per the OHLCV rules, respecting IST, sessions, holidays and gaps. 1-minute data is preserved, and nothing is precomputed.
- Two or three independent scanners, with no plug-in framework.
- A transparent, deterministic combined score (OD-02, "Combined Technical Setup Strength"). It is rejected when a required result is missing (OD-03).
- The engine works without AI.
- A beginner-friendly Windows GUI with pickers.
- Backup and restore defined before routine maintenance.
- Decisions D-01 to D-13, OD-01 to OD-09, I-01, I-02, G-03, G-04 and G-16 (§3).

**Technology:**
- Python 3.12.10 on the Owner's PC, run from IDLE or Thonny.
- Third-party packages: `duckdb`, `pandas`, `pyarrow` and `openpyxl` only, with exact `==` pins.
- Standard library: `tkinter`, `unittest`, `json`, `hashlib`, `os`, `shutil`, `datetime`, `dataclasses`, `queue`, `threading`, `logging`.
- The only command-line step is the one-time `pip install -r requirements.txt`.

**Coding standards:**
- Names that state their purpose.
- One task per function.
- Comments explain why.
- File order: Imports → Constants → Helpers → Main logic → Execution.
- Explicit error handling.
- Small changes.
- No unrequested files.

**GUI (I-02):**
- Required: file picker, folder picker, Save As, clear progress and error messages, and a simple consistent interface.
- Long work runs off the main thread. Closing the window mid-run must cause no error (E2E-03).
- Human-readable dates follow the Owner's style, e.g. `17 Aug 26, 09:15 AM`.
- Non-code outputs carry the `dd_mmm_yy_hhmmss` suffix.

**Out of scope:** P2/P3 items (07 §F); cloud; remote APIs; AI integration; the inventory script (G-01); `old-Q-MAP-ignore`.

---

## 3. Applicable decisions

| ID | Decision | Effect on M1a–M2 |
|---|---|---|
| D-01 | NIFTY IT text field 7 is read and ignored | Reader R3 |
| D-03 | Volume is optional; missing volume is not an error | Coverage records the volume dates |
| D-04, D-06 | CAS rules from 03-Aug-26 for CAS instruments; candidate until the Owner confirms | Session classification |
| D-07, D-10 | Auction prices are included in daily H/L, and the closing auction is the daily close | Daily bars |
| D-08 | Auction records are separate rows and never merged into candles | Record classification |
| D-09 | Closing print stamped 15:30 under the CAS rule; original time kept in `source_ts` (mandatory) | Standardisation |
| D-11 | No filled or invented candles | Aggregation and validation |
| D-12 | Indicator columns are not imported | Readers |
| D-13 | NIFTY IT is the separate dataset `NSE_SECTOR_INDEX_DAILY` | Datasets |
| OD-03 | Combined score is rejected when a required result is missing (M5) | — |
| OD-04 | Every historical revision is held for the Owner | M1b |
| OD-05 | No off-tick quarantine without a verified tick rule | Validation |
| OD-07 | Disclose coverage; report "unavailable" when history is insufficient | Interface |
| OD-08 | Net volume deferred | — |
| I-01, I-02 | Python 3.12.10; GUI conventions | Gate 0, all apps |
| G-03 | Every move beyond ±15% (open or close) opens an issue with `affects_continuity = true`; only the Owner's `VERIFIED_OK` unblocks it | Validation (V-PX-05) |
| G-04 | A tick rule is `verified = true` only with evidence, `effective_from` and `confirmed_at` | `instrument_rule` |
| G-09 | An Update examines only the folders selected for it. Inaccessible registered sources are reported as `SOURCE_INACCESSIBLE` and never removed. | M1b |
| G-16 | Only exact SHA-256 matches are duplicates; any other difference is `SOURCE_CONFLICT` for the Owner; never merge or auto-select | M1a, M1b |
| G-15 | Exact pins; tests only on the pins | Gate 0 |
| S-1 to S-6, T-DA-12 | ChatGPT technical rulings | §7.5 |
| TS-01 | Evidence timestamps `YYYY-MM-DD HH:MM:SS`, IST (Owner, Option A) | §11 |

---

## 4. Repository setup (Owner instruction applied)

**Repository and layout:**
- Use a fresh repository named **Q-MAP**. Never use, copy or rely on `old-Q-MAP-ignore`.
- Follow the layout in 08 §4.
- Create folders only when the milestone that needs them begins.
- `requirements.txt` sits at the root with exact pins.

**Approved sample historical-data files may be committed** (Owner permission, relayed in the close-out assignment).
- Put them under `tests\fixtures\source_samples\` with their **original file names unchanged**. The names are referenced throughout the evidence.
- They are test fixtures and acceptance answer keys. They are **not** the live database.
- Tests read them in place or from a temporary copy, and never modify them.
- The derived NIFTY files are answer keys only and are never imported as datasets (02 §3.1; T-FILE-06).

| File | Bytes | Role |
|---|---:|---|
| `Nifty_1min_09Jan25-06Nov26.parquet` | 3,638,795 | Source (NIFTY) |
| `NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet` | 417,440 | Source (BANKNIFTY) |
| `NSE_BANKNIFTY_1.csv` | 2,803,553 | Same data in CSV (reader R2 test; G-16 conflict test) |
| `CONCOR.txt` | 355,117 | Source (CONCOR); R-3 fixtures are built from it |
| `CONCOR_daily 26Nov98-06Nov26.parquet` | 138,313 | Same data in Parquet (T-MNT-11 conflict test) |
| `INFY_daily 02Jan98-06Nov26.parquet` | 144,271 | Source (INFY, authoritative) |
| `Nifty IT.txt` | 343,673 | Source (NIFTYIT) |
| `Nifty_3min_…`, `Nifty_5min_…`, `Nifty_15min_…`, `Nifty_daily_…`, `Nifty_monthly_02Jan23-30Oct26.parquet` | 3,000,898 / 1,941,000 / 781,206 / 147,422 / 22,915 | Derived answer keys (ACC-01) |
| **Total (12 files)** | **13,734,603** | Largest file 3.6 MB |

- **Git LFS is not required.** Every file is far below GitHub's 50 MB warning and 100 MB limit.
- The full SHA-256 of every file is in Annex B. Tests should assert them.
- `INFY.txt` was never supplied, so it is not in the repository.

**Never commit any of the following.** Add them to `.gitignore`:
- the Owner's data root (e.g. `D:\QMAP_DATA`) and anything inside it: `market\`, `staging\`, `held\`, `catalogue\`;
- live databases (`*.duckdb`, `*.duckdb.wal`);
- backups (`backups\`);
- production or full-universe data;
- generated outputs: `logs\`, `reports\`, scanner run outputs, and evidence exports.

Evidence exports go to ChatGPT with each milestone submission, not into the repository.

---

## 5. Database and catalogue requirements (02 v1.6)

**Data root and layout:**
- The Owner chooses the data root with a folder picker. It is outside the repository.
- Market data is stored at `market\<dataset>\<INSTRUMENT>\gen_<NNNNNN>\` (one file per year for intraday data; one file for daily data).
- Datasets: `NSE_INDEX_1M` (NIFTY, BANKNIFTY), `NSE_EQ_DAILY` (CONCOR, INFY), `NSE_SECTOR_INDEX_DAILY` (NIFTYIT).

**Catalogue:** one DuckDB file holding 11 tables (02 §5.2):
1. `dataset`
2. `instrument` (with `active_generation` and `previous_generation`)
3. `field_definition`
4. `coverage`
5. `day_profile`
6. `market_calendar` (with `evidence` and `confirmed_at`)
7. `data_file`
8. `import_log`
9. `maintenance_run`
10. `data_issue`
11. `instrument_rule`

No other tables.

**Status values (02 §5.4):**
- `quality_status`: `UNVALIDATED` / `PASS` / `PASS_WITH_WARNINGS` / `FAIL`. `FAIL` means the latest update was not activated; the previous generation stays readable.
- `completeness_status`: `COMPLETE` / `GAPS_REPORTED` / `UNKNOWN`.
- `completeness_basis`: `PROVISIONAL_DERIVED_CALENDAR` until an official calendar has recorded provenance (G-02).

**Canonical records (02 §4):**
- Intraday rows carry `ts` (naive IST wall clock, interval start), O/H/L/C, nullable volume, `record_type`, `source_ts` and `quality_flags`.
- Duplicate keys are impossible in canonical data.

**Readers R1–R4 (02 §6.1):**
- 1-minute resolution is recognised by the **most common** within-day step, so missing minutes never cause rejection (T-FILE-06 to 09).

**Generation commit (02 §9.4)**, one protocol for every change:
1. Stage.
2. Validate the whole generation.
3. Rename the folder into `market\` (still inactive).
4. Activate it in **one** catalogue transaction.
5. Prune.

- Readers resolve files only through `active_generation`.
- Files of an active generation are never modified in place.
- Start-up recovery handles interruptions at each step.
- V-INT-01 checks fingerprints and row counts at every start.

**Backup (02 §10):**
- A catalogue backup is taken before every maintenance run.
- Retained generations cover the last 10 backups.
- Restore = copy a catalogue backup, then run **Check integrity** (T-BKP-01).

**Logging (02 §11):**
- Every examined file ends with an explicit `import_log.action`.
- Run logs are `logs\qmap_data_manager_<dd_mmm_yy_hhmmss>.log`.
- Validation reports are Excel files with the same suffix.

---

## 6. Session classification and data-quality rules

**Observed day shape (02 §6.2):**

| Shape | Rule |
|---|---|
| `REGULAR_SHAPE` | First record 09:15; continuous to 15:29; nothing after |
| `CAS_SHAPE` | First 09:15; a 15:14 record; nothing 15:16–15:27; last record (at or after 15:15) flat |
| `OTHER` | Anything else |

**Status and type, from authoritative sources only:**
- `CONFIRMED_OFFICIAL`: verified calendar entry.
- `CONFIRMED_BY_OWNER`: Owner confirmation.
- `CANDIDATE` `REGULAR`: regular shape on a weekday.
- `CANDIDATE` `CAS`: CAS shape on or after 03-Aug-26.
- **`UNRECOGNISED_SESSION_SHAPE`** (type null): any weekend day without a confirmation, and any `OTHER` day.
- An observed shape never creates `SPECIAL`.

**Records:**

| Day | Records |
|---|---|
| Regular | All `CANDLE` |
| CAS | Continuous rows → `CANDLE`; 15:15 → `AUCTION_PHASE`; final flat print → `CLOSING_AUCTION`, `ts` 15:30, `source_ts` kept. All carry `CAS_CANDIDATE` while candidate. |
| Unrecognised | All `CANDLE` with `SESSION_UNCONFIRMED`; nothing quarantined or relabelled |

**Expected first-import counts** (source-verified, Verification Package v1.2 §3):

| Instrument | Days by status | Records |
|---|---|---|
| NIFTY | 383 candidate REGULAR, 67 candidate CAS, 3 UNRECOGNISED (01-Feb-25, 21-Oct-25, 01-Feb-26) | 168,556 `CANDLE`, of which 811 flagged `SESSION_UNCONFIRMED`; 67 `CLOSING_AUCTION` |
| BANKNIFTY | 59 candidate CAS, 1 UNRECOGNISED (08-Nov-26) | 21,295 `CANDLE` (57 flagged); 42 `AUCTION_PHASE`; 59 `CLOSING_AUCTION` |

The only missing minutes on recognised days are BANKNIFTY 19-Aug-26 13:28 and 13:29.

**Validation (02 §7.1), key rules:**

| Check | Rule |
|---|---|
| File level (V-FILE-01, V-SCH-01, V-TS-01) | ERROR: the file is not imported (`FAILED`) |
| V-PX-01 (invalid OHLC) | Row quarantined. Example: NIFTYIT 01-Jul-05. |
| V-PX-03 (off-tick) | Quarantined **only** under a verified tick rule; otherwise flagged `OFF_TICK_RULE_UNVERIFIED` |
| V-PX-04 (constant-step run) | `SUSPECT_FILL` flag only |
| V-PX-05 (±15% move) | Stored unchanged with `LARGE_GAP_UNVERIFIED` and an issue with `affects_continuity = true` (G-03). Expected: 17 issues (CONCOR 8, INFY 8, NIFTYIT 1). |
| V-VOL-03 (auction row with volume) | Stored as supplied with `VOLUME_SEMANTICS_UNVERIFIED`; one INFO issue per instrument |
| V-SES-03 (outside a confirmed session) | Quarantined only on confirmed days |
| V-REV-01 (history changed) | Held |
| V-INT-01 (integrity) | ERROR, with a restore offered |

**Source files (02 §9.6; G-09, G-16):**
- An Update examines only the folders selected for it.
- An unchanged SHA-256 gives `SKIPPED_UNCHANGED`.
- A byte-identical copy gives `DUPLICATE_SOURCE`.
- A different file for an instrument that already has a registered source gives `SOURCE_CONFLICT` for **all** the files involved. Nothing is imported until the Owner chooses.

---

## 7. Data-access interface contract (03 v1.2, interface 1.1, plus the rulings)

### 7.1 Public functions — exactly ten

1. `list_datasets()`
2. `list_instruments(dataset_id=None, instrument_type=None, active_only=True)`
3. `describe_instrument(instrument_id)`
4. `supported_timeframes(instrument_id)`
5. `check_availability(requirement)`
6. `get_bars(instrument_id, timeframe, start=None, end=None, *, fields=None, latest_n=None, include_auction_records=True, exclude_flagged=False)`
7. `get_trading_calendar(start, end)`
8. `get_day_profiles(instrument_id, start, end)`
9. `get_issues(instrument_id=None, start=None, end=None, min_severity="WARNING", status="OPEN")`
10. `close()`

Nothing else is public.

### 7.2 Parameters

- **Timeframes:** `1m 3m 5m 10m 15m 30m 60m 1D 1W 1MO`. Intraday codes apply to intraday datasets only; daily datasets support `1D`, `1W` and `1MO`.
- **Dates:** inclusive and interpreted as IST. A date-only `end` covers the whole day. `start > end` raises an error.
- **`fields`:** default is all five (`open`, `high`, `low`, `close`, `volume`). Volume requested where it is absent returns nulls plus a warning.

### 7.3 `BarResult`

- **Shape:** `bars` (DataFrame), `meta` (dict), `status` (`OK` / `PARTIAL` / `EMPTY`).
- **`bars` columns, in this order:** `ts`, `record_type`, `open`, `high`, `low`, `close`, `volume`, `expected_units`, `present_units`, `is_complete`, `is_forming`, `session_truncated`, `volume_complete`, `quality_flags`, `source_ts`.
- **`meta` keys:** as listed in 03 §A5, including `timezone` = `Asia/Kolkata`, `ts_meaning` = `interval_start_ist_wallclock`, `completeness_basis`, `session_summary`, `notes`, `warnings` and `data_version`.
- **`DataRequirement` and `AvailabilityReport`:** as defined in 03 §A5. Report statuses are `AVAILABLE` / `PARTIAL` / `UNAVAILABLE`.

### 7.4 Warnings, notes and exceptions (03 §A6)

**Warnings** (any warning makes the status `PARTIAL`):
- `RANGE_TRUNCATED_START`, `RANGE_TRUNCATED_END`
- `INCOMPLETE_BARS`
- `FORMING_BAR`
- `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE`
- `FLAGGED_ROWS_INCLUDED`
- `CONTINUITY_ISSUE_IN_RANGE`
- `UNRECOGNISED_SESSION_IN_RANGE`
- `HELD_REVISION_EXISTS`
- `NO_DATA_IN_RANGE` (with `EMPTY`)

**Notes** (these never change the status):
- `COMPLETENESS_PROVISIONAL`
- `CANDIDATE_SESSIONS_IN_RANGE`
- `DAILY_VOLUME_EXCLUDES_AUCTION`

**Exceptions** (all inherit from `QMapDataError`):
- `UnknownInstrumentError`
- `UnsupportedTimeframeError`
- `InvalidRequestError`
- `DatabaseUnavailableError`
- `DataIntegrityError`

### 7.5 Final technical rulings (ChatGPT, 12 Nov 26) — apply exactly

| ID | Rule |
|---|---|
| **S-1** | On an unrecognised day for a CAS-candidate instrument (BANKNIFTY 08-Nov-26), use the provisional window 09:15–15:29 **only** to compute expected units. The day stays `UNRECOGNISED_SESSION_SHAPE`, its rows keep `SESSION_UNCONFIRMED`, every bar is incomplete, no record becomes an auction, and the window is never presented as an official session. |
| **S-2** | Auction volumes are kept exactly as supplied. A null auction volume never triggers a volume warning. |
| **S-3** | `list_instruments` with an unknown `dataset_id` raises `InvalidRequestError` naming the value and listing the known datasets. |
| **S-4 / S-4a** | `check_availability`, for a missing **required** field: volume absent throughout → `UNAVAILABLE` + `VOLUME_UNAVAILABLE`; volume absent in part → `PARTIAL` + `VOLUME_PARTIAL`; another field absent throughout → `UNAVAILABLE` + `REQUIRED_FIELD_UNAVAILABLE`; another field absent in part → `PARTIAL` + `REQUIRED_FIELD_PARTIAL`. `missing_fields` lists the actual missing names, and the codes go in `reasons[].code`. Never report `AVAILABLE` while a required field is missing. An empty range is not a missing field. Optional fields never change the status. |
| **S-5** | Volume warnings are based on `CANDLE` records only. Some with volume and some without → `VOLUME_PARTIAL`; all with volume → none; all without → `VOLUME_UNAVAILABLE`. `volume_complete = False` alone never raises `VOLUME_PARTIAL`. |
| **S-6** | `FLAGGED_ROWS_INCLUDED` is raised for the data-quality flags `SUSPECT_FILL`, `OFF_TICK_RULE_UNVERIFIED`, `SESSION_UNCONFIRMED`, `LARGE_GAP_UNVERIFIED`, `LEVEL_BREAK_UNVERIFIED` and `VOLUME_SEMANTICS_UNVERIFIED`, wherever they appear on returned rows. That includes daily bars, whose `quality_flags` are the union of their source rows. It is **not** raised for `CAS_CANDIDATE` or `VOLUME_EXCLUDES_AUCTION`. |
| **T-DA-12** | Every listed warning set is a **minimum**. All mandatory warnings must be present, and all expressly prohibited warnings absent. |

**Interface version.** S-4a adds two reason-code values (`REQUIRED_FIELD_UNAVAILABLE`, `REQUIRED_FIELD_PARTIAL`). They are additive and have been reviewed by ChatGPT. Record them in the code's interface documentation as **"interface 1.1 + rulings of 12 Nov 26"**. The formal version label is for the next Design Package revision (Annex A, E-07).

---

## 8. Aggregation and auction-volume rules (03 Part B; R-5)

### 8.1 Principles

1. 1-minute data is the source of truth. Aggregation is computed on request and nothing is stored.
2. Only real data is aggregated. An interval with no candles produces no bar; an interval with some candles produces an incomplete bar.
3. Aggregation never crosses a session.
4. Auction records are never merged into intraday candles.
5. Timestamps are IST wall clock and mark the **interval start**.
6. Daily, weekly and monthly bars are labelled with the period's **first trading date** at 00:00.

### 8.2 Interval anchoring and windows

- Intervals are anchored at **09:15** each day. Unrecognised days also anchor at 09:15, never at their first observed record.

| Day | Continuous window | Bars at 3m / 5m / 15m |
|---|---|---|
| REGULAR | 09:15–15:29 | 125 / 75 / 25 |
| CAS | 09:15–15:14 | 120 / 72 / 24 — **no 15:15 interval** |

- 30m and 60m bars on a regular day end with a 15:15–15:29 `session_truncated` bar.

### 8.3 Building a bar (from `CANDLE` rows only)

| Output | Rule |
|---|---|
| `open` | First present candle |
| `high` / `low` | Maximum / minimum |
| `close` | Last present candle |
| `volume` | Sum of non-null volumes; null if none |
| `expected_units` | Minutes of the window inside the interval |
| `present_units` | Candles present |
| `is_complete` | `present_units == expected_units`; always False on an unrecognised day whose provisional expectation is not met |
| `volume_complete` | Every present candle has volume **and** `is_complete` |
| `quality_flags` | Union of the candles' flags |
| `is_forming` | Only on the latest stored day while it is not closed (03 §B6) |

### 8.4 Daily bars (indices)

| Output | Rule |
|---|---|
| `open` | First `CANDLE` |
| `high` / `low` | Over `CANDLE`, `AUCTION_PHASE` and `CLOSING_AUCTION` records |
| `close` | `CLOSING_AUCTION` if present, otherwise the last `CANDLE` |
| `volume` | **`CANDLE` rows only** |
| `volume_complete` | False if any candle lacks volume or any auction record has a volume. The bar is then flagged `VOLUME_EXCLUDES_AUCTION`. |
| `is_complete` | All candles present, plus the closing auction on CAS days |

**Weekly and monthly bars** are built from daily bars. A week runs Monday to Sunday; a month is the calendar month. Open first, high max, low min, close last, volume summed.

### 8.5 Auction-volume safeguard — six rules (R-5)

1. Auction records stay separate records.
2. Auction volume is never added to daily volume.
3. The BANKNIFTY final-print volume is kept exactly as supplied, including the zeros and the values equal to the 15:15 volume.
4. No volume is ever inferred, copied, corrected or de-duplicated.
5. `VOLUME_SEMANTICS_UNVERIFIED`, `VOLUME_EXCLUDES_AUCTION`, `volume_complete` False and `DAILY_VOLUME_EXCLUDES_AUCTION` stay intact.
6. The meaning of the pattern (equal on 19 of 43 days; millions from 12-Oct-26) is unconfirmed (V-09), so no logic may rely on it.

The per-day correct and **prohibited** values are in workbook sheet `Auction_Volume_Guard`. Example, 18-Aug-26:

| | Volume |
|---|---:|
| Correct | 123,512,346 |
| Prohibited: candles + final print | 123,532,339 |
| Prohibited: candles + both auction rows | 123,552,332 |

---

## 9. Milestone requirements

### 9.1 Gate 0 — technical (after the Owner's authorisation)

| Item | Requirement |
|---|---|
| Output | `requirements.txt` with exact `==` pins for Python 3.12.10 (`duckdb`, `pandas`, `pyarrow`, `openpyxl`), plus an IDLE script for T-ENV-01 |
| Test T-ENV-01 | `import duckdb, pandas, pyarrow, openpyxl, tkinter` succeeds in IDLE on the **Owner's PC**, and the printed versions equal `requirements.txt` |
| Evidence | EV-12 (`EV12_environment_<ts>.txt` and `requirements.txt`) |
| Acceptance | The Owner confirms the printout came from his PC |

### 9.2 M1a — database foundation on the inspected sample files

| Item | Requirement |
|---|---|
| Scope | Catalogue (11 tables); readers R1–R4; standardisation with separate session classification, record classification and completeness; validation and quarantine; derived calendar, plus the optional official calendar file with provenance (G-02); issue register; initial load; logs; Excel validation report; minimal Data Manager GUI |
| Runnable outcome | The Owner opens `apps\QMAP_Data_Manager.py` in IDLE, picks the data root and the files, runs **Initial load**, sees progress and the validation report, and sees the CAS and unrecognised-day confirmation lists |
| Tests | L1–L3 for M1a (06 v1.5 §5.1–§5.6, §9), including T-SES-06, 09, 10, 11; T-FILE-01 to 09; T-DQ-01 to 08 (incl. 02c, 07, 08); T-MNT-11, 11b; T-CAL-01 to 04 if a calendar file is supplied |
| Real-data acceptance | ACC-02, ACC-04, ACC-06, plus the counts in §6, checked against EV-01 to EV-04 |
| Owner | E2E-01 |

### 9.3 M1b — maintenance, held revisions, generations, backup and restore

| Item | Requirement |
|---|---|
| Scope | Incremental update with change detection (full-overlap comparison); every revision held, with evidence; approve and reject; generation commit with start-up recovery; catalogue backups; Check integrity; restore |
| Tests | T-MNT-01 to 16 and T-BKP-01 (06 §5.6), with failure injection **actually run** through a test hook. The Verification Package v1.2 matrix B-1 to B-13 lists the must / must-not / evidence for each. |
| **New: T-MNT-17a/17b** | A validation failure during an **incremental update** (Verification Package v1.2 §8.2; fixtures in sheet `R3_Fixtures`) |
| Owner | E2E-02 |

**T-MNT-17 in brief.** The existing import tests start from an empty catalogue, so they cannot prove that a **previous** generation survives a failed update. T-MNT-17 tests both failure points of the update flow.

**17a — reading or standardisation fails** (CONCOR):
1. Initial load with `CONCOR.txt` cut to its first 6,859 lines (SHA-256 `e226b249…eca117b`).
2. Replace it with the same file plus a 4-field line for 06-Nov-26 (SHA-256 `04a32652…ec3055bb2`). The result must be `FAILED`, naming the file and line 6,860.
3. Check what must **not** change:
   - the generation, its fingerprints and its 6,859 rows;
   - `get_bars` must return exactly the step-1 result.
4. `quality_status` becomes `FAIL`.
5. Re-running with the same bad file gives `FAILED` again, never `SKIPPED_UNCHANGED`.
6. Replace it with the Owner's original `CONCOR.txt`. The result must be `APPEND`: a new generation with 6,860 rows, the old generation retained, and latest 5 closes of 417.85, 419.15, 425.10, 440.85, 439.80.

**17b — staged-generation validation fails** (NIFTY, two year files):
1. Initial load without 06-Nov-26 (168,262 rows).
2. Update with the full file while the test hook corrupts the staged 2026 file. Validation must fail, staging is discarded, the instrument is `FAIL`, and no 06-Nov-26 row is ever readable.
3. Re-run without the hook. The result must be `APPEND` of 361 rows.

**The follow-up valid update is mandatory evidence** that a failure does not block later maintenance.

**Prohibited in both:**
- any new generation after the failure;
- partial data visible to readers;
- reporting the failed run as a success;
- a failure that needs manual clean-up before the next update.

### 9.4 M2 — data-access interface and aggregation

| Item | Requirement |
|---|---|
| Scope | `access.py` (the ten functions) and `aggregation.py` |
| Runnable outcome | An example script run from IDLE prints:<br>- `list_instruments()`;<br>- NIFTY 5m for 17-Aug-26;<br>- BANKNIFTY 19-Aug-26 with its incomplete 13:25 bar;<br>- the CONCOR latest 5 closes;<br>- one deliberate error message. |
| Tests | T-DA-01 to 15 (warning lists are minimum sets); T-AGG-01 to 13; **DA-1 to DA-24** (Verification Package v1.2 §7; sheet `DA_Expected`) |
| Real-data acceptance | **ACC-01**: zero O/H/L/C differences against the Owner's derived files over 09-Jan-25 – 30-Oct-26 at 3m, 5m, 15m and daily. Monthly is judged on Feb-25 – Oct-26 (Q-1; Jan-25 is a documented coverage difference).<br>**ACC-07**: the auction sets the daily H/L on 16 of 67 CAS days.<br>**ACC-10**: timing on the Owner's PC.<br>Manual verification of T-AGG-01, 02, 03, 07 and 13 recorded. |

---

## 10. Test cases and expected outcomes — where to find them

| Area | Source | Key expected values |
|---|---|---|
| Classification and counts | 06 T-SES-*; workbook `Classification` | §6 |
| Reference days | Workbook `NIFTY_17Aug26_5m`, `NIFTY_17Aug26_15m`, `BNF_19Aug26_5m`, `BNF_19Aug26_15m` | NIFTY 17-Aug-26 5m 09:15: O 24,354.65, H 24,357.60, L 24,282.80, C 24,306.65, V 9,824,234.<br>BANKNIFTY 19-Aug-26 13:25: 3 of 5 minutes, V 291,326. |
| Daily | `Daily_Refs`, `Daily_CrossCheck` (453 days) | NIFTY 17-Aug-26: O 24,354.65, H 24,360.10, L 24,226.95, C 24,287.65, V 218,297,189.<br>NIFTY 03-Aug-26: H 24,774.30 (auction). |
| Whole sample | `CrossCheck_ACC01`, `CrossCheck_DayTypes`, `Incomplete_Bars` | NIFTY 33,712 / 11,238 candle bars at 5m / 15m, plus 67 auction rows.<br>BANKNIFTY 4,261 / 1,421 candle bars, plus 101 auction rows.<br>38 incomplete bars. |
| Monthly | `Monthly_CrossCheck` | 21 months match (Feb-25 – Oct-26) |
| S-1 | `S1_BNF_08Nov26` | 13 bars at 5m and 5 at 15m, all incomplete |
| Interface | `DA_Expected` (DA-1 to DA-24) | Status, must and must-not codes, key values |
| Auction volume | `Auction_Volume_Guard` | Column K correct; L and M prohibited |
| Maintenance | 06 §5.6; Verification Package §8 | B-1 to B-13; T-MNT-17 |
| EMA (M3, later) | 10 v1.7; 13 v1.2 | Not part of M1a–M2 |

**Every test is specified and none has been executed. A green test report alone is never acceptance.**

---

## 11. Required machine-readable evidence (EV-00 to EV-12)

The full specification is in workbook sheet `Evidence_Checklist` (exact names, fields, producer, comparison and tolerance, supplier) and in Verification Package v1.2 §10.

| Milestone | Evidence items |
|---|---|
| Every submission | EV-00 (manifest with SHA-256) |
| Gate 0 | EV-12 |
| M1a | EV-01 to EV-04 |
| M1b | EV-11 (per test: catalogue tables before and after, `get_bars` before and after, run log) |
| M2 | EV-05 to EV-10 |

**Format:**
- CSV in UTF-8, comma-separated, with one header row.
- JSON for `meta` and `AvailabilityReport`.
- Nulls are empty fields; booleans `TRUE` / `FALSE`; no thousands separators.

**Timestamps (Owner-approved):**
- Inside evidence files, use `YYYY-MM-DD HH:MM:SS` in IST wall-clock time, never converted and with no offset (e.g. `2026-08-17 09:15:00`; daily bars `2026-08-17 00:00:00`).
- File names carry `_dd_mmm_yy_hhmmss`.
- Human-readable reports use `17 Aug 26, 09:15 AM`.

**Tolerance:** prices ±0.000001; everything else exact; flags and codes compared as sets.

---

## 12. Prohibited behaviour (from 08 §9, plus the rulings)

Do not implement:
- **Scope:** P2/P3 items; cloud, remote APIs, servers, AI calls; plug-in or event frameworks; SQLite or a second metadata store; precomputed timeframes; caches.
- **Data repair:** automatic application of any historical revision; automatic price adjustment, repair, interpolation or filling; import of indicator columns.
- **Session classification:** a `SPECIAL` session from observed records; treating a derived calendar row or a weekend shape as confirmation; official status for a calendar file without recorded provenance.
- **Data quality and source files:**
  - off-tick quarantine without a verified tick rule;
  - rejecting a 1-minute file because of missing minutes;
  - any exception to the ±15% blocking rule, or unblocking without the Owner's `VERIFIED_OK`;
  - anything but an exact SHA-256 match treated as a duplicate; importing a `SOURCE_CONFLICT` file before the Owner chooses; merging or auto-selecting sources;
  - scanning unselected folders; removing registered sources.
- **Storage:** modifying any file of an active generation.
- **Volume:** adding auction volume to daily volume; inferring, filling or de-duplicating any volume.
- **Interface:** any change to its contract beyond the recorded rulings; warning logic that contradicts S-2, S-5 or S-6.
- **Engine and scoring:** any scanner without an approved specification; adaptive or renormalised scoring; the OD-10 build order; the D-EMA-11 rule or P-01 before the Owner decides.
- **Inventory:** any inventory script (G-01).
- **Tests:** running or accepting tests on unpinned versions.
- **Repository:** code from `old-Q-MAP-ignore`; placeholder folders; unrequested helper files or documentation.

---

## 13. Outstanding Owner decisions and dependencies

| ID | Decision | Needed before | If undecided |
|---|---|---|---|
| **Q-3** | Authorise Claude 1 to begin production implementation | Gate 0 | Nothing is built |
| OD-12 | May M3 start before M1c while M1c is blocked? | When M2 is complete | M3 waits for M1c |
| **D-EMA-11** | No EMA score when a stock's data ends before the analysis date? | **Before M3** | M3 cannot start |
| **D-EMA-12** | Round to 6 decimal places before comparisons; store the score to 2 decimal places? | **Before M3** | M3 cannot pass T-EMA-10 |
| G-11 | Second (and third) scanner | Before M4 | M4 and M5 wait |
| G-10 | First combined profile and weights, including the EMA weight | Before M5 | M5 waits |
| G-01 | Authorise the inventory script | Before M1c | M1c blocked; **not authorised** |
| OD-10, P-01 | Optional proposals, not adopted | — | Baseline applies |

**Owner actions that run alongside the build:**
- Verify each ±15% occurrence (CONCOR 8, INFY 8, NIFTYIT 1). CONCOR 04-Jun-24 blocks the current CONCOR EMA result.
- Confirm the CAS days and special sessions in the Data Manager.

**Technical confirmations pending with ChatGPT:**
- **Q-1:** ACC-01 monthly scope.
- **Q-2:** `FLAGGED_ROWS_INCLUDED` on BANKNIFTY daily bars (DA-10).

Implement as stated in this handover. If either answer differs, the change is limited to that one acceptance scope and that one warning.

---

## 14. Implementation restrictions

- Build only Gate 0, M1a, M1b and M2, and only after the Owner's authorisation (Q-3).
- Use only the inspected sample files listed in §4. No pilot or full-universe load (M1c).
- Do not reopen approved decisions or alter the EMA methodology.
- Raise conflicts and gaps with ChatGPT and the Owner; do not solve them by adding features.
- Every milestone ends with something the Owner can run on actual data, plus the EV files.
- Never report a test as passed unless it was executed on the implementation with the pinned versions.

---

## 15. Responsibility boundary

| Party | Responsibility |
|---|---|
| **Completed by Claude 2** | Data inspection and source findings; independent reference calculations (Verification Package v1.0/v1.1); expected results DA-1 to DA-24; M1b test specifications including T-MNT-17; evidence specification EV-00 to EV-12; Design Package v1.10; this handover; the final cross-document review (Annex A) |
| **Claude 1** | Gate 0 checks and `requirements.txt`; M1a, M1b, M2; executing the prepared tests; producing the evidence files |
| **ChatGPT** | Reviewing Claude 1's implementation and evidence; milestone acceptance against the approved requirements; defects and corrective instructions; confirmations Q-1 and Q-2; the next Design Package revision (Annex A) |
| **Project Owner** | Q-3 and the decisions in §13; Owner-side confirmations; T-ENV-01 on his PC; E2E-01 and E2E-02; milestone acceptance |

Claude 2 is inactive after this handover. Re-engage it only for a specific exceptional offline investigation.

---

## Annex A — Corrections and clarifications to Design Package v1.10 text

**Statuses used:**
- **Status update:** a fact that has changed since v1.10 was written.
- **Ruled:** a ChatGPT technical ruling.
- **Owner instruction:** applied as given.
- **Proposed:** an editorial or acceptance-wording correction that needs ChatGPT's confirmation.

**Claude 2's judgement:** none of these requires an immediate new Design Package revision. The v1.10 baseline stays as approved, and this annex is the controlling list for Claude 1. All items are recommended for the next revision (v1.11), which ChatGPT should own.

| ID | v1.10 location | v1.10 says | Correct position | Status |
|---|---|---|---|---|
| E-01 | 00 header, §4 ("Pending Owner: GATE-0"); 08 header and §7 Gate 0; 11 §2 Gate 0 row and §6 ("not approved"); 12 §3, §5 row 1; HN §5 | Package approval pending | **Owner approval of v1.10 is completed** | Status update |
| E-02 | Same places | GATE-0 bundles package approval with the technical checks | Technical Gate 0 (pins, T-ENV-01, Owner's printout) is **pending**. Production start needs the Owner's explicit authorisation (Q-3). | Status update; Q-3 for the Owner |
| E-03 | 08 §4 last line; 02 §2.1 | Source market files are never placed in the repository | Approved **sample** files may be committed under `tests\fixtures\source_samples\` (§4). The data root, production data, live databases, backups and generated outputs are still excluded. No Git LFS. | Owner instruction |
| E-04 | 02 §6.3; 08 §10; 11 G-17 and §6; 12 §2 (G-17); HN finding 10 | Session counts "calculated, not re-run" | **Source-verified** (Verification Package v1.1/v1.2 §3). No rule changed. | Status update (R-1) |
| E-05 | 06 ACC-01; 08 §7 M2; 11 M2 checklist | "0 differences … monthly … 09-Jan-25 to 30-Oct-26" | Monthly judged on Feb-25 – Oct-26 (as T-AGG-12); Jan-25 is a coverage difference | Proposed (Q-1) |
| E-06 | 06 T-DA-12 | Warning list, pass "Exact" | The list is a **minimum** set; prohibitions apply | Ruled |
| E-07 | 03 §A6 and §A8 | Warning logic and reason codes not fully defined | S-2, S-4a, S-5 and S-6 apply (§7.5). Record the additive reason codes as an interface revision at v1.11. | Ruled |
| E-08 | 03 §B3 (unrecognised row) | "09:15–15:29, or 09:15–15:14 under a CAS rule" | For a CAS-candidate instrument on an unrecognised day: 09:15–15:29 until a CAS rule is **confirmed** (S-1) | Ruled |
| E-09 | 08 §7 quick reference | `qmap_db` | `qmap_database` (as in 08 §4 and §3) | Proposed (editorial) |
| E-10 | 08 §1 reading list ("01 v1.2", "07 v1.1"); 08 §3 title "Proposed architecture (pending review and approval)"; 08 §9 ("07 v1.1"); 11 cross-references ("02 v1.3", "06 v1.3") | Older version labels | Use the versions in §1. The architecture is approved with the package. | Proposed (editorial) |
| E-11 | 11 §5 (must-not list) | M3 waits for D-EMA-11 | M3 waits for **both** D-EMA-11 **and** D-EMA-12 (as 11 §2 and 08 Gate 3 already say) | Proposed (editorial) |
| E-12 | 11 Gate 0 "Evidence: screenshot or text" | Screenshot acceptable | EV-12 machine-readable file required (a screenshot may accompany it) | Owner instruction (R-4, TS-01) |
| E-13 | 06 §9 M1 row; 08 §7 M1 acceptance | T-MNT-17 absent | T-MNT-17a/17b added to the M1b acceptance | Ruled (R-3 adopted by the close-out assignment) |
| E-14 | 06 T-DA-01 to 15 | Narrower expectations | DA-1 to DA-24 (Verification Package v1.2) give the full expected results; where they add detail, they apply | Ruled |
| E-15 | 12 §2 (G-17), 11 G-17 | "Reviewer to confirm" | Counts confirmed from source (see E-04) | Status update |
| E-16 | Earlier Claude 2 chat handover (12 Nov 26, §5, §8) | "Claude 1 authorised for Gate 0, M1a, M1b, M2"; Workstream D (review of Claude 1) belongs to Claude 2 | Authorisation: see Q-3. Milestone review now belongs to **ChatGPT**; Claude 2 is inactive. | Status update; Q-3 for the Owner |

**Unchanged and confirmed by this review:**
- G-01 is **not authorised**.
- D-EMA-11 and D-EMA-12 are outstanding **before M3**.
- G-11 is needed before M4 and G-10 before M5.
- OD-10 and P-01 are proposals, not adopted.
- The EMA methodology D-EMA-01 to 10 is approved.
- Proposals are nowhere treated as approved scope.

---

## Annex B — Approved sample files: full SHA-256 fingerprints

| File | SHA-256 |
|---|---|
| `Nifty_1min_09Jan25-06Nov26.parquet` | `a4928e0d2f16bd6b6c8426297c2337e01e0291e859202c0abe3a372dd3472298` |
| `NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet` | `117c901dfa123302be71633c878748ff145bd616174774341fca772701f32573` |
| `NSE_BANKNIFTY_1.csv` | `94d448669d38aa4387f4c227ade3a87ddb78fbef8fb9cc7cfaf13a50d85380e3` |
| `CONCOR.txt` | `add449571b6bce38d09fe0c339fee2a23c70cde34a88bd1bd6714d7fa5c9d67c` |
| `CONCOR_daily 26Nov98-06Nov26.parquet` | `e3398485035d9c1692561882feb3895bc9df95f826d4ac7a5d8a31bbe24609a8` |
| `INFY_daily 02Jan98-06Nov26.parquet` | `2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01` |
| `Nifty IT.txt` | `7236641b5a04db8f815ecf303b9ac3a305e70e96010b6148d3f6305014eec6ef` |
| `Nifty_3min_02Jan23-30Oct26.parquet` | `31c9aba94c08a068a7bd650398010fb8f1154f2dcb88be3ed034a9b772afb2ab` |
| `Nifty_5min_02Jan23-30Oct26.parquet` | `d5acdcf83b15f43f4c3578c479a276f4574b71de98e8d625e4cab5b14113f040` |
| `Nifty_15min_02Jan23-30Oct26.parquet` | `91ed90d9fe028e94aaf596ea88f8648f44126bfcfc5bd7e20935a555dc231b84` |
| `Nifty_daily_02Jan23-30Oct26.parquet` | `192a5f03a9b85730b7449975c32be6ab968f178d7deea1cbacedc8a774e03018` |
| `Nifty_monthly_02Jan23-30Oct26.parquet` | `3322c27d5d3446502d9a07235ab198f415d655bfb796e34fa6a98331b02c4dbe` |

**R-3 fixtures** (built by the test setup from `CONCOR.txt`):

| Fixture | Size | SHA-256 |
|---|---:|---|
| 17a-INIT | 355,063 bytes | `e226b249691fbfc1eacc22d8f6a17d65e6423209adf4035aec9372526eca117b` |
| 17a-BAD | 355,096 bytes | `04a32652d426dafb332e54af3db5dfc84c546bda21fb0f0d4863270ec3055bb2` |

*End of the Consolidated Claude 1 Implementation Handover v1.0.*
