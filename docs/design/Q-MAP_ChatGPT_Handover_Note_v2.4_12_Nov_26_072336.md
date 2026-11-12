# Q-MAP — Final Handover Note for ChatGPT (Package v1.10)

**Version 2.4 | 12-Nov-26 | Prepared by Claude 2 | Replaces version 2.3. §00 covers the v1.10 INFY verification; §0 the v1.9 CONCOR verification; §0B the v1.8 final groundwork cycle; §0C the v1.7 correction; §1–§12 the v1.6 closure cycle. Full evidence for v1.10 is in the separate *Claude 2 v1.10 Completion Report*.**

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**

Self-contained summary for ChatGPT's final independent verification and Gate 0 recommendation. If it ever differs from a package document, the document prevails.

---

## 00. v1.10 — INFY source verification (Owner-approved, 12-Nov-26)

**Source.** The authoritative source is `INFY_daily_02Jan98-06Nov26.parquet`: 144,271 bytes, matching Deliverable 1; 7,169 rows; SHA-256 `2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01`. `INFY.txt` was compared for reference only and is identical. The earlier INFY attachment had not reached Claude 2's workspace before this file arrived.

| Result | Detail | Where |
|---|---|---|
| T-EMA-03 (06-Nov-26) | Window starts 17-Aug-23; EMA20 1,132.2614, EMA50 1,108.5365, EMA200 1,203.8765, EMA50 ten bars earlier 1,084.5193; +1 +1 −1 +1 −1 +1; net +2; 66.67 — **all exact**; no ±15% move in the window → **valid `OK`** | 13 v1.2 §3 |
| T-EMA-04 (03-Feb-26) | Window starts 16-Nov-22; 1,646.1038 / 1,617.6051 / 1,589.1800 / 1,598.2591; all +1; 100 — **all exact**; no ±15% move in the window → **valid `OK`** | 13 v1.2 §3 |
| INFY ±15% history | Eight occurrences. Seven are newly identified (close moves on 08-Aug-00, 11-Apr-01, 18-Apr-01, 10-Apr-03, 11-Jan-13, 12-Apr-13 and 22-Oct-19); 24-Oct-03 was already documented. All are G-03 blocking cases awaiting the Owner; none is classified, quarantined or unblocked. | 13 §6; 01, 02, 06, 07, 09, 10, 11, 12 |
| EMA reference verification | **Complete** for every example. Source verification is no longer an M3 condition. | 08 v1.7 Gate 3; 11 v1.7 M3 |

| Document | v1.9 | v1.10 package |
|---|---|---|
| 00 Master Index | 1.9 | **1.10** |
| 01 Data Inventory | 1.3 | **1.4** (INFY addendum) |
| 02 Database and Catalogue | 1.5 | **1.6** |
| 06 Testing | 1.4 | **1.5** |
| 07 Decision Register | 1.5 | **1.6** (new V-01b) |
| 08 Implementation Handover | 1.6 | **1.7** |
| 09 Stock Universe and Pilot | 1.5 | **1.6** |
| 10 EMA Scanner | 1.6 | **1.7** (methodology unchanged) |
| 11 Readiness Checklist | 1.6 | **1.7** |
| 12 Owner Decision Register | 1.4 | **1.5** |
| 13 EMA Verification Evidence | 1.1 | **1.2** |
| HN | 2.3 | **2.4** |

Unchanged: 01a, 03, 04, 05. No decision, rule or method changed.

## 0. v1.9 — CONCOR source verification and evidence corrections (Owner-approved, 12-Nov-26)

**Inputs.** The Owner supplied `CONCOR.txt`, the CONCOR daily Parquet and `Nifty_IT.txt`. They are identical in size and row count to the files of Deliverable 1, and their SHA-256 values are in document 13 §1. **The INFY file was not supplied.**

