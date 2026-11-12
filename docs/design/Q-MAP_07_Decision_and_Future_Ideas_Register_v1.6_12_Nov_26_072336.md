# Q-MAP — Decision, Feature and Future Ideas Register

**Package document 07 | Version 1.6 | 12-Nov-26 | Status: Register — v1.6 adds an INFY row to §D (INFY G-03 cases). Open Owner decisions are in document 12.**

| Field | Value |
|---|---|
| Covers | A. Material open decisions for the Project Owner; B. technical choices made by Claude 2 (for reviewer check); C. approved decisions carried forward; D. pending verification items; E. contradictions found; F. feature register (priority, complexity, status); G. Future Enhancements and Ideas Register |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed items | Reason (review item) |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | OD-01 to OD-09 recommendations | Updated as instructed in review section C. Alternatives retained. |
| 1.1 | TC-02, TC-15 revised; TC-21 to TC-24 added | Generations; provisional notes; daily volume rule; Python version (A1, A4, B1, B5) |
| 1.1 | New section D2: I-01, I-02 | Owner information needed: Python version; GUI conventions (B1, B2) |
| 1.1 | V-03, V-04, V-06, V-08 revised; V-09, V-10 added | Auction volume semantics; tick rules (A4, A6, B4, B5) |
| 1.1 | F-05, F-11, F-12 revised; F-23 added | Hold revisions; generation commit; tick-rule table (A1, A2, A6) |
| 1.1 | FI-17 added | Automatic corporate-action application deferred (A2) |
| 1.2 | §A | OD-01 to OD-09 marked **confirmed** (record: document 11 §1.1). Confirmed wording of OD-02, OD-03, OD-07 and OD-09 shown. Open decisions moved to document 12. |
| 1.2 | TC-10 | Corrected: daily volume does **not** include auction-record volume. v1.1 contradicted TC-23 and 03 §B7. |
| 1.2 | TC-12, TC-24, §D2 | Aligned with the confirmed I-01 (Python 3.12.10) and I-02 (GUI conventions) |
| 1.2 | TC-25 to TC-29 added | Technical choices made in the follow-up review (document 00 v1.5 §2) |
| 1.2 | §E note; E-10 to E-13 added | ID clash with document 11's gap IDs explained; new contradictions found and resolved |
| 1.2 | F-02, §E G-06 | Catalogue has **11** tables, not 10 |
| 1.2 | F-05, F-11, F-15, F-33, F-34 | Statuses updated for confirmed decisions |
| 1.3 | §A note | Owner decisions of 11-Nov-26 recorded by reference (G-03, G-04, G-16, D-EMA-01 to 10, pilot method; G-01 not authorised) — record: 11 v1.3 §1.3 |
| 1.3 | TC-25, TC-26, TC-29 | Revised for G-09, the resolution-test finding, and G-02 provenance |
| 1.3 | E-13; F-05, F-33 | E-13 resolved by the Owner's G-03 decision; statuses updated |
| 1.4 | §D V-04 | "Needed before" corrected: the pilot load (M1c) only; not Gate 0, M1a, M1b or M2; blocked until G-01 is authorised |
| 1.5 | §D V-01 | Lists all CONCOR ±15% cases including the three found in the v1.9 source check; corrects the stale "`affects_continuity` for 06-Sep-13" to the G-03 rule (every case blocks until verified) |
| 1.6 | §D V-01b (new) | INFY ±15% cases, including the seven found in the v1.10 source check; each blocks until verified (G-03) |

Approved decisions D-01 to D-13 are unchanged.

---

## A. Material Owner decisions OD-01 to OD-09 — all confirmed

**Status (v1.2).** All nine decisions in this section have been **confirmed by the Project Owner**. The written record is document 11 §1.1, which prevails where this table's wording differs. The table is kept because its "Alternatives" and "Consequences" columns explain each decision. Read the "Recommended" column as the confirmed position, with these clarifications:

- **OD-02 confirmed wording:** *Combined Technical Setup Strength measures how strongly a stock satisfies the technical conditions measured by the selected scanners.*
- **OD-03 confirmed wording:** *Reject the combined score if a required scanner result is missing or invalid.* Option B (renormalise) is not adopted.
- **OD-07 confirmed wording (broader than the row below):** *Use available history, disclose actual coverage and report calculations as unavailable when history is insufficient.* It governs every calculation, not only index history.
- **OD-09 confirmed wording:** *Fixed, documented, deterministic scoring rules. Exact scanner parameters still require approval.*

