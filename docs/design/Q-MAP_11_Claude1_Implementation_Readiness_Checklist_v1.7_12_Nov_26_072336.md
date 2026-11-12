# Q-MAP — Claude 1 Implementation-Readiness Checklist

**Supplementary document 11 | Version 1.7 | 12-Nov-26 | Status: Proposed — v1.7 records the INFY source verification (all EMA reference values now source-verified) and the seven newly identified INFY G-03 cases (v1.10 package); for ChatGPT final review and Project Owner approval**

> This checklist does not approve coding. Each milestone starts only when its own start conditions are met **and** the Project Owner has approved the package.

| Field | Value |
|---|---|
| Responds to | Additional Groundwork Assignment, Task 3 |
| Translates | 02 v1.6, 03 v1.2, 04 v1.3, 05 v1.1, 06 v1.5, 07 v1.6, 08 v1.7, supplements 09 v1.6, 10 v1.7 and 13 v1.2, the **Owner Decision Records** (§1.1–§1.3) and the open items of document 12 v1.5 into per-milestone checklists |
| Adds | **No new architecture, technology or feature.** Genuine gaps are listed in section 4, not filled. |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed sections | Reason |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | §1 → new §1.1 Owner Decision Record and §1.2 Confirmed information | OD-01 to OD-09 confirmed (G-12 closed); I-01 (Python 3.12.10) and I-02 (GUI conventions) confirmed (G-13 closed) |
| 1.1 | §2, Gate 0, M1a, M3, M6 | Readiness and blockers updated for the confirmations |
| 1.1 | §4 G-02, G-04, G-09, G-12, G-13, G-16 | Clarified or closed as instructed by the review; decision-maker and milestone retained |
| 1.1 | §4 G-01 | Script status: awaiting Owner authorisation |
| 1.2 | §2 | Readiness re-assessed; recommended build order M1a → M2 → M1b (OD-10) shown; start conditions now name the exact open decisions |
| 1.2 | §3 | References updated; M1a counts corrected for weekend sessions (02 v1.2 §6.3); new tests added; M3 includes D-EMA-11 and T-EMA-17/18; M5 reflects confirmed OD-03 (reject only) |
| 1.2 | §4 | Reviewer checks **completed and closed**: G-02, G-09, G-15. G-03, G-04, G-16 reviewed; recommendations refined; Owner decision still required (document 12). G-01 procedure fully designed (09 v1.2 §8); script still unauthorised. New gaps G-17 to G-21 recorded with their resolution. |
| 1.2 | §5 | Must-not list extended |
| 1.2 | new §6 | Evidence status and the original delivery plan |
| 1.3 | new §1.3 | Written record of the Owner decisions of 11-Nov-26: G-03, G-04, G-16, D-EMA-01 to 10, pilot method; G-01 not authorised |
| 1.3 | §2, §3 | Readiness re-assessed: G-03/G-04/G-16 no longer start conditions; baseline order M1a → M1b → M2 (OD-10 only a proposal); M3 needs D-EMA-11 and independent reproduction of the EMA reference values; G-16 consequences for CONCOR; new tests |
| 1.3 | §4, §5, §6 | Gap statuses updated; G-23 (resolution test) and G-24 (proposal P-01) added; must-not list and evidence status updated |
| 1.4 | §2, M1c checklist, §4 G-01 | **Targeted correction:** V-04 is not a Gate 0, M1a, M1b or M2 condition; it is mandatory for M1c only and blocked until G-01 is authorised; the four M1c prerequisites stated; M1c follows M2 in the baseline sequence. No other change. |
| 1.4 (Owner) | M1b risk/blocker row | **Corrected by the Project Owner (11-Nov-26):** G-03 recorded as decided and as an implementation requirement, not a start condition. Retained unchanged in v1.5. |
| 1.5 | §2 (order sentence, M3 row), M3 checklist, §4 (G-25, G-26), §6 | Sequence stated as approved: M1a → M1b → M2 → M1c → M3; M3 conditions add the EMA source verification (document 13), proposal D-EMA-12 (numeric precision, found in the final verification) and OD-12 (M3 while M1c is blocked). No other change. |
| 1.6 | §2 M3 row; M3 checklist; §4 G-27; §6 | CONCOR reference values source-verified (document 13 v1.1); **INFY source verification still a prerequisite before M3**; three newly identified CONCOR G-03 cases recorded. The Owner's M1b G-03 row is unchanged. |
| 1.7 | §2 M3 row; M3 checklist; §4 G-28; §6 | INFY reference values source-verified (document 13 v1.2): source verification is no longer an M3 condition; seven newly identified INFY G-03 cases recorded. The Owner's M1b G-03 row is unchanged. |

---

## 1. How to use this checklist

Each milestone has the same seven headings the assignment requires. A milestone may start only when its **Start conditions** are all ticked. It is complete only when every **Evidence** item exists and the Project Owner has accepted it (08 v1.2 §11).

### 1.1 Owner Decision Record (confirmed)

