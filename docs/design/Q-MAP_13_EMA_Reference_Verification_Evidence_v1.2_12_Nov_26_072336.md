# Q-MAP — EMA Reference Verification Evidence

**Package document 13 | Version 1.2 | 12-Nov-26 | Status: Evidence record. CONCOR and INFY reference examples verified against source data. Supports document 10 v1.7. Not approval to code.**

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**

**Change log**

| Version | Change |
|---|---|
| 1.0 | Arithmetic and fixture verification; no source data available |
| 1.2 | INFY examples T-EMA-03 and T-EMA-04 verified against the Owner-supplied INFY daily Parquet (exact to 4 dp; no ±15% move in either window). Complete INFY ±15% history recorded: eight occurrences, seven of them newly identified, all G-03 blocking cases awaiting the Owner's verification. Nothing now outstanding in this record. |
| 1.1 | CONCOR examples verified against the Owner-supplied CONCOR files; T-EMA-09 window-start correction; T-EMA-18 values calculated (conditional); three newly identified CONCOR ±15% cases recorded; Nifty IT findings recorded separately; INFY still outstanding |

| Field | Value |
|---|---|
| Purpose | Check every EMA reference value and worked example in document 10, recording exactly what was verified and how |
| Methodology checked against | D-EMA-01 to D-EMA-10 as approved on 11-Nov-26 (document 10 §A3–§A6, §B2, §B3). **Methodology not changed.** |
| Performed by | Claude 2, 11-Nov-26 (v1.0) and 12-Nov-26 (v1.1), using a throw-away exploratory calculation in Python. It is not a Q-MAP module and is not in the package. |
| Seeding and window | 800 trading days ending on the analysis date; each EMA seeded with the simple average of its first N closes in the window; α = 2 ÷ (N + 1); slope compares EMA50 with its value 10 bars earlier |

---

## 1. Source files used (supplied by the Owner, 12-Nov-26)

| File | Size (bytes) | Rows | SHA-256 | Same as Deliverable 1? |
|---|---:|---:|---|---|
| `CONCOR.txt` | 355,117 | 6,860 | `add449571b6bce38d09fe0c339fee2a23c70cde34a88bd1bd6714d7fa5c9d67c` | Yes — size, rows, first and last lines match 01 v1.2 §2 and Appendix C |
| `CONCOR_daily_26Nov98-06Nov26.parquet` | 138,313 | 6,860 | `e3398485035d9c1692561882feb3895bc9df95f826d4ac7a5d8a31bbe24609a8` | Yes |
| `Nifty_IT.txt` | 343,673 | 5,761 | `7236641b5a04db8f815ecf303b9ac3a305e70e96010b6148d3f6305014eec6ef` | Yes — **not used for any EMA example** (§5) |
| `INFY_daily_02Jan98-06Nov26.parquet` (supplied 12-Nov-26) — **authoritative source for INFY** | 144,271 | 7,169 | `2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01` | Yes — size matches 01 v1.2 §2; 02-Jan-98 – 06-Nov-26 |
| `INFY.txt` (reference only) | 393,110 | 7,169 | `672f7731b4470454f5d42859e93406e452ff72d9e1041197bdf4d1b61873214e` | Not used as the source; compared only: identical to the Parquet on all 7,169 rows (0 differences in OHLCV) |

**File check.** The CONCOR text and Parquet files agree on all 6,860 dates, with 0 differences in open, high, low, close and volume. Further checks: 0 duplicate dates; rows sorted; 30 weekend rows, as documented. The Parquet is the Owner's conversion of the text file, not a competing source. INFY Parquet: 7,169 rows, 0 duplicate dates, sorted, 34 weekend rows, 0 OHLC violations.

---

## 2. Result classes

| Class | Meaning |
|---|---|
| **V-S** Verified against source data | Recomputed from the original source file and found equal |
| **V-A** Arithmetic verified | Everything following from the written inputs confirmed; the inputs themselves **not** checked against source |
| **V-F** Verified (fully specified fixture) | The test defines all its own inputs |
| **N-V** Not verifiable | Required source data not available |
| **INC** Incorrect | Expected value wrong; correction given |

---

## 3. Evidence table