**Further Owner decisions recorded 11-Nov-26** (written record: 11 v1.3 §1.3): G-03 (every ±15% move blocks until the Owner verifies it), G-04 (tick-rule verification standard), G-16 (only exact SHA-256 duplicates; differing files to the Owner), D-EMA-01 to D-EMA-10 (EMA methodology approved, subject to G-03; combined weight deferred), the stratified pilot method; G-01 inventory script **not authorised**.

The "Owner approval?" column records that each item needed the Owner; it no longer means "pending". **Decisions still open are listed only in document 12 (Owner Decision Register).** Minor technical choices are in section B.

| ID | Subject | Current approved position | Alternatives | Recommended | Reason | Consequences and risks | Owner approval? | Blocks |
|---|---|---|---|---|---|---|---|---|
| **OD-01** | Which 2–3 scanners, and which is first | Examples only (MA Affinity, EMA Analysis, Breakout); none approved | Any combination; any order | First scanner = the one whose specification can be approved and hand-verified fastest on daily stock data. **EMA Analysis on daily stocks is a candidate for the first scanner — not an approved scanner.** Add the higher-complexity MA Affinity once the chain is proven. | Blueprint priority: a useful, verified result early; daily stock data is the most complete and simplest | Starting with a high-complexity scanner delays the first verified result | **Yes** | M3 (and every scanner specification) |
| **OD-02** | What a high combined score **means**; which scanners may share a profile | Weighted score approved; meaning undefined | e.g. "bullish set-up strength", "reliability of technical behaviour", or several profiles each with its own meaning | **A scoring profile must have an approved, clearly defined meaning** (one sentence) before use; scanners declare which meanings they support | A weighted sum of unlike measures is meaningless (document 05, section 3.3) | Without it, combined scores can mix opposing measures and mislead | **Yes** | M5 |
| **OD-03** | Missing or invalid scanner result in a combined score | Missing must not be treated as zero (Approved) | A: Reject. B: Renormalise (with minimum available weight). | **Option A (reject the combined score when a required result is missing) remains the preferred initial policy.** B only with a ≥ 70% minimum and visible flags. | Comparability; no flattering of results (document 05, section 5) | A: fewer instruments receive a score. B: scores rest on different scanner sets. | **Yes** | M5 |
| **OD-04** | Source revises previously supplied history | Not decided; append-only must not be assumed | (1) Hold every revision for owner review. (2) Auto-apply uniform-factor revisions, hold the rest. (3) Auto-apply everything. | **P1: (1) — hold all historical revisions for Project Owner review.** Uniform-factor revisions are detected and reported as *candidate* corporate actions, not proof. Existing canonical data is preserved until approval; the complete previous generation and the revision evidence are preserved. **Automatic corporate-action handling is deferred** (FI-17) until the factor and effective date can be matched to independently verified corporate-action information. | A uniform factor can also come from an erroneous source change (test T-MNT-03b); safety outweighs convenience in P1 | More manual review after every bonus or split. Mitigated by clear evidence in the Data Manager. | **Yes** | M1 incremental maintenance (not the initial load) |
| **OD-05** | Detection detail for synthetic candles (implementing D-11) | D-11: never store fills as trades; gaps reported | (a) Quarantine off-tick under a **verified** tick rule, flag otherwise, and flag constant-step runs. (b) Quarantine off-tick and constant-step runs regardless. (c) Flag everything. | **(a)** — the tick-size rule must be verified per instrument and period (`instrument_rule`) before automatic off-tick quarantine. Until then off-tick rows are flagged for review. Constant-step detection stays a warning-only heuristic. | Index values are calculated; 0.05 granularity is so far only *observed* in the data (Deliverable 1 v1.2, §4) | Until rules are verified, flagged fabricated rows may remain in use (visibly flagged) | **Yes** (it removes data from use) | M1 validation |
| **OD-06** | Size of the stock universe at M1 | Not decided | (i) Pilot: CONCOR, INFY plus about 50 stocks. (ii) All ~2,000 files at once. | **(i) Pilot of about 50 stocks, only after the full-universe inspection (V-04) has identified schema variations**; full universe afterwards | Only two stocks have been inspected; the format consistency of the universe is unverified | (ii) risks discovering format variants mid-load | **Yes** | M1 scope |
| **OD-07** | Daily history for indices before the 1-minute master begins | Indices are stored at 1 minute only | (i) Daily index bars only from 1-minute data. (ii) Also import a vendor daily index file as a separate dataset. | **Deferred until a concrete requirement arises** (an approved scanner needing longer index history) | No need to add a dataset before a scanner needs it | If a scanner needs long index history, (ii) becomes necessary | **Yes** (when relevant) | Only scanners needing long index history |
| **OD-08** | Net-volume extras store (D-02) | Net volume is optional and not structured data | P1 or P2 | **Deferred (P2) until a concrete requirement arises** | No current scanner needs it; it adds a store and rules | None for initial scanners | **Yes** (confirms D-02 timing) | No |
| **OD-09** | Score calibration of each scanner | Common 0–100 scale proposed | Fixed-anchor mapping, rule-based points, frozen percentile | **Fixed-anchor or rule-based calibration remains the preferred initial direction** (CAL-1 to CAL-7) | Deterministic, verifiable by hand, independent of the run universe | Poor calibration makes combined scores meaningless | **Yes** (per scanner specification) | M3/M4 for that scanner; M5 |

