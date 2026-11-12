# Q-MAP — Data Inventory and Quality Report

**Deliverable 1 of 11 | Version 1.4 | 12-Nov-26**

| Field | Value |
|---|---|
| Document | Q-MAP_Data_Inventory_and_Quality_Report |
| Version | 1.4 — v1.2 plus addenda from the v1.9 (CONCOR) and v1.10 (INFY) source checks (see Revision history); findings otherwise unchanged |
| Date | 11-Nov-26 |
| Prepared by | Claude 2 — Groundwork and Architecture Preparation |
| Governing documents | Q-MAP Human-Readable Blueprint v1.0; Q-MAP Technical Blueprint v1.0; Claude 2 Groundwork Assignment |
| Supporting workbook | Q-MAP_Data_Inventory_Workbook_v1.1_11_Nov_26_183420.xlsx (18 sheets: a Summary sheet plus 17 evidence sheets) |
| Exploratory script | QMAP_M0_Exploratory_Data_Inspection.py v1.1 (inspection only — not a Q-MAP module). **Not included in the package:** it was absent from the v1.4 ZIP and has not been re-supplied (index 00 §3.2). Its results are recorded in this report and the workbook. *(Corrected in v1.3; the earlier statement that it was included is withdrawn.)* |
| Review status | v1.0 and v1.1 reviewed by ChatGPT; v1.2 carries the second review's corrections. Pending final approval. |
| Blueprint milestone | M0 — Source inspection |

> This report is a design and preparation deliverable. It is not approval to begin production coding.

**Revision history**

| Version | Date | Change |
|---|---|---|
| 1.0 | 11-Nov-26 | First issue |
| 1.1 | 11-Nov-26 | Review corrections: (1) workbook has 18 sheets, not 17; (2) "no broken structure" qualified — all files parseable, but one invalid OHLC record exists (Nifty IT 01-Jul-05); (3) back-adjustment of stock history restated as a strong working hypothesis, not an established fact, with no automatic repair; (4) interpolated candles confirmed in the derived files only — presence in the 2023–24 1-minute master is an inference; (5) Nifty IT 28-May-04 level break explicitly unverified, no returns across it; (6) exploratory script supplied with the package; D-09 strengthened to retain the original source timestamp and provenance inside the stored data. |
| 1.2 | 11-Nov-26 | Second review: (a) §4 tick test qualified — the 0.05 step is a trading rule for traded securities, but for **indices** (calculated values) it is an *observed* property of the inspected data, not an established exchange rule; (b) new §6.5 and issue DQ-21 — closing-print volume semantics in the Bank Nifty source are inconsistent, so auction-record volumes must not simply be added to daily volume; (c) script inclusion statement corrected. Changed sections: header, §4, §6.2, new §6.5, §12. The workbook (v1.1) is unchanged; DQ-21 is documented here only. |
| 1.3 | 12-Nov-26 | (a) Header: the exploratory script is **not** in the package (correction). (b) **Addendum** after §8.4: the CONCOR source check (document 13 v1.1) found three further day-to-day moves beyond ±15% in the **close** — 31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%) — which the M0 check, built to count large **open** gaps, did not report. The count "4 large open gaps" remains correct as a count of open gaps. No other finding changed. The workbook (v1.1) is unchanged; these cases are documented here and in documents 02, 06, 09 and 13. |
| 1.4 | 12-Nov-26 | Addendum extended: the INFY source check (document 13 v1.2) found seven day-to-day **close** moves beyond ±15% that M0 did not report — 08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%). The count "1 large open gap" for INFY (24-Oct-03) remains correct as a count of open gaps. Workbook unchanged. |

**Status labels used in this report**

| Label | Meaning |
|---|---|
| Approved | Confirmed by the project owner (Sandeep) during inspection, or delegated by him to Claude 2 and recorded as such. |
| Proposed | Claude 2 recommendation. Not a requirement until approved. |
| Requires Clarification | Cannot be settled from the data alone. |
| Deferred | Recorded for later; not in initial scope. |

All dates use the dd-mmm-yy format. All times are India Standard Time (IST, Asia/Kolkata), and every intraday time is the **start** of the candle.

---

## 1. Purpose

This report records what the actual source files contain and how good their data is, as the blueprints require at milestone M0. It reports findings, not intentions.

Every number here comes from running checks against the files. The supporting workbook holds the detailed evidence (per-day, per-file and per-record tables). The exploratory script reproduces every figure from the source files.

---

## 2. Summary of findings

The data is generally well formed. Every file was readable and parsed without errors. No file had duplicate timestamps, null prices or non-positive prices. This does not mean every record is valid: one invalid OHLC record exists (Nifty IT, 01-Jul-05, an Open below the Low). All related files reconcile exactly with each other.

The material findings are about meaning and history, not file damage:

1. **Interpolated candles.** **Confirmed** in the derived 3/5/15-minute Nifty files on five days in 2023–24, including the two special Saturday sessions (02-Mar-24 and 18-May-24) where 90 minutes of non-trading time was filled. Their presence in the complete 2023–24 one-minute master is a strong **inference** — the derived files reproduce the master exactly over the period checked — but it has **not** been independently established, because the 1-minute sample starts on 09-Jan-25.
2. **Closing Auction Session (CAS) from 03-Aug-26.** CAS changes the shape of the trading day. It also looks different in raw source data (Bank Nifty: final print at 15:28 or 15:29, often with a 15:15 record) than in your standardised Nifty master (final print at 15:30).
3. **Auction price moves the daily range.** The auction price sets the daily High or Low on 16 of the 67 Nifty CAS days inspected. On 03-Aug-26 it is 200.75 points above the last traded close.
4. **Stock prices appear to be back-adjusted.** This is a strong **working hypothesis**, based on the off-tick price pattern; it is not conclusively established by that observation alone. If correct, each new bonus or split rewrites the whole price history, so stock maintenance cannot simply append new rows. Q-MAP will not automatically repair or adjust historical prices.
5. **Suspicious historical records need verification:**
   - CONCOR, 06-Sep-13: −36.5% open gap.
   - Nifty IT, 28-May-04: about −90% level break, possibly an index rebase — **unverified**. Returns must not be calculated across this date as if the series were continuous.
   - Nifty IT, 01-Jul-05: impossible open of 60.65.
6. **Indicator columns are unreliable as source data.** The embedded Pivot/CPR/Camarilla/ATR columns mix two calculation methods, and the monthly file carries daily values. They will not be imported (Approved).
7. **No timezone is stored in any Parquet file.** Only the Bank Nifty CSV states +05:30.
8. **Volume is optional by nature.** It is absent for Nifty before 17-Aug-26 and on every auction print. This is accepted as normal (Approved).