| Result | Detail | Where |
|---|---|---|
| CONCOR EMA reference values | T-EMA-01, 02, 05, 06, 07, 08, 09 and 18 recomputed from source; all equal to the written values to 4 dp | 13 v1.1 §3 |
| Correction | T-EMA-09: the 08-Dec-16 window starts **10-Sep-13**, not 09-Sep-13 (no 09-Sep-13 record); status unchanged | 10 v1.6 |
| T-EMA-18 | Values calculated from source and labelled **conditional**: valid only after the Owner verifies 15-May-06; the expected result remains `INVALID_DATA` | 10 v1.6; 13 §3 |
| New G-03 cases | CONCOR 31-Jan-08 (+15.83% close), 20-Mar-20 (+16.09%), 10-Aug-20 (−15.24%) — awaiting the Owner's individual verification; not classified, quarantined or unblocked. They extend CONCOR's blocked EMA periods; no test window is affected. | 13 §4; 02 §7.1–§7.2; 06 ACC-06; 07 V-01; 09 §2.6–§2.7; 01 addendum |
| Nifty IT | 28-May-04 break and invalid 01-Jul-05 record confirmed; no other ±15% move. Not used for any EMA example. | 13 §5 |
| INFY | **Still outstanding** — prerequisite before M3; cannot be closed with CONCOR or Nifty IT data | 13 §6; 11 M3 |
| Consistency defects found | 01 stated that the M0 script was included in the package (it is not) — corrected; 07 V-01 still said only 06-Sep-13 carried `affects_continuity` (pre-G-03 wording) — corrected | 01 v1.3; 07 v1.5 |

| Document | v1.8 | v1.9 package |
|---|---|---|
| 00 Master Index | 1.8 | **1.9** |
| 01 Data Inventory | 1.2 | **1.3** (header correction and addendum) |
| 02 Database and Catalogue | 1.4 | **1.5** |
| 06 Testing | 1.3 | **1.4** |
| 07 Decision Register | 1.4 | **1.5** |
| 08 Implementation Handover | 1.5 | **1.6** |
| 09 Stock Universe and Pilot | 1.4 | **1.5** |
| 10 EMA Scanner | 1.5 | **1.6** |
| 11 Readiness Checklist | 1.5 | **1.6** |
| 12 Owner Decision Register | 1.3 | **1.4** |
| 13 EMA Verification Evidence | 1.0 | **1.1** |
| HN | 2.2 | **2.3** |

Unchanged: 01a, 03, 04, 05. All Owner decisions remain as recorded; no rule, method or decision changed.

## 0B. v1.8 — final groundwork cycle (Owner's Final Completion Assignment)

| Task | Result | Where |
|---|---|---|
| A. Owner-corrected Document 11 | Installed byte-for-byte (v1.4; 34,733 bytes; SHA-256 `f7539a96e161f7155df83dc99054580d7f33be85a601d513dd38fe59a8f2d56c`). The only difference from the packaged v1.4 is the M1b G-03 row. Carried into v1.5 (below) with that row unchanged. | 11 v1.5 change log; index 00 v1.8 §2.1 |
| B. EMA verification | All example arithmetic verified (net, score, states, distances, 13 mappings, fixtures). **No value verified against source data** — the CONCOR and INFY files are not available to Claude 2. Two implementation-precision findings (EMA-F1, EMA-F2); **no incorrect expected value; methodology unchanged.** | New document 13 v1.0; 10 v1.5 notices |
| C. Consistency review | One substantive inconsistency found: 08 and 11 placed M3 directly after M2, while the approved sequence is M1a → M1b → M2 → M1c → M3. Corrected. No other contradictions found in 00–13, HN or the workbook. | 08 v1.5, 11 v1.5 |
| D. Sequence and handover | Sequence stated everywhere as approved; one-page quick reference for Claude 1 added to 08 §7 | 08 v1.5 §7; 11 v1.5 §2 |
| E. Owner decisions | Two new genuine items: **D-EMA-12** (numeric precision, before M3) and **OD-12** (may M3 start while M1c is blocked; after M2). Open-items table now states what, why, by when and the effect if undecided. | 12 v1.3 §3, §5 |
| F. Scripts 01b/01c | Still unavailable; not recreated; non-blocking | 00 v1.8 §3.2 |
| G. Integrity | Full SHA-256 (64 hex) for every indexed file; results in index §5 and in the completion report | 00 v1.8 |