---

## B. Technical choices made by Claude 2 (no owner decision needed — reviewer to check)

These follow the instruction to resolve minor technical details by choosing the simplest reliable option.

| ID | Choice | Simpler or alternative option rejected | Document |
|---|---|---|---|
| TC-01 | Catalogue = one DuckDB file holding metadata only; no SQLite | JSON/CSV (no transactions); SQLite (not needed) | 02 §5.1 |
| TC-02 | Each instrument stored as numbered **generations**; inside a generation, intraday files per year and daily as one file; the active generation is selected by a catalogue pointer (revised v1.1) | Files replaced one by one (multi-file replacement not atomic: review A1) | 02 §2, §9.4 |
| TC-03 | Timestamps naive IST wall-clock, microseconds, timezone declared in the catalogue; candle-start meaning | Timezone-aware storage (display shifts with PC settings) | 02 §4.5 |
| TC-04 | Prices DOUBLE; volume BIGINT nullable | DECIMAL (adjusted prices exceed 2 decimals; no gain) | 02 §4 |
| TC-05 | Datasets grouped by structure: `NSE_INDEX_1M`, `NSE_EQ_DAILY`, `NSE_SECTOR_INDEX_DAILY` | Blueprint's provisional per-index IDs (see G-01) | 02 §3.1 |
| TC-06 | `instrument_id` = NSE symbol; file-safe name rule; unknown files never guessed | Symbol inferred loosely from file names | 02 §3.2 |
| TC-07 | Exact duplicates collapsed; conflicting duplicates all quarantined | Keep-first (silently picks one value) | 02 §6.2 |
| TC-08 | Intraday intervals anchored at each session's open (09:15); last interval truncated and flagged | Clock-aligned hours | 03 §B4 |
| TC-09 | Week = Monday–Sunday; month = calendar month; labelled by first trading date (matches the existing monthly file) | Label by period start or end date | 03 §B8 |
| TC-10 | Daily bars from 1-minute data include auction-phase and closing-auction **prices** in H/L/C. Their **volumes are not added** to daily volume (see TC-23). *Corrected in v1.2.* | — (implements D-07, D-10) | 03 §B7 |
| TC-11 | All timeframes computed on demand in P1; minute codes limited to 1, 3, 5, 10, 15, 30, 60 until a scanner needs more | Precomputed timeframes | 03 §B10 |
| TC-12 | User applications in plain Tkinter, one self-contained file each, meeting the **confirmed** I-02 conventions (file picker, folder picker, Save As, clear progress and error messages, simple consistent interface). The owner's wider desktop preferences are optional, not required (v1.2). | Other frameworks (see §E G-03) | 04 §M-07 |
| TC-13 | Tests with standard-library `unittest`, run from IDLE via `run_all_tests.py` | pytest (needs the command line and an extra dependency) | 06 §2 |
| TC-14 | Run output = JSON plus Excel; non-code outputs named with a dd_mmm_yy_hhmmss suffix | — | 05 §7.2 |
| TC-15 | Keep catalogue backups for the last 10 maintenance runs, plus every generation any of them references; prune only after a successful run | Unlimited (disk growth) or none | 02 §10 |
| TC-16 | One writer at a time: Data Manager and Analysis Runner are not used simultaneously | Locking service (unnecessary complexity) | 02 §9.5 |
| TC-17 | Full precision stored; 2-decimal round-half-up for display only | Rounding stored values | 05 §2 |
| TC-18 | Scanner registry is an explicit dictionary, not automatic discovery | Plug-in discovery (forbidden) | 04 §M-03 |
| TC-19 | Combined scores only from results within one run | Combining saved results across runs (staleness rules needed) | 05 §4.3 |
| TC-20 | Off-tick test applied only where an `instrument_rule` tick rule exists for that instrument and period; quarantine only when that rule is verified; never applied to back-adjusted daily stock history (revised v1.1) | Applying a global 0.05 rule everywhere (review A6) | 02 §7.1 |
| TC-21 | Instrument-level commit = stage complete generation → validate → rename folder → one catalogue transaction switches the pointer; recovery on start-up | Per-file atomic replace | 02 §9.4 |
| TC-22 | Informational `notes` (provisional completeness, candidate sessions) are separated from status-affecting `warnings` | Making every response `PARTIAL` until the calendar is verified (would hide real warnings) | 03 §A6 |
| TC-23 | Daily volume = continuous-session candle volume only; auction-record volumes kept on their own records and excluded, pending V-09 | Summing all records (possible double count: DQ-21) | 03 §B7 |
| TC-24 | Python version: the owner's installed **Python 3.12.10** (I-01, confirmed). Package versions are pinned exactly for it at Gate 0, and all tests run only on those pins (TC-29, G-15). | — | 08 §6 |
| TC-25 | An Update examines only files in the folders the Owner explicitly selects for it; registered sources that are missing or unreadable in those folders are reported (`SOURCE_INACCESSIBLE`) and never removed or treated as deletion; registered sources outside the selection are listed as not in scope; an exact SHA-256 match is never imported twice (G-09; revised v1.3) | Scanning all previously imported paths automatically (outside the Owner's selection) | 02 §9.6 |
| TC-26 | Readers R1/R2 accept a file as 1-minute data when the **most common** within-day time step is 1 minute (at least 30 within-day steps); otherwise the file is refused with a reason; a coarser day inside an accepted file is flagged `RESOLUTION_SUSPECT` (revised v1.3) | Smallest step (v1.2; no answer for sparse files) or trusting the file name | 02 §6.1 |
| TC-27 | `DataRequirement` gains an optional `latest_n`; `context.fetch` maps a requirement to `get_bars` field by field (interface version 1.1, additive) | A second fetch route for look-backs (two ways to get data) | 03 §A5; 04 §7.2 |
| TC-28 | `affects_continuity` alone decides whether an issue blocks continuity-dependent calculations; marking an issue `VERIFIED_OK` clears it | Combining flag and status in each scanner (inconsistent rules) | 02 §5.2; 04 SC-07 |
| TC-29 | Official calendar file: holidays and special sessions only; ISO dates; import stores rows as `REFERENCE_FILE_UNCONFIRMED`; they become `OFFICIAL_REFERENCE`, `verified = true` only after the Owner records the official source (`evidence`, `confirmed_at`); a covered year counts as complete only then; under a CAS rule continuous trading ends 15 minutes before `session_close` (G-02; revised v1.3) | Treating any imported file as official (ChatGPT finding 6) | 02 §5.5 |

---

## C. Approved decisions carried forward (not reopened)

| ID | Decision | Where implemented |
|---|---|---|
| D-01 | Field 7: ignore when equal to Volume; lower = net volume; 0 or absent = unavailable | 02 §6.1, R3 |
| D-02 | Net volume optional, not structured | 02 §4.3; OD-08 timing |
| D-03 | Volume nullable; missing is not an error | 02 §4, V-VOL-02; 03 warnings |
| D-04 | CAS from 03-Aug-26: continuous trading ends 15:15 (last candle 15:14), auction print follows | 02 §6.2; 03 §B3 |
| D-05 | Non-CAS: continuous trading to 15:30 (last candle 15:29) | 02 §6.2; 03 §B3 |
| D-06 | CAS detected from data; reported for confirmation | 02 §6.2 (`pattern_confirmed`) |
| D-07 | Auction price included in daily OHLC | 03 §B7 |
| D-08 | Auction record kept separate in intraday timeframes | 03 §B1, §B9 |
| D-09 | Closing auction stamped at the official session close; **original source timestamp and provenance retained in the stored record** | 02 §4.1 (`source_ts`, `import_id`) |
| D-10 | 15:15 record kept as an auction-phase record, not a candle; included in daily H/L | 02 §6.2; 03 §B7 |
| D-11 | Synthetic fills never stored as genuine trades; gaps kept and reported | 02 §7 (V-PX-03/04); OD-05 detail |
| D-12 | Embedded indicator columns not imported | 02 §4.3 |
| D-13 | Nifty IT is a separate sector-index dataset | 02 §3.1 |

No approved decision has been changed. D-09 is implemented in its strengthened form, which retains `source_ts` in the data.

---

## D. Pending verification items (known limitations carried into the design)

| ID | Item | How the design represents it | Needed before |
|---|---|---|---|
| V-01 | CONCOR ±15% cases: 26/27-May-04, 15-May-06, **31-Jan-08**, 06-Sep-13, **20-Mar-20**, **10-Aug-20**, 04-Jun-24 (bold: found in the v1.9 source check, document 13 §4) | WARNING issues with flags; **every case `affects_continuity = true` until the Owner verifies it (G-03)**; scanners obey SC-07 | Long-history studies on CONCOR; the Owner's verification of each case |
| V-01b | INFY ±15% cases: **08-Aug-00, 11-Apr-01, 18-Apr-01, 10-Apr-03**, 24-Oct-03, **11-Jan-13, 12-Apr-13, 22-Oct-19** (bold: found in the v1.10 source check, document 13 §6) | WARNING issues with flags; **every case `affects_continuity = true` until the Owner verifies it (G-03)**; scanners obey SC-07 | Long-history studies on INFY; the Owner's verification of each case |
| V-02 | Nifty IT 28-May-04 suspected rebase (unverified) | Issue `LEVEL_BREAK_UNVERIFIED`, `affects_continuity = True`; no returns across it | Use of Nifty IT before Jun-04 |
| V-03 | NSE holidays and special-session times not checked against official records | `market_calendar.verified = false`; optional `reference\nse_market_calendar.csv`; **all completeness labelled `PROVISIONAL_DERIVED_CALENDAR`**; special sessions only through an official entry or owner confirmation | Final approval of completeness reporting |
| V-04 | Full 1-minute master and full stock universe not inspected | Ingestion rules marked sample-based; inventory via the G-01 script (**not authorised**); OD-06 pilot only **after** this inspection | The pilot load (M1c) and any wider load — **not** Gate 0, M1a, M1b or M2 |
| V-05 | Closing-auction price vs official NSE close | Not automated in P1; comparison is P2 once an official daily close file is available | Optional |
| V-06 | Back-adjustment of stock history (working hypothesis) | No automatic adjustment; every revision held (OD-04); uniform factor reported as a candidate only | Any future automatic corporate-action handling (FI-17) |
| V-07 | Interpolated candles in the 2023–24 master (inferred, not established) | V-PX-03 and V-PX-04 will reveal them on load; expected ACC-01 differences listed | Loading the 2023–24 master |
| V-08 | Official close time of special sessions (e.g. Muhurat) | **Explicitly unverified** until official reference data exists: the closing print keeps its source time with `SESSION_CLOSE_UNVERIFIED` | Use of special-session intraday bars |
| V-09 | Meaning of volume on auction records in vendor data (DQ-21: duplicated 15:15 values on 19 of 43 days; large values from 12-Oct-26) | Auction volumes preserved but excluded from daily volume; `volume_complete` False; flag `VOLUME_EXCLUDES_AUCTION` | Any scanner using daily volume of CAS instruments; confirm with vendor |
| V-10 | Tick-size rule per instrument and period (0.05 for indices observed, not established) | `instrument_rule` rows with `verified = false` (`OBSERVED_IN_DATA`); off-tick flagged, not quarantined | Automatic off-tick quarantine (OD-05) |

### D2. Information from the Project Owner — both items now confirmed (v1.2)

I-01 = **Python 3.12.10**. I-02 = **file picker, folder picker, Save As, clear progress and error messages, simple consistent interface**; the wider conventions in the I-02 row below are not required (document 11 §1.2). The original requests are kept for the record:

| ID | Information | Why | Needed before |
|---|---|---|---|
| I-01 | Installed Python version on the owner's Windows PC (in IDLE: `import sys; print(sys.version)`) | Choose compatible, pinned package versions. Package support differs by Python version: for example, pandas 3.x needs Python 3.11 or newer, while pandas 2.x supports older versions. If the installed Python is no longer supported by the needed packages, an upgrade becomes an owner decision. | Gate 0 |
| I-02 | Whether the owner's standing desktop-GUI conventions (numbered sections, scrollable frame, detailed live status, specific shutdown sequence) should apply to Q-MAP's two applications | They are documented owner preferences for desktop tools, but not yet stated as Q-MAP requirements | M1 (Data Manager GUI) |

---

## E. Contradictions and tensions identified

*Note on IDs (v1.2).* The IDs G-01 to G-09 in this section are local to document 07 and are **not** the gap IDs G-01 to G-16 of document 11 (for example, 07 §E G-01 is about dataset names, while 11 G-01 is the universe inventory). Cite these as "07 §E G-xx". New entries use E-xx to avoid further confusion.

| ID | Between | Description | Resolution |
|---|---|---|---|
| G-01 | Technical Blueprint (provisional dataset IDs) and TC-05 | Blueprint lists `NIFTY_1M`, `BANKNIFTY_1M`, `NIFTY_STOCKS_DAILY` | IDs were marked provisional. The grouping is a naming refinement, not a scope change. Reviewer to confirm. |
| G-02 | Blueprint ("check suspicious volume nulls") and D-03 | Volume is mostly null by nature | Volume nulls are reported as coverage information, not issues |
| G-03 | Blueprint ("choose UI after workflow is demonstrated") and the owner's documented Tkinter standard | Timing of the UI choice | TC-12 uses the owner's standard; the UI stays thin and separate, so it is cheap to change |
| G-04 | Blueprint ("preserve original 1-minute data") and D-09 / D-11 | Re-stamping and quarantining could seem to alter the original | Source files untouched; `source_ts` retained; quarantined rows kept |
| G-05 | Blueprint ("do not require command-line operation") and normal Python test practice | Testing tools usually need the command line | `unittest` plus an IDLE runner (TC-13) |
| G-06 | Blueprint ("keep the catalogue small") and the eleven catalogue tables | Size versus required capability | Each table maps to a required question (02 §5.2); a smaller three-table alternative is documented as insufficient for provenance and completeness |
| G-07 | Owner's file-naming preference (dd_mmm_yy_hhmmss suffix) and database files | Canonical data files need stable names | Suffix applied to reports, logs, backups and run outputs; canonical data files keep fixed names because they are database storage, not outputs |
| G-08 | Assignment ("data should be inspected before schemas are fixed") and the sample-only evidence | Schemas designed from samples | Schemas are deliberately minimal (OHLCV plus provenance); V-04 gate before the full-universe load |
| G-09 | Earlier Q-MAP work by the owner on MA Affinity and the instruction not to rely on old repositories | Temptation to reuse earlier code | Any MA Affinity scanner must be re-specified and approved in this project; no code is copied (04 §9) |
| E-10 | 02 v1.1 §6.2 (candidate REGULAR only on weekdays) and the expected count of 385 regular NIFTY days | The count included two full weekend Budget sessions (01-Feb-25, 01-Feb-26) that the rule does not cover | **Resolved (v1.2):** weekend sessions are unrecognised until confirmed, as A3 requires for special sessions; counts become 383 / 67 / 3 (02 v1.2 §6.3) |
| E-11 | 10 v1.2 §B2 (`latest_n` through `context.fetch`) and 03 v1.1 `DataRequirement` (no `latest_n`) | The scanner could not express its look-back through the only permitted data route | **Resolved (v1.2):** TC-27 |
| E-12 | TC-10 and TC-23 / 03 §B7 | TC-10 said daily volume includes auction volume | **Resolved (v1.2):** TC-10 corrected |
| E-13 | Proposed G-03 rule and close-only scanners | Open-only anomalies (CONCOR 26/27-May-04, 15-May-06; INFY 24-Oct-03) block close-based EMA windows although the closes are normal | **Resolved by Owner decision G-03 (11-Nov-26):** every ±15% move blocks until the Owner verifies it. The close/open distinction is kept only as unapproved proposal P-01 (document 12), not as design. |

---

## F. Feature register

**Priority:** P1 = initial useful version; P2 = later; P3 = future idea.
**Status:** Approved requirement, Proposed, Requires Owner decision, Deferred.

| ID | Feature | Problem it solves | Needed now? | Complexity | Simpler alternative? | If postponed | How tested | Priority | Status |
|---|---|---|---|---|---|---|---|---|---|
| F-01 | Data root and canonical Parquet storage | A consistent, reusable store | Yes | Moderate | Using source files directly (mixed formats, no provenance) | No database | T-CAT, ACC-02 | P1 | Approved (Parquet) / Proposed (layout) |
| F-02 | Catalogue (DuckDB file, 11 tables) | Discovery, status, provenance | Yes | Moderate | 3 tables (insufficient) | No discovery or status | T-CAT-01..04 | P1 | Proposed |
| F-03 | Readers R1–R4 | Different source formats | Yes | Moderate | One format only (would reject inspected sources) | Cannot load data | T-FILE-01..05 | P1 | Proposed |
| F-04 | Standardisation (IST, record types, auction stamp, `source_ts`) | Consistent sessions and auctions | Yes | Moderate | — (decisions D-04..D-10) | CAS days mis-handled | T-SES-01..09 | P1 | Approved (D-04..D-10) / Proposed (method) |
| F-05 | Validation and quarantine | No silent bad data | Yes | Moderate | Report-only (bad rows used) | Fabricated or invalid data in use | T-DQ (incl. 02a/02b), T-DUP | P1 | Approved (principle); OD-05 confirmed; verification standard G-04 **approved** 11-Nov-26 |
| F-06 | Session-pattern detection and confirmation | CAS auto-detection (D-06) | Yes | Moderate | Fixed date list (rejected by owner) | Wrong session boundaries | T-SES-06 | P1 | Approved (D-06) |
| F-07 | Market calendar (derived plus optional official file) | Holidays vs missing data | Yes | Low | Derived only (unverifiable) | Holidays reported as gaps | T-MISS-02 | P1 | Proposed |
| F-08 | Issue register | Known problems tracked and visible | Yes | Low | Log text only (not queryable) | Issues forgotten | ACC-06 | P1 | Proposed |
| F-09 | Initial preparation workflow | First load | Yes | Moderate | — | No data | E2E-01 | P1 | Approved (blueprint) |
| F-10 | Incremental maintenance (fingerprint, append) | Routine updates without rebuild | Yes | Moderate | Full rebuild each time (forbidden) | Manual rebuilds | T-MNT-01/02 | P1 | Approved (blueprint) |
| F-11 | Revision detection, evidence and owner review | Revised or back-adjusted history | Yes | Moderate | — (holding is already the simplest safe option) | Silent divergence from source | T-MNT-03 to 05, 03b to 03d | P1 | Approved (OD-04 confirmed: hold all) / Proposed (method) |
| F-12 | Generation-based instrument commit, retention, pre-run backups, restore validation | Recovery from failures; no mixed old and new files | Yes (before routine maintenance) | Moderate | Per-file replacement (not atomic across files) | Data loss or mixed-state risk | T-MNT-06a to 06c, T-MNT-10, T-BKP-01 | P1 | Approved (blueprint) / Proposed (method) |
| F-23 | `instrument_rule` table (effective-dated tick and session rules, with verification status) | Instrument-specific, verified rules (review A3, A6) | Yes | Low | Hard-coded global rules (not instrument-specific or effective-dated) | Off-tick and special-session handling would rely on unverified assumptions | T-DQ-02a/02b, T-SES-04b | P1 | Proposed |
| F-13 | Logs and Excel validation report | Visible results of maintenance | Yes | Low | Console only (not beginner-friendly) | Problems unseen | E2E-01 | P1 | Proposed |
| F-14 | Data Manager GUI (Tkinter) | Non-CLI operation | Yes | Moderate | Script editing (not beginner-friendly) | Needs developer help | E2E-01 manual | P1 | Proposed |
| F-15 | Net-volume extras store | Keep optional net volume | No | Low | Ignore (current) | None for current scanners | — | P2 | Deferred (OD-08 confirmed) |
| F-16 | One-click "undo last run" | Faster recovery | No | Moderate | Documented manual restore | Manual steps needed | — | P2 | Deferred |
| F-17 | Persisted derived-timeframe cache | Speed, if needed | No (benchmark) | Moderate | On demand (TC-11) | None unless slow | — | P2 | Deferred |
| F-18 | One-click full backup (zip) | Convenience | No | Low | Manual folder copy | Manual copy | — | P2 | Deferred |
| F-19 | Official closing-auction comparison | Verify close (V-05) | No | Low | Manual spot checks | Unverified close | — | P2 | Deferred |
| F-20 | Data-access interface `QMapData` | Stable seam between components | Yes | Moderate | Direct file access (forbidden) | Engine cannot be built | T-DA-01..10 | P1 | Approved (blueprint) / Proposed (spec) |
| F-21 | On-demand aggregation | Higher timeframes for scanners | Yes (those needed) | Moderate | Precomputed files | Scanners limited to stored timeframes | T-AGG, ACC-01 | P1 | Approved (blueprint) / Proposed (rules) |
| F-22 | Completeness and forming flags | Never mistake incomplete for complete | Yes | Low | Silent partial bars (forbidden) | Misleading bars | T-AGG-02, 05 | P1 | Approved (blueprint) |
| F-30 | Scanner contract and result validation | Uniform, verifiable results | Yes | Low | Free-form outputs (not combinable) | Scoring impossible | T-SCI | P1 | Proposed |
| F-31 | Run coordinator | Executes analyses | Yes | Moderate | Each scanner run by hand | No unified run | T-SCI-06..08 | P1 | Proposed |
| F-32 | Explicit scanner registry | Know available scanners | Yes | Low | — | — | T-SCI-01 | P1 | Proposed |
| F-33 | Scanners 1–3 | Analytical value | Yes | Moderate–High each | — | No analysis | T-SCC per scanner | P1 | OD-01 and OD-09 confirmed; EMA methodology D-EMA-01 to 10 **approved**; stale-data rule D-EMA-11 open; scanners 2–3 not selected (G-11) |
| F-34 | Weighted combined score | Combine scanners | Yes (after scanners) | Moderate | Show individual scores only | No combined view | T-SCO, T-MSR | P1 | Approved (blueprint); OD-02 and OD-03 confirmed; profile composition and weights pending (G-10) |
| F-35 | Run JSON with integrity hash | Machine-readable, AI-ready, reproducible | Yes | Low | Excel only (not machine-friendly) | AI and reproducibility harder | T-OUT-01/02 | P1 | Proposed |
| F-36 | Excel run report | Readable results | Yes | Low | JSON only (not beginner-friendly) | Hard to inspect | T-OUT-03 | P1 | Proposed |
| F-37 | Analysis Runner GUI | Non-CLI analysis | Yes | Moderate | Edit-and-run scripts | Needs developer help | E2E-03 | P1 | Proposed |
| F-38 | Interpretation file and hash verifier | Optional commentary kept separate | No | Low | Paste the JSON into an AI chat manually (already possible) | None | — | P2 | Deferred |
| F-39 | Direct AI integration | Automated explanation | No | High | Manual paste | None | — | P3 | Deferred |
| F-40 | `unittest` suite and IDLE runner | Repeatable checks | Yes | Low | Manual checks only | Regressions unnoticed | Itself | P1 | Proposed |
| F-41 | Real-data acceptance tests with answer keys | Proof on actual data | Yes | Low | Fixture-only tests (insufficient per blueprint) | Unproven milestones | ACC-01..08 | P1 | Proposed |

---

## G. Future Enhancements and Ideas Register

Recording an idea here does **not** authorise its implementation (Approved — blueprint). Each idea's "trigger" is the evidence that would justify reconsidering it.

| ID | Idea | Why deferred | Trigger to reconsider | Priority | Complexity |
|---|---|---|---|---|---|
| FI-01 | Cloud replica and local-to-cloud synchronisation | Storage, security, sync, recovery and cost decisions; local first | Local system proven useful; a need for multi-device access | P3 | High |
| FI-02 | Remote query API for other Python apps | Needs a service, authentication, operations | A second machine or user must query the data | P3 | High |
| FI-03 | Direct Claude/ChatGPT integration (F-39) | Optional; structured output suffices | Manual interpretation becomes a repeated bottleneck | P3 | High |
| FI-04 | Sophisticated multi-scanner decision engine | Weighted sum is the approved scope | Weighted scores proven insufficient with evidence | P3 | High |
| FI-05 | Adaptive or regime-dependent weights | Requires validation and governance | Evidence that fixed weights fail systematically | P3 | High |
| FI-06 | Advanced dashboard, alerts, automation | First establish reliable calculations | Stable outputs and a defined monitoring need | P3 | Moderate–High |
| FI-07 | Additional asset classes, markets, data sources | Start with the identified datasets | Specific use case plus verified source | P3 | Moderate |
| FI-08 | Advanced catalogue governance and data lineage | Not justified for single-user local use | Multiple users or regulated use | P3 | Moderate |
| FI-09 | Large scanner library | Add scanners only for defined use cases | Approved specification per scanner | P2/P3 | Per scanner |
| FI-10 | Persisted timeframe cache (F-17) | Benchmark shows no need | Measured retrieval > 5 s per instrument | P2 | Moderate |
| FI-11 | Net-volume extras (F-15) | No current need | A scanner requires net volume | P2 | Low |
| FI-12 | Undo-last-run and full-backup buttons (F-16, F-18) | Manual procedures suffice | Frequent recovery need | P2 | Low–Moderate |
| FI-13 | Official close comparison (F-19) | Needs an official data file | Official file becomes available | P2 | Low |
| FI-14 | Frozen reference-percentile calibration | Fixed anchors suffice first | Fixed anchors prove poorly comparable | P2 | Moderate |
| FI-15 | Consolidated yearly stock files | Not measured as necessary | Universe-wide query measured as slow | P2 | Low |
| FI-16 | Intraday stock data (1-minute for equities) | No source inspected yet | Source supplied and inspected | P2 | Moderate |
| FI-17 | Automatic application of corporate-action revisions | A uniform factor is not proof (review A2) | An independently verified corporate-action reference source is approved, and the factor and effective date match it | P2 | Moderate |

*End of document 07, v1.6.*