Main limitations: only samples of the intraday data were provided, and only two stocks represent the roughly 2,000-stock daily universe (section 13).

---

## 3. Source file inventory

Twelve data files were received, plus the assignment document.

| # | File | Format | Size (bytes) | Rows | First record | Last record | Role in Q-MAP |
|---|---|---|---:|---:|---|---|---|
| 1 | Nifty_1min_09Jan25-06Nov26.parquet | Parquet (ZSTD) | 3,638,795 | 168,623 | 09-Jan-25 09:15 | 06-Nov-26 15:30 | **Dataset A** — Nifty 1-min (sample of master) |
| 2 | NSE_BANKNIFTY__1_1min_17Aug26-11Nov26.parquet | Parquet (ZSTD) | 417,440 | 21,396 | 17-Aug-26 09:15 | 11-Nov-26 15:29 | **Dataset B** — Bank Nifty 1-min (sample) |
| 3 | NSE_BANKNIFTY__1.csv | CSV with header | 2,803,553 | 21,396 | 17-Aug-26 09:15 | 11-Nov-26 15:29 | Same data as file 2 (vendor export format) |
| 4 | CONCOR.txt | Headerless CSV text | 355,117 | 6,860 | 26-Nov-98 | 06-Nov-26 | **Dataset C** — stock daily (text) |
| 5 | CONCOR_daily_26Nov98-06Nov26.parquet | Parquet | 138,313 | 6,860 | 26-Nov-98 | 06-Nov-26 | Dataset C — created from file 4 |
| 6 | INFY_daily_02Jan98-06Nov26.parquet | Parquet | 144,271 | 7,169 | 02-Jan-98 | 06-Nov-26 | Dataset C — stock daily |
| 7 | Nifty_IT.txt | Headerless CSV text | 343,673 | 5,761 | 25-Aug-03 | 06-Nov-26 | Sector index — separate dataset (Approved) |
| 8 | Nifty_3min_02Jan23-30Oct26.parquet | Parquet | 3,000,898 | 117,943 | 02-Jan-23 09:15 | 30-Oct-26 15:30 | Derived from 1-min master — test reference |
| 9 | Nifty_5min_02Jan23-30Oct26.parquet | Parquet | 1,941,000 | 70,791 | 02-Jan-23 09:15 | 30-Oct-26 15:30 | Derived — test reference |
| 10 | Nifty_15min_02Jan23-30Oct26.parquet | Parquet | 781,206 | 23,639 | 02-Jan-23 09:15 | 30-Oct-26 15:30 | Derived — test reference |
| 11 | Nifty_daily_02Jan23-30Oct26.parquet | Parquet | 147,422 | 949 | 02-Jan-23 | 30-Oct-26 | Derived — test reference |
| 12 | Nifty_monthly_02Jan23-30Oct26.parquet | Parquet | 22,915 | 46 | 02-Jan-23 | 01-Oct-26 | Derived — test reference |

**How the derived files should be used (Proposed).** Files 8 to 12 were produced from the Nifty 1-minute master and reproduce it exactly (section 9). They are valuable as an independent answer key for testing Q-MAP's own timeframe aggregation. They should not be loaded as primary data, because the blueprint requires higher timeframes to be produced from the preserved 1-minute data.

### 3.1 Field structure as actually stored

| File group | Columns as stored | Time column |
|---|---|---|
| Nifty 1-min and derived Nifty files | `datetime`, `open`, `high`, `low`, `close`, 18 indicator columns (`TC`, `Pivot`, `BC`, `R1`–`R3`, `S1`–`S3`, `CamH3`–`CamH5`, `CamL3`–`CamL5`, `ATR in %`, `ATR Close-Close%`, `ATR in % (Prev)`, `ATR Close-Close% (Prev)`), `Volume` — 25 columns | `timestamp[ns]`, no timezone |
| Bank Nifty Parquet | `datetime`, `open`, `high`, `low`, `close`, `Volume` | `timestamp[us]`, no timezone |
| Bank Nifty CSV | `time`, `open`, `high`, `low`, `close`, `Volume`, `Plot`, `ATR in %`, `ATR`, `Daily ATR Closing to Closing%`, `Net Volume` | ISO 8601 text with offset, e.g. `2026-08-17T09:15:00+05:30` |
| Stock Parquet (CONCOR, INFY) | `datetime`, `open`, `high`, `low`, `close` (all non-null), `Volume` | `timestamp[us]`, no timezone, time 00:00 |
| Text files (CONCOR, Nifty IT) | No header. Field order: date, open, high, low, close, volume, field 7 | Text `YYYY-MM-DD` |

Prices are 64-bit decimals and Volume is a 64-bit whole number in every Parquet file. Column naming is mixed: OHLC in lower case, but `Volume` capitalised. Column-by-column detail is in the workbook sheet *Field_Schema*.

---

## 4. Inspection method

Checks were run on every row of every file. No data was sampled or edited. The main techniques were:

- **Structure checks:** column names and types, sort order, duplicate timestamps, nulls, non-positive prices, and OHLC relationships (High must be at or above Open, Close and Low; Low must be at or below Open, Close and High).
- **Tick test:** for traded NSE securities, prices move in steps of 0.05. A traded price that is not a multiple of 0.05 indicates either a corporate-action adjustment (daily stocks) or a calculated, filled-in value. **Qualification (v1.2):** index values (Nifty, Bank Nifty) are calculated, not traded. In this inspection, every one of the 190,019 one-minute index records in the clean 2025–26 samples (168,623 NIFTY plus 21,396 BANKNIFTY) lies on a 0.05 multiple. Off-tick index values appeared only inside the interpolated windows of the derived 2023–24 files. This is strong *empirical* evidence of 0.05 granularity in this vendor's index data. It is **not** an established exchange rule, so the design treats it as a rule that must be verified per instrument and period before off-tick values are declared synthetic (document 02 v1.1, V-PX-03).
- **Session reconstruction:** for each 1-minute trading day, the first candle, the last continuous-trading candle, the closing prints and every missing minute inside the session were identified.
- **Reconciliation:** coarser files were rebuilt from finer ones and compared value by value, and the two formats of the same data were compared.
- **Calendar comparison:** trading dates were compared across instruments, so that holidays (absent for everyone) can be told apart from missing data (absent for one instrument).

---

