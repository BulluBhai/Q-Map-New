# Q-MAP — Independent Verification Package (Gate 0, M1a, M1b, M2)

**Version 1.2 (final) | 12 Nov 26 | Prepared by Claude 2 for ChatGPT and Claude 1 | Baseline: Design Package v1.10 (approved by the Owner) plus ChatGPT technical rulings S-1 to S-6 and the T-DA-12 ruling, and the Owner-approved timestamp convention (12 Nov 26)**

**Companion workbook:** `Q-MAP_Independent_Reference_Results_v1.2_12_Nov_26_124620.xlsx`
- 24 sheets. Six were updated in v1.2: README, Change_Log, Rulings, DA_Expected, S1_BNF_08Nov26 (text only) and Evidence_Checklist.
- Every other sheet is value-identical to v1.1. This was checked sheet by sheet.

**Earlier versions:** v1.0 (07:45:16) and v1.1 (10:23:26) of this document and of its workbook are preserved unchanged as separate files.

> **No Q-MAP application test has been executed. There is no production implementation to test.**
>
> - Claude 2 has written no production code and has not accessed Claude 1's repository.
> - v1.2 changes documentation and expected results only. **No aggregation, reference value, comparison or fingerprint was recalculated**, as the close-out assignment instructs. The comparison formulas in the workbook were simply re-evaluated by the spreadsheet on save, with identical results.
> - The single item examined further (§6.3, item Q-2) was checked against the existing v1.1 reference table only.

---

## 0. In short (for the Project Owner)

- **This is the final version of the verification package.** It turns ChatGPT's last technical rulings and your timestamp approval into exact, testable expectations for Claude 1.
- **Nothing was recalculated.** All the v1.1 results stand as they were:
  - the five timeframe cross-checks against your derived files, with zero differences;
  - the reference days;
  - the daily and monthly comparisons;
  - the Bank Nifty auction-volume table;
  - the fingerprints.
- **Every data-access test case (DA-1 to DA-24) is now final.**
  - Each case has a fixed expected status.
  - Each case lists the warnings that must appear and the warnings that must not appear.
  - Each case has a pass rule.
  - No case still depends on an open question.
- **Your timestamp decision is applied.** Evidence files from Claude 1 write times as `2026-08-17 09:15:00` (India time, never converted). Your on-screen reports keep the `17 Aug 26, 09:15 AM` style.
- **Two small technical points go to ChatGPT for confirmation.** Neither needs a decision from you.
  - Q-1: the wording of the monthly comparison test (§6.3).
  - Q-2: one warning on the Bank Nifty daily result (§6.3).

---

## 1. Version history and change log

| Version | Date | Summary |
|---|---|---|
| 1.0 | 12 Nov 26 07:45 | Source checks; classification; 5m and 15m reference days; daily references; incomplete bars; 21 design-value checks; 5m cross-check; DA-1 to DA-17; M1b matrix; acceptance checklist |
| 1.1 | 12 Nov 26 10:23 | ACC-01 at all five timeframes; 15:30-print effects; S-1 to S-4 with examples; DA-18 to DA-24; T-MNT-17; R-4 evidence checklist; R-5 guard table (C-01 to C-11) |
| **1.2** | **12 Nov 26 12:46** | Final rulings and close-out (C-12 to C-20 below). No reference value changed. |

| ID | Change from v1.1 | Where |
|---|---|---|
| C-12 | **S-4a** applied: exact availability reason codes; DA-13 and DA-21 to DA-23 final | §6.1, §7; sheets `Rulings`, `DA_Expected` |
| C-13 | **S-5** applied: volume warnings come from `CANDLE` records only. DA-3, DA-4, DA-10, DA-18 and DA-19 now **prohibit** `VOLUME_PARTIAL`. | §6.1, §7 |
| C-14 | **S-6** applied: `FLAGGED_ROWS_INCLUDED` flag table. DA-3 and DA-4 now **require** it; DA-1, DA-2, DA-5, DA-11 and DA-20 prohibit it. | §6.1, §7 |
| C-15 | DA-10 now **requires** `FLAGGED_ROWS_INCLUDED` (literal application of S-6 with 03 §A5); flagged for ChatGPT confirmation | §6.3 Q-2 |
| C-16 | **T-DA-12 ruling:** every warning list is a minimum set plus explicit prohibitions; each DA case has a pass rule | §6.1, §7.2 |
| C-17 | **Timestamp convention** (Owner-approved Option A) applied; evidence checklist rewritten with exact file names, fields, producer, comparison method, tolerance and supplier | §10; sheet `Evidence_Checklist` |
| C-18 | `S1_BNF_08Nov26` text: "S-5 recommendation" replaced by the final ruling; no value changed | Workbook |
| C-19 | Acceptance checklist updated: Owner approval of v1.10 recorded as **completed**, and kept separate from the technical Gate 0 checks, which are **pending** | §9 |
| C-20 | New discrepancy X-7 (ACC-01 monthly wording); limitations, risks and responsibility boundary finalised | §13–§16 |

---

## 2. Status labels and data availability

| Label | Meaning |
|---|---|
| **Independently calculated and verified** | Calculated by Claude 2 from the original source file |
| **Compared and matched** | Claude 2's reference compared with another file (the Owner's derived files) and found equal |
| **Compared and mismatched** | Compared and found different; each difference listed and explained. **There are none in v1.1 or v1.2.** |
| **Prepared but not executed** | Expected result or test scenario ready to apply to Claude 1's implementation |
| **Not verified** | Could not be checked; the reason is stated |

| File (Owner-supplied) | Size (bytes) | SHA-256 | Used for | Status |
|---|---:|---|---|---|
| `Nifty_1min_09Jan25-06Nov26.parquet` | 3,638,795 | `a4928e0d2f16bd6b6c8426297c2337e01e0291e859202c0abe3a372dd3472298` | All NIFTY references | Identical to handover |
| `NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet` | 417,440 | `117c901dfa123302be71633c878748ff145bd616174774341fca772701f32573` | BANKNIFTY references | Identical |
| `NSE_BANKNIFTY_1.csv` | 2,803,553 | `94d448669d38aa4387f4c227ade3a87ddb78fbef8fb9cc7cfaf13a50d85380e3` | CSV equivalence | Identical |
| `CONCOR.txt` | 355,117 | `add449571b6bce38d09fe0c339fee2a23c70cde34a88bd1bd6714d7fa5c9d67c` | Source checks; R-3 fixtures | Identical |
| `CONCOR_daily 26Nov98-06Nov26.parquet` | 138,313 | `e3398485035d9c1692561882feb3895bc9df95f826d4ac7a5d8a31bbe24609a8` | Source checks | Identical |
| `INFY_daily 02Jan98-06Nov26.parquet` | 144,271 | `2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01` | Source checks | Identical |
| `Nifty IT.txt` | 343,673 | `7236641b5a04db8f815ecf303b9ac3a305e70e96010b6148d3f6305014eec6ef` | Source checks | Identical |
| `Nifty_3min_02Jan23-30Oct26.parquet` | 3,000,898 | `31c9aba94c08a068a7bd650398010fb8f1154f2dcb88be3ed034a9b772afb2ab` | ACC-01 (3m) | **New in v1.1** |
| `Nifty_5min_02Jan23-30Oct26.parquet` | 1,941,000 | `d5acdcf83b15f43f4c3578c479a276f4574b71de98e8d625e4cab5b14113f040` | ACC-01 (5m) | Identical |
| `Nifty_15min_02Jan23-30Oct26.parquet` | 781,206 | `91ed90d9fe028e94aaf596ea88f8648f44126bfcfc5bd7e20935a555dc231b84` | ACC-01 (15m) | **New in v1.1** |
| `Nifty_daily_02Jan23-30Oct26.parquet` | 147,422 | `192a5f03a9b85730b7449975c32be6ab968f178d7deea1cbacedc8a774e03018` | ACC-01 (1D) | **New in v1.1** |
| `Nifty_monthly_02Jan23-30Oct26.parquet` | 22,915 | `3322c27d5d3446502d9a07235ab198f415d655bfb796e34fa6a98331b02c4dbe` | ACC-01 (1MO), T-AGG-12 | **New in v1.1** |