| # | Example | Date | Data used | Expected (document 10) | Independently calculated | Result |
|---|---|---|---|---|---|---|
| 1 | CONCOR T-EMA-01 | 30-Oct-26 – 06-Nov-26 | CONCOR source | Closes 413.85, 417.85, 419.15, 425.10, 440.85, 439.80 → 416.95 / 421.025 / 430.9375 / 435.36875 | Same closes on the same dates; same EMA(3) | **V-S** |
| 2 | CONCOR T-EMA-02 / §A7 / §B8 | 06-Nov-26 | CONCOR source | Window 17-Aug-23 – 06-Nov-26; EMA20 432.7297, EMA50 452.6585, EMA200 486.4492, EMA50 ten bars earlier 466.7276; +1 −1 −1 −1 −1 −1; net −4; 16.67; BEARISH | Identical to 4 dp; same answers, net, score, state; distances 1.6339 / −2.8407 / −9.5897%; ±15% events inside window: 04-Jun-24 only | **V-S.** Default result `INVALID_DATA` (04-Jun-24, G-03) |
| 3 | INFY T-EMA-03 / §A7 | 06-Nov-26 | INFY Parquet | Window 17-Aug-23 – 06-Nov-26; close 1,181.40; EMA20 1,132.2614; EMA50 1,108.5365; EMA200 1,203.8765; EMA50 ten bars earlier 1,084.5193; +1 +1 −1 +1 −1 +1; net +2; 66.67; NEUTRAL | Window starts 17-Aug-23; all values identical to 4 dp; same answers, net and score; **no ±15% move in the window** | **V-S. Valid result `OK`** — no G-03 block |
| 4 | INFY T-EMA-04 / §A7 | 03-Feb-26 | INFY Parquet | Window 16-Nov-22 – 03-Feb-26; close 1,656.00; 1,646.1038 / 1,617.6051 / 1,589.1800 / 1,598.2591; all +1; net +6; 100; BULLISH | Window starts 16-Nov-22; all values identical to 4 dp; **no ±15% move in the window** (the nearest, 22-Oct-19, lies before it) | **V-S. Valid result `OK`** — no G-03 block |
| 5 | CONCOR T-EMA-05 / §A7 | 09-Sep-26 | CONCOR source | Window starts 21-Jun-23; 509.8872 / 504.0989 / 506.0167 / 502.3052; +1 +1 +1 +1 −1 +1; net +4; 83.33; BULLISH | Identical; ±15% events inside window: 04-Jun-24 only | **V-S.** Default `INVALID_DATA` (04-Jun-24) |
| 6 | §A7 table rounding | four examples | 4-dp values | 2-dp table | Consistent | **V-A** |
| 7 | CONCOR T-EMA-06 | 31-Dec-01 | CONCOR source | `INSUFFICIENT_DATA`, 690 bars | 690 bars | **V-S** |
| 8 | CONCOR T-EMA-07 | — | CONCOR source | First `OK` date 06-Jun-02; no ±15% move before it | 06-Jun-02 is the first date with 800 bars; no ±15% move before it | **V-S** |
| 9 | CONCOR T-EMA-08 | 30-Jun-14 | CONCOR source | Window 11-Apr-11 – 30-Jun-14 contains 06-Sep-13 → `INVALID_DATA` | Window starts 11-Apr-11; the only ±15% event inside is 06-Sep-13 | **V-S** |
| 10 | CONCOR T-EMA-09 | 07-Dec-16 / 08-Dec-16 | CONCOR source | 07-Dec-16 `INVALID_DATA` (window contains 06-Sep-13); 08-Dec-16 `OK`, window starts **09-Sep-13** | 07-Dec-16 window starts on 06-Sep-13 itself → `INVALID_DATA` under the documented date-overlap rule; 08-Dec-16 window starts **10-Sep-13** (the file has no 09-Sep-13 record) → `OK` | **INC (date only)** — corrected in 10 v1.6. Statuses verified (**V-S**). |
| 11 | Fixture T-EMA-10 | — | Fully specified | net 0; 50 | Exact arithmetic: same; float64: net −2 (EMA200 = 100.0000000000001) | **V-F**; finding EMA-F1 |
| 12 | Fixtures T-EMA-11, T-EMA-12 | — | Fully specified | 100 / 0 | 100 / 0 | **V-F** |
| 13 | T-EMA-16 | — | Net −6 … +6 | 13 scores and states | All 13 match | **V-F** |
| 14 | §B8 stored score | 06-Nov-26 | net −4 | 16.666666666666668 | Three float results, depending on formula order | Finding EMA-F2 |
| 15 | §B4 warm-up residuals | — | α = 2/201 | 100 / 13.5 / 1.8 / 0.25 / 0.03% | 100.00 / 13.53 / 1.83 / 0.25 / 0.03% | **V-F** |
| 16 | T-EMA-17 | 10-Nov-26 | — | Depends on D-EMA-11 | — | **N-V** (proposal pending) |
| 17 | CONCOR T-EMA-18 | 31-Dec-07 | CONCOR source | `INVALID_DATA` (15-May-06); values to be calculated | Window 14-Oct-04 – 31-Dec-07; the only ±15% event inside is 15-May-06 (26/27-May-04 lie before the window; 31-Jan-08 after). **Conditional values** — see the note below. | **V-S** (status and window). Values calculated from source and **conditional** |