| Document | v1.7 | v1.8 package |
|---|---|---|
| 00 Master Index | 1.7 | **1.8** |
| 08 Implementation Handover | 1.4 | **1.5** |
| 10 EMA Scanner | 1.4 | **1.5** (notices only; methodology unchanged) |
| 11 Readiness Checklist | 1.4 (Owner-corrected) | **1.5** |
| 12 Owner Decision Register | 1.2 | **1.3** |
| 13 EMA Reference Verification Evidence | — | **1.0** (new) |
| HN (this note) | 2.1 | **2.2** |

All other files are byte-identical to v1.7.

## 0C. v1.7 targeted correction (Owner instruction, 11-Nov-26)

**Problem.** Document 08 v1.3 listed V-04 (the full stock-universe inventory) among the Gate 0 conditions. That conflicted with the approved sequence and with G-01 being unauthorised.

**Correction (no other change):**
- **Gate 0:** V-04 is removed from its conditions.
- **Gate 0, M1a, M1b and M2:** proceed on the already inspected sample files (NIFTY and BANKNIFTY 1-minute samples, CONCOR, INFY, NIFTYIT).
- **V-04:** a mandatory prerequisite of **M1c only**. It cannot be performed until the Owner explicitly authorises G-01.
- **M1c may begin only when all four hold:**
  1. G-01 has been explicitly authorised.
  2. The inventory has been completed and its results reviewed.
  3. The proposed pilot list has been presented to the Owner.
  4. The Owner has approved that actual list.
- **Sequence preserved:** M1a → M1b → M2, followed by M1c (subject to its prerequisites).

| Document | v1.6 | v1.7 | What changed |
|---|---|---|---|
| 08 Implementation Handover | 1.3 | **1.4** | Gate 0 bullet replaced; M1 data row; new M1c subsection with the four prerequisites; §10 V-04 row; index reference |
| 11 Readiness Checklist | 1.3 | **1.4** | §2 baseline-order sentence and M1c row; M1c checklist dependencies; §4 G-01 row; references to index v1.7 |
| 09 Stock Universe and Pilot | 1.3 | **1.4** | Header; §4 (V-04 blocks M1c only; M1c prerequisites); index reference |
| 12 Owner Decision Register | 1.1 | **1.2** | GATE-0 now refers to v1.7; G-01 entry states V-04 blocks M1c only and that the actual list needs separate approval |
| 02 Database and Catalogue | 1.3 | **1.4** | §13 limitation 1 no longer implies V-04 gates ingestion before M1c |
| 07 Decision Register | 1.3 | **1.4** | V-04 row "needed before" corrected to the pilot load (M1c) |
| 00 Master Index | 1.6 | **1.7** | Versions, fingerprints, results |
| HN (this note) | 2.0 | **2.1** | This section, and the v1.7 references |

Unchanged: 01, 01a, 03, 04, 05, 06, 10. No approved decision, architecture or methodology was altered. No script or code was created.

## 1. What the v1.6 closure cycle did

The Project Owner's *Final Consolidated Closure Instruction* (11-Nov-26) recorded six decisions and passed on ChatGPT's 14 findings on v1.5. Claude 2 implemented the decisions, resolved every finding, repeated the full consistency review, re-ran the arithmetic checks, and rebuilt and verified the package as **v1.6**. No production code, repository work or inventory script was created.

## 2. Owner decisions incorporated (record: 11 v1.3 §1.3)

| ID | Decision | Implemented in |
|---|---|---|
| G-03 | Every ±15% move blocks by default until the Owner verifies that occurrence and marks it `VERIFIED_OK` | 02 v1.3 §5.2, §7.1, §7.2; 04 v1.3 SC-07; 06 v1.3 T-DQ-07/08, ACC-06; 10 v1.4 §A7, §B9.3; 09 v1.3 |
| G-04 | Tick rule verified only with evidence, effective-from (effective-to where known) and confirmation; otherwise flag only | 02 v1.3 §5.2, V-PX-03; 06 T-DQ-02a/02c |
| G-16 | Only exact SHA-256 matches are duplicates; any difference to the Owner; no automatic merging or selection | 02 v1.3 §9.6; 06 T-MNT-11/11b/12; 09 v1.3 §2.7, §6.1, §6.6, §8.3 U-02 |
| D-EMA-01 to 10 | EMA v1.2 methodology approved, subject to G-03; combined weight deferred | 10 v1.4 (status, §A3–§A10, §B9.3); 04 v1.3 §9; 08 v1.3 Gate 3 |
| Pilot | Stratified 30 + 10 + 10 method approved; CONCOR and INFY within ~50; list pending the inventory | 09 v1.3 header, §6.3a |
| G-01 | Inventory script **not authorised** | 09 v1.3 §8.1; 08 v1.3 §9; 11 v1.3 §4, §5 |