**Not supplied:**
- `INFY.txt` (reference only; the INFY Parquet is authoritative).
- Any derived BANKNIFTY file.
- Any weekly file.

---

## 3. Workstream A1 — Source-data checks (unchanged from v1.0) and R-1

**Status: Independently calculated and verified.** The full table is in sheet `Source_Checks`, unchanged.

| Dataset | Rows | First – last | Duplicate keys | Missing / invalid | OHLC violations | Key observations |
|---|---:|---|---:|---|---:|---|
| NIFTY 1m | 168,623 | 09-Jan-25 09:15 – 06-Nov-26 15:30 | 0 | Volume null on 148,103 rows (every row before 17-Aug-26, plus 57 closing prints) | 0 | 453 days; naive IST; 0 off-tick |
| BANKNIFTY 1m | 21,396 | 17-Aug-26 09:15 – 11-Nov-26 15:29 | 0 | 0 | 0 | 60 days; CSV identical after +05:30 conversion |
| CONCOR | 6,860 | 26-Nov-98 – 06-Nov-26 | 0 | 0 | 0 | Text file identical |
| INFY | 7,169 | 02-Jan-98 – 06-Nov-26 | 0 | 0 | 0 | |
| NIFTY IT | 5,761 | 25-Aug-03 – 06-Nov-26 | 0 | 0 | **1** (01-Jul-05) | Field 7 on 4,873 rows |

**R-1 (recorded as instructed).** The following figures are **source-verified** (sheet `Classification`, and design-value checks T-SES-06 and T-SES-09):

| Instrument | CANDIDATE REGULAR | CANDIDATE CAS | UNRECOGNISED | CANDLE | AUCTION_PHASE | CLOSING_AUCTION | `SESSION_UNCONFIRMED` rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| NIFTY | 383 | 67 | 3 | 168,556 | 0 | 67 | 811 |
| BANKNIFTY | 0 | 59 | 1 | 21,295 | 42 | 59 | 57 |

- These figures appear in 02 §6.3, 06 T-SES-06 and T-SES-09, and document 11. The Design Package had recorded them as "calculated, not re-run".
- **No session-classification rule is changed by this confirmation.**
- Recording the confirmation in the Design Package itself is for its next revision, if ChatGPT so instructs.

---

## 4. Workstream A2 — Aggregation reference results (unchanged from v1.0)

**Status: Independently calculated and verified.** Rules: 02 §6.2 and 03 §B3–§B7, with no official calendar and no Owner confirmations.

| Reference | Bars | Separate rows | Incomplete | Sheet |
|---|---:|---|---|---|
| NIFTY 17-Aug-26 5m | 72 (09:15–15:10) | `CLOSING_AUCTION` ts 15:30, `source_ts` 15:30, 24,287.65, volume null | none | `NIFTY_17Aug26_5m` |
| NIFTY 17-Aug-26 15m | 24 (09:15–15:00) | as above | none | `NIFTY_17Aug26_15m` |
| BANKNIFTY 19-Aug-26 5m | 72 | `AUCTION_PHASE` 15:15 (57,157.75, vol 16,378); `CLOSING_AUCTION` ts 15:30, `source_ts` 15:29 (57,239.75, vol 16,378) | 13:25 bar, 3 of 5 | `BNF_19Aug26_5m` |
| BANKNIFTY 19-Aug-26 15m | 24 | as above | 13:15 bar, 13 of 15 | `BNF_19Aug26_15m` |

Daily references (sheet `Daily_Refs`) and whole-sample totals are unchanged:
- **NIFTY:** 33,712 five-minute and 11,238 fifteen-minute candle bars, plus 67 auction rows.
- **BANKNIFTY:** 4,261 and 1,421 candle bars, plus 101 auction rows.
- **Incomplete bars:** 38, listed in sheet `Incomplete_Bars`.

---

## 5. ACC-01 extended aggregation cross-check (new in v1.1)

### 5.1 Method

| Item | Applied |
|---|---|
| Source of truth | NIFTY 1-minute Parquet; read only, never modified |
| Classification | 02 §6.2 as in §3 |
| Intraday bars | 03 §B4–§B5: intervals anchored at 09:15 each day; CAS window 09:15–15:14; regular and provisional window 09:15–15:29; `CANDLE` rows only; nothing filled |
| Closing print | Kept as a separate `CLOSING_AUCTION` row (ts 15:30), compared with the derived file's 15:30 row (06 ACC-01) |
| Daily bars | 03 §B7: H/L over candle **and** auction records; close = closing auction if present; volume = `CANDLE` rows only |
| Monthly bars | 03 §B8, built from the daily bars; label = first trading date |
| Comparison | Outer join on timestamp (on date for daily and monthly). A price difference counts when \|reference − derived\| > 0.000001. Volumes must be exactly equal, and a null on one side only counts as a mismatch. |
| Overlap | 09-Jan-25 – 30-Oct-26: the first source day to the last derived day |

### 5.2 Results — Compared and matched (all five timeframes)

| Timeframe | Expected records (session rules) | Claude 2 reference | Derived, in overlap | Matched | Only in reference | Only in derived | Duplicate ts in derived | O/H/L/C differences | Max \|diff\| | Volume rows compared | Volume differences |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 3m | 55,648 | 55,648 | 55,648 | 55,648 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0.00 | 6,240 | 0 |
| 5m | 33,414 | 33,414 | 33,414 | 33,414 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0.00 | 3,744 | 0 |
| 15m | 11,180 | 11,180 | 11,180 | 11,180 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0.00 | 1,248 | 0 |
| 1D | 448 | 448 | 448 | 448 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0.00 | 52 | 0 |
| 1MO (Feb-25 – Oct-26) | 21 | 21 | 21 | 21 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0.00 | 3 | 0 |

**Volume null patterns:** in every timeframe, there are 0 rows where one side has volume and the other does not.

**Fingerprints and whole-file facts** (sheet `Derived_Files`):

| File | Total rows | Rows in overlap | Duplicate timestamps (whole file) |
|---|---:|---:|---:|
| 3m | 117,943 | 55,648 | 0 |
| 5m | 70,791 | 33,414 | 0 |
| 15m | 23,639 | 11,180 | 0 |
| Daily | 949 | 448 | 0 |
| Monthly | 46 | 21 full months (plus Jan-25, see §5.5) | 0 |

**What this covers:**
- **ACC-01** is now independently reproduced at every timeframe it names (3m, 5m, 15m, daily, monthly).
- **T-AGG-12** (monthly from daily, Feb-25 – Oct-26, label = first trading date) is satisfied: 21 of 21 months match, labels included.
- **15m and daily** were built directly from 1-minute data. Deliverable 1 §9.1 had rebuilt them from the 3m and 5m files instead, so the earlier result is now confirmed by an independent route.

### 5.3 Expected versus actual counts by session type (sheet `CrossCheck_DayTypes`)

| Timeframe | Candidate REGULAR (383 days) | Candidate CAS (62 days) | UNRECOGNISED (3 days) | Derived − reference |
|---|---|---|---|---:|
| 3m | 125 / day → 47,875 | 120 / day → 7,440, plus 62 rows at 15:30 | 271 (125 + 125 + 21) | 0 |
| 5m | 75 / day → 28,725 | 72 / day → 4,464, plus 62 | 163 (75 + 75 + 13) | 0 |
| 15m | 25 / day → 9,575 | 24 / day → 1,488, plus 62 | 55 (25 + 25 + 5) | 0 |