**T-EMA-18 note.** The values below are what the scanner would produce **only after** the Owner verifies the 15-May-06 occurrence and marks it `VERIFIED_OK` (G-03). They are **not** an accepted or valid scanner result, and the scanner's actual result for this date is `INVALID_DATA`.

| Close | EMA20 | EMA50 | EMA200 | EMA50 ten bars earlier | Answers | Net | Score | State |
|---:|---:|---:|---:|---:|---|---:|---:|---|
| 246.61 | 236.3180 | 241.2234 | 252.5792 | 244.1076 | +1 +1 −1 −1 −1 −1 | −2 | 33.33 | NEUTRAL |

**Summary**

| Class | Count | Items |
|---|---:|---|
| V-S | 10 | Rows 1, 2, 3, 4, 5, 7, 8, 9, 17 (status and window), and the statuses in row 10 |
| INC | 1 | Row 10: the 08-Dec-16 window starts 10-Sep-13, not 09-Sep-13. The date is corrected; the status was right. |
| V-F | 5 | Rows 11–13, 15 (row 11 with finding EMA-F1) |
| V-A only | 1 | Row 6 (table rounding, a presentation check) |
| N-V | 1 | Row 16 (T-EMA-17 depends on proposal D-EMA-11) |

**Status of the four worked examples after source verification:**

| Example | Source-verified | Result the scanner gives |
|---|---|---|
| CONCOR 06-Nov-26 (T-EMA-02) | Yes | **Blocked** — `INVALID_DATA` until the Owner verifies 04-Jun-24; the listed values apply afterwards |
| CONCOR 09-Sep-26 (T-EMA-05) | Yes | **Blocked** — as above |
| INFY 06-Nov-26 (T-EMA-03) | Yes | **Valid** — `OK`, net +2, 66.67, NEUTRAL |
| INFY 03-Feb-26 (T-EMA-04) | Yes | **Valid** — `OK`, net +6, 100, BULLISH |
| CONCOR 31-Dec-07 (T-EMA-18) | Yes (status, window) | **Blocked**; values **conditional** on the Owner verifying 15-May-06 |

No methodology defect was found. The EMA-F1 and EMA-F2 findings (implementation precision; proposal D-EMA-12) are unchanged from v1.0, and none of the source-verified results (CONCOR or INFY) changes under the proposed rounding rule, which was checked for T-EMA-03 and T-EMA-04 as well.

---

## 4. CONCOR ±15% occurrences found in the source file (G-03)

All open-versus-previous-close and close-versus-previous-close changes beyond ±15% in `CONCOR.txt`:

| Date | Previous close | Open | Close | Open % | Close % | Status in the package before v1.9 |
|---|---:|---:|---:|---:|---:|---|
| 26-May-04 | 73.64 | 88.32 | 75.91 | +19.93 | +3.08 | Documented |
| 27-May-04 | 75.91 | 88.19 | 76.13 | +16.18 | +0.29 | Documented |
| 15-May-06 | 228.75 | 265.36 | 220.49 | +16.00 | −3.61 | Documented |
| **31-Jan-08** | 198.54 | 207.38 | 229.97 | +4.45 | **+15.83** | **Newly identified** |
| 06-Sep-13 | 270.61 | 171.78 | 181.53 | −36.52 | −32.92 | Documented |
| **20-Mar-20** | 228.72 | 230.76 | 265.52 | +0.89 | **+16.09** | **Newly identified** |
| **10-Aug-20** | 364.72 | 346.40 | 309.12 | −5.02 | **−15.24** | **Newly identified** |
| 04-Jun-24 | 939.40 | 944.00 | 759.00 | +0.49 | −19.20 | Documented |

**Treatment of the three new cases.** Each is a G-03 blocking case awaiting the Owner's individual verification. They are **not** classified as data errors or as genuine market moves, are **not** quarantined, and nothing is unblocked. Why they were missed: the M0 inspection counted large **open** gaps (01 §8.4); close-only moves were looked for only in the latest 800-bar window (09 §2.6).

**Blocked CONCOR EMA analysis dates under G-03** (800-bar window, date-overlap rule):