## 5. Dataset A — Nifty 1-minute (sample of master)

### 5.1 Checklist (assignment items 1–17)

| # | Item | Finding |
|---|---|---|
| 1 | File name and format | `Nifty_1min_09Jan25-06Nov26.parquet`, Parquet, ZSTD compression, 1 row group |
| 2 | Number of files | 1 (a sample extracted from the master) |
| 3 | File size | 3,638,795 bytes (about 3.5 MB) |
| 4 | Records | 168,623 |
| 5 | Columns | 25 (OHLC, 18 indicators, Volume) — see 3.1 |
| 6 | Data types | `timestamp[ns]`; prices `double`; Volume `int64` |
| 7 | Symbol coverage | One instrument. No symbol column: identity comes only from the file name. |
| 8 | Earliest record | 09-Jan-25 09:15 |
| 9 | Latest record | 06-Nov-26 15:30 |
| 10 | Timestamp format | Native Parquet timestamp, whole minutes (no seconds), candle start time |
| 11 | Timezone | None stored. Values are IST wall-clock times. |
| 12 | Duplicates | 0 duplicate timestamps |
| 13 | Missing values | Prices: 0. Volume: null on 148,103 rows (present only from 17-Aug-26, and never on the 15:30 auction print) |
| 14 | Missing dates/candles | 453 trading days. **No missing candles inside any continuous session.** 26 absent weekdays, all consistent with holidays (section 9.3). |
| 15 | Consistency | 0 OHLC violations; 0 off-tick prices; sorted ascending |
| 16 | Unusual records | 67 flat 15:30 auction prints; 1 flat 14:45 Muhurat closing print; see 5.3 |
| 17 | Suitability | Suitable as the primary intraday source, subject to the session rules in section 10 |

### 5.2 Intraday-specific checks

| Check | Finding |
|---|---|
| One-minute spacing | Every consecutive pair within a session is exactly 1 minute apart, except the expected jump from 15:14 to 15:30 on CAS days (67 occurrences). |
| Opening or closing label | **Start-of-candle.** Regular days run 09:15 to 15:29, which is 375 candles covering 09:15–15:30. A closing-time label would run 09:16 to 15:30. |
| Session boundaries | 385 regular days (09:15–15:29, 375 candles); 67 CAS days (09:15–15:14 plus a 15:30 print, 361 records); 1 Muhurat session (21-Oct-25, 13:45–14:44 plus a 14:45 print). |
| Records outside regular hours | Only the Muhurat session, which is legitimate. |
| Missing intervals | None inside continuous trading. |
| Duplicate timestamps | None. |
| OHLC relationships | All valid. |
| Volume | Present on 20,520 rows (57 days, 17-Aug-26 to 06-Nov-26). No zero or negative values. |

### 5.3 Closing Auction Session (CAS) behaviour in the master

From 03-Aug-26 the master shows continuous candles up to 15:14, nothing from 15:15 to 15:29, then one flat record at 15:30 (Open = High = Low = Close). That record equals the daily close. You confirmed that the 15:30 placement was a deliberate standardisation by your Market Data Manager.

Example, 03-Aug-26 (actual records):

| Time | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 15:13 | 24,578.40 | 24,583.80 | 24,575.30 | 24,575.30 | — |
| 15:14 | 24,577.35 | 24,584.05 | 24,569.00 | 24,573.55 | — |
| 15:30 | 24,774.30 | 24,774.30 | 24,774.30 | 24,774.30 | — |

On 16 of the 67 CAS days, the auction price lies outside the range traded between 09:15 and 15:14, so it sets the daily High (10 days) or Low (6 days). The largest effect is 03-Aug-26: the auction is 200.75 points above the 15:14 close and 164.80 points above the highest traded price. The full list is in the workbook sheet *CAS_Effect*. Under your decision D-07, the auction price **is** included in the daily OHLC.

---

## 6. Dataset B — Bank Nifty 1-minute (sample)

### 6.1 Checklist

| # | Item | Finding |
|---|---|---|
| 1–2 | Files and format | Two files holding the same data: a vendor CSV export with header, and a Parquet made from it |
| 3 | Size | CSV 2,803,553 bytes; Parquet 417,440 bytes |
| 4 | Records | 21,396 in each |
| 5–6 | Columns and types | Parquet: 6 columns (OHLC non-null `double`, Volume `int64`). CSV: 11 columns, including 5 calculated columns. |
| 7 | Symbol coverage | One instrument. Identity comes from the file name only. |
| 8–9 | Range | 17-Aug-26 09:15 to 11-Nov-26 15:29 (60 sessions, all after CAS began) |
| 10–11 | Timestamp and timezone | CSV: ISO 8601 with `+05:30`, the only file that explicitly states IST. Parquet: naive, offset removed, same wall-clock values. |
| 12 | Duplicates | 0 |
| 13 | Missing values | Prices and Volume: 0 nulls. CSV calculated columns contain blanks. |
| 14 | Missing candles | 2 missing candles inside continuous trading: **19-Aug-26 13:28 and 13:29** (left as a gap, not filled) |
| 15 | Consistency | 0 OHLC violations; 0 off-tick prices; CSV and Parquet identical on all OHLCV values |
| 16 | Unusual records | 7 zero-volume records, all closing or 15:15 prints; Muhurat session 08-Nov-26 |
| 17 | Suitability | Suitable. It shows the raw vendor form of CAS days, which is essential for designing import rules. |

### 6.2 Closing pattern — raw form of CAS

Bank Nifty shows how CAS days arrive from the vendor before any standardisation:

| Pattern after the 15:14 candle | Days |
|---|---:|
| 15:15 record, then final print at 15:29 | 24 |
| 15:15 record, then final print at 15:28 | 19 |
| Final print at 15:29 only | 10 |
| Final print at 15:28 only | 7 |

- **The final print** is always flat and is the closing auction price. Its time (15:28 or 15:29) varies with no pattern that carries meaning.
- **The 15:15 record** appears on 43 of 60 days. It is flat on 38 of them. On the other 5 it has a very small range (for example 18-Aug-26: 57,314.55 to 57,308.15), and its volume is always small (median about 17,000 against several hundred thousand for a normal minute).
- **Volume on the final print** varies from 0 to 23.6 million, and its meaning is not consistent across the period (§6.5).

This differs from the Nifty master (15:30 print, no 15:15 record). The import rules must therefore standardise raw vendor files into one consistent form. The decisions are D-09 and D-10 in section 11.

### 6.3 Missing-candle example — 19-Aug-26 (actual records)

