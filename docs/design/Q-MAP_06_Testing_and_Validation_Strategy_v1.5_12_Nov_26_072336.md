# Q-MAP — Testing and Validation Strategy

**Package document 06 | Version 1.5 | 12-Nov-26 | Status: Proposed — v1.5 records the INFY source verification and the seven newly identified INFY G-03 cases; pending ChatGPT review and Project Owner approval**

> **Evidence status in one line:** every Q-MAP test in this document is **specified, not executed**. No Q-MAP code exists yet, so no test has passed or failed. Section 11 separates what has actually been checked, by whom, and on what.

| Field | Value |
|---|---|
| Covers | Test principles, tooling, test data, test layers, the full test-case catalogue with expected results, manual verification, real-data acceptance tests, regression, end-to-end tests, milestone evidence |
| Depends on | Documents 02 v1.1, 03 v1.1, 04 v1.1, 05 v1.0; Deliverable 1 v1.2 |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed tests or sections | Reason (review item) |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | T-DQ-02 split into T-DQ-02a and T-DQ-02b | Off-tick quarantine only under a verified tick rule (A6) |
| 1.1 | T-SES-04, T-SES-05, T-SES-06, T-SES-07, T-SES-09 revised; T-SES-04b, T-SES-05b, T-SES-10 added | Session classification separated; special sessions only when confirmed; truncated-day test (A3, B4) |
| 1.1 | T-MNT-02, T-MNT-03 to T-MNT-05 revised; T-MNT-03b to T-MNT-03d added | All revisions held; false-positive uniform-factor scenario; approve and reject paths (A2) |
| 1.1 | T-MNT-06 replaced by T-MNT-06a to T-MNT-06c; T-MNT-10 added | Instrument-level generation commit with failure injection (A1) |
| 1.1 | T-BKP-01 added | Backup-and-restore consistency validation (B3) |
| 1.1 | T-DA-11 to T-DA-13 added | Provisional completeness, unrecognised sessions, held revisions (A2, A3, B5) |
| 1.1 | T-AGG-07, T-AGG-09, T-AGG-10 revised; T-AGG-13 added | Daily volume excludes auction volume; special anchoring after confirmation (A3, A4) |
| 1.1 | ACC-02, ACC-03 revised; ACC-09, ACC-10 added | Counts by confirmation state; benchmark reproduction and owner-PC performance check (A3, A5) |
| 1.1 | §9 | Milestone evidence updated |
| 1.2 | T-SES-06, T-SES-09, T-CAT-04, ACC-03; new T-SES-11 | Weekend full-length sessions are unrecognised until confirmed (document 02 v1.2 §6.2) |
| 1.2 | New T-FILE-06, T-CAL-01 to T-CAL-03, T-MNT-11 to T-MNT-14, T-DA-14, T-DA-15, T-ENV-01 | Tests for the v1.2 clarifications: R1 1-minute check, official calendar file (G-02), duplicate and conflicting sources (G-16), moved files (G-09), held revisions with new rows, `latest_n` through a requirement, stale-data warning, pinned versions (G-15) |
| 1.2 | T-MSR-02, T-MSR-03 | OD-03 confirmed (reject only): T-MSR-02 now proves a `RENORMALISE` profile is refused; T-MSR-03 withdrawn |
| 1.2 | §9 | Gate 0 and M1 evidence updated |
| 1.2 | new §11 | Test evidence ledger: specified versus executed, and what each kind of check needs |
| 1.3 | T-FILE-06 revised; T-FILE-07 to 09 added | Resolution test now uses the most common time step (TC-26; ChatGPT finding 11) |
| 1.3 | T-DQ-02a revised; T-DQ-02c, T-DQ-07, T-DQ-08 added; ACC-06 revised | G-04 and G-03 as approved by the Owner |
| 1.3 | T-CAL-01 revised; T-CAL-04 added | Calendar file is official only after provenance is recorded (G-02) |
| 1.3 | T-MNT-11, T-MNT-12, T-MNT-13 revised; T-MNT-11b, T-MNT-15, T-MNT-16 added | G-16 (exact SHA-256 only) and G-09 (selected folders only; inaccessible sources reported) |
| 1.3 | §9, §11 | Milestone evidence and ledger updated; this cycle's checks recorded |
| 1.4 | ACC-06; §11.2, §11.3 | ACC-06 adds the three newly identified CONCOR G-03 cases (31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%)); ledger records the CONCOR source verification of the EMA reference values (document 13 v1.1) and the outstanding INFY check |
| 1.5 | ACC-06; §11.2, §11.3 | ACC-06 adds the seven INFY cases found in the source check; ledger records the INFY source verification (T-EMA-03, 04) as done |

All other tests and sections are unchanged.

---

## 1. Principles

1. **A green test report is not proof that a result is correct** (Approved — blueprint). Every important calculation is also checked against a **hand-verified example**. Most examples here use actual market data and can be checked with a calculator or in Excel.
2. **Real data, not only toy data.** Each milestone is accepted on the actual inspected files (section 7), not just on invented fixtures.
3. **Focused testing.** Each change runs the tests for the part it touches plus the shared-interface tests. The full suite runs at milestones (Approved — blueprint).
4. **Expected results are written before the code.** The numbers in this document are the targets Claude 1 must meet.

---

## 2. Tooling (TC-13)

| Item | Choice | Reason |
|---|---|---|
| Test framework | Python's built-in `unittest` | Standard library; no extra dependency |
| Running tests | `tests/run_all_tests.py`, opened in IDLE or Thonny and run with F5. Prints a plain summary (passed, failed, skipped) and the name of every failed test with its message. | The Project Owner works without the command line (Approved — blueprint) |
| Real-data tests | Read the user's source files and data root from the local settings file. If the files are not present, the test is **skipped with a clear message**, not failed. | Market data is not committed to GitHub |
| Small fixtures | Tiny CSV/TXT files under `tests/fixtures`, plus Parquet fixtures generated by the tests from those CSV files | Readable, reviewable fixtures |

---

## 3. Test data

| Kind | Content | Where |
|---|---|---|
| **Hand fixtures** | A few rows each, copying exact values from the actual examples below, plus deliberately broken rows (duplicates, bad OHLC, bad offsets) | `tests/fixtures` (committed) |
| **Real source files** | The inspected files listed in Deliverable 1, section 3 | User's computer (not committed) |
| **Answer keys** | The user's derived Nifty 3/5/15-minute, daily and monthly files. These were proven to reproduce the 1-minute master exactly (Deliverable 1, section 9.1). | User's computer |
| **Golden outputs** | Approved scanner results saved after manual verification, used for regression | `tests/golden` (committed; small JSON) |

---

## 4. Test layers