OD-01 to OD-09 have been **confirmed by the Project Owner**, as communicated in ChatGPT's consolidated review of 11-Nov-26. This table is the written decision record referred to in gap G-12. Where the Owner's own wording was supplied (OD-02, OD-03, OD-07, OD-09), it is reproduced as given. The other positions are those confirmed in the earlier review (its section C) and recorded in register 07 v1.1. **These decisions are not reopened here.**

| ID | Confirmed decision | Source of wording |
|---|---|---|
| OD-01 | EMA Analysis on daily stocks is the **first scanner candidate**, subject to data suitability. Its formulas and parameters are **not** approved (see document 10). | Review section C; 07 v1.1 |
| OD-02 | **Combined Technical Setup Strength** measures how strongly a stock satisfies the technical conditions measured by the selected scanners. | Owner wording |
| OD-03 | **Reject the combined score if a required scanner result is missing or invalid.** | Owner wording |
| OD-04 | Hold all historical revisions for Owner review; preserve existing data, previous versions and revision evidence; automatic corporate-action handling deferred | Review section C; 07 v1.1 |
| OD-05 | The tick-size rule must be verified before automatic off-tick quarantine; constant-step detection is warning-only | Review section C; 07 v1.1 |
| OD-06 | Pilot of about 50 stocks only after the full-universe inspection has identified schema variations | Review section C; 07 v1.1 |
| OD-07 | **Use available history, disclose actual coverage and report calculations as unavailable when history is insufficient.** | Owner wording |
| OD-08 | Net-volume extras deferred until a concrete requirement arises | Review section C; 07 v1.1 |
| OD-09 | **Fixed, documented, deterministic scoring rules. Exact scanner parameters still require approval.** | Owner wording |

**Note on OD-07.** Register 07 v1.1 framed OD-07 narrowly, as daily index history before the 1-minute master begins. The confirmed decision is broader and governs every calculation. Where 07 v1.1 differs, **this record prevails**. *(v1.2: document 07 has since been updated to v1.2 and now shows the confirmed wording of OD-02, OD-03, OD-07 and OD-09 in its §A; this record remains the authority.)*

### 1.2 Confirmed information (formerly open items)

| ID | Confirmed | Effect |
|---|---|---|
| I-01 | **Python 3.12.10** on the Owner's Windows PC | Package versions are pinned for Python 3.12 at Gate 0 |
| I-02 | GUI conventions: **file picker, folder picker, Save As, progress messages, error messages, and a simple, consistent interface** | These are the required conventions for both applications. The more detailed conventions listed as proposals in 04 v1.1 and 08 v1.1 (scrollable outer frame, ETA counters, a specific shutdown sequence) are **not** part of this confirmation and are not required. Running long work outside the window's main thread remains a technical necessity, so that progress messages can update. |

---

### 1.3 Owner decisions recorded 11-Nov-26 (closure instruction)

Source: the Project Owner's *Final Consolidated Closure Instruction*, 11-Nov-26. These decisions are final and are not reopened.

| ID | Decision (as given by the Owner) | Where implemented |
|---|---|---|
| **G-03** | Price movements beyond ±15% are blocking by default until the Owner personally verifies each occurrence and marks it `VERIFIED_OK`. | 02 v1.3 §5.2, §7.1 V-PX-05; 04 SC-07; 06 T-DQ-07/08; 10 v1.4 |
| **G-04** | Tick-size rules require supporting evidence and effective dates. Until verified, off-tick observations are flagged, not automatically quarantined. | 02 v1.3 §5.2 `instrument_rule`, §7.1 V-PX-03; 06 T-DQ-02a/b/c |
| **G-16** | Only exact SHA-256 matches qualify as duplicates. Differing files must be referred to the Owner. No automatic merging or selection. | 02 v1.3 §9.6; 06 T-MNT-11, 11b, 12; 09 v1.3 |
| **D-EMA-01 to D-EMA-10** | EMA v1.2 methodology approved, subject to G-03. The actual combined-score weight is deferred until the scoring profile is finalised. | 10 v1.4 |
| **Pilot** | The stratified 30 + 10 + 10 selection methodology is approved. CONCOR and INFY must be included within approximately 50 stocks. The actual list remains pending the full-universe inventory. | 09 v1.3 §6 |
| **G-01** | The exploratory stock-universe inventory script is **not** authorised. It must not be created without the Owner's explicit further approval. | 09 v1.3 §8.1 |

## 2. Readiness summary (re-assessed in v1.3)

"Ready" means **ready to start once its start conditions are met** — never "approved". Every milestone also needs the Owner's approval of this package (Gate 0). **Approved implementation sequence: M1a → M1b → M2 → M1c → M3**, then M4 → M5, with M6 after M3. Gate 0 allows M1a, M1b and M2 on the inspected sample files. M1c has its own prerequisites (G-01 authorisation, completed and reviewed inventory, presented and Owner-approved pilot list). M3 follows M1c in this sequence; whether M3 may start on CONCOR and INFY while M1c is still blocked is open Owner decision **OD-12** (document 12) — until the Owner decides, M3 waits for M1c. The alternative order of proposal OD-10 is **not adopted**. **V-04 (the full stock-universe inventory) is not a condition of Gate 0, M1a, M1b or M2**: these proceed on the already inspected sample files.