| Time | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 13:26 | 57,069.75 | 57,076.10 | 57,062.00 | 57,071.35 | 114,180 |
| 13:27 | 57,071.25 | 57,072.50 | 57,068.40 | 57,068.40 | 2,486 |
| *13:28 and 13:29 — no record* | | | | | |
| 13:30 | 57,071.30 | 57,080.75 | 57,062.40 | 57,076.60 | 177,373 |

This is a genuine gap that was correctly not filled. It will serve as a test case for completeness reporting and for aggregation of incomplete intervals.

### 6.4 Calculated columns in the CSV

`Plot`, `ATR in %`, `ATR`, `Daily ATR Closing to Closing%` and `Net Volume` are calculated by the charting tool, not supplied by the exchange. In particular, `Net Volume` equals plus or minus `Volume` on 21,395 of 21,396 rows, with the sign set by whether the candle closed up or down. It is therefore unrelated to the delivery-style net volume in the stock text files. Under decision D-12 none of these columns are imported.

### 6.5 Volume on auction records (new in v1.2)

The second review asked whether the 15:15 and final-print volumes are independent, duplicated or cumulative. On BANKNIFTY 18-Aug-26 both show 19,993. Checking all 60 sessions:

| Observation | Days |
|---|---:|
| Days with a 15:15 record | 43 |
| …of which the final-print volume **exactly equals** the 15:15 volume | **19** (e.g. 17-Aug-26 15,007 / 15,007; 18-Aug-26 19,993 / 19,993; 31-Aug-26 27,637 / 27,637) |
| Final-print volume = 0 | 6 |
| Final-print volume > 100,000 | 23, almost all from **12-Oct-26 onwards** (e.g. 27-Oct-26 23,608,288) |
| Final-print volume ≤ 100,000 | 31, almost all **before 12-Oct-26** |

**Interpretation (evidence-based, not conclusive).**
- Before about 12-Oct-26, the final-print volume often repeats the 15:15 value exactly, which looks like duplication.
- From 12-Oct-26, it is consistently in the millions, which looks like a genuine auction quantity.
- The vendor's volume semantics for these records therefore **changed or are inconsistent**, and cannot be established from the data alone.
- The NIFTY master carries no volume on its 15:30 prints, so the question does not arise there.

**Consequence (DQ-21).**
- Auction-record volumes are preserved exactly as supplied on their own records.
- They are **not** added to daily volume.
- Daily volume is reported as the continuous-session volume, marked incomplete with a reason (document 03 v1.1, §B7).

**Manual example, BANKNIFTY 18-Aug-26.** The sum of continuous candle volumes from 09:15 to 15:14 is **123,512,346**. Adding both auction records would give 123,552,332, counting the possibly duplicated 19,993 twice.

---

## 7. Derived Nifty files (3-min, 5-min, 15-min, daily, monthly)

### 7.1 Structure and consistency

These files cover 02-Jan-23 to 30-Oct-26: 949 trading days, 46 months. They have no duplicate timestamps, no OHLC violations and no null prices. Monthly rows are labelled with the first trading day of the month, not the 1st of the month. Daily rows carry time 00:00.

Day shapes found in the 3-min file:

| First bar | Last bar | Bars per day | Days | Meaning |
|---|---|---:|---:|---|
| 09:15 | 15:27 | 125 | 882 | Regular day before CAS |
| 09:15 | 15:30 | 121 | 62 | CAS day (03-Aug-26 onwards) |
| 09:15 | 12:27 | 65 | 2 | Special Saturdays 02-Mar-24, 18-May-24 (see 7.2) |
| 18:15 / 18:00 / 13:45 | — | 20 / 20 / 21 | 3 | Muhurat 12-Nov-23, 01-Nov-24, 21-Oct-25 |

### 7.2 Interpolated (synthetic) candles — important

Prices that break the 0.05 tick were found in the intraday derived files on five days:

| Date | Time window (3-min file) | Off-tick bars (3-min) | Nature |
|---|---|---:|---|
| 14-Jun-23 | 12:39–12:45 | 3 | Short fill |
| 07-Aug-23 | 15:21 | 1 | Short fill |
| 02-Mar-24 | 10:00–11:27 | 30 | 90-minute fill during a period with no trading |
| 23-Apr-24 | 10:51–10:57 | 3 | Short fill |
| 18-May-24 | 10:00–11:27 | 30 | 90-minute fill during a period with no trading |

Evidence from 02-Mar-24 (actual records): the close rises by exactly 0.4055 every 3 minutes, while High and Low stay fixed at 22,410.35 and 22,389.95. Real trading does not do this.

| Time | Open | High | Low | Close |
|---|---:|---:|---:|---:|
| 10:00 | 22,394.40000 | 22,410.35 | 22,389.95 | 22,394.80549 |
| 10:03 | 22,394.80549 | 22,410.35 | 22,389.95 | 22,395.21099 |
| 10:06 | 22,395.21099 | 22,410.35 | 22,389.95 | 22,395.61648 |
| 11:30 | 22,406.70000 | 22,410.35 | 22,389.95 | 22,399.55000 |

**Evidence status.** The fills are **confirmed** in the inspected derived files. That they also exist in the 2023–24 one-minute master is an **inference**: the derived files reproduce the master exactly wherever the two overlap (09-Jan-25 onwards), but the master's 2023–24 period was not provided and has **not** been inspected. The 2025–26 one-minute sample contains no fills. The project owner has attributed such fills to occasional technical glitches that can affect any instrument on any day. Confirmation requires inspecting the full master (item C-4).

**Limitation:** the tick test only catches a filled value that happens to break the 0.05 tick. A fill that lands on a valid tick is invisible to it. The validation design will therefore add a second test that looks for runs of candles with a constant step and a frozen High/Low (Proposed).

### 7.3 Embedded indicator columns

| Check | Result |
|---|---|
| Same value on every intraday bar of a day | Yes — they are daily-level values repeated on every bar |
| Monthly file indicators | Equal to the first trading day's **daily** values in 46 of 46 months, so they are not monthly pivots |
| Pivot = previous day (H+L+C)/3 from the same file, before 03-Aug-26 | Exact on 3 of 886 days; mean difference 4.35 points, maximum 39.90 |
| Same test from 04-Aug-26 | Exact on 57 of 61 days; mean difference 0.25 |
| Days where TC < BC | 468 of 949 (CPR top/bottom labels not normalised) |

So two different calculation methods or data sources are mixed in these columns. This supports decision D-12: indicators are not stored in the database, and scanners calculate them.

