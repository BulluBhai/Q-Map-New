# Q-MAP — Stock-Universe Inventory and Pilot Selection

**Supplementary document 09 | Version 1.6 | 12-Nov-26 | Status: Partially complete — the full stock universe has not been inspected. Pilot selection **method approved** (11-Nov-26); the actual list awaits the inventory and separate Owner approval. Inventory procedure designed; the script is **not created and not authorised**.**

| Field | Value |
|---|---|
| Responds to | Additional Groundwork Assignment, Task 1 |
| Relates to | Deliverable 1 v1.2; document 07 v1.3 (V-04, OD-06); document 02 v1.3 (readers R3/R4, validation, §9.6); document 12 v1.1 (decisions); document 11 v1.3 §1.3 (pilot method approved; G-01 not authorised) |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed sections | Reason |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | §2.7 | Duplicate-file rule aligned with the confirmed G-16 position: identical files → one canonical source plus an alias; differing files → conflict for Owner review; never merged |
| 1.1 | §3.1, §6.1, new §6.5 | Legitimate non-trading days, listing dates and suspensions are not automatically missing-data defects |
| 1.1 | §8 | Status of the exploratory inventory script (requested by the review; awaiting Owner authorisation) |
| 1.2 | §3 (output line) | Output is one workbook only; the separate Markdown summary is dropped (its content is the Summary sheet) |
| 1.2 | §6.1 item 5, new §6.6 | Pilot method reviewed against the follow-up assignment's checklist; small refinements (group C cases tied to G-03 and G-16; sizes are targets); approval needed is stated |
| 1.2 | §8 (rewritten) | Complete design of the inventory procedure: why M0 is not sufficient, exact per-file and universe checks, workbook sheets, use of results, acceptance of the run. **The script itself is not created** (no authorisation). |
| 1.3 | §2.5, §2.7, §6.1, §6.6, §8.3, §8.5 | G-16 as approved by the Owner: only exact SHA-256 matches are duplicates; any differing file goes to the Owner (CONCOR `.txt`/`.parquet` is therefore a conflict, not a duplicate) |
| 1.3 | §2.6, §6.6, §8.3, §8.5 | G-03 as approved: every ±15% move blocks until the Owner verifies it |
| 1.3 | Header, §6.3a, §8.1 | Pilot method recorded as approved; G-01 recorded as not authorised (Owner, 11-Nov-26) |
| 1.4 | Header, §4 | **Targeted correction:** V-04 is required before M1c only; Gate 0, M1a, M1b and M2 use the inspected sample files; M1c prerequisites stated. Methodology unchanged. |
| 1.5 | §2.6, §2.7 | CONCOR source check (document 13 v1.1): three further ±15% close moves outside the latest 800-bar window (31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%)) recorded as G-03 blocking cases awaiting the Owner's verification. Methodology unchanged. |
| 1.6 | §2.6, §2.7 | INFY source check (document 13 v1.2 §6): seven further ±15% close moves outside the latest 800-bar window, recorded as G-03 blocking cases. Methodology unchanged. |

Evidence and findings are otherwise unchanged. **Nothing in this document is a finding about the whole universe**: the only stock-type files inspected are four files for three instruments (CONCOR twice, INFY, NIFTYIT).

---

## 1. Headline: what could and could not be inspected

**The complete stock-file universe (about 2,000 daily files) has not been supplied to Claude 2.** The only daily stock-type files available in this project are:

| File | Type | Inspected |
|---|---|---|
| `CONCOR.txt` | Headerless daily text, one stock | Fully |
| `CONCOR_daily_26Nov98-06Nov26.parquet` | Parquet converted from the text file | Fully |
| `INFY_daily_02Jan98-06Nov26.parquet` | Parquet, one stock | Fully |
| `Nifty_IT.txt` | Headerless daily text, sector index (D-13: separate dataset) | Fully |

So, of the eight questions in Task 1, this document can:
- answer them **for these files only**, as representative evidence;
- define **exactly how** the universe inventory must be done;
- define the **pilot selection method** (section 6).