| Layer | Verifies | Run when |
|---|---|---|
| L1 File and schema | Discovery, readers, column mapping, file-level errors | Any change to readers |
| L2 Import and data quality | Standardisation, record types, validation codes, quarantine | Any change to import or validation |
| L3 Catalogue and maintenance | Catalogue contents, provenance, incremental updates, revisions, atomic writes, integrity | Any change to the database writer |
| L4 Data access | Interface functions, parameters, warnings, exceptions | Any change to the database; every milestone |
| L5 Aggregation | Interval rules, sessions, completeness flags | Any change to aggregation |
| L6 Scanner interface | Contract, registry, runner behaviour | Any change to the engine core |
| L7 Scanner calculations | Each scanner's hand-verified examples and golden outputs | Any change to that scanner; every milestone (regression) |
| L8 Scoring and output | Weights, policies, contributions, JSON/Excel | Any change to scoring or output |
| L9 End-to-end | Complete user workflows on real data | Milestones M1, M2, M3, M5, M6 |

---

## 5. Test-case catalogue

Every test states its **objective**, **input**, **expected result** and **pass/fail condition**. All times are IST, candle-start.

### 5.1 L1 — File discovery and schema

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-FILE-01 | Recognise each inspected format | One file of each type: R1 1-minute Parquet, R2 vendor CSV, R3 6-field TXT, R3 7-field TXT, R4 daily Parquet | Correct reader chosen for each | Reader name matches for all five |
| T-FILE-02 | Missing required column | 1-minute Parquet without `close` | File not imported; `import_log.action = FAILED`; message names `close` | No rows stored; message present |
| T-FILE-03 | Unknown extra columns | NIFTY 1-minute file with its 18 indicator columns | Indicators ignored; one INFO listing them | Canonical file has exactly the canonical columns |
| T-FILE-04 | Unreadable file | Truncated Parquet (first 1,000 bytes only) | `FAILED`, "file is incomplete or damaged" | No partial data stored |
| T-FILE-05 | Unknown file name | `XYZ_data.txt` with no alias | Listed as "unrecognised — please map"; not imported | Nothing stored for it |
| T-FILE-06 | A derived multi-minute file is not taken as 1-minute data (revised v1.3) | `Nifty_3min_02Jan23-30Oct26.parquet`, even if mapped to NIFTY | Rejected: "most common time step is 3 minutes; 1-minute data required"; `FAILED` | Nothing stored |
| T-FILE-07 | Genuine 1-minute data with missing minutes is accepted (v1.3) | BANKNIFTY sample (missing 19-Aug-26 13:28–13:29; CAS jumps 15:14→15:15/15:28/15:29) | Accepted as 1-minute (most common within-day step 1 minute); gaps reported as missing candles, not as a resolution problem | File imported; T-MISS-01 result unchanged |
| T-FILE-08 | Resolution cannot be established (v1.3) | Fixture: 1-minute-style file with one record per day for 40 days | File-level ERROR "cannot establish 1-minute resolution"; nothing imported; reported to the Owner | Nothing stored |
| T-FILE-09 | A coarser day inside a 1-minute file is flagged, not changed (v1.3) | Fixture: 5 days of 1-minute data plus one day of 3-minute records (125 rows) | File accepted; that day kept unchanged with a WARNING issue `RESOLUTION_SUSPECT`; nothing resampled or deleted | Exact |

### 5.2 L2 — Import, parsing and data quality

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-IMP-01 | ISO offset handled | CSV row `2026-08-17T09:15:00+05:30` | Stored `ts` = 17-Aug-26 09:15 (no offset) | Exact equality |
| T-IMP-02 | Wrong offset rejected | Same row with `+00:00` | File `FAILED`: "time offset +00:00 is not IST (+05:30)" | Nothing stored |
| T-IMP-03 | 6- and 7-field lines in one file | Lines `2026-11-06,33270.15,33616.2,32727.05,32977.9,49068677` and `2003-08-25,13933.45,14193.35,13142.6,13522.95,30749892,30749892` | Both imported; field 7 ignored (D-01) | 2 rows; volumes 49,068,677 and 30,749,892 |
| T-IMP-04 | Volume missing accepted | NIFTY 09-Jan-25 09:15 row with null Volume | Stored; `volume` null; no issue (D-03) | Row present; no issue created |
| T-DQ-01 | Invalid OHLC quarantined | Nifty IT `2005-07-01,60.65,3062.75,3041.8,3051.35,…` | Quarantined `INVALID_OHLC`; 01-Jul-05 reported `MISSING_DAY` for NIFTYIT | Row only in quarantine; issue exists |
| T-DQ-02a | Off-tick row under a **verified** tick rule is quarantined (D-11) | Fixture `instrument_rule` NIFTY TICK_SIZE 0.05 with `evidence`, `effective_from`, `confirmed_at` recorded and `verified = true` (G-04); candle with close 22,394.80549 | Quarantined `OFF_TICK_SYNTHETIC`; minute reported missing | Not in canonical data |
| T-DQ-02b | Off-tick row under an **unverified** rule is flagged, not quarantined (A6) | Same candle; rule `OBSERVED_IN_DATA`, `verified = false` (or no rule) | Stored with `OFF_TICK_RULE_UNVERIFIED`; WARNING issue opened; **not** quarantined | Row present and flagged; quarantine empty |
| T-DQ-03 | On-tick constant-step run flagged | Five candles with closes rising by exactly 0.40 each and identical High/Low | Stored with `SUSPECT_FILL`; one WARNING issue | Flag on all 5 rows; issue count 1 |
| T-DQ-04 | Large daily gap flagged, not changed | CONCOR 06-Sep-13 (prev close 270.61, open 171.78) | Stored unchanged with `LARGE_GAP_UNVERIFIED`; issue OPEN with `affects_continuity = True` | Values unchanged; flag and issue present |
| T-DQ-05 | Negative volume | Row with volume −100 | Quarantined | Not in canonical data |
| T-DQ-06 | No automatic price adjustment | CONCOR full file | Stored prices identical to the source for all 6,860 rows | 0 differences |
| T-DQ-02c | A tick rule without the G-04 record stays unverified (v1.3) | Rule with `source = OWNER_CONFIRMED` but no `evidence` (or no `effective_from`) | Data Manager refuses to set `verified = true` and says which item is missing; off-tick rows stay flagged `OFF_TICK_RULE_UNVERIFIED`, not quarantined | Exact |
| T-DQ-07 | Every ±15% move blocks by default, including open-only moves (G-03; v1.3) | CONCOR 15-May-06 (open +16.0%, close −3.6%) and 04-Jun-24 (close −19.2%) | Both stored unchanged with `LARGE_GAP_UNVERIFIED`; both issues `affects_continuity = true`, status `OPEN`; issue evidence shows both percentages | Exact |
| T-DQ-08 | Owner verification unblocks only that occurrence (G-03; v1.3) | Owner marks CONCOR 04-Jun-24 `VERIFIED_OK` | That issue becomes `VERIFIED_OK` with `affects_continuity = false`; every other CONCOR issue unchanged; `CONTINUITY_ISSUE_IN_RANGE` no longer raised for a range containing only 04-Jun-24 | Exact |