### 7.4 Volume in derived files

Volume is present only for 17-Aug-26 to 30-Oct-26 (52 days). It is null on all other days and on the 15:30 auction bar. Where present, each derived file's Volume equals the sum of the finer file's Volume.

---

## 8. Dataset C — Daily stocks, and Nifty IT

### 8.1 Checklist

| # | Item | CONCOR | INFY | Nifty IT |
|---|---|---|---|---|
| 1–2 | Files | `CONCOR.txt`, plus Parquet created from it | Parquet only | `Nifty_IT.txt` |
| 3 | Size (bytes) | 355,117 / 138,313 | 144,271 | 343,673 |
| 4 | Records | 6,860 | 7,169 | 5,761 |
| 5 | Fields | Text: 7 fields. Parquet: OHLCV. | OHLCV | Text: 7 fields until 10-Apr-23, then 6 |
| 6 | Types | Prices decimal; Volume whole number | Same | Same |
| 7 | Symbol identity | **File name only** — one symbol per file, no symbol field | Same | Same |
| 8–9 | Range | 26-Nov-98 to 06-Nov-26 | 02-Jan-98 to 06-Nov-26 | 25-Aug-03 to 06-Nov-26 |
| 10 | Date format | Text `YYYY-MM-DD`; Parquet timestamp at 00:00 | Parquet timestamp at 00:00 | Text `YYYY-MM-DD` |
| 11 | Timezone | Not applicable (exchange trading date) | Same | Same |
| 12 | Duplicates | 0 | 0 | 0 |
| 13 | Missing values | 0 in OHLCV | 0 | 0 in OHLCV; field 7 absent on 888 rows |
| 14 | Missing dates | None against the Nifty calendar 2023–26; sparse trading in 1998–99 (gaps of up to 18 days) | None against the Nifty calendar | None against the Nifty calendar |
| 15 | OHLC consistency | 0 violations | 0 violations | **1 violation** (01-Jul-05) |
| 16 | Suspicious records | 4 large open gaps (8.4) | 1 large open gap | Level break 28-May-04; bad open 01-Jul-05 |
| 17 | Suitability | Suitable after flagged records are verified | Suitable | Suitable after the 2004 break is handled |

**Data content:** these files hold **full OHLCV**, not close prices only. Multiple stocks are stored **separately**, one file per symbol. Line endings are Windows CRLF and the files have no byte-order mark.

### 8.2 Text file vs Parquet

`CONCOR.txt` and `CONCOR_daily_26Nov98-06Nov26.parquet` are identical on all 6,860 rows for Open, High, Low, Close and Volume. Field 7 was dropped during conversion, which matches decision D-01.

### 8.3 Field 7 behaviour

| File | Period | Field 7 |
|---|---|---|
| CONCOR | 26-Nov-98 to 26-Jul-18 | Equal to Volume (4,810 rows) |
| CONCOR | 27-Jul-18 to 06-Nov-26 | Mostly lower than Volume (about 47% on average) — net volume; equal on isolated days |
| Nifty IT | 25-Aug-03 to 25-Nov-20 | Equal to Volume |
| Nifty IT | 26-Nov-20 to 12-Aug-22 | Zero |
| Nifty IT | 16-Aug-22 to 10-Apr-23 | Equal to Volume |
| Nifty IT | 11-Apr-23 to 06-Nov-26 | Field absent (6 fields per line) |

Handling (D-01, D-02, Approved): ignore field 7 when it equals Volume. When it is lower, it is net volume, an optional extra that is not part of the fixed structure. When it is zero or absent, net volume is not available. A reader must accept both 6- and 7-field lines.

### 8.4 Corporate-action adjustment and suspicious records

**Back-adjustment (working hypothesis).** The share of closes that sit on the 0.05 tick is near zero for older years and 100% for recent years:

- CONCOR: off-tick prices continue up to **03-Jul-25**.
- INFY: off-tick prices continue up to **03-Sep-18**.

This pattern is **consistent with** back-adjusted prices, where history before each bonus or split has been divided by an adjustment factor. Off-tick prices are strong evidence but do not conclusively prove it: confirmation would need the vendor's adjustment policy or a comparison with unadjusted exchange data. **Q-MAP must not automatically repair, adjust or un-adjust historical prices.** Consequence (Proposed): because adjusted history can be rewritten by the source, **maintenance cannot be assumed to be append-only for stocks.** When a new corporate action is applied at source, the whole history of that symbol changes and must be reloaded and revalidated. Nifty IT is entirely on-tick, as expected for an index.

**Records needing verification** (actual values):

| File | Date | Prev close | Open | High | Low | Close | Observation | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| CONCOR | 26-May-04 | 73.64 | 88.32 | 88.32 | 74.37 | 75.91 | Open +19.9% but close only +3.1% | Requires Clarification |
| CONCOR | 27-May-04 | 75.91 | 88.19 | 88.19 | 66.59 | 76.13 | Open +16.2%, close +0.3% | Requires Clarification |
| CONCOR | 15-May-06 | 228.75 | 265.36 | 265.36 | 217.86 | 220.49 | Open +16.0%, close −3.6% | Requires Clarification |
| CONCOR | 06-Sep-13 | 270.61 | 171.78 | 191.44 | 171.78 | 181.53 | −36.5% gap; possible unadjusted corporate action or bad data | Requires Clarification |
| INFY | 24-Oct-03 | 69.03 | 81.25 | 81.25 | 69.03 | 71.16 | Open +17.7%, close +3.1% | Requires Clarification |
| Nifty IT | 28-May-04 | 21,264.15 | 2,132.05 | 2,139.40 | 1,989.10 | 2,011.25 | Level falls ~90%; possibly an index rebase — **unverified**; no returns may be calculated across this date | Requires Clarification |
| Nifty IT | 01-Jul-05 | 3,072.10 | 60.65 | 3,062.75 | 3,041.80 | 3,051.35 | Open impossible (below Low); OHLC violation | Invalid record |

The pattern "open far above the previous close, close near the previous close" in 2003–06 is typical of early-session data errors in old vendor data. These records are flagged, not corrected. Q-MAP must never silently repair source data.

**Weekend dates.** CONCOR has 30 weekend dates, INFY 34 and Nifty IT 28. These match NSE's historical Saturday and special sessions (for example 25-Oct-03, 15-Nov-03, 17-Oct-09) and are treated as legitimate.

---