| Milestone | Readiness | Start conditions still open | Depends on the stock-universe inventory? | Who acts |
|---|---|---|---|---|
| Gate 0 | **Open** | ChatGPT's final review; Owner approval of package v1.10; exact package pins for Python 3.12.10 (G-15) | No | ChatGPT, Owner; Claude 1 (pins) |
| M1a Database foundation on inspected files | **Ready after Gate 0** | None besides Gate 0 (G-04, G-16 decided) | No | — |
| M1b Maintenance, revisions, generations, backup | **Ready after M1a** | None (G-03 decided) | No | — |
| M2 Data access and aggregation | **Ready after M1b** (baseline). After M1a only if the Owner approves proposal OD-10. | None in the baseline order | No | Owner (only for OD-10) |
| M1c Pilot universe load | **Blocked** | (1) G-01 explicitly authorised (not given); (2) V-04 inventory completed and results reviewed; (3) proposed pilot list presented to the Owner; (4) Owner approval of the actual list. Method already approved. M2 complete. | **Yes** (V-04) | Owner; Claude 2 (script, list proposal); Owner |
| M3 First scanner (EMA) and engine core | **Blocked** | M2 complete; M1c complete per the approved sequence (or OD-12 decided in favour of starting earlier); D-EMA-11 and D-EMA-12 decided. (All T-EMA reference values are now source-verified — document 13 v1.2.) | No (runs on CONCOR and INFY) | Owner (OD-12, D-EMA-11, D-EMA-12) |
| M4 Further scanners | **Blocked** | Second and third scanners selected (G-11) and each specification approved | Not for selection; the pilot is needed for realistic acceptance | Owner |
| M5 Combined scoring | **Blocked** | Two approved scoring scanners (M3, M4); profile composition and weights, including the EMA weight (G-10) | No | Owner |
| M6 Practical output | **Ready after M3** (combined sections after M5) | None | No | — |

**What must be demonstrated on actual historical data:** M1a (import of the inspected NIFTY, BANKNIFTY, CONCOR, INFY and NIFTYIT files with the expected counts), M1b (update, held revision, restore on copies of those files), M2 (ACC-01 against the Owner's derived files; ACC-10 on the Owner's PC), M3 (CONCOR and INFY results matching the independently reproduced values), M1c (the pilot stocks).

## 3. Milestone checklists

### Gate 0 — before any code