The universe-level answers — total files, unique symbols, structural variants, corrupt or duplicate files, coverage per stock — **remain unverified**. Section 7 lists them, and section 8 proposes how to obtain them.

No figure in this document is extrapolated to the universe. Where a finding concerns only the inspected files, it says so.

---

## 2. Answers to Task 1 for the inspected files

### 2.1 Number of files and symbols (Task 1.1)

| Item | Inspected set | Universe |
|---|---|---|
| Files | 4: three distinct instruments (CONCOR, INFY, NIFTYIT), with CONCOR present twice (`.txt` and `.parquet`) | **Unverified** (about 2,000 expected, per the Project Owner) |
| Unique stock symbols | 2 (CONCOR, INFY) plus 1 sector index | **Unverified** |

The CONCOR pair already shows that **the same symbol can exist in two formats**, which the universe inventory must detect. The two CONCOR files are identical in OHLCV across all 6,860 rows (Deliverable 1, §8.2).

### 2.2 File formats, columns and fields (Task 1.2)

| Format | Example | Structure observed |
|---|---|---|
| Headerless text | `CONCOR.txt` | `YYYY-MM-DD,Open,High,Low,Close,Volume,Field7`. 7 fields on every line. Windows CRLF line endings. No byte-order mark. |
| Headerless text, mixed field count | `Nifty_IT.txt` | 7 fields until 10-Apr-23, then **6 fields** (field 7 absent) within the **same file** |
| Parquet | `INFY_daily…parquet`, `CONCOR_daily…parquet` | `datetime` (timestamp, 00:00), `open`, `high`, `low`, `close`, `Volume`. Mixed capitalisation: `Volume` capitalised, prices in lower case. |

Every file holds full OHLCV, not close prices only. One file holds one symbol, and identity comes **only from the file name**.

### 2.3 Date ranges (Task 1.3)

| Instrument | First date | Last date | Rows |
|---|---|---|---:|
| CONCOR | 26-Nov-98 | 06-Nov-26 | 6,860 |
| INFY | 02-Jan-98 | 06-Nov-26 | 7,169 |
| NIFTYIT | 25-Aug-03 | 06-Nov-26 | 5,761 |

All three end on the same date, 06-Nov-26.

### 2.4 Structural consistency (Task 1.4)

Even among these four files there are **three structural variants**: 7-field text, mixed 6/7-field text, and Parquet. Field 7 also changes meaning over time within a file (equal to volume, lower than volume, zero, or absent; Deliverable 1, §8.3). **Uniform structure across the universe cannot be assumed.**

### 2.5 Empty, corrupt, duplicate or inconsistent files (Task 1.5)