### 5.3 Duplicates

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-DUP-01 | Exact duplicate collapsed | NIFTY 09-Jan-25 09:16 row appearing twice with identical values (O 23,642.75, H 23,642.75, L 23,631.20, C 23,638.70) | One row stored; INFO "1 exact duplicate removed" | Count for 09:16 = 1 |
| T-DUP-02 | Conflicting duplicate quarantined | 09:16 twice: close 23,638.70 and close 23,640.00 | **Both** quarantined `DUPLICATE_CONFLICT`. 09:16 reported missing. The 5-minute 09:15 bar is built from 09:15, 09:17, 09:18 and 09:19: O 23,674.75, H 23,689.50, L 23,607.75, C 23,618.20, `present_units` 4, `is_complete` False. | All values exact; neither copy stored |
| T-DUP-03 | Defensive check in aggregation | Canonical file edited by hand to contain a duplicate key | `DataIntegrityError` | Exception raised |

### 5.4 Missing data

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-MISS-01 | Missing candles detected | BANKNIFTY 1-minute file | `day_profile` for 19-Aug-26: expected 360, present 358, missing `13:28-13:29`; no other day has missing candles | Exact match |
| T-MISS-02 | Holidays not counted as missing | NIFTY data around 26-Jan-26 (holiday) | No `MISSING_DAY` issue for 26-Jan-26; calendar `HOLIDAY`, `DERIVED_FROM_DATA`, `verified = false` | Exact |
| T-MISS-03 | Missing day for one instrument | Daily fixture: two instruments, one missing a date the other has | `MISSING_DAY` WARNING for that instrument and date only | One issue |

### 5.5 Session and timestamp validation

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-SES-01 | Regular day | NIFTY 31-Jul-25 | Observed shape `REGULAR_SHAPE`; status `CANDIDATE`, type `REGULAR` (no official calendar loaded); 375 `CANDLE` records 09:15–15:29 | Exact |
| T-SES-02 | CAS day, master style | NIFTY 17-Aug-26 | Shape `CAS_SHAPE`; status `CANDIDATE`, type `CAS`; 360 `CANDLE` (09:15–15:14); `CLOSING_AUCTION` `ts` 15:30, `source_ts` 15:30, price 24,287.65; flag `CAS_CANDIDATE` on all records until confirmed | Exact |
| T-SES-03 | CAS day, raw vendor style (D-09, D-10) | BANKNIFTY 18-Aug-26 | 15:15 record → `AUCTION_PHASE` (O 57,314.55, L 57,308.15 — not flat); 15:29 print → `CLOSING_AUCTION` with `ts` **15:30** and `source_ts` **15:29**, price 57,262.40 | Exact; `source_ts` retained |
| T-SES-04 | Short session **before** confirmation (A3) | NIFTY 21-Oct-25, no calendar entry, no owner confirmation | Shape `OTHER`; status **`UNRECOGNISED_SESSION_SHAPE`**; all 61 records retained as `CANDLE` with `SESSION_UNCONFIRMED`; no auction label; completeness reports "possible missing data 09:15-13:44, 14:46-15:29" against `PROVISIONAL_REGULAR_ASSUMPTION`; WARNING issue | Exact; **not** classified `SPECIAL` |
| T-SES-04b | Same day **after** owner confirmation | Owner confirms 21-Oct-25 as a special session 13:45–14:45 | `REVALIDATE` run creates a new generation: status `CONFIRMED_BY_OWNER`, type `SPECIAL`; 60 candles 13:45–14:44; 14:45 → `CLOSING_AUCTION` with `ts` = `source_ts` = 14:45 and flag `SESSION_CLOSE_UNVERIFIED` (no official close known); expected candles 60, nothing missing | Exact |
| T-SES-05 | Short session with CAS-like ending, before confirmation | BANKNIFTY 08-Nov-26 | Status `UNRECOGNISED_SESSION_SHAPE`; 57 records as `CANDLE` with `SESSION_UNCONFIRMED` | Exact; not `SPECIAL_CAS` |
| T-SES-05b | Same day after owner confirmation | Owner confirms a special session from 14:20 with CAS ending | `CONFIRMED_BY_OWNER`, `SPECIAL_CAS`; continuous 14:20–15:14 (55); 15:15 `AUCTION_PHASE`; 15:29 → `CLOSING_AUCTION` (`source_ts` 15:29; `ts` stays 15:29 with `SESSION_CLOSE_UNVERIFIED`, since the official close is unknown) | Exact |
| T-SES-06 | Classification counts after first import | Full NIFTY and BANKNIFTY samples, no calendar file, no confirmations | NIFTY: **383** `CANDIDATE` REGULAR, 67 `CANDIDATE` CAS, **3** `UNRECOGNISED_SESSION_SHAPE` (21-Oct-25, 01-Feb-25, 01-Feb-26). BANKNIFTY: 59 `CANDIDATE` CAS, 1 `UNRECOGNISED_SESSION_SHAPE` (08-Nov-26). No `SPECIAL` without confirmation. (Corrected in v1.2; derived from Deliverable 1 §9.4, not re-run.) | Exact counts |
| T-SES-07 | Record outside a confirmed session | Fixture: a day with a `CONFIRMED_OFFICIAL` regular calendar entry plus an extra record at 15:31 | Quarantined `OUTSIDE_SESSION`. (Without a confirmed calendar entry the same day becomes `UNRECOGNISED_SESSION_SHAPE` and nothing is quarantined.) | Exact |
| T-SES-08 | Non-whole-minute timestamp | Row at 09:15:30 | Quarantined `BAD_TIMESTAMP` | Not stored |
| T-SES-09 | Totals after import | Full samples | **Before confirmations:** NIFTY 168,556 CANDLE + 67 CLOSING_AUCTION; BANKNIFTY 21,295 CANDLE + 42 AUCTION_PHASE + 59 CLOSING_AUCTION. **After confirming the four special sessions** (NIFTY 21-Oct-25, 01-Feb-25, 01-Feb-26; BANKNIFTY 08-Nov-26): NIFTY 168,555 + 68; BANKNIFTY 21,293 + 43 + 60. 0 quarantined. Before confirmation, NIFTY has **811** records flagged `SESSION_UNCONFIRMED` (61 + 375 + 375) and BANKNIFTY 57. | Exact counts |
| **T-SES-10** | Truncated normal day must not become a special session (A3) | NIFTY 31-Jul-25 source file cut after 11:59 (records 09:15–11:59 only) | Shape `OTHER`; status `UNRECOGNISED_SESSION_SHAPE`; 165 records retained (`SESSION_UNCONFIRMED`); expected 375 (`PROVISIONAL_REGULAR_ASSUMPTION`); missing range `12:00-15:29` reported as "possible missing data"; WARNING issue; **no** `SPECIAL` classification; no auction label | All conditions hold |
| T-SES-11 | Weekend full-length session is not assumed regular (v1.2) | NIFTY 01-Feb-26 (Sunday), no calendar entry, no confirmation; then after the owner confirms a special session 09:15–15:30 | Before: shape `REGULAR_SHAPE`, status `UNRECOGNISED_SESSION_SHAPE`, 375 `CANDLE` records flagged `SESSION_UNCONFIRMED`; 5-minute bars complete but flagged. After: `CONFIRMED_BY_OWNER`, `SPECIAL`; flags removed in the new generation; prices unchanged | Both states exact |