## 3. ChatGPT findings — resolution

| # | Finding | Resolution | Where |
|---|---|---|---|
| 1 | G-16 content/first-file rule | Removed. Exact SHA-256 only; CONCOR `.txt`/Parquet is now a conflict for the Owner; ACC-05 runs each into its own data root | 02 §9.6; 06 T-MNT-11, 11b, ACC-05; 09; 11 M1a |
| 2 | G-03 open-only exception | Removed from the design. Kept only as unapproved proposal **P-01** | 02 §7.1–§7.2; 10 §A7; 12 §3 |
| 3 | G-04 approval | Recorded; rule stated on `instrument_rule`; new test T-DQ-02c | 02 §5.2; 06 |
| 4 | EMA approval | D-EMA-01 to 10 approved; weight deferred (G-10) | 10 v1.4 |
| 5 | Pilot method | Approved; list not finalised | 09 v1.3 |
| 6 | G-02 provenance | Import stores `REFERENCE_FILE_UNCONFIRMED`, `verified = false`; official only after the Owner records the source (`evidence`, `confirmed_at` — two fields added to `market_calendar`); a changed file loses official status | 02 v1.3 §5.5; 06 T-CAL-01 to 04 |
| 7 | G-09 scope | Only explicitly selected folders; inaccessible registered sources reported as `SOURCE_INACCESSIBLE`, never removed or treated as deletion; out-of-scope sources listed | 02 v1.3 §9.6; 06 T-MNT-15/16 |
| 8 | D-EMA-11 | Presented as a new proposal with a recommendation | 12 §3; 10 v1.4 §A10 |
| 9 | New rules in v1.5 | Every new rule classified as clarification, implementation of an Owner instruction, or proposal; **OD-10 is a proposal — baseline order M1a → M1b → M2 restored** | 12 §2; 08 v1.3 §7; 11 v1.3 §2 |
| 10 | Session counts | Labelled **calculated, not re-run** wherever they appear | 02 §6.3; 06; 11 §6 |
| 11 | TC-26 risk | Smallest-step test replaced by most-common within-day step (≥ 30 steps); sparse files refused with a reason; coarser days flagged `RESOLUTION_SUSPECT`; missing minutes never cause rejection; tests T-FILE-06 to 09 | 02 v1.3 §6.1; 06 |
| 12 | G-15 | Exact pins and tests only on them retained (T-ENV-01) | 08 §6; 06 §11.4 |
| 13 | G-18, TC-25, TC-28 | G-18: additive interface field, consistent with the "only door" rule. TC-25: rewritten for G-09/G-16. TC-28: implements G-03 (only `VERIFIED_OK` unblocks) | 03 v1.2; 02 v1.3; 07 v1.3 §B |
| 14 | EMA reference values | Arithmetic re-check separated from independent verification; states that **no independent verification has been performed** | 10 v1.4 header, §B9; 06 §11.2 |

## 4. Additional corrections from the full consistency review

- 08 v1.3: Gate 0 no longer lists decided items; R-18 added for the 11-Nov-26 decisions; must-not list extended for G-02, G-03, G-09, G-16 and TC-26; Gate 3 now requires D-EMA-11 and independent reproduction.
- 11 v1.3: readiness table shows, for every milestone, start conditions, dependence on the stock-universe inventory, and who acts; gaps G-23 and G-24 added; evidence status updated.
- 07 v1.3: TC-25, TC-26, TC-29 revised; E-13 resolved by the G-03 decision.
- 09 v1.3: "open-only moves do not affect EMA" statements corrected for G-03.
- 02 v1.3: the update flow diagram starts from the selected folders.
- Cross-references to superseded versions updated where they pointed to changed sections. Elsewhere the section numbers are unchanged, and the index states the convention.
- Unchanged after review (no defect found): 01 v1.2, 03 v1.2, 05 v1.1, and the workbook v1.1. The workbook has 18 sheets, and its Decisions sheet matches D-01 to D-13.