**Notes on the session types:**
- **No 15:15 interval on CAS days.** The continuous window ends at 15:14, and no derived file has a bar there either.
- **The three unrecognised days.**
  - 01-Feb-25 and 01-Feb-26 are full-length weekend sessions: complete, but flagged `SESSION_UNCONFIRMED`.
  - 21-Oct-25 has records 13:45–14:45 only, so all of its bars are incomplete (21, 13 and 5 bars at 3m, 5m and 15m).
  - Expected bars on these days are the bars that contain data, because intervals with no candles produce no bar (03 §B5).

### 5.4 The separate 15:30 closing print — effect checked (sheet `Auction_Effect`)

| Measure | Overlap (to 30-Oct-26) | Full sample (to 06-Nov-26) |
|---|---:|---:|
| CAS candidate days | 62 | 67 |
| Intraday 15:30 rows in each derived file = reference `CLOSING_AUCTION` rows | 62 | — |
| Days the auction price sets the daily **high** | 6 | 10 |
| Days it sets the daily **low** | 6 | 6 |
| Days it sets high or low (ACC-07 expects 16 of 67) | 12 | **16 — matches ACC-07** |
| Days the daily **close** (auction) differs from the last traded close | 62 | 67 |
| Days on which a "traded candles only" daily would differ from the derived daily file | **62** | — |
| NIFTY auction prints with non-null volume | 0 | 0 |
| Months whose **high** is an auction price | 1 (Aug-26: 24,774.30 from 03-Aug-26; traded-only 24,677.60) | 1 |
| Months whose **close** is an auction price | 3 (Aug, Sep, Oct-26) | 4 (Nov-26 still forming) |

**What this shows:**
- **The derived files follow D-07, D-08 and D-10 exactly.** The print is a separate intraday row, is included in daily and monthly H/L, and is the daily and monthly close.
- **An implementation that ignores the print fails ACC-01 on every CAS day.** It would also fail ACC-07.
- **Volume:** the derived files have null volume on every 15:30 row, and so does the NIFTY source. The NIFTY derived files therefore **cannot** test the auction-volume rule. BANKNIFTY is the test for it (§11).

### 5.5 Coverage differences — not calculation errors

| Item | Finding | Classification |
|---|---|---|
| **Jan-25 monthly bar** | The derived month starts 01-Jan-25 and contains 6 trading days (01–08 Jan) that are not in the 1-minute sample.<br>Differences: open +37.10 (reference 23,674.75 vs derived 23,637.65); high −537.20 (reference 23,689.50 vs derived 24,226.70, which is on 02-Jan-25).<br>Low and close are equal. Labels differ for the same reason (09-Jan-25 vs 01-Jan-25). | Coverage difference — explained. **Not** a calculation error. |
| **Nov-26 monthly bar** | Source only (02–06 Nov-26). Reference: label 02-Nov-26, O 23,227.90, H 25,030.35, L 23,207.05, C 25,030.35 | Not compared — no derived row. The month is forming until 30-Nov-26 (03 §B8). |
| **02–06 Nov-26 daily bars** | Source only. Reference values are in `Daily_CrossCheck`. | Not compared — after the derived file ends |
| **2023–2024 rows in the derived files** | Before the 1-minute sample starts | Not verified — no source. This includes the five filled days of V-07. |
| **Aug-26 monthly volume** | Sum of 11 of 21 days (volume exists from 17-Aug-26); equal to the derived value | Matched. Q-MAP must still report `volume_complete` False for this month. |
| **Weekly (1W)** | No derived weekly file exists | Not verified |
| **BANKNIFTY at any timeframe** | No derived BANKNIFTY files exist; the references are single-source | Independently calculated and verified (no second file to compare against) |
| **21-Oct-25 after Owner confirmation** | ACC-01 says the result holds after confirmation. Structural check: at 3m, 5m and 15m the 14:45 record (the future `CLOSING_AUCTION`) is the only record in its bar, and it is inside the daily H/L either way. | Arithmetic and structural only; the confirmed state was not modelled |

---

## 6. Technical rulings — final (S-1 to S-6, T-DA-12) and the timestamp convention

### 6.1 Rulings as applied

All of the following are **approved** (ChatGPT technical rulings, 12 Nov 26; the timestamp convention is Owner-approved). They are applied directly, not recommended.

| ID | Rule | Implementation must | Must NOT | Applied in |
|---|---|---|---|---|
| **S-1** | Unrecognised day for a CAS-candidate instrument (BANKNIFTY 08-Nov-26): provisional window **09:15–15:29**, used for expected units only | Compute `expected_units` from 09:15–15:29. Keep `UNRECOGNISED_SESSION_SHAPE`, `SESSION_UNCONFIRMED` on all 57 rows, and `UNRECOGNISED_SESSION_IN_RANGE`. Every bar stays incomplete. | Reclassify the day; remove either flag; mark any bar complete; label the 15:15 or 15:29 record an auction; present the window as an official session; override calendar or Owner-confirmation requirements | DA-18, DA-19; sheet `S1_BNF_08Nov26` |
| **S-2** | A null `CLOSING_AUCTION` volume alone never triggers a volume warning | Keep every auction volume exactly as supplied | Infer, copy, fill or correct an auction volume | DA-1, DA-20 |
| **S-3** | Unknown `dataset_id` in `list_instruments` → `InvalidRequestError` | The message names the bad value and lists `NSE_INDEX_1M`, `NSE_EQ_DAILY`, `NSE_SECTOR_INDEX_DAILY` | Return an empty table or ignore the filter | DA-7, DA-24 |
| **S-4 / S-4a** | `check_availability` status and reason codes for missing **required** fields (table below) | `missing_fields` lists the actual missing field names; the codes appear in `AvailabilityReport.reasons[].code` | Report `AVAILABLE` while a required field is missing; list a field in `missing_fields` only because the range has no records | DA-13, DA-21, DA-22, DA-23 |
| **S-5** | Volume completeness is evaluated on `CANDLE` records only (table below) | Derive the warning from the present `CANDLE` rows, including the `CANDLE` rows behind each daily bar | Raise `VOLUME_PARTIAL` from `volume_complete = False` alone. Incomplete price intervals are reported by `INCOMPLETE_BARS`. | DA-1, DA-3, DA-4, DA-10, DA-11, DA-17 to DA-20 |
| **S-6** | `FLAGGED_ROWS_INCLUDED` is raised when a returned record carries a **data-quality** flag (table below) | Check every returned row: `CANDLE` rows, auction rows and daily bars (whose `quality_flags` are the union of their source rows, 03 §A5) | Raise it for `CAS_CANDIDATE` or `VOLUME_EXCLUDES_AUCTION` alone | DA-1 to DA-5, DA-10, DA-11, DA-17 to DA-20 |
| **T-DA-12** | Every warning list in T-DA-12 and in every DA case is a **minimum** required set | All mandatory warnings present; all expressly prohibited warnings absent | Fail a correct implementation because it raises extra warnings that 03 §A6 requires | §7.2 |
| **TS-01** | Machine-readable CSV and JSON evidence uses `YYYY-MM-DD HH:MM:SS` in IST wall-clock time (e.g. `2026-08-17 09:15:00`); daily bars use `00:00:00` | Write times as stored | Append `+05:30` or `Z`; convert to UTC; use `17 Aug 26` inside evidence files | §10 |

Human-readable reports keep the existing style, e.g. `17 Aug 26, 09:15 AM`.

**S-4a — reason codes (exact)**