| Check | Inspected files |
|---|---|
| Empty or unreadable | None |
| Duplicate dates within a file | None |
| Same symbol in more than one file | CONCOR (`.txt` and `.parquet`: identical OHLCV values, but different files with different SHA-256 fingerprints — under G-16 a conflict for the Owner, not a duplicate) |
| OHLC violations | 1 (NIFTYIT 01-Jul-05, open 60.65 below low) |
| Non-positive prices | None |
| Runs of 20 or more identical volume values (a placeholder-volume pattern the owner's own conversion tool already treats specially) | None in these files |
| Zero volume | None |

### 2.6 Missing dates, gaps and coverage (Task 1.6) — **new finding**

Deliverable 1 found that all files agree exactly on trading days for **2023–26**. Extending the comparison to the **full history** of the three daily files shows that this agreement **does not hold before 2023**:

| Date | Day | CONCOR | INFY | NIFTYIT | Observation |
|---|---|---|---|---|---|
| 27-May-05 | Fri | — | — | present | Only the index has data |
| 14-Aug-06 | Mon | — | — | present | Only the index has data |
| 14-Jun-10 | Mon | — | — | present | Only the index has data |
| 03-Mar-12 | **Sat** | — | — | present | Weekend session in the index only |
| 28-Apr-12 | **Sat** | — | — | present | Weekend session in the index only |
| 04-Jun-19 | Tue | present | — | — | Only CONCOR has data |
| 25-Nov-19 | Mon | present | — | — | Only CONCOR has data |
| 31-Mar-22 | Thu | present | present | — | Index missing a day both stocks have |

In addition, **CONCOR is missing 87 trading days in 1998–2001** (22, 23, 28 and 14 per year). This is consistent with thin trading in its early listing years, but unverified.

**Consequences:**
1. The "derived calendar" (document 02 v1.1, §8) can mark these dates as missing for one file, but **cannot tell** whether a stock did not trade or the file is incomplete. Completeness for pre-2023 history is therefore materially more uncertain than for 2023–26. This strengthens the need for an official NSE calendar (V-03).
2. A stock's early years may be too sparse for analysis. The pilot method (section 6) uses only recent, dense history.

**Coverage against the proposed EMA scanner's needs (document 10):** each of the three files has more than 800 trading days, so each meets the proposed minimum. The latest 800-bar window, 17-Aug-23 to 06-Nov-26, contains **no missing day** in any of the three.

It does contain **one large move: CONCOR on 04-Jun-24**, when the close fell **−19.2%** (939.40 → 759.00; the open was +0.5%). The date matches the 2024 general-election result day, so a genuine market move is plausible. It is **unverified**, however, and under check V-PX-05 it becomes a flagged issue. Under the Owner's G-03 decision (11-Nov-26) this issue **blocks** long-window calculations until the Owner verifies it and marks it `VERIFIED_OK`.

*Earlier history (v1.5).* Outside that window, the CONCOR source check (document 13 v1.1 §4) found three further close moves beyond ±15% not previously recorded: 31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%). Each is a G-03 blocking case awaiting the Owner's individual verification. They block CONCOR EMA analysis dates 31-Jan-08 – 03-May-11, 20-Mar-20 – 09-Jun-23 and 10-Aug-20 – 27-Oct-23 respectively. The latest window is not affected. The INFY source check (document 13 v1.2 §6) likewise found seven close moves beyond ±15% before the latest window: 08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%). Each is a G-03 blocking case awaiting the Owner's verification. INFY's latest window is not affected.

### 2.7 Other issues affecting import or analysis (Task 1.7)

| Issue | Evidence | Effect |
|---|---|---|
| Same symbol in two formats | CONCOR `.txt` + `.parquet` (identical OHLCV, different fingerprints) | **G-16 (Owner-approved 11-Nov-26):** only files with **identical SHA-256** fingerprints are duplicates (content imported once, extra paths recorded). Any difference in fingerprint — including the CONCOR pair — is a conflict referred to the Owner; nothing is imported for that symbol until the Owner chooses. Files are **never merged or selected automatically**. |
| 6/7-field lines in one file | Nifty IT | The text reader must accept both (already in R3) |
| Back-adjusted history (working hypothesis) | Off-tick prices up to 03-Jul-25 (CONCOR) and 03-Sep-18 (INFY) | History can change on every corporate action; revisions are held (OD-04) |
| Unverified anomalies | CONCOR 06-Sep-13 (−36.5% gap); NIFTYIT 28-May-04 (~90% break, re-confirmed 12-Nov-26); CONCOR 04-Jun-24 (−19.2% close, plausibly genuine); CONCOR **31-Jan-08 (+15.83% close), 20-Mar-20 (+16.09% close), 10-Aug-20 (−15.24% close)** — found in the v1.9 source check; INFY **08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%)** — found in the v1.10 source check | Each blocks long-window calculations until the Owner verifies it (G-03, Owner-approved). None is classified, quarantined or unblocked automatically. |
| Open-price-only anomalies | CONCOR 26/27-May-04, 15-May-06; INFY 24-Oct-03 | The values affect only measures that use the open, but under G-03 (Owner-approved) each occurrence **blocks** continuity-dependent calculations, including the close-based EMA, until the Owner verifies it |
| Cross-file calendar disagreements before 2023 | Section 2.6 | Provisional completeness; official calendar needed |
| Symbol naming | File stems equal plain symbols here | Symbols with `&` or `-` (e.g. M&M, BAJAJ-AUTO) are untested |

---

## 3. What the universe inventory must establish (specification)