| Heading | Content |
|---|---|
| Objective and scope | Confirm the environment and approvals so that M1 starts on firm ground |
| Required components and dependencies | Approved package (index 00 v1.10, after ChatGPT's final review); Owner Decision Record (§1.1, confirmed); I-01 = Python 3.12.10; I-02 conventions confirmed (§1.2) |
| Expected runnable output | `requirements.txt` with versions pinned for **Python 3.12.10**; a one-line IDLE check printing the Python and package versions on the owner's PC |
| Acceptance criteria | Exact pins (`==`) installed on the owner's PC and recorded; code targets the pinned versions only, and test runs on other versions are not evidence (G-15, closed; T-ENV-01) |
| Essential tests and expected results | **T-ENV-01**: `import duckdb, pandas, pyarrow, openpyxl, tkinter` succeeds in IDLE; printed versions equal `requirements.txt` |
| Evidence | Screenshot or text of the version printout; the approved `requirements.txt` |
| Risks, blockers, open matters | None beyond package approval. Note: a later DuckDB upgrade may convert the catalogue file so that the old version cannot read it; upgrades need a catalogue backup and a full re-test (08 v1.2 §6). |

### M1a — Local database foundation on the inspected files

| Heading | Content |
|---|---|
| Objective and scope | Import the inspected files into canonical Parquet generations with an 11-table catalogue: NIFTY and BANKNIFTY 1-minute samples, CONCOR, INFY, NIFTYIT. Includes validation, quarantine, session classification with confirmation lists, the derived (provisional) calendar, the issue register, an Excel validation report and a minimal Data Manager GUI. |
| Required components | `settings.py`, `errors.py`, `catalogue.py`, `readers.py` (R1–R4), `session_rules.py`, `standardise.py`, `validation.py`, `storage.py` (generation commit), `maintenance.py` (initial load), `apps/QMAP_Data_Manager.py`; tests L1–L3 |
| Dependencies | Gate 0. Specifications: 02 v1.3 §2–§8, §9.4, §9.6, §11. Test catalogue 06 v1.3 §5.1–5.6, §11.4. |
| Expected runnable output | The Owner opens the Data Manager in IDLE, picks a data root and the source files, runs **Initial load**, watches progress, opens the validation report, and sees the confirmation lists (67 NIFTY CAS candidates; 59 BANKNIFTY CAS candidates; **4 unrecognised days**: NIFTY 21-Oct-25, 01-Feb-25, 01-Feb-26; BANKNIFTY 08-Nov-26). If both CONCOR files are selected, **both are reported as `SOURCE_CONFLICT`** (different SHA-256) and CONCOR is imported only after the Owner chooses one (G-16). The ±15% issues appear blocking, awaiting the Owner's verification (G-03). |
| Acceptance criteria | Counts and statuses exactly as listed below; no file modified at source; every stored row traceable to a source fingerprint |
| Essential tests and expected results | **T-SES-06 (corrected v1.2):** NIFTY 383 CANDIDATE REGULAR, 67 CANDIDATE CAS, 3 UNRECOGNISED; BANKNIFTY 59 CANDIDATE CAS, 1 UNRECOGNISED. **T-SES-09 (before confirmation):** NIFTY 168,556 CANDLE (811 flagged `SESSION_UNCONFIRMED`) + 67 CLOSING_AUCTION; BANKNIFTY 21,295 + 42 AUCTION_PHASE + 59 CLOSING_AUCTION. **T-SES-11:** weekend session unrecognised until confirmed. **T-FILE-06:** a 3-minute file is not accepted as 1-minute data. **T-FILE-07:** a 1-minute file with missing minutes is accepted. **T-MNT-11:** CONCOR `.txt` + Parquet → `SOURCE_CONFLICT`, nothing imported until the Owner chooses; **T-MNT-11b:** byte-identical copy → `DUPLICATE_SOURCE`. **T-DQ-07:** every ±15% issue `affects_continuity = true`. **T-DQ-02c:** a tick rule without evidence and dates stays unverified. **T-SES-03:** BANKNIFTY 18-Aug-26 closing auction `ts` 15:30, `source_ts` 15:29. **T-SES-10:** truncated day → UNRECOGNISED, not SPECIAL. **T-MISS-01:** BANKNIFTY 19-Aug-26 missing 13:28–13:29 only. **T-DQ-01:** NIFTYIT 01-Jul-05 quarantined. **T-DQ-02b:** off-tick row flagged, not quarantined (no verified tick rule). **ACC-02:** CONCOR 6,860; INFY 7,169; NIFTYIT 5,760 + 1 quarantined. **ACC-05:** CONCOR text and Parquet, each imported into its own fresh data root, give identical canonical data. **T-CAT-03:** provenance hashes match. |
| Evidence | Test summary from `run_all_tests.py`; validation report (Excel); catalogue coverage printout; the owner's E2E-01 confirmation; screenshot of the confirmation lists |
| Risks, blockers, open matters | **Start condition:** Gate 0 only (G-04 and G-16 decided 11-Nov-26). G-02 revised in v1.3: a calendar file is official only after the Owner records its source (T-CAL-01 to 04 apply only if a file is supplied). The corrected session counts were **calculated** from Deliverable 1, **not re-run** on the files; M1a recomputes them and any difference goes to the Owner with evidence. |

### M1b — Incremental maintenance, held revisions, generations and backup

| Heading | Content |
|---|---|
| Objective and scope | Safe routine updates: fingerprint change detection; appends via new generations; **every** historical revision held with evidence; owner approve or reject; re-validation after confirmations; start-up recovery; retention; catalogue backups; restore check |
| Required components | `maintenance.py` (update, held revisions, approve/reject, revalidate), `storage.py` (recovery, retention, integrity), Data Manager screens for **Update**, **Held revisions**, **Confirm sessions** and **Check integrity** |
| Dependencies | M1a. Specification 02 v1.3 §9–§10, including §9.6 (G-09, G-16). OD-04 (hold all) and G-03 (blocking until verified) — both decided. |
| Expected runnable output | The owner adds one new day to a CONCOR copy and runs **Update** → `APPEND`. The owner edits a historical close in an INFY copy → the revision appears under **Held revisions** with evidence and Approve/Reject buttons. The owner confirms the 21-Oct-25 special session → re-validation produces the confirmed counts. |
| Acceptance criteria | No historical change is ever applied without approval; no reader ever sees a mixed generation; restore yields a consistent database |
| Essential tests and expected results | **T-MNT-12 to 14:** conflicting sources not imported; a moved file not imported twice; a held revision also holds its new rows and the data-access interface reports `HELD_REVISION_EXISTS` and `RANGE_TRUNCATED_END`. **T-MNT-02:** new generation with 6,861 rows; previous generation intact. **T-MNT-03:** ×0.8 revision held; active data unchanged. **T-MNT-03b:** ×10 error held as a "candidate", not applied. **T-MNT-03c/03d:** approve → new generation; reject → unchanged. **T-MNT-06a/06b/06c:** interruptions leave one complete generation readable. **T-BKP-01:** restored catalogue and generations consistent; reads equal pre-update values. **T-SES-04b / T-SES-05b / T-SES-11, after confirming the four special sessions:** NIFTY 168,555 + 68; BANKNIFTY 21,293 + 43 + 60. |
| Evidence | Test summary; log excerpts of a held revision and its approval; failure-injection test output; restore test output; the owner's E2E-02 confirmation |
| Risks, blockers, open matters | **G-03** was approved by the Project Owner on 11-Nov-26. Every price movement beyond ±15% remains blocking until the Owner verifies the individual occurrence and marks it `VERIFIED_OK`. This is an implementation requirement, not an outstanding condition for starting M1b. Failure-injection and restore tests are specified only; they become evidence only when run on the implementation. Windows may refuse a folder rename while another program (e.g. antivirus or a file viewer) holds a file open: the rename step must fail cleanly, leave the previous generation active and tell the user to close the program and retry (02 v1.2 §9.4 recovery). Storage overhead of retained generations (02 §13). |

### M1c — Pilot universe load (~50 stocks)

| Heading | Content |
|---|---|
| Objective and scope | Load the approved pilot list with the M1a/M1b machinery; no new features |
| Required components | None new |
| Dependencies | **M1c may not begin until all of the following hold:** (1) the Project Owner has **explicitly authorised G-01** (the exploratory universe-inventory script; currently **not authorised**); (2) the inventory (V-04) has been **completed** and its results **reviewed**; (3) the proposed pilot list (about 50 stocks, CONCOR and INFY included, chosen by the approved method) has been **presented to the Project Owner**; (4) the Project Owner has **approved that actual list**. V-04 cannot be performed before G-01 is authorised. M1a, M1b and M2 are also complete (baseline sequence M1a → M1b → M2, then M1c). Pilot **method** approved 11-Nov-26; the script, once authorised, follows 09 v1.4 §8. |
| Expected runnable output | Initial load of the pilot; validation report listing every issue per stock; edge-case stocks (group C) behaving as designed |
| Acceptance criteria | Every pilot file either imported or rejected with a stated reason; edge cases produce their expected statuses (e.g. a short-history stock is stored correctly and later yields `INSUFFICIENT_DATA` in M3) |
| Essential tests and expected results | Per pilot stock: row count equals the inventory count minus documented quarantines; for every group C stock, its intended edge behaviour is observed |
| Evidence | Pilot list with reasons; validation report; owner sign-off |
| Risks, blockers, open matters | **Blocked by G-01** (script not authorised). The pre-2023 calendar disagreements (doc 09 §2.6) will create many provisional `MISSING_DAY` warnings; these are expected and must not be "fixed". The number of ±15% occurrences needing the Owner's verification is unknown until the inventory (09 §8.3 U-07). |

### M2 — Common data-access interface and aggregation

| Heading | Content |
|---|---|
| Objective and scope | The read-only `QMapData` interface (10 functions) and on-demand aggregation, as in 03 v1.2 (interface version 1.1) |
| Required components | `access.py`, `aggregation.py`; tests L4–L5 |
| Dependencies | M1b in the baseline order (M1a only, if the Owner approves proposal OD-10; then the held-revision tests T-DA-13 and T-MNT-14 run once M1b exists). Interface version 1.1 (03 v1.2: `DataRequirement.latest_n`). |
| Expected runnable output | An IDLE example script printing: `list_instruments()`; NIFTY 5-minute bars for 17-Aug-26; the incomplete BANKNIFTY 13:25 bar of 19-Aug-26; the latest 5 CONCOR closes; a plain-English error for `get_bars("CONCOR","15m")` |
| Acceptance criteria | **ACC-01:** zero O/H/L/C differences against the owner's derived 3m/5m/15m/daily/monthly files (09-Jan-25 to 30-Oct-26). **ACC-10:** measured performance on the owner's PC; under 5 s per instrument keeps on-demand aggregation. Every response carries `completeness_basis`. |
| Essential tests and expected results | **T-AGG-01:** 09-Jan-25 09:15 5-minute bar 23,674.75 / 23,689.50 / 23,607.75 / 23,618.20. **T-AGG-01b:** volume 9,824,234. **T-AGG-02:** BANKNIFTY 13:25 bar 3 of 5 minutes, volume 291,326, incomplete. **T-AGG-03:** NIFTY 17-Aug-26 15:00 bar plus a separate 15:30 auction 24,287.65. **T-AGG-07:** NIFTY daily 17-Aug-26 C 24,287.65, V 218,297,189. **T-AGG-13:** BANKNIFTY daily volume 18-Aug-26 = 123,512,346 (auction volumes excluded). **T-DA-07:** CONCOR closes 417.85, 419.15, 425.10, 440.85, 439.80. **T-DA-11 to 13:** provisional basis, unrecognised-session and held-revision warnings. **T-DA-14, 15:** `latest_n` through a requirement; `RANGE_TRUNCATED_END` only for real staleness. |
| Evidence | Test summary; the example script output; the manual verification record for T-AGG-01, 02, 03, 07 and 13; the ACC-01 comparison report; the ACC-10 timing record |
| Risks, blockers, open matters | ACC-10 might exceed the threshold on the owner's PC. Then F-17 (cache) is **reviewed**, not built automatically. |

### M3 — First scanner (EMA Trend Alignment) and engine core

| Heading | Content |
|---|---|
| Objective and scope | Engine core (`contract.py`, `registry.py`, `runner.py`, JSON output) and **one** scanner, built exactly to the **approved** version of document 10; a minimal Analysis Runner |
| Required components | `qmap_engine/*` (no scoring yet), `qmap_scanners/ema_trend_alignment/`, `docs/scanners/ema_trend_alignment_spec_v1.0.md` (the approved specification), `apps/QMAP_Analysis_Runner.py` (minimal) |
| Dependencies | M2 and M1b; M1c per the approved sequence, unless the Owner decides OD-12 otherwise. EMA methodology **approved** (D-EMA-01 to 10, 11-Nov-26). Still required: (1) Owner decisions **D-EMA-11** (stale data) and **D-EMA-12** (numeric precision — document 13 §3); (2) the approved specification copied to `docs/scanners/`. The reference values for CONCOR and INFY are **source-verified** (document 13 v1.2) and are the M3 test targets. |
| Expected runnable output | The owner selects CONCOR and INFY, analysis date 06-Nov-26, runs, and opens the JSON |
| Acceptance criteria | Results match the independently produced Excel values (doc 10 §B9.2) to 4 decimals; contract validation passes; determinism holds |
| Essential tests and expected results (approved methodology; reference values source-verified, document 13 v1.2) | **T-EMA-01:** EMA(3) 416.95 / 421.025 / 430.9375 / 435.36875. **T-EMA-02:** CONCOR 06-Nov-26 → 432.7297 / 452.6585 / 486.4492; net −4; score 16.67; BEARISH. **T-EMA-03:** INFY → net +2; 66.67; NEUTRAL. **T-EMA-04:** INFY 03-Feb-26 → 100; BULLISH. **T-EMA-06:** CONCOR 31-Dec-01 → INSUFFICIENT_DATA (690 bars). **T-EMA-08/09:** INVALID until 07-Dec-16, OK from 08-Dec-16. **T-EMA-16:** all 13 scores and states. **T-EMA-17:** stale data per D-EMA-11. **Under the approved G-03 rule**, T-EMA-02, 05, 13 and 14 return `INVALID_DATA` until the Owner verifies CONCOR 04-Jun-24 (the values listed apply afterwards); **T-EMA-18:** `INVALID_DATA` until 15-May-06 is verified. *All T-EMA tests are specified, not executed.* **T-SCI-01 to 09:** contract and runner behaviour. **T-SCC-01:** fixture SMA5 428.55, score 76.25. |
| Evidence | Approved specification; test summary; Excel verification workbook for T-EMA-02 to 05 (made independently of Q-MAP); saved golden output; the owner's run confirmation |
| Risks, blockers, open matters | Blocked until OD-12 (or M1c), D-EMA-11 and D-EMA-12 are decided. **Known implementation hazard (document 13, EMA-F1):** with ordinary floating-point arithmetic, T-EMA-10 returns net −2 instead of 0; the D-EMA-12 rule removes this. T-EMA-09 expects the 08-Dec-16 window to start on **10-Sep-13** (corrected); the T-EMA-18 values are **conditional** on the Owner verifying 15-May-06. Under the 800-bar rule, stocks with fewer than 800 bars get no EMA score and therefore no combined score (OD-03). Under G-03, CONCOR has eight blocking cases (three newly identified: 31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%)) and therefore no current EMA score until 04-Jun-24 is verified; its blocked periods are in document 13 §4. INFY has eight blocking cases (seven newly identified: 08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%)); the INFY reference dates are unaffected (document 13 §6). |