| Occurrence | Analysis dates blocked |
|---|---|
| 26-May-04 | 26-May-04 – 06-Aug-07 |
| 27-May-04 | 27-May-04 – 07-Aug-07 |
| 15-May-06 | 15-May-06 – 06-Aug-09 |
| **31-Jan-08** | **31-Jan-08 – 03-May-11** |
| 06-Sep-13 | 06-Sep-13 – 07-Dec-16 |
| **20-Mar-20** | **20-Mar-20 – 09-Jun-23** |
| **10-Aug-20** | **10-Aug-20 – 27-Oct-23** |
| 04-Jun-24 | 04-Jun-24 – end of data (06-Nov-26) |

Combined effect, until the Owner verifies any occurrence: CONCOR has an EMA result only for analysis dates **06-Jun-02 – 25-May-04, 04-May-11 – 05-Sep-13, 08-Dec-16 – 19-Mar-20 and 30-Oct-23 – 03-Jun-24**. The three new cases extend the blocked periods to 26-May-04 – 03-May-11 (previously ending 06-Aug-09) and add 20-Mar-20 – 27-Oct-23. **No EMA test case is affected:** none of the windows of T-EMA-02, 05, 07, 08, 09 or 18 contains a new case (rows 2, 5, 8, 9, 10, 17).

---

## 5. Nifty IT findings (recorded separately; not a substitute for INFY)

| Check | Result |
|---|---|
| 28-May-04 level break | **Confirmed**: open −89.97%, close −90.54% versus the previous close 21,264.15 |
| 01-Jul-05 invalid record | **Confirmed**: open 60.65 lies below the low 3,041.80 (the one OHLC violation in the file); open −98.03%, close −0.68% |
| Other ±15% moves | **None** found in the file (25-Aug-03 – 06-Nov-26) |

The existing treatment is unchanged: 28-May-04 is a G-03 blocking issue; 01-Jul-05 is quarantined (invalid OHLC). The source file was not modified.

---

## 6. INFY ±15% occurrences found in the source file (G-03)

Every open-versus-previous-close and close-versus-previous-close change beyond ±15% in `INFY_daily_02Jan98-06Nov26.parquet`:

| Date | Previous close | Open | Close | Open % | Close % | Status in the package before v1.10 | Analysis dates blocked (800-bar window) |
|---|---:|---:|---:|---:|---:|---|---|
| **08-Aug-00** | 100.60 | 101.40 | 116.55 | +0.80 | **+15.85** | **Newly identified** | 08-Aug-00 – 17-Oct-03 |
| **11-Apr-01** | 59.82 | 62.74 | 50.24 | +4.88 | **−16.01** | **Newly identified** | 11-Apr-01 – 17-Jun-04 |
| **18-Apr-01** | 47.74 | 48.24 | 55.38 | +1.05 | **+16.00** | **Newly identified** | 18-Apr-01 – 23-Jun-04 |
| **10-Apr-03** | 64.88 | 64.06 | 47.65 | −1.26 | **−26.56** | **Newly identified** | 10-Apr-03 – 14-Jun-06 |
| 24-Oct-03 | 69.03 | 81.25 | 71.16 | +17.70 | +3.09 | Documented | 24-Oct-03 – 27-Dec-06 |
| **11-Jan-13** | 290.29 | 315.12 | 339.01 | +8.55 | **+16.78** | **Newly identified** | 11-Jan-13 – 08-Apr-16 |
| **12-Apr-13** | 364.59 | 328.13 | 287.08 | −10.00 | **−21.26** | **Newly identified** | 12-Apr-13 – 12-Jul-16 |
| **22-Oct-19** | 767.85 | 691.10 | 643.55 | −10.00 | **−16.19** | **Newly identified** | 22-Oct-19 – 05-Jan-23 |

**Treatment of the seven new cases.** Each is a G-03 blocking case awaiting the Owner's individual verification. They are **not** classified as data errors or as genuine market moves, are **not** quarantined, and nothing is unblocked. Why they were missed: the M0 inspection counted large **open** gaps (01 §8.4); close moves were checked only in the latest 800-bar window (09 §2.6), which contains none.

**Combined effect.** INFY's first date with 800 bars is 12-Mar-01. Until any occurrence is verified, INFY has an EMA result only for analysis dates **28-Dec-06 – 10-Jan-13, 13-Jul-16 – 18-Oct-19 and 06-Jan-23 – 06-Nov-26**. Both INFY reference dates (03-Feb-26 and 06-Nov-26) lie in the last period, so T-EMA-03 and T-EMA-04 are valid results. No other EMA test uses INFY.

**INFY source verification is complete.** Nothing in this document remains outstanding.

*End of document 13, v1.2.*