When the full universe is inspected, the following must be produced, **per file** and **per universe**. This is a specification of an inspection, not production code.

### 3.1 Per file

| # | Item | Purpose |
|---|---|---|
| 1 | Path, file name, extension, size, modified time, SHA-256 | Traceability; duplicate detection |
| 2 | Symbol derived from the file name (exact stem) and its file-safe form | Identity; collision check (02 v1.1 §3.2) |
| 3 | Format detected: text 6-field, text 7-field, text mixed, Parquet daily, other or unknown | Reader coverage |
| 4 | Readability: parse errors (count, first line number), header presence, line endings, encoding or BOM | Corrupt or variant files |
| 5 | Rows; first date; last date; trading days in the last 800 and the last 2,500 rows | Coverage |
| 6 | Duplicate dates, unsorted rows, OHLC violations, non-positive prices, zero or negative volume | Quality |
| 7 | Field 7 state by period (equal, lower, zero, absent) | D-01, D-02 |
| 8 | Runs of 20 or more identical volume values (placeholder pattern) | Volume reliability |
| 9 | Off-tick share of closes by year; last off-tick date | Back-adjustment evidence |
| 10 | Day-to-day open or close changes beyond ±15% | Continuity candidates |
| 11 | Absent days against the universe calendar (section 3.2), by year and within the last 800 rows, counted **only between the file's own first and last date**. Reported as *absences for review*, not as defects (§6.5). | Completeness |

### 3.2 Per universe

| # | Item |
|---|---|
| 1 | Total files; unique symbols; symbols with more than one file (and whether the files are identical) |
| 2 | Count of files per format variant; list of unknown or unreadable files |
| 3 | **Universe calendar:** for each date, the number of files with data. Dates traded by almost all active files are trading days; dates traded by only a handful are flagged. |
| 4 | Distribution of first and last dates; files whose last date is earlier than the universe's latest date (possibly delisted or stale) |
| 5 | Files with fewer than 800 rows (insufficient for the proposed EMA scanner) |
| 6 | Symbols with special characters or file-name collisions |
| 7 | Summary of quality findings by severity, using document 02 v1.1 check codes |