**Addendum (v1.3, 12-Nov-26) — CONCOR close moves beyond ±15%.** This section's check counted large **open** gaps. The later source check of `CONCOR.txt` (document 13 v1.1 §4) also covered **close-to-close** moves and found, in addition to 04-Jun-24 (−19.2%, documented in 09 §2.6), three further cases: 31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%). All are unverified. Under G-03 (Owner decision, 11-Nov-26) each is a blocking case awaiting the Owner's individual verification. None is classified as an error or a genuine move, quarantined or unblocked.

**Addendum (v1.4, 12-Nov-26) — INFY close moves beyond ±15%.** The INFY source check (document 13 v1.2 §6) found, besides the documented open gap on 24-Oct-03, seven close moves beyond ±15%: 08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%). All are unverified. Under G-03 each is a blocking case awaiting the Owner's individual verification. None is classified, quarantined or unblocked.

## 9. Cross-dataset checks

### 9.1 Reconciliation (all PASS)

| Check | Rows compared | Differences |
|---|---:|---:|
| Nifty 1-min rebuilt to 3-min vs Nifty_3min file (09-Jan-25 to 30-Oct-26) | 55,648 | 0 |
| Nifty 3-min rebuilt to 15-min vs Nifty_15min file | 23,639 | 0 |
| Nifty 5-min rebuilt to 15-min vs Nifty_15min file | 23,639 | 0 |
| Nifty 3-min rebuilt to daily vs Nifty_daily file | 949 | 0 |
| Nifty daily rebuilt to monthly vs Nifty_monthly file | 46 | 0 |
| CONCOR.txt vs CONCOR Parquet (OHLCV) | 6,860 | 0 |
| Bank Nifty CSV vs Bank Nifty Parquet (OHLCV) | 21,396 | 0 |

The rebuild used the standard rule: Open = first, High = maximum, Low = minimum, Close = last, with intervals anchored at 09:15 within each day. These results prove that the existing derived files follow exactly that rule, including the CAS print, which sits as its own 15:30 bar intraday and inside the daily candle. This makes them a reliable answer key for later aggregation tests.

### 9.2 Calendar alignment

Between 02-Jan-23 and 30-Oct-26, CONCOR, INFY and Nifty IT trade on **exactly** the same dates as Nifty, with zero differences in either direction. Absent weekdays are therefore market-wide closures, not gaps in individual files.

### 9.3 Weekdays with no data (02-Jan-23 to 06-Nov-26) — 57 days

| Year | Count | Dates |
|---|---:|---|
| 2023 | 15 | 26-Jan, 07-Mar, 30-Mar, 04-Apr, 07-Apr, 14-Apr, 01-May, 29-Jun, 15-Aug, 19-Sep, 02-Oct, 24-Oct, 14-Nov, 27-Nov, 25-Dec |
| 2024 | 16 | 22-Jan, 26-Jan, 08-Mar, 25-Mar, 29-Mar, 11-Apr, 17-Apr, 01-May, 20-May, 17-Jun, 17-Jul, 15-Aug, 02-Oct, 15-Nov, 20-Nov, 25-Dec |
| 2025 | 13 | 26-Feb, 14-Mar, 31-Mar, 10-Apr, 14-Apr, 18-Apr, 01-May, 15-Aug, 27-Aug, 02-Oct, 22-Oct, 05-Nov, 25-Dec |
| 2026 | 13 | 15-Jan, 26-Jan, 03-Mar, 26-Mar, 31-Mar, 03-Apr, 14-Apr, 01-May, 28-May, 26-Jun, 14-Sep, 02-Oct, 20-Oct |

These are consistent with NSE trading holidays and occur identically in every dataset. **They have not yet been checked against NSE's official holiday lists**, so their status is "consistent with holidays — verification pending".

### 9.4 Special sessions found

| Date | Day | Session | Evidence |
|---|---|---|---|
| 12-Nov-23 | Sun | Muhurat | 18:15–19:12 (3-min file) |
| 20-Jan-24 | Sat | Special full session | Full regular day |
| 02-Mar-24 | Sat | Special session (disaster-recovery test) | 09:15–12:27, with interpolated fill 10:00–11:27 |
| 18-May-24 | Sat | Special session (disaster-recovery test) | Same pattern as 02-Mar-24 |
| 01-Nov-24 | Fri | Muhurat (evening) | 18:00–18:57 |
| 01-Feb-25 | Sat | Budget-day session | Full regular day |
| 21-Oct-25 | Tue | Muhurat | 13:45–14:44, plus 14:45 closing print |
| 01-Feb-26 | Sun | Budget-day session | Full regular day |
| 08-Nov-26 | Sun | Muhurat (Bank Nifty sample) | 14:20–15:14 plus 15:15 and 15:29 prints (CAS-style close) |

---

## 10. Session rules established from the data

| Session type | Applies to | Continuous candles (start times) | Closing record(s) | Status |
|---|---|---|---|---|
| Regular, before CAS | All instruments up to 31-Jul-26; non-CAS instruments afterwards | 09:15–15:29 (375) | None | Approved (D-05) |
| CAS | CAS instruments from 03-Aug-26 (Nifty and Bank Nifty confirmed in data; about 200 stocks) | 09:15–15:14 (360) | Optional 15:15 record, then closing auction print | Approved (D-04) |
| Special | Muhurat, Budget-day, DR-test and similar sessions | Varies by occasion | Closing print may exist | Times to be held as reference data (Proposed) |

**CAS detection rule (generalised from the agreed approach; Proposed for confirmation):** a day is a CAS day for an instrument when:

- a 15:14 candle exists, and
- no record exists between 15:16 and 15:27, and
- the day ends with a flat print at or after 15:15.

This rule correctly classified all 67 Nifty CAS days and all 59 regular-hours Bank Nifty days. It also recognised the Bank Nifty Muhurat of 08-Nov-26 as a CAS-style special session. It produced no false positives on the 385 pre-CAS Nifty days.

---

## 11. Decisions recorded during inspection