## 5. Outstanding items and impact (document 12)

| ID | Item | Impact |
|---|---|---|
| GATE-0 | Package approval | No coding until given |
| D-EMA-11 | Stale-data rule (proposal) | Blocks M3 |
| D-EMA-12 | Numeric precision of comparisons and stored score (proposal, v1.8) | Blocks M3 |
| OD-12 | May M3 start while M1c is blocked (proposal, v1.8) | Needed after M2; if undecided, M3 waits for M1c |
| EMA source verification | **Complete** (CONCOR v1.9; INFY v1.10) | — |
| OD-10 | Build M2 before M1b (proposal, optional) | Baseline applies if undecided |
| G-11 | Second scanner | Blocks M4, M5 and the Day 7 target |
| G-10 | First profile and EMA weight | Blocks M5 |
| P-01 | Open-only moves non-blocking for close-based scanners (optional proposal) | Historical EMA availability only |
| G-01 | Inventory script (not authorised) | Blocks M1c only |
| G-20 | Scripts 01b/01c not supplied (Owner action) | Reproduction of Deliverable 1 and the benchmark only |

## 6. Files and versions (v1.5 → v1.6; for v1.7 see §0B, for v1.8 see §0A)

| # | Document | v1.5 | v1.6 |
|---|---|---|---|
| 00 | Master Index | 1.5 | **1.6** |
| 01 | Data Inventory and Quality Report | 1.2 | 1.2 |
| 01a | Workbook | 1.1 | 1.1 |
| 01b, 01c | Exploratory scripts | not supplied | not supplied |
| 02 | Database and Catalogue | 1.2 | **1.3** |
| 03 | Data Access and Aggregation | 1.2 | 1.2 |
| 04 | Engine and Scanner Architecture | 1.2 | **1.3** |
| 05 | Combined Scoring and Output | 1.1 | 1.1 |
| 06 | Testing and Validation | 1.2 | **1.3** |
| 07 | Decision and Future Ideas Register | 1.2 | **1.3** |
| 08 | Claude 1 Implementation Handover | 1.2 | **1.3** |
| 09 | Stock Universe and Pilot | 1.2 | **1.3** |
| 10 | EMA Scanner (approved methodology) | 1.3 | **1.4** |
| 11 | Readiness Checklist | 1.2 | **1.3** |
| 12 | Owner Decision Register | 1.0 | **1.1** |
| HN | Handover note | 1.0 | **2.0** (this file) |

## 7. Package integrity

Sizes and SHA-256 fingerprints of every file except the index (which cannot fingerprint itself) are in index 00 v1.10 §3.1. The verification procedure and its results are in index §5. The ZIP was tested after the final build, and the results are restated in Claude 2's submission message. To reproduce:
1. `unzip -t` the ZIP.
2. Compute SHA-256 for each extracted file.
3. Compare the first 16 hex characters and the sizes with index §3.1.

## 8. Tests actually performed, and tests not performed

| Kind | Status | Result |
|---|---|---|
| Arithmetic re-check of documented figures, re-run this cycle: T-EMA-16 (13 scores), T-EMA-01, the six answers and net of T-EMA-02 to 05, T-AGG-01b and T-AGG-02 volumes, T-SCC-01, T-SCO-01, the 75.33 illustration, the ±15% percentages, warm-up residuals | Performed by Claude 2 | All match the documents |
| Package integrity checks (§7) | Performed by Claude 2 | See index §5 and the submission message |
| Q-MAP tests (T-*, ACC-*, E2E-*) | **Not performed.** No code exists. | 0 executed / 0 passed / 0 failed |
| Failure injection, backup and restore, end-to-end on the Owner's PC | **Not performed.** Needs the implementation and the Owner's PC. | — |
| Automated EMA tests | **Not performed.** Needs the implementation. | — |
| Independent verification of the EMA reference values | **Complete — CONCOR (v1.9) and INFY (v1.10) verified against source data** (document 13 v1.2) | — |
| Re-running the session counts (383 / 67 / 3) | **Not performed.** Same reason; the counts are calculated. | — |
| Universe inventory and pilot list | **Not performed.** The script is not authorised. | — |