The output follows the existing evidence style: one Excel workbook named with the `dd_mmm_yy_hhmmss` suffix (sheets in §8.4). *(v1.2: the separate Markdown summary proposed in v1.1 is dropped; the workbook's Summary sheet covers it.)*

---

## 4. Effect of the gap on decisions already made

- **OD-06 (confirmed direction):** the ~50-stock pilot happens **only after** the universe inspection. That inspection is still outstanding, so the **pilot selection cannot be finalised yet**.
- **Gate 0, M1a, M1b and M2 are not blocked by the inventory.** They are built and accepted on the files already inspected (Nifty and Bank Nifty samples, CONCOR, INFY, NIFTYIT). V-04 is **not** a Gate 0 condition.
- **The pilot load (M1c) requires V-04.** **M1c may not begin until all of the following hold:** (1) the Project Owner has **explicitly authorised G-01** (the exploratory universe-inventory script; currently **not authorised**); (2) the inventory (V-04) has been **completed** and its results **reviewed**; (3) the proposed pilot list (about 50 stocks, CONCOR and INFY included, chosen by the approved method) has been **presented to the Project Owner**; (4) the Project Owner has **approved that actual list**. V-04 cannot be performed before G-01 is authorised. M1a, M1b and M2 are also complete (baseline sequence M1a → M1b → M2, then M1c).

---

## 5. Representative examples (actual data)

| Example | Data |
|---|---|
| Typical text line | `2026-11-06,437.00,439.80,430.00,439.80,494505,175794` (CONCOR; field 7 lower = net volume) |
| 6-field line | `2026-11-06,33270.15,33616.2,32727.05,32977.9,49068677` (Nifty IT) |
| Early sparse trading | CONCOR 1998: 4 rows between 26-Nov-98 and 18-Dec-98 |
| Calendar disagreement | 04-Jun-19: CONCOR has data; INFY and NIFTYIT do not |

---

## 6. Recommended method for selecting the ~50-stock pilot (Proposed — requires Owner approval)

The pilot has two jobs: to prove the database on **clean, representative** stocks, and to exercise the **known difficult cases** on purpose. A purely random sample would do neither reliably.

### 6.1 Step 1 — Eligibility filter (objective, from the universe inventory)

A file is eligible for the **core** group only if all of these hold:

1. It is readable by reader R3 or R4, with no file-level errors.
2. It is the **single** source for its symbol, or its other files are byte-identical (same SHA-256), or the Owner has already resolved the conflict and chosen it (G-16).
3. Its last date equals the universe's latest date (the stock is currently active).
4. It has **at least 2,500 rows** (about 10 years). This comfortably exceeds the proposed EMA minimum of 800 and allows long-history tests.
5. In its **latest 800 rows**: no OHLC violation, no quarantinable row, and no **unexplained** absence against the universe calendar (§6.5). Continuity candidates (±15% changes) do not automatically exclude a stock: large genuine market-wide moves, such as 04-Jun-24, would otherwise remove many good stocks. Instead they are listed for owner review, and at most a few are kept deliberately in group C.

### 6.2 Step 2 — Composition (about 50)

| Group | Size | How chosen | Why |
|---|---:|---|---|
| A. Core, large and liquid | ~30 | From eligible files: the Nifty 50 constituents, if the owner can supply the list; otherwise the 30 eligible stocks with the highest median daily volume over the latest 250 rows | Realistic, clean, high-value analysis set |
| B. Variety | ~10 | Eligible files spread across price levels (below ₹100 up to above ₹5,000) and listing ages (10 to 28 years) | Avoid testing only one kind of stock |
| C. Deliberate edge cases | ~10 | One or two files each of: fewer than 800 rows (tests `INSUFFICIENT_DATA`); 6-field and mixed 6/7-field text; a symbol with `&` or `-`; a stale or delisted file; a placeholder-volume run; a known continuity candidate (e.g. CONCOR); a symbol present in two formats; a file with early sparse years | Prove the import, validation and scanner rules on the difficult cases before the full universe |

CONCOR and INFY should be included regardless of the rules above. Their expected results are already documented, so they serve as reference stocks.

### 6.3 Step 3 — Record and freeze

The pilot list, the reason each stock was chosen and the inventory figures behind it are recorded in one table. It is frozen for M1 acceptance; any change is a recorded decision.

### 6.3a What the Owner approves now, and what later (v1.2)

- **Approved by the Owner (11-Nov-26):** the *method* in §6.1–§6.3 — the eligibility filter, the stratified groups of about 30 + 10 + 10, CONCOR and INFY always included within about 50 stocks, and the freeze rule.
- **Later, after the inventory:** the *actual list* of about 50 stocks, which Claude 2 proposes from the workbook's Pilot_Eligibility sheet with the reason for each choice.
- **Optional information from the Owner:** a current Nifty 50 constituent list for group A. Without it, group A uses the median-volume rule in §6.2.

### 6.4 Alternatives considered

| Method | Advantage | Disadvantage |
|---|---|---|
| **Stratified with edge cases (recommended)** | Proves both normal operation and error handling | Needs the inventory first |
| Nifty 50 only | Simple and familiar | Clean by construction; hides edge cases until the full load |
| Random 50 | Unbiased | May miss edge cases entirely, or include many unusable files |
| First 50 alphabetically | Trivial | Arbitrary; unrepresentative |

### 6.5 Absences are not automatically defects

When a stock has no row for a date, there are several legitimate explanations. The inventory and the pilot filter must **not** classify an absence as a missing-data defect automatically.

| Cause of absence | How it is treated |
|---|---|
| Exchange holiday, or weekend without a special session | Not an absence at all: the date is not a trading day in the calendar |
| Dates **before the stock's listing date** (its first row) or after delisting (its last row) | Not counted. Coverage is measured only between the file's own first and last date. |
| **Suspension** of trading in that stock, or days with no trades (e.g. CONCOR's thin 1998–2001 years) | Legitimate but unverifiable from the files alone. Reported as an *absence for review*; never filled. |
| A genuinely incomplete file | Also appears as an absence. It is distinguished from the above only by evidence: an official calendar (V-03), exchange suspension notices, or the Owner's review. |

**In practice:**
- The inventory reports absences, grouped by date range, as *for review*.
- Many stocks absent on the same dates suggests a calendar or vendor effect.
- One stock absent alone suggests suspension or a file gap.
- The pilot eligibility rule (§6.1, item 5) excludes a stock only for absences in the latest 800 rows that remain **unexplained after review**.

---

### 6.6 Review of the pilot method against the required coverage (new in v1.2)

| The pilot must cover | Covered by | Refinement in v1.2 |
|---|---|---|
| Different file formats and schemas | Group C (6-field and mixed 6/7-field text); groups A and B include whichever formats are common | Group C takes one file of **every** format variant the inventory finds (F-02), not only the two seen so far |
| Data coverage | Eligibility item 4 (≥ 2,500 rows) for A and B; group C short-history case | Group C includes one stock with 200–799 rows and one with fewer than 200, so both EMA `INSUFFICIENT_DATA` paths are exercised |
| Clean and representative data | Groups A and B through the eligibility filter | — |
| Duplicate or conflicting files | Group C (symbol in two formats) | Group C includes one **byte-identical** pair if any exists (expected `DUPLICATE_SOURCE`) and one **differing** pair such as CONCOR `.txt`/`.parquet` (expected `SOURCE_CONFLICT`, resolved by the Owner before the load) — G-16 |
| Suspicious price movements | Group C (known continuity candidate, e.g. CONCOR) | Group C includes one stock with a ±15% close move and one with an open-only ±15% move; under G-03 **both** block until the Owner verifies them, so the verification step is exercised |
| Missing or incomplete history | Group C (early sparse years); eligibility item 5 | — |
| Different listing histories | Group B (listing ages 10–28 years); group C (stale or delisted file) | — |

**Assessment.** The stratified method meets the requirement that the pilot test both normal data and known difficult cases; a random sample would not. Group sizes (~30 / ~10 / ~10) are **targets**: if the inventory finds fewer edge-case types, the remaining places go to group A. The rule of §6.5 is unchanged: absences caused by holidays, listing dates or suspensions are not defects.

## 7. What remains unverified

| Item | Status |
|---|---|
| Total files and unique symbols | **Unverified** |
| Format variants beyond the three observed | **Unverified** |
| Corrupt, empty or duplicate files | **Unverified** (except CONCOR duplicate) |
| Per-stock date ranges and coverage | **Unverified** (except the 3 files) |
| Universe calendar, and how widespread the pre-2023 disagreements are | **Unverified** |
| Symbols with special characters | **Unverified** |
| Placeholder-volume runs | **Unverified** (none in the 3 files) |

---

## 8. The universe inventory: procedure and script specification (rewritten in v1.2)

### 8.1 Status and authorisation

| Item | Status |
|---|---|
| Inventory procedure (this section) | **Designed — complete** |
| Exploratory universe-inventory script | **Not created. Not authorised** — the Owner confirmed on 11-Nov-26 that it must not be created without his explicit further approval. |
| Existing M0 inspection script (01b) | **Not modified** and must not be modified for this purpose |
| Inventory results | **None.** Nothing in this document is a universe finding. |

Once authorised, Claude 2 writes the script to this specification, the Owner runs it on his own PC, and shares the workbook. Claude 2 then updates this document with the findings and proposes the pilot list for approval (§6).

### 8.2 Why the existing M0 inspection script is not enough

*Basis:* the M0 script (01b) is not in the v1.4 ZIP received for this review (document 00 v1.7 §3.2), so this assessment rests on its documented purpose, inputs and 18 output sheets (Deliverable 1, Appendices B and C; index v1.4 §4), not on its source code.

| Need of the universe inventory | M0 script, as documented |
|---|---|
| Treat ~2,000 daily stock files uniformly and summarise them | Built around the 12 inspected files and their roles. Most of its sheets (intraday sessions, missing candles, derived-file shapes, CAS effect, reconciliation of the derived Nifty files, indicator check) do not apply to daily stock files. |
| Compare files **with each other** by content (duplicates, conflicts, one symbol in two formats) | Compares specific known pairs (CONCOR text vs Parquet; Bank Nifty CSV vs Parquet). It has no general symbol-level duplicate or conflict detection. |
| Build a **universe calendar** (for each date, how many files have data) | Compares the calendars of a handful of named datasets; no date-by-file-count view |
| Classify each file's **format variant** and list unknown formats | Reads the known formats; no per-file format classification across a folder |
| Count **close-only versus open-only** ±15% moves, and how many fall on the same date across stocks (market-wide moves) | Lists large gaps per inspected file; no split by type and no cross-file grouping. Both are needed for the G-03 decision and its review workload. |
| Report **EMA coverage** (rows, 800-bar availability, first scoreable date) per file | Not an M0 purpose |
| Produce one row per file at a size Excel handles, with long lists grouped | Per-record sheets sized for 12 files; at universe scale some (e.g. every anomaly, rows per year per file) would become unwieldy |
| Apply the pilot eligibility tests of §6.1 | Not an M0 purpose |

Extending M0 would mix two different jobs in one script and risk changing the reproducibility of Deliverable 1, which rests on it. A separate script is cleaner.

### 8.3 What the script would do (specification for the authorised script)

**Character.** Exploratory and read-only, like M0. It is not a Q-MAP module, is not extended into production code, and writes nothing except its workbook.

**Environment and use.** Python 3.12.10 from IDLE or Thonny (press F5). Packages: `pandas`, `pyarrow`, `openpyxl` (no DuckDB needed). Tkinter dialogs: a **folder picker** for the stock folder; a **Save As** dialog for the workbook (I-02). Progress lines in the shell: current file, files done of total, elapsed time; a clear message for every unreadable file; a final line with the saved path.

**Scope of the folder.** The selected folder **and its subfolders** (an inventory should see everything); each file's relative subfolder is reported. Files with extensions other than `.txt`, `.csv` and `.parquet` are listed as "not inspected (unsupported type)", never silently skipped.

**Per file** (items 1–11 of §3.1, plus):

| ID | Check | Rule |
|---|---|---|
| F-01 | Identity | Path, relative folder, name, extension, size, modified time, SHA-256; symbol = exact file stem (text) or stem before the first `_` followed by `daily` (Parquet, as in `INFY_daily_…`); file-safe form (02 §3.2) |
| F-02 | Format variant | `TXT7`, `TXT6`, `TXT_MIXED_6_7`, `CSV_HEADER`, `PARQUET_DAILY`, `OTHER` (with the reason), `UNREADABLE` (with the first error and line number) |
| F-03 | Basic structure | Rows; first and last date; header present; line endings; byte-order mark; encoding errors; empty file |
| F-04 | Record checks | Duplicate dates (exact and conflicting); unsorted rows; null or non-numeric values per field; non-positive prices; OHLC violations (02 V-PX-01); negative or non-whole volume; zero volume count; weekend dates |
| F-05 | Field 7 | Periods where it equals volume, is lower, is zero, or is absent (D-01) |
| F-06 | Placeholder volume | Runs of 20 or more identical volume values: count and longest |
| F-07 | Tick profile | Share of closes on the 0.05 grid by year; last off-tick date (back-adjustment evidence; reported only, never used to judge validity — TC-20) |
| F-08 | Large moves | Every day with open-vs-previous-close **or** close-vs-previous-close beyond ±15%, recorded with both percentages and a type: `CLOSE_MOVE` (close beyond ±15%) or `OPEN_ONLY` (open beyond, close within) |
| F-09 | Coverage | Rows in total, in the last 800 rows and in the last 2,500 rows; date of the 800th-last row; for EMA: first date with 800 rows of history |
| F-10 | Absences | Dates in the universe calendar (§8.3, U-03) absent from this file **between its own first and last date**, grouped into ranges, each with the number of other files also absent on those dates; marked *for review*, never as defects (§6.5) |

**Per universe:**

| ID | Output |
|---|---|
| U-01 | Total files; inspected, unsupported and unreadable counts; distinct symbols |
| U-02 | Symbols with more than one file: groups of **byte-identical** files (same SHA-256 — duplicates under G-16) and groups of **differing** files (conflicts for the Owner), with each file's size, row count and date range to help the Owner choose. No content-based matching is used to classify. |
| U-03 | Universe calendar: for every date, files with data, files "alive" on that date (between their first and last date), and the share. Shares near 100% suggest a trading day; very low shares suggest a data or special-session effect. Weekend dates listed separately. |
| U-04 | Distribution of last dates; files ending before the universe's latest date (possibly delisted or stale) |
| U-05 | Coverage buckets: fewer than 200 rows; 200–799; 800–2,499; 2,500 or more. Shows how many stocks the proposed 800-bar EMA policy (document 10 §A6) would leave unscored. |
| U-06 | Symbols with characters outside A–Z and 0–9; file-safe name collisions |
| U-07 | Large moves grouped by date: for each date, how many files show a move beyond ±15% (open or close). A date shared by many files suggests a market-wide event (e.g. 04-Jun-24); a lone file suggests a stock-specific event or a data problem. Totals give the Owner's verification workload under G-03 (every occurrence blocks until verified). |
| U-08 | Pilot eligibility flags per file (§6.1 items 1–5) — flags only, **not** a selection |

**Thresholds** (fixed, stated in the workbook): ±15% (V-PX-05); 20 identical volumes; 800 and 2,500 rows; 0.05 tick grid.

### 8.4 Workbook to be produced

File name: `Q-MAP_Universe_Inventory_<dd_mmm_yy_hhmmss>.xlsx`, saved where the Owner chooses. Dates shown as dd-mmm-yy. **No other output file** (the Summary sheet replaces the Markdown summary proposed in v1.1, avoiding an extra file).

| Sheet | Contents | Rows (approximate) |
|---|---|---|
| Summary | Run date, folder, script version, Python and package versions, run time, U-01 counts, U-05 buckets, counts of every problem type | ~40 |
| Files | One row per file: F-01 to F-09 in columns | ~2,000 |
| Symbols | One row per symbol: file count, identical or differing (U-02), files involved | ~2,000 |
| Format_Variants | Count and three example files per variant | <10 |
| Problems | Unreadable, empty, unsupported and `OTHER`-format files, with the reason | as found |
| Universe_Calendar | U-03, one row per date | ~7,500 |
| Large_Moves | F-08, one row per move | as found |
| Moves_By_Date | U-07 | as found |
| Absences_For_Review | F-10 ranges | as found |
| Coverage | U-04, U-05, U-06 | ~20 |
| Pilot_Eligibility | U-08 flags per file | ~2,000 |
| Notes | Method, thresholds, limitations, the read-only statement | ~20 |

### 8.5 How the results are used

| Result | Feeds |
|---|---|
| U-01, U-02, F-02, Problems | Reader coverage for M1c; G-16 cases for the Owner; V-04 closure |
| U-03 | Shows how far the pre-2023 calendar disagreements (§2.6) extend; supports the official-calendar request (V-03) |
| U-05, F-09 | How many stocks the EMA 800-bar policy leaves unscored (D-EMA-08) |
| U-07, F-08 | The size of the Owner's G-03 verification task |
| U-08 | The pilot proposal (§6), which the Owner then approves |

### 8.6 Acceptance of the inventory run

The run is accepted when: every file in the folder appears in exactly one of Files, Problems or the unsupported list; the Summary counts add up; no source file's modified time or fingerprint has changed (the script re-checks the fingerprints of a sample of 20 files at the end and reports the result); and the Owner confirms the folder was the complete stock universe.

### 8.7 Options considered for obtaining the inventory

| Option | How | Assessment |
|---|---|---|
| **(a) Recommended** | Separate exploratory script to this specification, run by the Owner | Data stays on the Owner's PC; one run; results tailored to §3. **Awaiting explicit authorisation.** |
| (b) | Owner uploads the stock folder | Likely too large; slower |
| (c) | Owner runs the existing M0 script on the stock folder | Not sufficient (§8.2) |

*End of document 09, v1.6.*