### M4 — Further approved scanner(s)

| Heading | Content |
|---|---|
| Objective and scope | Add one or two more scanners, each independently, without editing existing scanners |
| Required components | New scanner folder(s); one registry line each; their approved specifications |
| Dependencies | M3; **selection and specification approval** (G-11) |
| Expected runnable output | Each new scanner runs alongside EMA in the Analysis Runner |
| Acceptance criteria | As M3, per scanner; T-SCC-REG shows the EMA golden output unchanged |
| Essential tests and expected results | Defined by each approved specification (template 04 v1.2 §8) |
| Evidence | As M3, per scanner |
| Risks, blockers, open matters | **Blocked:** no second or third scanner has been selected or specified |

### M5 — Weighted combined scoring

| Heading | Content |
|---|---|
| Objective and scope | `scoring.py` and `config/scoring_profiles.json` per 05 v1.1: **reject** policy only (OD-03 confirmed); meaning Combined Technical Setup Strength (OD-02 confirmed) |
| Required components | `scoring.py`; profile file; combined section in the JSON |
| Dependencies | At least two approved **scoring** scanners; a profile whose composition and weights are approved under the confirmed meaning **Combined Technical Setup Strength** (OD-02); EMA inclusion per D-EMA-10 |
| Expected runnable output | A run with a profile shows each scanner's score, weight and contribution, and the combined score |
| Acceptance criteria | Hand-recomputable from the JSON; missing results never treated as zero |
| Essential tests and expected results | **T-SCO-01:** 80/70/60 at 40/35/25 → 71.50. **T-MSR-01:** a missing result → `REJECTED_MISSING_RESULT`, null. **T-SCO-02:** weights totalling 95 are rejected. **T-MSR-02 (v1.2):** a profile with `RENORMALISE` is refused. **T-MSR-05:** never 56.50. |
| Evidence | Test summary; a calculator check by the owner; JSON and Excel |
| Risks, blockers, open matters | **Blocked:** the M4 scanners and profile approval (the OD-02 meaning itself is confirmed) |