| ID | Subject | Recorded position | Decided by | Status |
|---|---|---|---|---|
| D-01 | Field 7 in text files | Ignore when equal to Volume; when lower it is net volume; zero or absent means not available | Sandeep | Approved |
| D-02 | Net volume | Optional extra only; not part of the fixed data structure | Sandeep | Approved |
| D-03 | Volume | Field always defined; missing values allowed and not an error | Sandeep | Approved |
| D-04 | CAS session | From 03-Aug-26 for CAS instruments: continuous trading ends 15:15 (last candle 15:14); auction print follows | Sandeep | Approved |
| D-05 | Non-CAS session | Continuous trading until 15:30 (last 1-min candle 15:29) | Sandeep | Approved |
| D-06 | CAS identification | Detected automatically from the data; instruments and dates reported for confirmation; official list optional cross-check | Sandeep | Approved |
| D-07 | Auction price in daily OHLC | Included in daily High, Low and Close | Sandeep | Approved |
| D-08 | Auction price in intraday timeframes | Kept as a separate labelled record; not merged into the last candle | Sandeep | Approved |
| D-09 | Auction print timestamp | Stored at the session's official closing time (15:30 on regular days) and labelled as closing auction. **The original source timestamp and source provenance are retained in the stored record itself** (not only in the original files), so standardisation never destroys the original timing. | Claude 2, at Sandeep's request; strengthened by review | Approved (delegated) |
| D-10 | 15:15 record | Kept at 15:15, labelled as an auction-phase record, excluded from intraday candles, included in daily High/Low | Sandeep | Approved |
| D-11 | Filled-in candles | Never stored as real trades; gaps kept as gaps and reported | Sandeep | Approved |
| D-12 | Indicator columns | Not stored in the database; scanners calculate indicators | Sandeep | Approved |
| D-13 | Nifty IT | Separate sector-index dataset, not part of the stock dataset | Sandeep | Approved |

**Reasoning for D-09 (delegated decision).**

- *It matches the existing master.* Your Nifty master already uses 15:30, so one convention covers both old and new data.
- *The vendor's minute carries no meaning.* Bank Nifty puts the same event at 15:28 on some days and 15:29 on others.
- *A fixed time stays unambiguous.* 15:30 cannot clash with a continuous-trading candle for non-CAS instruments, because their last candle starts at 15:29.

The record is identified by an explicit "closing auction" label, not by its clock time alone. This is a safeguard if NSE ever changes the auction timing. As strengthened by the review, every standardised record also keeps its original source timestamp and a link to its source file, so the vendor's 15:28/15:29 timing is never lost.

---

## 12. Issues register (summary)

The full register, with evidence and handling, is in the workbook sheet *Issues_Register*. Severity: **High** means it can distort analytical results if unhandled; **Medium** means it needs a design rule; **Low** means a minor or cosmetic issue; **Info** means expected behaviour that still needs to be documented.

| ID | Dataset | Finding | Severity | Status |
|---|---|---|---|---|
| DQ-01 | Nifty (2023–24) | Interpolated candles on 5 days | High | Approved handling (D-11) |
| DQ-02 | Nifty | Tick test cannot detect on-tick fills | Medium | Proposed (add run detection) |
| DQ-03 | Nifty, Bank Nifty | CAS session shape from 03-Aug-26 | Info | Approved (D-04, D-06) |
| DQ-04 | Nifty | Auction sets daily High/Low on 16 of 67 CAS days | Info | Approved (D-07) |
| DQ-05 | Bank Nifty vs Nifty master | Raw final print at 15:28/15:29 plus optional 15:15 record, vs standardised 15:30 | Medium | Approved (D-09, D-10) |
| DQ-06 | Nifty | Volume absent before 17-Aug-26 and on auction prints | Low | Approved (D-03) |
| DQ-07 | Nifty derived files | Indicators repeated per bar; monthly file holds daily values | Medium | Approved (D-12) |
| DQ-08 | Nifty derived files | Indicator method changed around Aug-26 | Medium | Approved (D-12) |
| DQ-09 | Bank Nifty | 2 missing candles on 19-Aug-26 | Low | Approved handling |
| DQ-10 | Bank Nifty CSV | Calculated columns, including tool-calculated Net Volume | Low | Approved (D-12) |
| DQ-11 | Text files | Field 7 meaning varies by period | Low | Approved (D-01) |
| DQ-12 | Stocks | Back-adjusted history (working hypothesis); maintenance cannot be assumed append-only; no automatic repair | High | Proposed |
| DQ-13 | CONCOR | −36.5% gap on 06-Sep-13 | High | Requires Clarification |
| DQ-14 | CONCOR | Abnormal opens 2004–06 | Medium | Requires Clarification |
| DQ-15 | Nifty IT | ~90% level break on 28-May-04 (unverified; no returns across it) | High | Requires Clarification |
| DQ-16 | Nifty IT | Invalid open on 01-Jul-05 | High | Proposed (flag/reject in validation) |
| DQ-17 | All Parquet | No timezone stored | Medium | Proposed (catalogue declares Asia/Kolkata) |
| DQ-18 | Calendar | Holiday list not yet officially verified | Low | Proposed |
| DQ-19 | Special sessions | Non-standard session times | Medium | Proposed (reference data) |
| DQ-20 | Nifty IT | Index volume has vendor-defined meaning | Low | Proposed (optional field) |
| DQ-21 | Bank Nifty | Auction-record volume semantics inconsistent (duplicated 15:15 value on 19 days; large values from 12-Oct-26) | Medium | Proposed (exclude from daily volume; flag; verify with vendor) — new in v1.2 |