### 5.6 L3 — Catalogue and maintenance

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-CAT-01 | Coverage correct | After initial load of all inspected files | NIFTY 09-Jan-25 09:15 to 06-Nov-26 15:30; BANKNIFTY 17-Aug-26 to 11-Nov-26; CONCOR 26-Nov-98 to 06-Nov-26; INFY 02-Jan-98 to 06-Nov-26; NIFTYIT 25-Aug-03 to 06-Nov-26 | Exact |
| T-CAT-02 | Volume availability recorded | Same | NIFTY volume 17-Aug-26 to 06-Nov-26 | Exact |
| T-CAT-03 | Provenance | Any stored row | `import_id` → `import_log` row whose `source_sha256` equals the actual file's SHA-256 | Hash equal |
| T-CAT-04 | Calendar derivation | Initial load | 57 weekdays `HOLIDAY` (`verified = false`) between 02-Jan-23 and 06-Nov-26 where data overlaps; weekend dates with data present as `SPECIAL` with `source = DERIVED_FROM_DATA`, `verified = false`. These derived rows do **not** confirm any session (document 02 v1.2 §6.2). | Counts as stated for the loaded range; no day_profile becomes `CONFIRMED_*` from them |
| T-CAL-01 | Calendar file becomes official only after provenance is recorded (G-02; revised v1.3) | `nse_market_calendar.csv` for 2025 with the 2025 holidays from Deliverable 1 §9.3 and two `SPECIAL` rows (01-Feb-25 09:15–15:30; 21-Oct-25 13:45–14:45) | **Step 1 (import):** rows stored with `REFERENCE_FILE_UNCONFIRMED`, `verified = false`; completeness basis and session statuses unchanged. **Step 2 (Owner records the source and confirms 2025):** rows become `OFFICIAL_REFERENCE`, `verified = true` with `evidence` and `confirmed_at`; 2025 completeness basis becomes `OFFICIAL_CALENDAR`; 2026 stays provisional; 01-Feb-25 and 21-Oct-25 become `CONFIRMED_OFFICIAL` after re-validation; 21-Oct-25 closing print no longer flagged `SESSION_CLOSE_UNVERIFIED` | Exact |
| T-CAL-02 | Malformed calendar file refused | Same file with `trade_date` `01-02-25`, or a `SPECIAL` row without times, or a duplicated date | File not loaded; message names the line and the problem; catalogue unchanged | Exact |
| T-CAL-04 | A changed calendar file loses its official status (v1.3) | After T-CAL-01, edit one row of the file and import it again | New SHA-256 detected; its rows return to `REFERENCE_FILE_UNCONFIRMED`; 2025 completeness back to provisional until provenance is recorded again | Exact |
| T-CAL-03 | Calendar versus data conflict reported, not acted on | File declares a 2025 weekday `TRADING` on which no instrument has data | WARNING issue; nothing changed or filled | Exact |
| T-MNT-01 | Unchanged file skipped | Re-run update with no file changes | Every file `SKIPPED_UNCHANGED`; no data file rewritten | Data-file hashes unchanged |
| T-MNT-02 | Append | CONCOR file plus one new day (09-Nov-26) | Action `APPEND`; new generation active with 6,861 rows; previous generation (6,860) retained | Row count; previous generation intact |
| T-MNT-03 | Uniform-factor revision is **held**, not applied (A2) | CONCOR file with every price before 04-Jul-25 multiplied by 0.8 | Action `HELD_REVISION`; evidence records "uniform factor 0.8000, effective 04-Jul-25, candidate corporate action"; the revised data is saved in `held`; the active generation is **unchanged**; WARNING issue `HELD_REVISION`; data access returns warning `HELD_REVISION_EXISTS` | Active generation fingerprints unchanged |
| **T-MNT-03b** | False positive: uniform factor caused by an **erroneous** source change | CONCOR file in which every price before 01-Jan-20 was mistakenly multiplied by 10 (a vendor unit error, not a corporate action) | Detected as a uniform factor (10.0000), labelled a *candidate* only, **held**; active data unchanged; nothing applied automatically | Active generation unchanged; issue states "candidate — not verified" |
| T-MNT-03c | Owner approves a held revision | T-MNT-03 held revision; owner approves | Run `APPLY_APPROVED_REVISION`: new generation active with revised prices; previous generation retained; import action `APPLIED_APPROVED_REVISION` | New values visible; previous generation readable |
| T-MNT-03d | Owner rejects a held revision | T-MNT-03b held revision; owner rejects | Marked `REJECTED_REVISION`; active data unchanged; the same source fingerprint is not offered again | Exact |
| T-MNT-04 | Unexplained revision held | CONCOR file with one close changed on 01-Jan-20 | `HELD_REVISION`, not uniform; active data unchanged | Active generation fingerprints unchanged |
| T-MNT-05 | Removed rows held | CONCOR file missing its first 10 rows | `HELD_REVISION` (10 removed rows); nothing deleted | Active row count unchanged |
| **T-MNT-06a** | Failure injection: interrupted **during staging** (A1) | NIFTY active generation G (NIFTY_2025 and NIFTY_2026). Update appends one day; inject a failure after `NIFTY_2025.parquet` of the new generation is written to staging, before `NIFTY_2026.parquet` | Active generation still G; `get_bars("NIFTY","1m",...)` for both years returns exactly the pre-update data; next start deletes the staging folder and logs it | All fingerprints of G unchanged; reads identical to pre-update |
| **T-MNT-06b** | Failure injection: interrupted **after the folder rename, before activation** | As 06a, failure after the complete new generation folder `gen_<next>` is renamed into `market\` but before the catalogue transaction | Active generation still G; readers never read `gen_<next>`; next start reports it as unactivated and removes or quarantines it | Reads identical to pre-update; no mixture |
| **T-MNT-06c** | Failure injection: interrupted **inside the activation transaction** | As 06a, process killed during the catalogue transaction | Either the new generation is fully active (the transaction committed), with both years from the new generation, or G is fully active. Never one year from each. | Every file read belongs to one generation |
| T-MNT-07 | Integrity check | Manually replace a canonical file with a different one | Start-up check reports `INTEGRITY_MISMATCH` and offers restore | Detected |
| T-MNT-08 | Pre-run backup | Any update run | New file in `backups\catalogue` before changes | File exists, timestamp before the run start |
| T-MNT-09 | Scanner run never rebuilds | Run an analysis | No `maintenance_run` row created; no data files written | Unchanged |
| T-MNT-11 | Same prices, different files = conflict (G-16 as approved; revised v1.3) | `CONCOR.txt` and the CONCOR Parquet selected together in a fresh initial load | Fingerprints differ, so **both** `SOURCE_CONFLICT`; nothing imported for CONCOR; WARNING issue lists both files (size, rows 6,860 each, dates, fingerprints). After the Owner chooses `CONCOR.txt`, only it is imported (6,860 rows). | No CONCOR data before the choice; exactly one source after |
| T-MNT-11b | Byte-identical copy = duplicate (G-16; v1.3) | `CONCOR.txt` and an exact copy `CONCOR (copy).txt` mapped to CONCOR | Same SHA-256: content imported once; second path `DUPLICATE_SOURCE` | One generation; 6,860 rows |
| T-MNT-12 | Conflicting sources are not imported (G-16) | Two CONCOR text files, one with a changed close on 01-Jan-20 | Neither imported; both `SOURCE_CONFLICT`; WARNING issue listing the files; after the Owner picks one, only that one is imported; no merge | Exact |
| T-MNT-13 | Moved source file is not imported twice (G-09) | After T-MNT-11, copy `CONCOR.txt` unchanged (same SHA-256) to a new folder and run Update selecting only that folder | `SKIPPED_UNCHANGED`; new path recorded; no new generation | Generation unchanged |
| T-MNT-15 | Inaccessible registered source is reported, not removed (G-09; v1.3) | Rename the registered `CONCOR.txt` in its folder; run Update selecting that folder | WARNING `SOURCE_INACCESSIBLE` naming the path and reason; registration kept; active data and generation unchanged; the renamed file is listed as unrecognised | Generation fingerprints unchanged |
| T-MNT-16 | Only selected folders are in scope (G-09; v1.3) | Sources registered in folders A and B; Update selects only A | Nothing in B examined; report lists B's registered sources as "not in scope for this update"; B's instruments unchanged | Exact |
| T-MNT-14 | Held revision also holds new rows, visibly | CONCOR file with every price before 04-Jul-25 × 0.8 **and** one new day 09-Nov-26 | `HELD_REVISION`; active data still ends 06-Nov-26; `get_bars("CONCOR","1D", end="2026-11-09", latest_n=5)` returns the unrevised closes to 06-Nov-26 with warnings `HELD_REVISION_EXISTS` and `RANGE_TRUNCATED_END` | Exact |
| T-MNT-10 | Retention never removes a needed generation | 12 update runs | Generations referenced by any of the last 10 catalogue backups still exist; older ones pruned only after a successful run | Exact |
| **T-BKP-01** | Backup and restore produce a consistent database (B3) | 1) Record `get_bars` results and row counts for NIFTY and CONCOR. 2) Run an update (new day). 3) Restore the catalogue backup taken before the update. 4) Run **Check integrity**. | Integrity check passes (every active-generation file exists with matching fingerprint and row count); the newer generation is reported as unactivated; `get_bars` results and row counts equal step 1 exactly | Catalogue and Parquet generations mutually consistent; results identical |

### 5.7 L4 — Data-access interface

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-DA-01 | Unknown instrument | `get_bars("NIFTI", "1D")` | `UnknownInstrumentError` suggesting NIFTY | Exception and message |
| T-DA-02 | Unsupported timeframe | `get_bars("CONCOR", "15m")` | `UnsupportedTimeframeError` listing 1D, 1W, 1MO | Exception |
| T-DA-03 | Bad range | `start = 2026-09-30`, `end = 2026-09-01` | `InvalidRequestError` | Exception |
| T-DA-04 | Holiday-only range | `get_bars("NIFTY", "1m", "2026-01-26", "2026-01-26")` | `status = EMPTY`; warning `NO_DATA_IN_RANGE`; no exception | Exact |
| T-DA-05 | Volume unavailable | `get_bars("NIFTY", "1D", "2025-01-09", "2025-01-31", fields=["close", "volume"])` | Volume null on all rows; warning `VOLUME_UNAVAILABLE`; `status = PARTIAL` | Exact |
| T-DA-06 | Continuity warning | `get_bars("NIFTYIT", "1D", "2004-01-01", "2004-12-31")` | Warning `CONTINUITY_ISSUE_IN_RANGE` referencing 28-May-04 | Present |
| T-DA-07 | Latest bars | `get_bars("CONCOR", "1D", latest_n=5, fields=["close"])` | 417.85, 419.15, 425.10, 440.85, 439.80 for 02-Nov-26 to 06-Nov-26 | Exact |
| T-DA-08 | Database locked | Data Manager holds write access | `DatabaseUnavailableError` with plain message | Exception |
| T-DA-09 | Meta always present | Any successful call | `meta` contains timezone `Asia/Kolkata`, `ts_meaning`, `data_version` and every key in document 03, section A5 | All keys present |
| T-DA-10 | Availability report | `check_availability(NIFTYIT, 1D, 2003-01-01..2005-12-31, min_bars=200)` | `PARTIAL`; reasons `RANGE_TRUNCATED_START`, `CONTINUITY_ISSUE_IN_RANGE`, `MISSING_DAY` (01-Jul-05) | Exact codes |
| T-DA-11 | Provisional completeness reported (B5) | Any request, with no official calendar loaded | `meta["completeness_basis"] = "PROVISIONAL_DERIVED_CALENDAR"`; note `COMPLETENESS_PROVISIONAL`; status not changed by the note alone | Exact |
| T-DA-12 | Unrecognised session reported | `get_bars("NIFTY","5m","2025-10-21","2025-10-21")` before confirmation | Warning `UNRECOGNISED_SESSION_IN_RANGE`; status `PARTIAL`; bars flagged `SESSION_UNCONFIRMED` | Exact |
| T-DA-13 | Held revision reported | After T-MNT-03, `get_bars("CONCOR","1D", latest_n=5)` | Unrevised (active) closes 417.85 … 439.80 returned; warning `HELD_REVISION_EXISTS` | Exact |
| T-DA-14 | `latest_n` through a requirement (v1.2) | `context.fetch(DataRequirement("CONCOR","1D", end="2026-11-06", required_fields=("close",), latest_n=5))` from the fixture scanner | Same five closes as T-DA-07; `data_references` records `latest_n = 5` | Exact |
| T-DA-15 | `RANGE_TRUNCATED_END` only for real staleness | CONCOR `end = 2026-11-08` (Sunday after the last bar, 06-Nov-26); then `end = 2026-11-10` with no data after 06-Nov-26 | First request: no `RANGE_TRUNCATED_END`. Second: `RANGE_TRUNCATED_END` naming 06-Nov-26 and 10-Nov-26 (09-Nov-26 and 10-Nov-26 are trading days in the derived calendar because BANKNIFTY has data on them) | Exact |

### 5.8 L5 — Timeframe aggregation (manually verifiable)

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| **T-AGG-01** | 1-minute → 5-minute | NIFTY 09-Jan-25, 09:15–09:19 (five candles, document 03, B11.1) | One bar at 09:15: O **23,674.75**, H **23,689.50**, L **23,607.75**, C **23,618.20**, volume null, 5/5, complete | All values exact |
| T-AGG-01b | 5-minute with volume | NIFTY 17-Aug-26 09:15–09:19 | O 24,354.65, H 24,357.60, L 24,282.80, C 24,306.65, V **9,824,234** (3,543,906 + 2,066,703 + 1,588,777 + 1,319,775 + 1,305,073) | Exact |
| **T-AGG-02** | Missing minutes / incomplete interval | BANKNIFTY 19-Aug-26 13:25 interval | O 57,061.60, H 57,076.10, L 57,052.95, C 57,068.40, V **291,326**; `expected_units` 5, `present_units` 3, `is_complete` **False**, `is_forming` False | Exact; no filled candle |
| **T-AGG-03** | Closing-auction record, 15-minute | NIFTY 17-Aug-26 | 15:00 bar O 24,337.70, H 24,360.10, L 24,330.70, C 24,341.90, V 23,634,943, complete; **no** 15:15 bar; separate `CLOSING_AUCTION` row at 15:30 = 24,287.65 | Exact |
| T-AGG-04 | Auction excluded on request | Same, `include_auction_records=False` | Last row is the 15:00 bar | Exact |
| **T-AGG-05** | Forming bar | Fixture: NIFTY day ending at 11:02 (latest stored day) | 15-minute 11:00 bar with `is_forming` True, `is_complete` False, `present_units` 3; warning `FORMING_BAR` | Exact |
| T-AGG-06 | Truncated hourly bar | NIFTY 31-Jul-25, 60m | Last bar 15:15: O 24,762.30, H 24,766.60, L 24,747.55, C 24,765.60, 15/15, complete, `session_truncated` True | Exact |
| T-AGG-07 | Daily from 1-minute (CAS day) | NIFTY 17-Aug-26 | O 24,354.65, H 24,360.10, L 24,226.95, C **24,287.65** (auction), V 218,297,189 (auction volume null, so `volume_complete` True) | Equal to the user's daily file |
| T-AGG-08 | Auction sets daily High (D-07) | NIFTY 03-Aug-26 | Daily H = **24,774.30** (traded high 24,609.50) | Exact |
| T-AGG-09 | Daily with auction-phase record (D-10) | BANKNIFTY 18-Aug-26 | O 57,331.10, H 57,584.70, L 57,217.60, C 57,262.40 (OHLC unchanged by v1.1) | Exact |
| T-AGG-10 | Special-session anchoring after confirmation | NIFTY 21-Oct-25, 60m, after T-SES-04b | One bar anchored at **13:45** covering 13:45–14:44 (60/60, complete), then `CLOSING_AUCTION` 14:45. Before confirmation (T-SES-04), anchoring is at 09:15: 60m bars at 13:15 (13:45–14:14, 30 present) and 14:15 (14:15–14:45, 31 present), both incomplete and flagged. | Exact in both states |
| **T-AGG-13** | Daily volume excludes auction-record volume (A4) | BANKNIFTY 18-Aug-26 | Daily `volume` **123,512,346** (sum of 360 candles); 15:15 (19,993) and final print (19,993) **not** added; `volume_complete` False; flag `VOLUME_EXCLUDES_AUCTION`; note `DAILY_VOLUME_EXCLUDES_AUCTION` | Exact; **not** 123,552,332 |
| T-AGG-11 | Excluding flagged rows | T-DQ-03 fixture, `exclude_flagged=True` | Flagged minutes count as missing; bar incomplete | Exact |
| T-AGG-12 | Monthly from daily | NIFTY daily from 1-minute, Feb-25 to Oct-26 | Equal to the user's monthly file for those months; label = first trading date | 0 differences |

### 5.9 L6 — Scanner interface

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-SCI-01 | Registry completeness | All registered scanners | Each exposes `INFO`, `default_parameters`, `validate_parameters`, `data_requirements`, `run`; IDs unique and matching | All pass |
| T-SCI-02 | Score only when OK | Result with status `INSUFFICIENT_DATA` and score 50 | `validate_result` fails → status `ERROR` | Rejected |
| T-SCI-03 | Score range | Results with score 101, −1, NaN | Each rejected | Rejected |
| T-SCI-04 | Interpretation forbidden | Result with non-null `interpretation` | Rejected | Rejected |
| T-SCI-05 | References captured | Fixture scanner fetches CONCOR 1D | `data_references` holds the request, `data_version`, timezone and warnings automatically | Present and correct |
| T-SCI-06 | Exception isolation | Fixture scanner raising `ZeroDivisionError` on one instrument | That result `ERROR` with the message; other instruments `OK`; traceback in log | Run completes |
| T-SCI-07 | Unavailable data | Fixture requiring 10,000 bars of INFY | Scanner not called; result `INSUFFICIENT_DATA` with availability reasons | Exact |
| T-SCI-08 | Determinism (SC-01) | The same run executed twice | Sections 1–4 identical apart from `run_id` and `created_at`; scanner sections byte-identical | Identical |
| T-SCI-09 | Invalid parameters | Fixture with N = 0 | Run refused before start with the scanner's message | Exact |

### 5.10 L7 — Scanner calculations

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| **T-SCC-01** | Sample scanner result (test fixture, document 04, section 7.8) | `fixture_close_vs_sma`, CONCOR, N = 5, to 06-Nov-26 | facts: last close **439.80**, SMA5 **428.55**; calculations: distance **2.6251%** (to 4 dp); score **76.25** (to 2 dp); status OK | Exact to stated precision |
| T-SCC-xx | Per approved scanner | At least three hand-verified examples from that scanner's specification (document 04, section 8), on real data, including an edge case | As written in the specification, computed independently (e.g. in Excel) **before** coding | Exact to specified precision |
| T-SCC-REG | Regression | All scanners, golden inputs | Identical to saved golden outputs unless the scanner version changed with an approved reason | Identical |

### 5.11 L8 — Combined scoring and output

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| **T-SCO-01** | Weighted score | Scores 80, 70, 60; weights 40, 35, 25 | Contributions 32.00, 24.50, 15.00; combined **71.50**; status `COMPLETE` | Exact |
| T-SCO-02 | Weights not totalling 100 | Weights 40, 35, 20 | Profile invalid: "weights total 95, must total 100"; run does not start | Message; no run |
| T-SCO-03 | Duplicate scanner in profile | Same scanner twice | Profile invalid | Rejected |
| T-SCO-04 | Version mismatch | Profile pins major 1; scanner now 2.0.0 | Profile invalid until reconfirmed | Rejected |
| T-SCO-05 | Single-scanner profile | One scanner, weight 100, score 64.3 | Combined 64.3 | Exact |
| T-SCO-06 | Rounding | Combined 70.125 | Displayed 70.13 (round half up); JSON stores 70.125 | Both exact |
| **T-MSR-01** | Missing result, option A | Momentum `INSUFFICIENT_DATA`; policy REJECT | `REJECTED_MISSING_RESULT`; combined **null**; message names the scanner and reason | Exact |
| **T-MSR-02** | Renormalisation is refused (OD-03 confirmed; revised v1.2) | Profile with `missing_result_policy = RENORMALISE` | Profile invalid under W-6; run does not start; message names the field and says only `REJECT` is permitted | Rejected |
| T-MSR-03 | *Withdrawn in v1.2* | — | Option B is not adopted, so a minimum-weight test has nothing to test. The 75.33 figure in document 05 §5.3 remains only as the illustration behind OD-03. | — |
| T-MSR-04 | Nothing valid | All three missing | `NO_VALID_RESULTS`; null | Exact |
| T-MSR-05 | Missing is never zero | Option A or B inputs above | Combined is never 56.50 (the "missing = 0" answer) | Assertion holds |
| T-OUT-01 | JSON round trip | Any run | JSON read back equals the in-memory results exactly | Equal |
| T-OUT-02 | Integrity hash | Change one score in a copy of the JSON | Recomputed `content_sha256` differs from the stored one | Differs |
| T-OUT-03 | Excel equals JSON | Any run | Every score, weight and contribution in Excel equals the JSON (after display rounding) | Equal |
| T-OUT-04 | Unwritable folder | Read-only output folder | Clear message; no partial file left | Exact |

---

## 6. Manual verification protocol

For every milestone that produces analytical numbers:

1. Pick at least **three cases**: a normal one, an edge case (gap, auction day, short history) and one chosen by the Project Owner.
2. Compute the expected values **independently**. Use a calculator or Excel on the raw rows for aggregation and scoring, or the scanner specification's own worked method for scanners.
3. Compare with Q-MAP's output at the specified precision.
4. Record each check in the milestone evidence: case, inputs, hand result, Q-MAP result, match (Yes/No), checked by, date (dd-mmm-yy).

A milestone is not accepted while any recorded check shows "No" without an approved explanation.

---

## 7. Real-data acceptance tests

These use the actual files from Deliverable 1. The expected figures come from that inspection.

| ID | Objective | Expected result |
|---|---|---|
| ACC-01 | Aggregation reproduces the user's derived files over the overlap 09-Jan-25 to 30-Oct-26 | 3m, 5m, 15m, daily and monthly: **0 differences** in O/H/L/C. The intraday 15:30 rows are compared with Q-MAP's `CLOSING_AUCTION` rows. This holds both before and after the 21-Oct-25 special session is confirmed: 13:45 lies on the 09:15 grid for 3, 5 and 15 minutes, and the daily OHLC is the same either way. Volume is not part of ACC-01 (DQ-21). |
| ACC-02 | Import totals | As T-SES-09, in both states; CONCOR 6,860; INFY 7,169; NIFTYIT 5,760 stored + 1 quarantined (01-Jul-05) |
| ACC-03 | Session classification | As T-SES-06; after confirming the CAS rule and the four special sessions (three NIFTY, one BANKNIFTY), every day is `CONFIRMED_BY_OWNER` |
| ACC-04 | Completeness | BANKNIFTY: only 19-Aug-26 13:28–13:29 missing. NIFTY sample: no missing candles. |
| ACC-05 | Text and Parquet equivalence | Importing CONCOR.txt into one fresh data root and the CONCOR Parquet into another yields identical canonical data. (Selecting both in **one** load is a G-16 conflict — T-MNT-11.) |
| ACC-06 | Known issues represented | Issues exist for CONCOR 26-May-04, 27-May-04, 15-May-06, **31-Jan-08**, 06-Sep-13, **20-Mar-20**, **10-Aug-20**, 04-Jun-24; INFY **08-Aug-00, 11-Apr-01, 18-Apr-01, 10-Apr-03**, 24-Oct-03, **11-Jan-13, 12-Apr-13, 22-Oct-19**; NIFTYIT 28-May-04 — **each with `affects_continuity = true`** until the Owner verifies it (G-03); quarantine for NIFTYIT 01-Jul-05. *(Bold cases were found in the source checks: CONCOR in v1.4, document 13 §4; INFY in v1.5, document 13 §6. This list covers the inspected files only.)* |
| ACC-07 | Auction effect on daily bars | NIFTY daily H/L set by the auction on exactly 16 of 67 CAS days (list in Deliverable 1 workbook, CAS_Effect) |
| ACC-08 | Calendar | Absent weekdays and weekend sessions match Deliverable 1, section 9.3 and 9.4, for the loaded date range; all derived entries `verified = false` |
| ACC-09 | Benchmark reproduction (exploratory evidence, not acceptance of performance) | Running `QMAP_Exploratory_Benchmark.py` on the NIFTY sample reproduces 1,011,738 input rows, 2,718 days, and 202,266 / 67,422 / 18,588 bars at 5 / 15 / 60 minutes |
| ACC-10 | Performance on the owner's PC (M2) | Measured with the real loaded data on the owner's Windows PC. Retrieval plus aggregation of the full available history of one instrument at 5 minutes is recorded. Under 5 seconds keeps on-demand aggregation; above that triggers the F-17 review (document 03 v1.1, §B10). |

**Note on 2023–24 data.** If the full master is later loaded, the derived-file comparison for 2023–24 is **expected** to differ on the five days with interpolated candles (Deliverable 1, section 7.2), because Q-MAP quarantines off-tick rows. Those differences are correct behaviour and must be listed, not "fixed".

---

## 8. End-to-end tests

| ID | Workflow | Expected outcome |
|---|---|---|
| E2E-01 | Fresh data root → initial load of all inspected files via the Data Manager → `list_instruments` → `get_bars` for each instrument | Catalogue and coverage as T-CAT-01; validation report written; all requests answer correctly |
| E2E-02 | Incremental update: add one new day to CONCOR and a modified historical close to INFY | CONCOR `APPEND`; INFY `HELD` with an issue; report lists both; analysis still runs on held data |
| E2E-03 | Analysis Runner (manual checklist) | Folder pickers work; Run disabled until inputs are valid; progress, elapsed time and log update; closing the window mid-run shuts down cleanly with no errors; output files open in Excel and Notepad |
| E2E-04 | Reproducibility | The same run twice → identical sections 1–4 apart from run ID and timestamp; identical `content_sha256` when those two fields are excluded |
| E2E-05 | Scoring path | Approved scanners → profile → combined scores in JSON and Excel; one instrument with a missing result shows the approved policy outcome |

---

## 9. Evidence required at each milestone

| Milestone | Required evidence |
|---|---|
| Gate 0 | T-ENV-01 run on the owner's PC; version printout recorded |
| M1 Local database foundation | L1–L3 tests pass, **including T-SES-10, T-SES-11, T-MNT-03b, T-MNT-06a to 06c, T-MNT-11, 11b and 12 to 16, T-FILE-06 to 09, T-DQ-02c, T-DQ-07, T-DQ-08 and T-BKP-01** (T-CAL-01 to 04 only if the owner supplies a calendar file); ACC-02 to ACC-06 and ACC-08 pass; E2E-01 run by the Project Owner; validation report reviewed |
| M2 Data interface and aggregation | L4–L5 tests pass; ACC-01, ACC-07 and **ACC-10** pass; manual verification of T-AGG-01, 02, 03, 07 and **13** recorded |
| M3 First scanner | L6 tests; that scanner's T-SCC tests; manual verification of three cases; golden output saved |
| M4 Further scanners | As M3 per scanner; T-SCC-REG shows earlier scanners unchanged |
| M5 Combined scoring | L8 tests; E2E-05; manual check of one combined score from the JSON with a calculator |
| M6 Practical output | E2E-03 and E2E-04 performed by the Project Owner |

---

## 10. Limits of this test strategy

- Real-data acceptance figures come from samples. When the full master and the stock universe are loaded (V-04), new acceptance figures must be derived from the exploratory inspection of those files before they are treated as expected results.
- Tests cannot prove that an unverified source record is true (CONCOR 2013, Nifty IT 2004). They prove only that Q-MAP **flags** it.
- GUI behaviour is checked manually (E2E-03), not automatically, to avoid adding a GUI test framework.
- The failure-injection tests (T-MNT-06a to 06c) simulate interruptions at defined points through a test hook. They cannot reproduce every possible power-loss timing on Windows. The design's guarantee rests on the single catalogue transaction as the commit point (document 02 v1.1, §9.4).
- The benchmark (ACC-09) is a repeated-sample experiment. Only ACC-10 measures performance on the owner's PC.

## 11. Test evidence ledger (new in v1.2)

This section exists so that nobody mistakes a written expected result for a passed test.

### 11.1 Q-MAP application tests

| Measure | Count | Note |
|---|---:|---|
| Tests specified in this document (T-*, ACC-*, E2E-*) | All | Targets written before coding |
| Tests executed | **0** | No Q-MAP code exists |
| Tests passed | **0** | — |
| Tests failed | **0** | — |
| Tests not yet executed | All | Each becomes executable at the milestone named in §9 |

In particular, the following have **not** been done and must not be reported as done: automated failure-injection testing (T-MNT-06a to 06c); backup-and-restore testing (T-BKP-01); end-to-end testing on the owner's Windows PC (E2E-01 to 05); automated execution of the EMA tests (T-EMA-01 to 16, document 10); the full stock-universe inventory and the pilot load.

### 11.2 What has actually been checked, and by whom

| Kind of check | What | Who and when | Evidence | Re-runnable here? |
|---|---|---|---|---|
| Source inspection on sample files (M0) | All figures in Deliverable 1, including the zero-difference reconciliations (01 §9.1), CAS detection on 67 + 59 days, auction-volume analysis (01 §6.5) | Claude 2, previous chat, 11-Nov-26 | Deliverable 1 v1.2; workbook 01a | **No.** The source files and the scripts 01b/01c are not in this workspace (see document 00 v1.6 §3.2). |
| Exploratory calculations on sample files | Benchmark (03 §B10); EMA reference values and warm-up differences (10 §A7, §B4, §B9) | Claude 2, previous chat | Documents 03 and 10 | **No**, same reason. **No independent verification (Excel or otherwise) of these reference values has been performed by anyone.** Document 10 requires it before M3. |
| **Source verification of EMA reference values (v1.4)** | CONCOR: T-EMA-01, 02, 05, 06, 07, 08, 09, 18 recomputed from `CONCOR.txt` and equal to the written values (T-EMA-09 window-start date corrected; T-EMA-18 conditional values added). Full list of CONCOR ±15% occurrences; Nifty IT findings. **INFY (v1.5): T-EMA-03, 04 recomputed from the INFY daily Parquet and equal to the written values; full INFY ±15% list.** | Claude 2, 12-Nov-26, on Owner-supplied files | Document 13 v1.2 | Yes, with the same files |
| Arithmetic re-verification of documented figures | T-EMA-01 (416.95, 421.025, 430.9375, 435.36875); T-EMA-16 (all 13 scores and states); the six answers and net of T-EMA-02 to 05 from their listed EMA values; the distances in 10 §B8; warm-up residuals (100%, 13.5%, 1.8%, 0.25%, 0.03%); T-AGG-01b volume 9,824,234; T-AGG-02 volume 291,326; T-SCC-01 (428.55, 2.6251%, 76.25); T-SCO-01 (71.50); the 75.33 illustration; the ±15% percentages quoted in documents 02, 09, 10 and 12 | Claude 2, v1.5 cycle; **re-run in the v1.6 closure cycle with the same results** | Recomputed from the values written in the documents | Yes — but this checks arithmetic only, **not** that the written input values match the source data. It is **not** independent verification of the EMA reference values. |
| Design and consistency review | Documents 00–12 cross-checked (v1.5 cycle; repeated in the v1.6 closure cycle); corrections listed in document 00 v1.6 §2 | Claude 2, 11-Nov-26 | Change logs of each revised document | — |
| Package integrity | ZIP integrity, file list, versions, sizes and SHA-256 of every indexed file | Claude 2, v1.6 closure cycle | Results in document 00 v1.6 §5 and the handover note | Yes, by anyone with the ZIP |

### 11.3 What each remaining kind of check needs

| Needs | Checks |
|---|---|
| An implemented Q-MAP application | Every T-*, ACC-* and E2E-* test |
| The owner's Windows PC | T-ENV-01, ACC-10, E2E-01 to E2E-05, the GUI checks |
| The full stock universe | The universe inventory (document 09 §8), pilot selection, M1c acceptance, new acceptance figures for V-04 |
| The full 1-minute master | V-07 (2023–24 fills), the expected ACC-01 differences on fill days |
| (Done in v1.5) | All EMA reference values are source-verified (document 13 v1.2); nothing further is needed from source files for M3 |
| An Owner action first | T-EMA-02, 05, 13, 14 produce values only after the Owner verifies CONCOR 04-Jun-24 (G-03, decided); T-EMA-17 needs the D-EMA-11 decision; T-EMA-18 values are conditional on the Owner verifying 15-May-06 |

### 11.4 Environment test (new in v1.2)

| ID | Objective | Input | Expected result | Pass if |
|---|---|---|---|---|
| T-ENV-01 | Code runs only on the pinned versions (G-15) | `tests/run_all_tests.py` on the owner's PC | The runner first prints the Python, DuckDB, pandas, pyarrow and openpyxl versions and compares them with `requirements.txt`. Any difference is reported at the top of the summary as "untested environment", and the run is not accepted as milestone evidence. | Versions equal the pins |

*End of document 06, v1.5.*