| Condition | `status` | Reason code |
|---|---|---|
| Required volume absent throughout the range | `UNAVAILABLE` | `VOLUME_UNAVAILABLE` |
| Required volume absent for part of the range | `PARTIAL` | `VOLUME_PARTIAL` |
| Another required field absent throughout the range | `UNAVAILABLE` | `REQUIRED_FIELD_UNAVAILABLE` |
| Another required field absent for part of the range | `PARTIAL` | `REQUIRED_FIELD_PARTIAL` |

`reasons` is the 03 §A5 field (a list of `{code, message}`). `reason_codes` in the evidence file (EV-10) is simply the list of those codes, so this is **not** a change to the interface contract.

**S-5 — volume warnings (`CANDLE` records only)**

| `CANDLE` records in the result | Warning |
|---|---|
| Some with volume, some without | `VOLUME_PARTIAL` |
| All with volume | none |
| All without volume | `VOLUME_UNAVAILABLE` |
| Auction record with null volume (any number) | none on that account |
| `volume_complete = False` only because a bar is incomplete | none on that account (`INCOMPLETE_BARS` covers it) |

**S-6 — flags that raise `FLAGGED_ROWS_INCLUDED`**

| Flag | Triggers? | Where it arises |
|---|---|---|
| `SUSPECT_FILL` | Yes | V-PX-04 |
| `OFF_TICK_RULE_UNVERIFIED` | Yes | V-PX-03 |
| `SESSION_UNCONFIRMED` | Yes | Unrecognised days (02 §6.2) |
| `LARGE_GAP_UNVERIFIED` | Yes | V-PX-05 (G-03) |
| `LEVEL_BREAK_UNVERIFIED` | Yes | NIFTYIT 28-May-04 |
| `VOLUME_SEMANTICS_UNVERIFIED` | Yes | V-VOL-03: every BANKNIFTY auction row with a non-null volume |
| `CAS_CANDIDATE` | No | Covered by the note `CANDIDATE_SESSIONS_IN_RANGE` |
| `VOLUME_EXCLUDES_AUCTION` | No | Covered by the note `DAILY_VOLUME_EXCLUDES_AUCTION` |

### 6.2 S-1 reference values (unchanged from v1.1)

**5-minute** (sheet `S1_BNF_08Nov26`): 13 bars, 14:20–15:25.

| Bars | Expected units | Present units |
|---|---:|---:|
| 14:20 to 15:10 | 5 | 5 |
| 15:15 (58,923.65; volume 0) | 5 | 1 |
| 15:25 (the 15:29 record, 58,850.65; volume 0) | 5 | 1 |

**15-minute:** 5 bars.

| Bar | Expected units | Present units |
|---|---:|---:|
| 14:15 | 15 | 10 |
| 14:30, 14:45, 15:00 | 15 | 15 |
| 15:15 | 15 | 2 |

The day as a whole expects 375 units provisionally, with 57 present.

**Every bar** has `is_complete` False and the flag `SESSION_UNCONFIRMED`. There are no auction rows.

**Every candle has volume**, so under S-5 there is no volume warning. The 15:15 and 15:29 records carry a volume of 0, which is not null.

### 6.3 Items for ChatGPT confirmation (technical; no Owner decision)

Both were found while applying the rulings. Each was examined **only as far as the specific question required**, without any new data calculation.

| ID | Item | Why it needs confirmation | How v1.2 treats it until confirmed |
|---|---|---|---|
| **Q-1** | ACC-01 is worded as "0 differences … 3m/5m/15m/daily/**monthly** over 09-Jan-25 to 30-Oct-26" (06 ACC-01, 08 §7 M2, 11 M2 checklist). The Jan-25 monthly bar cannot match, because the derived month includes 01–08 Jan-25, which is not in the 1-minute sample. This was already documented in v1.1 §5.5. | A literal reading would fail a correct implementation | Monthly ACC-01 is judged on the 21 full months **Feb-25 – Oct-26**, exactly as T-AGG-12 already specifies. Jan-25 is reported, but as a coverage difference (X-7). |
| **Q-2** | DA-10 (BANKNIFTY daily, Aug-26). Each daily bar includes the day's auction records (D-07, D-10). Every BANKNIFTY auction record has a non-null volume, including 5 zero values (existing v1.1 table), so each carries `VOLUME_SEMANTICS_UNVERIFIED` (V-VOL-03). 03 §A5 defines a bar's `quality_flags` as the union of its source rows. | S-6 then **requires** `FLAGGED_ROWS_INCLUDED` for DA-10. The ruling's example — "a daily result carrying only `VOLUME_EXCLUDES_AUCTION` does not trigger" — is correct, but it does not describe BANKNIFTY daily bars. | DA-10 **requires** `FLAGGED_ROWS_INCLUDED` (literal application). If ChatGPT intends daily bars to exclude auction-row flags from `quality_flags`, only this one warning in DA-10 changes. |

### 6.4 S-4 examples (final)

| Case | Requirement | Expected `AvailabilityReport` |
|---|---|---|
| DA-13 | NIFTY 5m, 09–31 Jan-25, required close and volume | `UNAVAILABLE`; `missing_fields` ("volume",); code `VOLUME_UNAVAILABLE`; `estimated_bars` 1,275 |
| DA-21 | NIFTY 1D, 10–21 Aug-26, required close and volume | `PARTIAL`; `missing_fields` ("volume",); code `VOLUME_PARTIAL` (message names 10–14 Aug-26); `estimated_bars` 10 |
| DA-22 | NIFTY 1D, 17–21 Aug-26, required close and volume | `AVAILABLE`; `missing_fields` (); `estimated_bars` 5 |
| DA-23 | NIFTY 1D, 09–31 Jan-25, default fields (volume **optional**) | `AVAILABLE`; `missing_fields` (); an optional field never makes a requirement `UNAVAILABLE` or `PARTIAL` |

---

## 7. Data-access test cases DA-1 to DA-24 (final)

**Status of every case: Prepared but not executed — awaiting Claude 1.** The full machine-readable table is sheet `DA_Expected`. Its columns are:
- call;
- expected status or exception;
- rows;
- warnings or reason codes that must be present;
- warnings that must not be present;
- notes and other meta;
- key values;
- rulings applied;
- pass rule;
- v1.2 change.

### 7.1 Summary