Totals: 5 High, 8 Medium, 6 Low, 2 Info (DQ-21 added in v1.2; the workbook's live count shows the v1.1 total of 20).

---

## 13. Suitability for intended analytical purposes

| Purpose | Dataset | Assessment |
|---|---|---|
| Intraday scanners (1-min up to hourly) | Nifty 1-min | **Suitable.** The 2025–26 sample is clean. The 2023–24 master contains known fill days, which must be flagged so scanners can exclude them. |
| Intraday scanners | Bank Nifty 1-min | **Suitable** within the sample period. A longer history has not been inspected. |
| Daily, weekly and monthly scanners (e.g. MA Affinity) | CONCOR, INFY | **Suitable.** If the working hypothesis of back-adjustment holds, the prices are appropriate for trend and moving-average work. The flagged records must be verified or excluded before long-history studies. |
| Volume-based analysis | Nifty, Bank Nifty | **Limited.** Nifty volume covers only 57 days. Scanners that need volume must check availability first. |
| Volume-based analysis | Stocks | **Suitable** — volume is present on every row of the samples. |
| Sector-index analysis | Nifty IT | **Suitable from 28-May-04** onwards. Data before that date appears to sit on a different level basis (DQ-15, unverified); returns must not be calculated across the break. |
| Testing Q-MAP aggregation | Derived Nifty files | **Very suitable** as an answer key (9.1). |
| Any use of embedded indicators | Derived Nifty files, Bank Nifty CSV | **Not suitable** — not imported (D-12). |

---

## 14. Checks not completed and limitations

1. **Full master size and history.** Only a 1-minute sample (09-Jan-25 to 06-Nov-26) was provided. The full master's size, start date and the exact extent of filled days in 2023–24 at 1-minute level are unconfirmed.
2. **Bank Nifty history.** Only 60 post-CAS sessions were inspected. Pre-CAS Bank Nifty data, and any fills in it, are unknown.
3. **Stock universe.** Two stocks represent a universe of about 2,000 daily files. Format consistency, naming, adjustment status and duplicate handling across the whole universe are unverified. A full-universe inventory run of the exploratory script is recommended (Proposed).
4. **Official holiday list.** Absent weekdays were not compared with NSE's published holiday lists, because those lists were not available to Claude 2.
5. **Corporate actions.** The suspected events (DQ-13, DQ-14, DQ-15) could not be confirmed without an independent price or corporate-action source.
6. **On-tick fills.** Filled candles that land exactly on the 0.05 tick are undetectable with the current test (DQ-02).
7. **Official close.** Whether the auction print equals NSE's officially published closing price could not be verified without official daily data. Your Market Data Manager v4.3 already compares High/Low with an official daily CSV, and that check could be extended to Close.

---

## 15. Points carried forward to the database design (Deliverable 2)

These are inputs to the next phase, not decisions. Each will be presented with alternatives and status in the database architecture.

1. Each instrument needs its own session pattern with effective dates. Records need a label for their type: continuous candle, auction-phase record, or closing auction.
2. Every NSE dataset must declare its timezone (Asia/Kolkata) in the catalogue, because no Parquet file stores it.
3. Stock maintenance must detect history changes caused by corporate actions and reload the affected symbol. Append-only updating is not safe.
4. Volume and net volume are optional fields. Scanners must check availability through the data-access interface.
5. Gaps, suspected fills, flagged records and holidays must be reported in the catalogue's completeness and quality status, never repaired silently.
6. A small reference list of special sessions and holidays is needed so that intentional closures are not reported as missing data.
7. Symbol identity currently comes only from file names, so the import process must fix one naming rule.

---

## 16. Items requiring clarification

| # | Question | Why it matters | Suggested resolution |
|---|---|---|---|
| C-1 | Can the CONCOR 06-Sep-13 gap and the 2004–06 abnormal opens be verified against another source? | Distorts long-history statistics | Check against NSE bhavcopy or a second vendor; until then, flag the records |
| C-2 | Is the Nifty IT break on 28-May-04 an index rebase? | Returns across the break are meaningless | Confirm from NSE index history; then use data from 28-May-04 or adjust earlier history |
| C-3 | Can NSE holiday lists for 2023–26 be supplied as a file? | Separates holidays from missing data | Provide yearly holiday lists (CSV or PDF) |
| C-4 | Should a full inventory be run across all stock files and the full 1-minute master on your computer? | Two-stock and sample-only evidence | Run the exploratory script locally and share the workbook |
| C-5 | Is the auction print identical to NSE's official closing price? | Daily Close correctness | Extend the existing official-CSV comparison to Close |

---

## Appendix A — Example records (actual data)

**Nifty 1-min, regular day (31-Jul-25), last candles**

| Time | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 15:27 | 24,755.05 | 24,756.25 | 24,750.25 | 24,756.05 | — |
| 15:28 | 24,756.70 | 24,763.50 | 24,749.25 | 24,754.55 | — |
| 15:29 | 24,754.40 | 24,766.60 | 24,747.55 | 24,765.60 | — |

**Nifty 1-min, CAS day with volume (17-Aug-26)**

| Time | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 15:13 | 24,356.15 | 24,358.90 | 24,350.90 | 24,357.20 | 1,507,649 |
| 15:14 | 24,357.35 | 24,357.35 | 24,330.70 | 24,341.90 | 2,225,266 |
| 15:30 | 24,287.65 | 24,287.65 | 24,287.65 | 24,287.65 | — |

**Bank Nifty raw CAS close with 15:15 record (11-Nov-26)**

| Time | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|
| 15:14 | 60,547.15 | 60,568.85 | 60,516.70 | 60,530.15 | 2,403,516 |
| 15:15 | 60,548.10 | 60,548.10 | 60,548.10 | 60,548.10 | 54,132 |
| 15:29 | 60,792.40 | 60,792.40 | 60,792.40 | 60,792.40 | 9,477,104 |

**Text file lines (raw)**

```
CONCOR.txt   first line: 1998-11-26,29.61,29.61,29.44,29.44,3906,3906
CONCOR.txt   last line:  2026-11-06,437.00,439.80,430.00,439.80,494505,175794
Nifty_IT.txt last line:  2026-11-06,33270.15,33616.2,32727.05,32977.9,49068677
```

## Appendix B — Exploratory inspection script

`QMAP_M0_Exploratory_Data_Inspection.py` is **exploratory only**. It is not part of the Q-MAP application and must not be extended into one.

It reads the source files without modifying them, performs every check in this report, and writes the supporting workbook. It runs from IDLE or Thonny, with folder pickers for the input and output folders. It needs `pandas`, `pyarrow` and `openpyxl`.

Its value is reproducibility: the independent reviewer or Claude 1 can re-run it on the same files and obtain the same numbers, and you can run it over the full master and the whole stock universe (C-4).

## Appendix C — Workbook sheet guide (18 sheets)

| Sheet | Contents |
|---|---|
| Summary | Purpose, version, live issue counts by severity |
| File_Inventory | One row per file: size, rows, time storage, range, quality counts |
| Field_Schema | Columns as stored |
| Intraday_Sessions | Per-day session pattern for each 1-minute file (513 days) |
| Missing_Candles | Each missing candle inside a continuous session |
| Derived_Shapes | Bars per day patterns in the 3, 5 and 15-minute files |
| Synthetic_Candles | Off-tick intraday days (interpolation evidence) |
| CAS_Effect | Days where the auction sets the Nifty daily High or Low |
| Reconciliation | Cross-file comparisons |
| Calendar | Absent weekdays and weekend sessions |
| Calendar_Alignment | Cross-dataset date agreement |
| Daily_Anomalies | Large gaps and OHLC violations in daily files |
| Adjustment_Profile | On-tick share by year (back-adjustment evidence) |
| Field7 | Field 7 behaviour by period |
| Rows_Per_Year | Daily row counts by year |
| Indicator_Check | Evidence for decision D-12 |
| Issues_Register | Full issues register |
| Decisions | Decisions D-01 to D-13 |

*End of Deliverable 1, v1.4.*