### M6 — Practical output and reporting

| Heading | Content |
|---|---|
| Objective and scope | The full Analysis Runner, the Excel run report and the integrity hash |
| Required components | `output.py` (Excel); Analysis Runner completion |
| Dependencies | M3 (and M5 for combined sections); GUI conventions as confirmed in I-02 |
| Expected runnable output | The owner runs an analysis end-to-end without help and reviews the Excel report |
| Acceptance criteria | E2E-03 and E2E-04 performed by the owner; T-OUT-01 to 04 pass |
| Essential tests and expected results | **T-OUT-02:** changing one value changes `content_sha256`. **E2E-04:** two runs give identical sections 1–4, apart from the run ID and timestamp. |
| Evidence | Owner sign-off; sample report |
| Risks, blockers, open matters | None specific (I-02 confirmed) |

---

## 4. Gaps: status after the v1.3 review

"Closed" means resolved within the approved architecture or by an Owner decision; the reviewer (ChatGPT) should confirm. Open Owner items are in document 12.

| ID | Gap | v1.3 status | Resolution | Decider | Needed before |
|---|---|---|---|---|---|
| G-01 | Full stock-universe inventory (V-04) | **Not authorised** (Owner, 11-Nov-26) | Procedure designed (09 v1.4 §8). The script must not be created without the Owner's explicit further approval. V-04 therefore cannot be performed yet. It blocks **M1c only** — not Gate 0, M1a, M1b or M2. | Owner | M1c |
| G-02 | Official calendar file | **Closed (revised v1.3)** | Import stores rows as `REFERENCE_FILE_UNCONFIRMED`; official status only after the Owner records the source (`evidence`, `confirmed_at`); a changed file loses it (02 v1.3 §5.5; T-CAL-01 to 04). Two fields added to `market_calendar` to hold the provenance — the minimum needed to meet the instruction; reviewer to confirm. | Reviewer | M1a |
| G-03 | ±15% moves and continuity | **Decided** (11-Nov-26) | Every occurrence blocks until the Owner marks it `VERIFIED_OK`. The v1.2 open-only exception is removed; it survives only as unapproved proposal P-01 (G-24). | Owner | — |
| G-04 | Verified tick rule | **Decided** (11-Nov-26) | Evidence, effective-from (effective-to where known) and confirmation required before `verified = true`; otherwise flag only | Owner | — |
| G-05 to G-08 | Screens, settings, report layout, test hook | Closed (unchanged) | 11 v1.1 positions; settings also remember the last selected update folders (offered, not automatically in scope) | Reviewer | M1a/M1b |
| G-09 | Which source files an Update examines | **Closed (revised v1.3)** | Only explicitly selected folders; inaccessible registered sources reported as `SOURCE_INACCESSIBLE`, never removed or treated as deletion; out-of-scope sources listed (02 v1.3 §9.6; T-MNT-15/16) | Reviewer | M1b |
| G-10 | First combined profile, including the EMA weight | Open | Document 12 | Owner | M5 |
| G-11 | Second and third scanners | Open | Document 12 | Owner | M4 |
| G-12, G-13 | Decision record; I-01, I-02 | Closed | §1.1, §1.2 | — | — |
| G-14 | Auction-volume semantics | Unchanged | Conservative treatment kept | — | Volume-based scanners |
| G-15 | DuckDB version | **Closed** | Exact pins; tests only on the pins (T-ENV-01); upgrade procedure (08 v1.3 §6) | Reviewer | Gate 0 |
| G-16 | Several files for one symbol | **Decided** (11-Nov-26) | Exact SHA-256 only; differing files to the Owner; nothing imported until chosen; no merge or automatic selection | Owner | — |
| G-17 | Weekend full sessions | Closed (technical clarification) | Unrecognised until confirmed (follows accepted rule A3). Counts **calculated**, not re-run. | Reviewer | M1a |
| G-18 | `latest_n` through `context.fetch` | Closed (technical clarification) | Interface 1.1, additive (03 v1.2) | Reviewer | M2 |
| G-19 | Stale data in a scanner | Open proposal **D-EMA-11** | Document 12 | Owner | M3 |
| G-20 | Exploratory scripts 01b, 01c not supplied | Owner action | Not recreated. Package reviewable without them (00 v1.10 §3.2). | Owner | Reproduction of Deliverable 1 |
| G-21 | Build order | Open proposal **OD-10**; baseline M1a → M1b → M2 applies until decided | Document 12 | Owner | After M1a |
| G-22 | Stale or contradictory text in older documents | Closed | 00 v1.10 §2.5 | Reviewer | Gate 0 |
| G-23 *(new)* | Resolution test could misjudge genuine data with gaps (ChatGPT finding 11) | **Closed (revised v1.3)** | Most common within-day step; ≥ 30 steps; coarser days flagged, not deleted (02 v1.3 §6.1; T-FILE-06 to 09) | Reviewer | M1a |
| G-24 *(new)* | Open-only ±15% moves block close-based calculations | Open proposal **P-01** (not adopted) | Document 12. Until decided, the approved G-03 rule applies; the Owner can verify individual occurrences. | Owner | Optional |
| G-25 *(new v1.5)* | Floating-point noise can break exact ties and make the stored score depend on formula order (document 13, EMA-F1, EMA-F2) | Open proposal **D-EMA-12** | Document 12. Recommended: compare values rounded to 6 decimal places; store the score rounded to 2 decimal places (as T-EMA-16 already lists). | Owner | M3 |
| G-26 *(new v1.5)* | Approved sequence places M3 after M1c, but M1c is blocked while G-01 is not authorised | Open decision **OD-12** | Document 12. Recommended: allow M3 on CONCOR and INFY once M2 is complete, without waiting for M1c. Until decided, M3 waits. | Owner | After M2 |
| G-27 *(new v1.6)* | Three CONCOR ±15% close moves not previously recorded (31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%)) | Recorded; awaiting the Owner's individual verification (G-03) | Added to the expected issues (02 §7.2, 06 ACC-06, 07 V-01, 09 §2.6–§2.7, 13 §4). Not classified, quarantined or unblocked. No EMA test window affected. | Owner (verification) | When CONCOR history in those periods is needed |
| G-28 *(new v1.7)* | Seven INFY ±15% close moves not previously recorded (08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%)) | Recorded; awaiting the Owner's individual verification (G-03) | Added to the expected issues (02 §7.2, 06 ACC-06, 07 V-01b, 09 §2.6–§2.7, 13 §6, 01 addendum). Not classified, quarantined or unblocked. No EMA test window affected. | Owner (verification) | When INFY history in those periods is needed |