## 9. What Claude 1 may implement after Owner approval

Only after GATE-0, in the approved sequence M1a → M1b → M2 → M1c → M3, and only when each milestone's start conditions in 11 v1.5 §2 are met:
- Gate 0: exact pins for Python 3.12.10, plus T-ENV-01.
- M1a: database foundation on the inspected files.
- M1b: maintenance, held revisions, generations, backup and restore.
- M2: data access and aggregation, after M1b in the baseline order.
- M1c: pilot load, only after its four prerequisites (§0C).
- M3: EMA scanner and engine core — after M1c in the approved sequence (or earlier if the Owner approves OD-12), once D-EMA-11 and D-EMA-12 are decided (reference values are source-verified) (complete for CONCOR and INFY, document 13 v1.2).
- M6: output, after M3.

**V-04 and the pilot (v1.7).** V-04 (full stock-universe inventory) is **not** a Gate 0 condition. Gate 0, M1a, M1b and M2 use the already inspected sample files. M1c follows M2 and may begin only when: G-01 is explicitly authorised, the inventory is completed and reviewed, the proposed pilot list is presented to the Owner, and the Owner approves that actual list (08 v1.4 §7; 11 v1.4 §2).

Every milestone must end in a runnable demonstration on actual historical data, with the evidence and acceptance listed in 06 v1.3 §9 and 11 v1.3 §3.

## 10. Still prohibited or unauthorised

- Production coding and repository work before GATE-0.
- Using `old-Q-MAP-ignore`.
- The G-01 inventory script.
- Any exception to the ±15% rule.
- Content-based duplicate detection, automatic source selection, or merging.
- Scanning unselected folders, or treating missing files as deletions.
- Treating an imported calendar as official without recorded provenance.
- Quarantine under unverified tick rules.
- Renormalised combined scores.
- Implementing OD-10, D-EMA-11 or P-01 before the Owner decides.
- P2/P3 features: cloud, remote APIs, AI integration, caches, dashboards.
- Reporting a test as passed without executing it.

## 11. Final self-check against the closure instruction

| Instruction section | Done | Evidence |
|---|---|---|
| §1 Decisions treated as final and applied consistently | Yes | §2 above; sweep for stale wording (G-03 exception, content duplicates, pending G-03/G-04/G-16) found no remaining instances outside change logs |
| §2 Findings 1–14 | Yes | §3 above |
| §3 Full consistency review | Yes | §4 above; 00 v1.8 §2.3 |
| §4 Package reconciliation; scripts not recreated | Yes | 00 v1.8 §3.2, §5 |
| §5 Readiness and handover | Yes | 11 v1.3 §2–§6; 08 v1.3 |
| §6 Unresolved matters in one register, no repeat questions | Yes | 12 v1.1 §3 (only new or open items) |
| §7 Deliverables 1–9 | Yes | ZIP plus separate key documents |
| §8 Evidence rather than assertion | Yes | §7–§8 above; index §5 |

## 12. Next steps

| Who | Action | Awaiting |
|---|---|---|
| ChatGPT | Independently verify v1.10 and prepare the Gate 0 recommendation | The package (provided to ChatGPT by the Owner) |
| Project Owner | Decide GATE-0; then D-EMA-11, OD-10 (optional), G-11 and G-10 as the milestones approach; re-send scripts 01b/01c if available | ChatGPT's recommendation |
| Claude 2 | Apply any final corrections ChatGPT raises; add the scripts with fingerprint verification if supplied | ChatGPT's findings; the Owner's instruction |
| Claude 1 | Remain on hold | Explicit Owner approval (GATE-0) |

Claude 2 has not sent anything to ChatGPT or Claude 1; the Owner passes this package on.

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**

*End of handover note v2.0.*