| ID | Request (short) | Status / exception | Must contain | Must NOT contain |
|---|---|---|---|---|
| DA-1 | NIFTY 5m 17-Aug-26 (73 rows) | `OK` | — | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE`, `FLAGGED_ROWS_INCLUDED`, `INCOMPLETE_BARS` |
| DA-2 | DA-1 without auction rows (72) | `OK` | — | as DA-1 |
| DA-3 | BANKNIFTY 5m 19-Aug-26 (74) | `PARTIAL` | `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED` | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE` |
| DA-4 | BANKNIFTY 15m 19-Aug-26 (26) | `PARTIAL` | `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED` | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE` |
| DA-5 | CONCOR 1D `latest_n=5`, close | `OK` (417.85, 419.15, 425.10, 440.85, 439.80) | — | `RANGE_TRUNCATED_END`, `CONTINUITY_ISSUE_IN_RANGE`, `FLAGGED_ROWS_INCLUDED` |
| DA-6 | `NIFTI` | `UnknownInstrumentError` suggesting NIFTY | — | — |
| DA-7 | `list_instruments(dataset_id="NSE_FUT_1M")` | `InvalidRequestError` listing the 3 datasets | — | — |
| DA-8 | NIFTY 5m 26-Jan-26 | `EMPTY` | `NO_DATA_IN_RANGE` | (no exception) |
| DA-9 | NIFTY 5m 03–07 Jun-24 | `EMPTY` | `NO_DATA_IN_RANGE` | (no exception); `RANGE_TRUNCATED_START` optional |
| DA-10 | BANKNIFTY 1D Aug-26 (11 bars) | `PARTIAL` | `RANGE_TRUNCATED_START`, `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED` (Q-2) | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE` |
| DA-11 | NIFTY 1D Jan-25, close and volume (17) | `PARTIAL` | `VOLUME_UNAVAILABLE` | `VOLUME_PARTIAL`, `FLAGGED_ROWS_INCLUDED` |
| DA-12 | CONCOR fields `oi` | `InvalidRequestError` naming `oi` | — | — |
| DA-13 | Availability: volume required, Jan-25 | `UNAVAILABLE`; `missing_fields` ("volume",) | `VOLUME_UNAVAILABLE` | `VOLUME_PARTIAL`, `REQUIRED_FIELD_UNAVAILABLE` |
| DA-14 | CONCOR 15m | `UnsupportedTimeframeError` | — | — |
| DA-15 | NIFTY 7m | `UnsupportedTimeframeError` | — | — |
| DA-16 | Start 30-Sep-26 > end 01-Sep-26 | `InvalidRequestError` | — | — |
| DA-17 | NIFTY 5m 21-Oct-25 (13) | `PARTIAL` | `UNRECOGNISED_SESSION_IN_RANGE`, `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED`, `VOLUME_UNAVAILABLE` | `VOLUME_PARTIAL` |
| DA-18 | BANKNIFTY 5m 08-Nov-26 (13) | `PARTIAL` | `UNRECOGNISED_SESSION_IN_RANGE`, `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED` | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE`, any auction row, note `CANDIDATE_SESSIONS_IN_RANGE` |
| DA-19 | BANKNIFTY 15m 08-Nov-26 (5) | `PARTIAL` | as DA-18 | as DA-18 |
| DA-20 | NIFTY 5m 14–17 Aug-26 (146) | `PARTIAL` | `VOLUME_PARTIAL` | `VOLUME_UNAVAILABLE`, `INCOMPLETE_BARS`, `FLAGGED_ROWS_INCLUDED` |
| DA-21 | Availability: volume required, 10–21 Aug-26 | `PARTIAL`; `missing_fields` ("volume",) | `VOLUME_PARTIAL` | `VOLUME_UNAVAILABLE` |
| DA-22 | Availability: volume required, 17–21 Aug-26 | `AVAILABLE`; `missing_fields` () | — | `VOLUME_PARTIAL`, `VOLUME_UNAVAILABLE` |
| DA-23 | Availability: volume optional, Jan-25 | `AVAILABLE`; `missing_fields` () | — | `REQUIRED_FIELD_UNAVAILABLE`; any volume code that changes the status |
| DA-24 | `list_instruments(dataset_id="NSE_INDEX_1M")` | BANKNIFTY, NIFTY | — | — |

### 7.2 Pass rule and the DA-17 / T-DA-12 discrepancy

**Pass rule for every case:**
- The status or exception class is exact.
- Every "must contain" code is present.
- Every "must NOT contain" code is absent.
- Key values are equal: prices to ±0.000001; counts and volumes exactly.
- Messages are compared by the values they name, not by wording.

**DA-17 and T-DA-12.** Design Package 06 T-DA-12 lists only `UNRECOGNISED_SESSION_IN_RANGE`, with the pass rule "Exact". Under the ChatGPT ruling, that list is a **minimum set**.
- DA-17 must also contain:
  - `INCOMPLETE_BARS` (all 13 bars are incomplete);
  - `FLAGGED_ROWS_INCLUDED` (`SESSION_UNCONFIRMED`, S-6);
  - `VOLUME_UNAVAILABLE` (volume is requested by default and every candle lacks it, S-5).
- It must not contain `VOLUME_PARTIAL`.
- T-DA-12 is recorded for correction in the next Design Package revision (X-1).

---

## 8. Workstream B — M1b failure and recovery verification

### 8.1 Matrix B-1 to B-13 (unchanged from v1.0; Prepared but not executed)

| # | Scenario (06 test) | Must happen | Must not happen | Evidence |
|---|---|---|---|---|
| B-1 | Interrupted during staging (T-MNT-06a) | Active generation unchanged; leftover staging reported and removed | Readers see a new file; mixed generations | Before/after `get_bars` identical; `active_generation` unchanged; start-up log |
| B-2 | Interrupted after rename, before activation (T-MNT-06b) | Previous generation active; new folder reported as unactivated | Readers use it | As B-1, plus the folder listing |
| B-3 | Interrupted inside activation (T-MNT-06c) | Old or new generation fully active | One year from each | Generation ID of every file read |
| B-4 | Failed validation | File-level error → `FAILED`; row-level problem → quarantined | Partial silent import | **Now specified fully as T-MNT-17 (§8.2)** |
| B-5 | Revision detected (T-MNT-04, 05) | `HELD_REVISION` with evidence | Active data changed | Row count 6,860; closes unchanged |
| B-6 | Revision held for the Owner (T-MNT-03, 03b, 14) | Held; labelled a *candidate* only; `HELD_REVISION_EXISTS`, `RANGE_TRUNCATED_END` | Automatic adjustment | `latest_n=5` = 417.85 … 439.80 with both warnings |
| B-7 | Revision rejected (T-MNT-03d) | `REJECTED_REVISION`; not offered again | Active data changed | `import_log`; `SKIPPED_UNCHANGED` on re-run |
| B-8 | Revision approved (T-MNT-03c) | New generation; previous one retained | Loss of the previous generation | Revised closes; old files readable |
| B-9 | Generation creation (T-MNT-02) | New generation with 6,861 rows; previous one (6,860) retained | In-place modification | Two generation folders; old hashes unchanged |
| B-10 | Generation activation | One catalogue transaction | Mixed state | Catalogue before/after; `data_version` changes |
| B-11 | Recovery (T-MNT-06a–c, 07) | Start-up recovery report; `INTEGRITY_MISMATCH` detected | Silent continuation | Start-up log; integrity report |
| B-12 | Backup created (T-MNT-08) | Catalogue backup before changes | Backup after changes | Backup time earlier than run start |
| B-13 | Restore and integrity (T-BKP-01) | Integrity passes; `get_bars` equals the pre-update results | Catalogue pointing to pruned files | Row counts and CSV SHA-256 before/after; "PASS" report |

### 8.2 Test T-MNT-17 — validation failure during an **incremental update** (R-3)

**Status: Proposed test; Prepared but not executed.**

**Can an existing test satisfy this requirement?** No. Each candidate fails for a specific reason:

| Existing test | Why it does not satisfy R-3 |
|---|---|
| T-FILE-02, T-FILE-04, T-FILE-08 | **Initial import.** There is no prior active generation, so they cannot show that one stays unchanged, and they have no follow-up update. Relabelling them would not test the update path. |
| T-DQ-01, T-DQ-05 | Row-level quarantine; the file is still imported. This is not a failed update. |
| T-MNT-06a–c | Interruption (process killed), not a validation failure |
| T-MNT-07 | Integrity of stored files after the fact |
| T-MNT-15 | Inaccessible source → WARNING `SOURCE_INACCESSIBLE`. The file is never read, so validation never runs. |
| T-MNT-03 to 05, 14 | Revisions are **held**, which is not a failure |

**Two failure points exist in the update flow (02 §9.2), so T-MNT-17 has two parts:**
- **17a** — the changed source file fails reading or standardisation (V-FILE-01, V-SCH-01, V-TS-01).
- **17b** — the staged generation fails whole-generation validation (§9.4 step 2).

**Fixtures** (sheet `R3_Fixtures`). They are built from byte-exact prefixes of the Owner files, so every expected value is real and nothing is invented.

| Fixture | Construction | Size | SHA-256 |
|---|---|---:|---|
| 17a-INIT `CONCOR.txt` | First 6,859 lines of the Owner `CONCOR.txt` (to 2026-11-05; CR LF) | 355,063 | `e226b249691fbfc1eacc22d8f6a17d65e6423209adf4035aec9372526eca117b` |
| 17a-BAD `CONCOR.txt` | 17a-INIT plus the line `2026-11-06,437.00,439.80,430.00` + CR LF (the real 06-Nov-26 row cut to 4 fields) | 355,096 | `04a32652d426dafb332e54af3db5dfc84c546bda21fb0f0d4863270ec3055bb2` |
| 17a-GOOD `CONCOR.txt` | The Owner `CONCOR.txt`, unchanged | 355,117 | `add449571b6bce38d09fe0c339fee2a23c70cde34a88bd1bd6714d7fa5c9d67c` |
| 17b-INIT NIFTY | The Owner NIFTY 1-minute Parquet without the 361 rows of 06-Nov-26 | content check | 168,262 rows; last ts 2026-11-05 15:30; year files 2025 = 90,811, 2026 = 77,451 |
| 17b-UPDATE NIFTY | The Owner NIFTY 1-minute Parquet, unchanged | 3,638,795 | `a4928e0d2f16bd6b6c8426297c2337e01e0291e859202c0abe3a372dd3472298` |

All three 17a fixtures sit in one fixture folder, at the same path, under the name `CONCOR.txt`.

**T-MNT-17a — steps, expected results and evidence**

| Step | Action | Expected (must happen) | Prohibited (must not happen) | Evidence required |
|---|---|---|---|---|
| 1 | Initial load with 17a-INIT. Record the baseline. | `NEW`; 6,859 rows; generation G1 active.<br>`get_bars("CONCOR","1D",latest_n=5,fields=["close"])` = 413.85, 417.85, 419.15, 425.10, 440.85 (30-Oct – 05-Nov-26). | — | `data_file` rows of G1 (path, sha256, row_count); `instrument.active_generation`; the `get_bars` export |
| 2 | Replace the file with 17a-BAD at the same path; run Update with that folder selected | Fingerprint changed, so the file is read (§9.6) | `SKIPPED_UNCHANGED` | `import_log` row for the new `source_sha256` |
| 3 | Validation | Fails at file level: line 6,860 has 4 fields, expected 6 or 7 (V-FILE-01, 02 §11 message style) | Row-level quarantine of line 6,860 with the rest imported | Live log and run log line naming `CONCOR.txt` and line 6,860 |
| 4 | Recording | `import_log.action = FAILED`, with `source_path`, `source_sha256` `04a32652…`, and a message naming the file and line.<br>`maintenance_run` status is not success.<br>`coverage.quality_status = FAIL` for CONCOR (02 §5.4: "latest update … not activated because of a blocking ERROR"). | Status shown as success; no `import_log` row | `import_log.csv`, `maintenance_run.csv`, `coverage` export |
| 5 | Active generation unchanged | `active_generation` still G1; G1 fingerprints and row count (6,859) unchanged; no new `data_file` rows | Any new generation; any changed file of G1 | `data_file` before/after (identical); generation folder listing |
| 6 | No partial data visible to readers | `get_bars` equals step 1 exactly: same 5 closes, last bar 05-Nov-26 | A 06-Nov-26 bar; any row from the bad file | `get_bars` export compared by row count and CSV SHA-256 |
| 7 | A failed file is not "known" | Re-running Update with 17a-BAD still present gives `FAILED` again | `SKIPPED_UNCHANGED` (a failed fingerprint was never imported, §9.6) | Second `import_log` row |
| 8 | Subsequent valid update | Replace with 17a-GOOD and run Update: `APPEND` (1 new row); generation G2 active with 6,860 rows; G1 retained.<br>`latest_n=5` = 417.85, 419.15, 425.10, 440.85, 439.80.<br>`quality_status` returns to `PASS_WITH_WARNINGS`, because the G-03 issues stay open. | The failure blocks later updates; G1 removed; any held revision (history is byte-identical) | `import_log`, `data_file`, generation folders, `get_bars` export |

**T-MNT-17b — staged-generation validation failure (NIFTY, two year files)**

| Step | Action | Expected | Prohibited | Evidence |
|---|---|---|---|---|
| 1 | Initial load with 17b-INIT | Generation G1: 2025 = 90,811 rows, 2026 = 77,451 rows | — | `data_file`, `get_bars("NIFTY","1m","2026-11-05","2026-11-05")` row count 361 |
| 2 | Update with 17b-UPDATE; a test hook (the same mechanism as T-MNT-06) alters the staged `NIFTY_2026.parquet` after it is written, e.g. drops one row so that the read-back row count differs | §9.4 step 2 fails; staging discarded; instrument `FAIL`; `maintenance_run` not success | Folder renamed into `market\`; catalogue transaction run | Run log naming the file and the failed check; staging folder gone |
| 3 | Reader check | G1 still active; `get_bars` for 05-Nov-26 unchanged (361 rows); no 06-Nov-26 row is returned | Any 06-Nov-26 row visible | `get_bars` exports |
| 4 | Re-run without the hook | `APPEND` 361 rows (360 `CANDLE` + 1 `CLOSING_AUCTION`); G2: 2026 = 77,812 rows; G1 retained | — | `data_file` before/after |

**Gaps that Claude 1 must document (not new rules):**
- 02 §5.2 does not enumerate `maintenance_run.status` values. Claude 1 must document the value used for a failed run.
- A `data_issue` row for a file-level failure is not required by 02 §11. If one is created, it must name the file.

**Why the subsequent valid update matters (17a step 8; 17b step 4).**
- A failed update must leave the instrument fully maintainable.
- The proof is a follow-up valid update. It must run as an ordinary `APPEND`, on the **same registered path** and with the **same machinery**, and it must activate a new generation.
- Three things must **not** carry over from the failed run:
  - no lingering lock or "failed" state blocks the run;
  - the failed fingerprint is not mistaken for an imported one;
  - no manual clean-up is needed.
- If the follow-up update is refused, held, or needs intervention, T-MNT-17 fails, even if steps 1–7 passed.

**Evidence file names** follow EV-11 (§10), with `<test>` = `T-MNT-17a` or `T-MNT-17b`.

**Status:** this is a specification for Claude 1 to implement and execute. It has **not** been executed by Q-MAP.

---

## 9. Workstream C — Milestone acceptance checklist (final)

**Status: Prepared but not executed.** "Actual-data verification" means comparison with this package and its workbook.

| Gate or milestone | Status now | Design requirement | Implementation evidence | Test execution | Actual-data verification | Owner action |
|---|---|---|---|---|---|---|
| **Owner approval of Design Package v1.10** | **Completed** (Owner) | — | — | — | — | Done |
| **Owner authorisation to begin production implementation** | **Pending** (Owner) — see Q-3, §15 | — | — | — | — | Explicit go-ahead to Claude 1 |
| **Gate 0 — technical** | **Pending** (Claude 1, then Owner) | Python 3.12.10; exact `==` pins incl. DuckDB (08 §6, G-15) | `requirements.txt`; EV-12 | T-ENV-01 on the Owner's PC | — | Owner runs the check and confirms the printout is from his PC |
| **M1a** | Not started | 02 §2–§8, §9.6, §11; G-04, G-16 | Data Manager from IDLE; catalogue; validation report; confirmation lists | L1–L3 for M1a (06 §9) | EV-01 to EV-04 against `Source_Checks`, `Classification`, §3; ACC-02, ACC-04, ACC-06 | E2E-01 |
| **M1b** | Not started | 02 §9–§10; OD-04; G-03; G-09; G-16 | Update, held revision, approve/reject, generations, backup and restore | Matrix §8.1 **and T-MNT-17a/17b**, with failure injection actually run | EV-11; CONCOR append; held revision leaves the 5 latest closes unchanged | E2E-02 |
| **M2** | Not started | 03 Parts A and B; interface 1.1; rulings S-1 to S-6 and T-DA-12 (§6) | `QMapData` with exactly the 10 public functions; the example script of 08 §7 M2 | T-DA-01 to 15 (warning lists as minimum sets), T-AGG-01 to 13, ACC-01, ACC-07, ACC-10 | EV-05 to EV-10: DA-1 to DA-24 per `DA_Expected`; four reference days; ACC-01 at five timeframes (monthly on Feb-25 – Oct-26, Q-1); 38 incomplete bars; `Auction_Volume_Guard` | ACC-10 timing on the Owner's PC; Owner runs the example script |

**Test reports alone are not acceptance.** Each submission must include the EV files in §10. ChatGPT compares them with this package mechanically.

---

## 10. Machine-readable milestone evidence (R-4, final)

The full specification is in sheet `Evidence_Checklist`. For every item it gives:
- the exact file name;
- the required columns or JSON fields;
- the producing function or operation;
- the reference to compare against;
- the comparison method and tolerance;
- who supplies it.

`<ts>` = the run suffix `dd_mmm_yy_hhmmss`.

| ID | Milestone | Evidence | Exact file name(s) | Produced by | Compare against | Supplied by |
|---|---|---|---|---|---|---|
| EV-00 | Every submission | Manifest | `EV00_manifest_<ts>.csv` | Claude 1 script | All files in the submission (SHA-256) | Claude 1 |
| EV-01 | M1a | Source fingerprints | `EV01_source_fingerprints_<ts>.csv` | Initial load (`import_log`) | `Source_Checks`, `Derived_Files` | Claude 1 |
| EV-02 | M1a | Day classification | `EV02_day_profiles_<inst>_<ts>.csv` (NIFTY, BANKNIFTY) | `get_day_profiles` | `Classification`, `S1_BNF_08Nov26` | Claude 1 |
| EV-03 | M1a | Record counts | `EV03_record_counts_<ts>.csv` | Catalogue query | `Classification` | Claude 1 |
| EV-04 | M1a | Data-quality findings | `EV04_issues_<ts>.csv`, `EV04_quarantine_<ts>.csv` | `get_issues(min_severity="INFO", status=None)`; quarantine export | `Source_Checks`; 13 §4/§6; ACC-04, ACC-06 | Claude 1 |
| EV-05 | M2 | NIFTY 17-Aug-26 5m and 15m | `EV05_bars_NIFTY_<tf>_20260817_<ts>.csv` + `EV05_meta_…json` | `get_bars` | `NIFTY_17Aug26_5m`, `NIFTY_17Aug26_15m` | Claude 1 |
| EV-06 | M2 | BANKNIFTY 19-Aug-26 5m and 15m | `EV06_bars_BANKNIFTY_<tf>_20260819_<ts>.csv` + meta | `get_bars` | `BNF_19Aug26_5m`, `BNF_19Aug26_15m` | Claude 1 |
| EV-07 | M2 | Daily reference outputs | `EV07_bars_<inst>_1D_all_<ts>.csv` + meta | `get_bars(inst,"1D")` | `Daily_Refs`, `Daily_CrossCheck`, `Auction_Volume_Guard` | Claude 1 |
| EV-08 | M2 | Whole-sample aggregation | `EV08_bars_NIFTY_{3m,5m,15m,1MO}_all_<ts>.csv`; `EV08_bars_BANKNIFTY_{5m,15m}_all_<ts>.csv` + meta | `get_bars` | `CrossCheck_ACC01`, `CrossCheck_DayTypes`, `Monthly_CrossCheck`, §4 | Claude 1 |
| EV-09 | M2 | Incomplete bars | `EV09_incomplete_bars_<ts>.csv` | Filter of EV-06/EV-08 | `Incomplete_Bars` (38) | Claude 1 |
| EV-10 | M2 | DA-1 to DA-24 | `EV10_da_results_<ts>.csv` plus one bars/meta, exception or availability JSON per case | Each call in `DA_Expected` | `DA_Expected` | Claude 1 |
| EV-11 | M1b | Maintenance and failure injection | `EV11_<test>_{maintenance_run,import_log,data_file_before,data_file_after,generations,get_bars_before,get_bars_after}_<ts>.csv` + run log | Data Manager runs and the test hook | §8 matrix; `R3_Fixtures` | Claude 1 (Owner performs E2E-02) |
| EV-12 | Gate 0 (technical) | Environment | `EV12_environment_<ts>.txt`; `requirements.txt` | T-ENV-01 in IDLE on the Owner's PC | 08 §6; T-ENV-01 | Claude 1 (script); Owner (runs and confirms) |

**Comparison method and tolerance:**
- Prices: ±0.000001.
- Counts, volumes, booleans, record types and timestamps: exact.
- `quality_flags`, warning codes and note codes: compared as sets.
- DA cases: as §7.2.
- Before/after maintenance reads: identical row count and an identical SHA-256 of the CSV export.

**Format rules:**
- **Files:** CSV in UTF-8, comma-separated, with one header row and no index column.
- **Numbers:** full precision, no thousands separators.
- **Values:** null = empty field; booleans `TRUE` / `FALSE`.
- **JSON:** UTF-8, with the 03 §A5 key names.

**Timestamps (Owner-approved Option A):**
- Inside the evidence files, use `YYYY-MM-DD HH:MM:SS`, e.g. `2026-08-17 09:15:00`.
- Times are IST wall-clock, never converted to UTC and never given an offset.
- Daily and monthly bars use `00:00:00`.
- Human-readable reports keep the style `17 Aug 26, 09:15 AM`.

---

## 11. Auction-volume safeguard (R-5, final)

**Six rules Claude 1 must not break:**

1. **Auction records remain separate records.**
   - `AUCTION_PHASE` and `CLOSING_AUCTION` rows are never merged into a candle (D-08).
   - They are never dropped.
2. **Auction volume is never added to continuous-session daily volume.**
   - Daily `volume` is the sum of `CANDLE` volumes only (03 §B7, T-AGG-13).
3. **BANKNIFTY final-print volume is preserved exactly as supplied.**
   - This includes the five zero values and the cases where it equals the 15:15 volume.
4. **No volume is inferred, copied, corrected or automatically de-duplicated.** This applies on any record, for any reason.
5. **The warnings and completeness status stay intact.**
   - Auction rows carry `VOLUME_SEMANTICS_UNVERIFIED`, with one INFO issue per instrument (V-VOL-03), and they trigger `FLAGGED_ROWS_INCLUDED` (S-6).
   - BANKNIFTY CAS daily bars have `volume_complete` False and the flag `VOLUME_EXCLUDES_AUCTION`.
   - Responses carry the note `DAILY_VOLUME_EXCLUDES_AUCTION`.
6. **The meaning of the BANKNIFTY auction-volume pattern is unconfirmed (V-09).** No logic may depend on any interpretation of it. The pattern is:
   - the final print equals the 15:15 volume on 19 of 43 days with a 15:15 record;
   - from 12-Oct-26 the final print is consistently in the millions.

**Reference table (unchanged from v1.1).** Sheet `Auction_Volume_Guard` covers all 60 BANKNIFTY days. For each day it gives the correct daily volume (column K) and the two **prohibited** values (columns L and M). A Q-MAP daily volume equal to L or M, on a day where that value differs from K, is a data-integrity defect. Example (T-AGG-13, 18-Aug-26):

| | Volume |
|---|---:|
| Correct | 123,512,346 |
| Prohibited: candles + final print | 123,532,339 |
| Prohibited: candles + both auction rows | 123,552,332 |

**Special case — 08-Nov-26 (unrecognised).** Its 15:15 and 15:29 records are `CANDLE` rows until the day is confirmed. Their volume is 0 each, so the daily candle volume is 74,042,113 either way.

**Observation O-1 (retained).**
- The first million-scale final print is on 21-Sep-26 (4,043,240), an isolated case. Million-scale prints are continuous only from 12-Oct-26.
- No rule depends on this, and it was not investigated further, as instructed.

---

## 12. Workstream D — Review of Claude 1's submissions (handed over)

**Status: Not performed by Claude 2; handed over to ChatGPT.** No Claude 1 submission was received during Claude 2's assignment. Following the close-out instruction, milestone review now belongs to **ChatGPT**. ChatGPT will use this package, its workbook and the evidence specification in §10.

Each review should report:
- confirmed items;
- defects;
- missing evidence;
- data-integrity risks;
- architecture deviations;
- exact corrective actions.

A green test suite is never a pass on its own. Claude 2 may be re-engaged only for a specific exceptional offline investigation.

---

## 13. Limitations register (final)

| Item | Status | Reason |
|---|---|---|
| Weekly (1W) aggregation | Not verified | No derived weekly file exists |
| BANKNIFTY aggregation against a second file | Not verified (single-source reference) | No derived BANKNIFTY file exists |
| Derived-file rows 2023–24, including the V-07 fills | Not verified | Before the 1-minute sample begins |
| Jan-25 and Nov-26 monthly bars | Coverage case; not compared | v1.1 §5.5; Q-1 |
| States after Owner confirmation (21-Oct-25, 08-Nov-26, the Budget days) | Structural check only | Not modelled |
| Flags not modelled row by row (`VOLUME_SEMANTICS_UNVERIFIED`, `LARGE_GAP_UNVERIFIED`, `LEVEL_BREAK_UNVERIFIED`) | Expected from the specification and §6.1 tables | The reference models `CAS_CANDIDATE` and `SESSION_UNCONFIRMED`, plus the daily `VOLUME_EXCLUDES_AUCTION` flag |
| T-AGG-05 forming bar; T-SES-07, 08, 10; all failure injection; T-MNT-17 | Prepared but not executed | Need fixtures or Claude 1's implementation |
| 17b-INIT byte fingerprint | Content check only | Parquet bytes depend on the writer version |
| ACC-10 performance | Prepared but not executed | Must be measured on the Owner's PC |
| Any Q-MAP test | **0 executed / 0 passed / 0 failed** | No implementation exists |

---

## 14. Discrepancies with Design Package v1.10 (documented, not changed in the baseline)

| ID | Finding | Handling (v1.2) |
|---|---|---|
| X-1 | 06 T-DA-12 lists one warning with the pass rule "Exact" | **Ruled:** the list is a minimum set (§7.2). Correct the text at the next Design Package revision. |
| X-2 | 03 §B7: final-print volume "millions from 12-Oct-26"; an isolated earlier case on 21-Sep-26 | Descriptive only (O-1) |
| X-3 | 03 §B5 `volume_complete` versus `VOLUME_PARTIAL` | **Ruled** (S-5) |
| X-4 | Scope of `FLAGGED_ROWS_INCLUDED` | **Ruled** (S-6); DA-10 consequence for confirmation (Q-2) |
| X-5 | 02 §5.2 does not enumerate `maintenance_run.status` values | Claude 1 documents the failure value (§8.2) |
| X-6 | v1.0 wording about the 15m, daily and monthly cross-checks | Resolved by v1.1 §5 |
| **X-7** *(new)* | ACC-01 wording includes the monthly bar for Jan-25, which cannot match because of source coverage (06 ACC-01; 08 §7 M2; 11 M2) | Judge monthly ACC-01 on Feb-25 – Oct-26, as T-AGG-12 already does; ChatGPT to confirm (Q-1); correct at the next revision |

Wider cross-document findings (status lines, repository guidance, module naming, stale "not re-run" labels) are recorded in the Close-out Report §5 and the Consolidated Claude 1 Handover, Annex A.

---

## 15. Risks, open items and recommendations (final)

| ID | Item | Status | Who |
|---|---|---|---|
| R-1 | Session and record counts source-verified | **Done** (v1.1 §3) | ChatGPT to carry into the next revision |
| R-2 | Rulings before M2 | **Done** (S-1 to S-6, T-DA-12) | — |
| R-3 | Update-path validation failure test | **Specified** (T-MNT-17a/17b) | Claude 1 implements and runs; ChatGPT reviews |
| R-4 | Machine-readable evidence | **Specified** (EV-00 to EV-12, final) | Claude 1 produces; ChatGPT compares |
| R-5 | Auction volume never added | **Specified and emphasised** (§11) | Claude 1; ChatGPT review |
| R-6 | S-4a, S-5, S-6 rulings | **Done** | — |
| R-7 | Timestamp format | **Done** (Owner, Option A) | — |
| R-8 | T-DA-12 "Exact" | **Done** (minimum-set ruling); text correction at the next revision | ChatGPT |
| Q-1 | ACC-01 monthly scope (X-7) | **Open** — confirmation | ChatGPT |
| Q-2 | DA-10 `FLAGGED_ROWS_INCLUDED` (§6.3) | **Open** — confirmation | ChatGPT |
| Q-3 | Start of production implementation | **Open** — the earlier Claude 2 chat handover recorded GATE-0 as approval **and** authorisation for Gate 0, M1a, M1b and M2. The close-out assignment lists a separate Owner authorisation as still to come. The conservative reading is used until the Owner confirms. | Owner |

---

## 16. Responsibility boundary

| Party | Responsibility |
|---|---|
| **Completed by Claude 2** | Data inspection and source findings; the independent reference calculations (v1.0, v1.1); data-access expected results and examples (DA-1 to DA-24); M1b test specifications (B-1 to B-13, T-MNT-17); machine-readable evidence specification (EV-00 to EV-12); technical documentation and implementation handover; final cross-document consistency review |
| **Claude 1 — implement and demonstrate** | Gate 0 environment check and `requirements.txt`; M1a; M1b; M2; execution of the prepared DA, aggregation and maintenance tests; production evidence exports |
| **ChatGPT — review** | Claude 1's actual implementation and evidence; milestone acceptance against the approved requirements; defects, deviations and missing evidence; consolidated corrective instructions; confirmations Q-1 and Q-2 |
| **Project Owner — decide or perform** | Q-3 (authorisation to begin production implementation); the outstanding decisions OD-12, D-EMA-11, D-EMA-12, G-11, G-10 and G-01; Owner-side confirmations (CAS days, special sessions, every ±15% occurrence); the T-ENV-01 run on his PC; E2E-01 and E2E-02; milestone acceptance |

**Workstream D** (Claude 2 reviewing Claude 1's submissions) is **not** part of this close-out. Claude 2 becomes inactive after this delivery; milestone review passes to ChatGPT.

---

## 17. Restrictions observed and deliverables

**Restrictions observed:**
- No production code was written.
- Claude 1's repository was not accessed.
- No Owner file was modified.
- No aggregation, reference value, comparison or fingerprint was recalculated in v1.2.
- No dependency was added to Q-MAP.
- No inventory script was created or run.
- No scanner work was done, and the EMA methodology was not changed.
- No Owner decision was reopened.
- No test was claimed as executed.
- v1.0 and v1.1 are unchanged.

| File | Size (bytes) | SHA-256 |
|---|---:|---|
| `Q-MAP_Independent_Reference_Results_v1.2_12_Nov_26_124620.xlsx` | see the Close-out Report §2 | see the Close-out Report §2 |
| `Q-MAP_Independent_Verification_Package_v1.2_12_Nov_26_124620.md` (this file) | Close-out Report §2 | Close-out Report §2 |

*End of verification package v1.2.*