---

## 5. Things Claude 1 must not do (reminder from 08 v1.3 §9)

- Do not start any milestone before the Owner approves the package (Gate 0), or before that milestone's start conditions in §2 are met. Do not create or modify any GitHub repository before then.
- Do not start M3 before D-EMA-11 is decided and the reference values are independently reproduced; do not code any parameter other than the approved methodology.
- Do not add any exception to the ±15% blocking rule; do not unblock an occurrence without the Owner's `VERIFIED_OK`.
- Do not treat anything except an exact SHA-256 match as a duplicate; do not import any file of a `SOURCE_CONFLICT` before the Owner chooses; never merge or auto-select.
- Do not scan unselected folders; do not remove registered sources or treat missing files as deletions.
- Do not make a calendar file official without the Owner's recorded provenance.
- Do not reject a 1-minute file because of missing minutes.
- Do not mark a tick rule verified without evidence, effective-from date and confirmation.
- Do not implement renormalised combined scores (OD-03), the OD-10 order or proposal P-01 without the Owner's decision.
- Do not write, extend or run any stock-universe inventory script (G-01).
- Do not treat absences caused by holidays, listing dates or suspensions as defects; do not "fix" flagged data.
- Do not add a cache, a new table or new tooling to close a gap; raise it instead.
- Do not report a test as passed unless it was executed on the implementation with pinned versions (06 v1.3 §11).

