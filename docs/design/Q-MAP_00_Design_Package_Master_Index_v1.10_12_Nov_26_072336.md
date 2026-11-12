# Q-MAP — Design Package Master Index

**Package document 00 | Version 1.10 | 12-Nov-26 | Status: Final Claude 2 documentation and evidence package for ChatGPT's independent review and the Project Owner's Gate 0 decision**

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**
>
> No production code exists. No GitHub repository has been created or modified. No Q-MAP test has been executed. The G-01 inventory script has not been created. Scripts 01b and 01c have not been recreated.

**Change log**

| Version | Change |
|---|---|
| 1.0–1.7 | Earlier submissions (see each document's change log) |
| 1.8 | Final groundwork cycle: Owner-corrected 11 v1.4; approved sequence; EMA arithmetic verification; D-EMA-12 and OD-12 |
| 1.9 | CONCOR source verification; T-EMA-09 date correction; T-EMA-18 conditional values; three new CONCOR G-03 cases; Nifty IT findings |
| **1.10** | **INFY source verification (Owner-approved, 12-Nov-26):** T-EMA-03 and T-EMA-04 verified exactly against `INFY_daily_02Jan98-06Nov26.parquet`, with no ±15% move in either window. All EMA reference values are now source-verified. Seven newly identified INFY G-03 cases — 08-Aug-00 (+15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%), 22-Oct-19 (−16.19%) — recorded wherever expected issues are listed. |

---

## 1. Current version of every file

| # | Document | v1.9 | **v1.10** |
|---|---|---|---|
| 00 | Master Index | 1.9 | **1.10** |
| 01 | Data Inventory and Quality Report | 1.3 | **1.4** |
| 01a | Data Inventory Workbook (18 sheets) | 1.1 | 1.1 |
| 01b, 01c | Exploratory scripts | not supplied | **not supplied** (§3.2) |
| 02 | Database and Catalogue Architecture | 1.5 | **1.6** |
| 03 | Data Access and Timeframe Aggregation | 1.2 | 1.2 |
| 04 | Analytical Engine and Scanner Architecture | 1.3 | 1.3 |
| 05 | Combined Scoring and Output Design | 1.1 | 1.1 |
| 06 | Testing and Validation Strategy | 1.4 | **1.5** |
| 07 | Decision and Future Ideas Register | 1.5 | **1.6** |
| 08 | Claude 1 Implementation Handover | 1.6 | **1.7** |
| 09 | Stock Universe Inventory and Pilot Selection | 1.5 | **1.6** |
| 10 | EMA Scanner Design (methodology approved) | 1.6 | **1.7** |
| 11 | Implementation-Readiness Checklist | 1.6 | **1.7** |
| 12 | Owner Decision Register | 1.4 | **1.5** |
| 13 | EMA Reference Verification Evidence | 1.1 | **1.2** |
| HN | ChatGPT Handover Note | 2.3 | **2.4** |

**Cross-reference convention.** A reference such as "02 v1.1 §9.4" points to a section whose number is unchanged; the current version of every document is the one in this table. Change logs and decision records cite versions historically.

---

## 2. What changed

### 2.1 v1.10 — INFY verification

| Item | Change | Documents |
|---|---|---|
| T-EMA-03, T-EMA-04 | Source-verified, exact to 4 dp; valid `OK` results (no G-03 block) | 13 §3; 10; 06 §11; 08 Gate 3; 11 M3; HN §00 |
| INFY ±15% history | Eight occurrences; seven newly identified G-03 cases awaiting the Owner; none classified, quarantined or unblocked; blocked periods recorded | 13 §6; 01 addendum; 02 §7.2; 06 ACC-06; 07 V-01b; 09 §2.6–§2.7; 10 §A7; 11 G-28; 12 §4 |
| M3 conditions | Source verification removed as a condition (complete); D-EMA-11, D-EMA-12 and OD-12 (or M1c) remain | 08, 11 |

### 2.2 v1.9 — CONCOR verification

CONCOR examples verified; T-EMA-09 date corrected (10-Sep-13); T-EMA-18 conditional values; CONCOR 31-Jan-08, 20-Mar-20 and 10-Aug-20 recorded; Nifty IT findings; defects in 01 and 07 corrected.

### 2.3 v1.8 — final groundwork cycle

Owner-corrected Document 11 v1.4 incorporated (34,733 bytes; SHA-256 `f7539a96e161f7155df83dc99054580d7f33be85a601d513dd38fe59a8f2d56c`); approved sequence; D-EMA-12 and OD-12.

### 2.4 v1.7 — V-04 correction

V-04 required before M1c only.

### 2.5 v1.6 — closure cycle

Owner decisions G-03, G-04, G-16, D-EMA-01 to 10 and the pilot method implemented; ChatGPT findings 1–14 resolved (HN §3).

---

## 3. Package contents

### 3.1 Files in `Q-MAP_Design_Package_v1.10_12_Nov_26_072336.zip`

The index does not fingerprint itself, because it cannot contain its own hash. Its fingerprint is reported in the separate *Claude 2 v1.10 Completion Report*, which is outside the ZIP.

| # | File | Version | Status vs v1.9 | Size (bytes) | SHA-256 |
|---|---|---|---|---:|---|
| 00 | Q-MAP_00_Design_Package_Master_Index_v1.10_12_Nov_26_072336.md | 1.10 | This file | (self) | (reported outside the ZIP) |
| 01 | Q-MAP_01_Data_Inventory_and_Quality_Report_v1.4_12_Nov_26_072336.md | 1.4 | Revised (INFY addendum) | 49,219 | `577c9c1331a32297fc072483e7c8b4ad4013f411e41a4a0b31d05a2875a7ecf1` |
| 01a | Q-MAP_Data_Inventory_Workbook_v1.1_11_Nov_26_183420.xlsx | 1.1 | Unchanged | 69,088 | `d53a0ad95d68682fc8c6825511b7b4ab094c64a6216e78c61cca3eabc24395a7` |
| 02 | Q-MAP_02_Database_and_Catalogue_Architecture_v1.6_12_Nov_26_072336.md | 1.6 | Revised | 69,274 | `81da54c51e90d4e9254fbcf79ff36d690afee100e2fe37f811426959563fb7b8` |
| 03 | Q-MAP_03_Data_Access_and_Timeframe_Aggregation_Specification_v1.2_11_Nov_26_225736.md | 1.2 | Unchanged | 36,684 | `d73660eed97d92ba1ea843e49f81a101030b2c3a0915a5ed34c43d8a63b1192f` |
| 04 | Q-MAP_04_Analytical_Engine_and_Scanner_Architecture_v1.3_11_Nov_26_232056.md | 1.3 | Unchanged | 29,543 | `6e41079e712f1c830ad77ca6cfb3e79efc57ed5fa224a592837196ff5f74333e` |
| 05 | Q-MAP_05_Combined_Scoring_and_Output_Design_v1.1_11_Nov_26_225736.md | 1.1 | Unchanged | 18,665 | `45d3bacd858fb7d77eba1f01309b860352e13ed37375c08d7c2620bfcba3eb87` |
| 06 | Q-MAP_06_Testing_and_Validation_Strategy_v1.5_12_Nov_26_072336.md | 1.5 | Revised | 50,759 | `5156275644a461f34e7b95420bb5a7f4ba75b6446b5a89f80341097c09b97a94` |
| 07 | Q-MAP_07_Decision_and_Future_Ideas_Register_v1.6_12_Nov_26_072336.md | 1.6 | Revised | 35,909 | `8353da35cc780f2682beb03a67e0cef16297e68ad99551b825c553778b468913` |
| 08 | Q-MAP_08_Claude1_Implementation_Handover_v1.7_12_Nov_26_072336.md | 1.7 | Revised | 33,889 | `9c63418d9375a1823b3bc3b1f94c8b3116a45fbd82e9b5f6e881577bcac87f9e` |
| 09 | Q-MAP_09_Stock_Universe_Inventory_and_Pilot_Selection_v1.6_12_Nov_26_072336.md | 1.6 | Revised | 33,898 | `a54ced351328bd9666b1bb9458ac56cafb8e34a055d7d9eb0b7e39d813b4a40e` |
| 10 | Q-MAP_10_EMA_Scanner_Design_Proposal_v1.7_12_Nov_26_072336.md | 1.7 | Revised (methodology unchanged) | 43,001 | `5396b001ecf3fa3fe0883d26719308ba8be164f16606f8b11d959d24fd76572c` |
| 11 | Q-MAP_11_Claude1_Implementation_Readiness_Checklist_v1.7_12_Nov_26_072336.md | 1.7 | Revised | 38,897 | `55f7bc167a65dfe747b5049941bab865a42be697567eb7562a1c6aa34f2744d0` |
| 12 | Q-MAP_12_Owner_Decision_Register_v1.5_12_Nov_26_072336.md | 1.5 | Revised | 16,770 | `0181ad506ebde6dad30034c66c03475b45192d734743011718097bdd603d666f` |
| 13 | Q-MAP_13_EMA_Reference_Verification_Evidence_v1.2_12_Nov_26_072336.md | 1.2 | Revised | 14,698 | `7225e3ecf0afd91f3819625ab906b11fa015e452d9b5f8f3da868bfba1539ec0` |
| HN | Q-MAP_ChatGPT_Handover_Note_v2.4_12_Nov_26_072336.md | 2.4 | Revised | 21,474 | `88bbbabbd62c6399b54fd751f84ff17038483319857bfce7e3c8a0ef180218bd` |

The ZIP contains exactly these **16** files: no superseded version, no `.py` file, no production code and no source data. The Owner-supplied source files are identified by fingerprint in 13 §1.

### 3.2 Exploratory scripts 01b and 01c — unavailable, non-blocking

- **What they are:** `QMAP_M0_Exploratory_Data_Inspection.py` (v1.1; 44,230 bytes; SHA-256 begins `1401b917b2b98088`) and `QMAP_Exploratory_Benchmark.py` (v1.0; 4,121 bytes; begins `5d582970bdb5d842`).
- **Status:** not supplied and not recreated.
- **Effect on the design or milestones:** none.
- **Where their results are:** 01, 01a and 03 §B10.
- **What their absence prevents:** re-running the original M0 inspection and the benchmark (ACC-09).
- **Recorded as:** an unavailable, non-blocking historical artefact.

### 3.3 Reading order

- **ChatGPT:** HN v2.4 §00 → completion report → change logs of the revised documents → 13 v1.2.
- **Owner:** 12 v1.5 §4–§5 → completion report §7.
- **Claude 1 (after approval only):** 08 v1.7 §1 and §7 quick reference → 11 v1.7.

---

## 4. Decision status (unchanged in v1.10)

| Status | Items |
|---|---|
| Confirmed | D-01 to D-13; OD-01 to OD-09; I-01; I-02; G-03; G-04; G-16; D-EMA-01 to 10; pilot method |
| Not authorised | G-01 inventory script; production coding; repository work |
| Pending Owner | GATE-0; D-EMA-11; D-EMA-12; OD-12; G-11; G-10; G-01 authorisation (when wanted) |
| Optional, not adopted | OD-10; P-01 |
| Pending Owner action | Verification of each ±15% occurrence (G-03): CONCOR 8, INFY 8, NIFTYIT 1 in the inspected files |
| Approved sequence | M1a → M1b → M2 → M1c → M3 → M4 → M5; M6 after M3 |

---

## 5. Verification results

Performed by Claude 2 on 12-Nov-26 on the final ZIP; the per-file table is in the completion report.

| Check | Result |
|---|---|
| ZIP opens; `unzip -t` | Passed — no errors |
| File list against §3.1 | 16 files; none missing; none extra; no `.py` files |
| Sizes | 15 of 15 indexed files match |
| SHA-256 (full) | 15 of 15 indexed files match |
| Versions | File name, index and document header agree for all files |
| Standalone copies match ZIP copies | Yes (byte comparison) |
| Unchanged files byte-identical to v1.9 | 01a, 03, 04, 05 |

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**

*End of master index, v1.10.*