---

## 6. Evidence status and the original delivery plan

| Item | Status |
|---|---|
| Design package | v1.10 complete for final review; **not approved** |
| Q-MAP code | **None** |
| Q-MAP tests executed / passed / failed | **0 / 0 / 0** (06 v1.3 §11) |
| Failure-injection, restore, end-to-end, EMA automated tests | Specified, **not executed** |
| Independent verification of the EMA reference values | **Complete: CONCOR and INFY verified against source data** (document 13 v1.2; one date corrected; T-EMA-18 values conditional) |
| Corrected session counts (383 / 67 / 3) | **Calculated** from Deliverable 1, **not re-run** on the source files |
| Full stock-universe inventory; pilot list | **Not done** (script not authorised) |
| Package integrity (ZIP, file list, versions, sizes, SHA-256) | Checked by Claude 2 on the v1.10 ZIP; results in 00 v1.10 §5 and in the v1.10 completion report |
| Day 3 target — real historical data retrievable locally | **Not demonstrated.** Baseline route: Gate 0 → M1a → M1b → M2 (sooner via M1a → M2 if OD-10 is approved). |
| Day 5 target — first scanner result | **Not demonstrated.** Needs OD-12 (or M1c), D-EMA-11 and D-EMA-12. |
| Day 7 target — two scanners and combined scoring | **Not demonstrated.** Needs G-11 and G-10. |

*End of document 11, v1.7.*
