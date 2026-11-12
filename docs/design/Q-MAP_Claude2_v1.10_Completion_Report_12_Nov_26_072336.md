# Q-MAP — Claude 2 v1.10 Completion Report

**12-Nov-26 | Prepared by Claude 2 | Package: `Q-MAP_Design_Package_v1.10_12_Nov_26_072336.zip` | Supplied outside the ZIP so that it can record the index's own fingerprint.**

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**

## 1. INFY source verification

**Source:** `INFY_daily_02Jan98-06Nov26.parquet`, the authoritative file.
- 144,271 bytes, matching Deliverable 1; 7,169 rows; 02-Jan-98 – 06-Nov-26.
- SHA-256 `2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01`.
- Data checks: 0 duplicate dates, rows sorted, 0 OHLC violations, 34 weekend rows.
- `INFY.txt` was compared for reference only: identical on all 7,169 rows.

| Item | T-EMA-03 (06-Nov-26) | T-EMA-04 (03-Feb-26) |
|---|---|---|
| Window start | 17-Aug-23 ✔ | 16-Nov-22 ✔ |
| Close | 1,181.40 ✔ | 1,656.00 ✔ |
| EMA20 | 1,132.2614 ✔ | 1,646.1038 ✔ |
| EMA50 | 1,108.5365 ✔ | 1,617.6051 ✔ |
| EMA200 | 1,203.8765 ✔ | 1,589.1800 ✔ |
| EMA50 ten bars earlier | 1,084.5193 ✔ | 1,598.2591 ✔ |
| Six contributions | +1 +1 −1 +1 −1 +1 ✔ | +1 +1 +1 +1 +1 +1 ✔ |
| Net / score / state | +2 / 66.67 / NEUTRAL ✔ | +6 / 100 / BULLISH ✔ |
| ±15% moves in the window | **None** | **None** (nearest: 22-Oct-19, before the window) |
| G-03 blocking | None — **valid `OK` result** | None — **valid `OK` result** |
| Unchanged under the D-EMA-12 rounding proposal? | Yes | Yes |

All values are exact to 4 dp. **Every EMA reference example in document 10 is now verified against source data.** The CONCOR examples T-EMA-02 and T-EMA-05 are source-verified but blocked by G-03 (04-Jun-24). The T-EMA-18 values remain conditional (15-May-06).

## 2. INFY ±15% history — newly identified G-03 cases

| Date | Prev close | Open | Close | Open % | Close % | Previously documented? | EMA analysis dates blocked |
|---|---:|---:|---:|---:|---:|---|---|
| 08-Aug-00 | 100.60 | 101.40 | 116.55 | +0.80 | **+15.85** | **No** | 08-Aug-00 – 17-Oct-03 |
| 11-Apr-01 | 59.82 | 62.74 | 50.24 | +4.88 | **−16.01** | **No** | 11-Apr-01 – 17-Jun-04 |
| 18-Apr-01 | 47.74 | 48.24 | 55.38 | +1.05 | **+16.00** | **No** | 18-Apr-01 – 23-Jun-04 |
| 10-Apr-03 | 64.88 | 64.06 | 47.65 | −1.26 | **−26.56** | **No** | 10-Apr-03 – 14-Jun-06 |
| 24-Oct-03 | 69.03 | 81.25 | 71.16 | +17.70 | +3.09 | Yes | 24-Oct-03 – 27-Dec-06 |
| 11-Jan-13 | 290.29 | 315.12 | 339.01 | +8.55 | **+16.78** | **No** | 11-Jan-13 – 08-Apr-16 |
| 12-Apr-13 | 364.59 | 328.13 | 287.08 | −10.00 | **−21.26** | **No** | 12-Apr-13 – 12-Jul-16 |
| 22-Oct-19 | 767.85 | 691.10 | 643.55 | −10.00 | **−16.19** | **No** | 22-Oct-19 – 05-Jan-23 |

- **Treatment:** the seven new cases are G-03 blocking cases awaiting your individual verification. None was classified, accepted, quarantined or unblocked.
- **Combined effect:** until any occurrence is verified, INFY has an EMA result only for analysis dates 28-Dec-06 – 10-Jan-13, 13-Jul-16 – 18-Oct-19 and 06-Jan-23 – 06-Nov-26. Both reference dates fall in the last period.
- **Why they were missed earlier:** the M0 inspection counted open gaps only.

## 3. Changes made

| Document | v1.9 | v1.10 | Reason |
|---|---|---|---|
| 00 Master Index | 1.9 | **1.10** | Contents, fingerprints, results |
| 01 Data Inventory | 1.3 | **1.4** | INFY addendum (seven close moves); header updated |
| 02 Database and Catalogue | 1.5 | **1.6** | §7.2 expected issues include the INFY cases |
| 06 Testing | 1.4 | **1.5** | ACC-06 includes the INFY cases; ledger records the INFY verification as done |
| 07 Decision Register | 1.5 | **1.6** | New row V-01b for the INFY cases |
| 08 Implementation Handover | 1.6 | **1.7** | Gate 3 and quick reference: source verification complete, no longer an M3 condition; §10 G-03 row |
| 09 Stock Universe and Pilot | 1.5 | **1.6** | §2.6–§2.7 record the INFY cases |
| 10 EMA Scanner | 1.6 | **1.7** | INFY examples marked source-verified; INFY history note. **Methodology unchanged.** |
| 11 Readiness Checklist | 1.6 | **1.7** | M3 conditions; new gap G-28; evidence status. Your M1b G-03 row is unchanged. |
| 12 Owner Decision Register | 1.4 | **1.5** | GATE-0 now refers to v1.10; INFY file action closed; INFY occurrences to verify. No decision changed. |
| 13 EMA Verification Evidence | 1.1 | **1.2** | INFY evidence; summary (10 source-verified); new §6 INFY ±15% list; nothing outstanding |
| ChatGPT Handover Note | 2.3 | **2.4** | New §00 |

Unchanged and byte-identical to v1.9: 01a, 03, 04, 05.

## 4. Package integrity (performed 12-Nov-26 on the final ZIP)

- `unzip -t`: no errors detected. All Markdown files read correctly as UTF-8.
- File list: 16 files (15 indexed plus the index); none missing, none extra; no `.py` files, no source data and no code.
- Versions: the file name, index entry and document header agree for every file.
- Index (by convention not fingerprinted inside itself): `Q-MAP_00_Design_Package_Master_Index_v1.10_12_Nov_26_072336.md`, 9,587 bytes, SHA-256 `38c64c0255c3b79efb7ead74aab749341ec695411661b6f9490166eb97dad247`, header version 1.10.
- Standalone copies: compared byte-for-byte with the ZIP copies; all identical (results in the submission message).

| File | Expected size | Actual size | Expected SHA-256 | Actual SHA-256 | Result |
|---|---:|---:|---|---|---|
| Q-MAP_01_Data_Inventory_and_Quality_Report_v1.4_12_Nov_26_072336.md | 49,219 | 49,219 | `577c9c1331a32297fc072483e7c8b4ad4013f411e41a4a0b31d05a2875a7ecf1` | `577c9c1331a32297fc072483e7c8b4ad4013f411e41a4a0b31d05a2875a7ecf1` | **PASS** |
| Q-MAP_Data_Inventory_Workbook_v1.1_11_Nov_26_183420.xlsx | 69,088 | 69,088 | `d53a0ad95d68682fc8c6825511b7b4ab094c64a6216e78c61cca3eabc24395a7` | `d53a0ad95d68682fc8c6825511b7b4ab094c64a6216e78c61cca3eabc24395a7` | **PASS** |
| Q-MAP_02_Database_and_Catalogue_Architecture_v1.6_12_Nov_26_072336.md | 69,274 | 69,274 | `81da54c51e90d4e9254fbcf79ff36d690afee100e2fe37f811426959563fb7b8` | `81da54c51e90d4e9254fbcf79ff36d690afee100e2fe37f811426959563fb7b8` | **PASS** |
| Q-MAP_03_Data_Access_and_Timeframe_Aggregation_Specification_v1.2_11_Nov_26_225736.md | 36,684 | 36,684 | `d73660eed97d92ba1ea843e49f81a101030b2c3a0915a5ed34c43d8a63b1192f` | `d73660eed97d92ba1ea843e49f81a101030b2c3a0915a5ed34c43d8a63b1192f` | **PASS** |
| Q-MAP_04_Analytical_Engine_and_Scanner_Architecture_v1.3_11_Nov_26_232056.md | 29,543 | 29,543 | `6e41079e712f1c830ad77ca6cfb3e79efc57ed5fa224a592837196ff5f74333e` | `6e41079e712f1c830ad77ca6cfb3e79efc57ed5fa224a592837196ff5f74333e` | **PASS** |
| Q-MAP_05_Combined_Scoring_and_Output_Design_v1.1_11_Nov_26_225736.md | 18,665 | 18,665 | `45d3bacd858fb7d77eba1f01309b860352e13ed37375c08d7c2620bfcba3eb87` | `45d3bacd858fb7d77eba1f01309b860352e13ed37375c08d7c2620bfcba3eb87` | **PASS** |
| Q-MAP_06_Testing_and_Validation_Strategy_v1.5_12_Nov_26_072336.md | 50,759 | 50,759 | `5156275644a461f34e7b95420bb5a7f4ba75b6446b5a89f80341097c09b97a94` | `5156275644a461f34e7b95420bb5a7f4ba75b6446b5a89f80341097c09b97a94` | **PASS** |
| Q-MAP_07_Decision_and_Future_Ideas_Register_v1.6_12_Nov_26_072336.md | 35,909 | 35,909 | `8353da35cc780f2682beb03a67e0cef16297e68ad99551b825c553778b468913` | `8353da35cc780f2682beb03a67e0cef16297e68ad99551b825c553778b468913` | **PASS** |
| Q-MAP_08_Claude1_Implementation_Handover_v1.7_12_Nov_26_072336.md | 33,889 | 33,889 | `9c63418d9375a1823b3bc3b1f94c8b3116a45fbd82e9b5f6e881577bcac87f9e` | `9c63418d9375a1823b3bc3b1f94c8b3116a45fbd82e9b5f6e881577bcac87f9e` | **PASS** |
| Q-MAP_09_Stock_Universe_Inventory_and_Pilot_Selection_v1.6_12_Nov_26_072336.md | 33,898 | 33,898 | `a54ced351328bd9666b1bb9458ac56cafb8e34a055d7d9eb0b7e39d813b4a40e` | `a54ced351328bd9666b1bb9458ac56cafb8e34a055d7d9eb0b7e39d813b4a40e` | **PASS** |
| Q-MAP_10_EMA_Scanner_Design_Proposal_v1.7_12_Nov_26_072336.md | 43,001 | 43,001 | `5396b001ecf3fa3fe0883d26719308ba8be164f16606f8b11d959d24fd76572c` | `5396b001ecf3fa3fe0883d26719308ba8be164f16606f8b11d959d24fd76572c` | **PASS** |
| Q-MAP_11_Claude1_Implementation_Readiness_Checklist_v1.7_12_Nov_26_072336.md | 38,897 | 38,897 | `55f7bc167a65dfe747b5049941bab865a42be697567eb7562a1c6aa34f2744d0` | `55f7bc167a65dfe747b5049941bab865a42be697567eb7562a1c6aa34f2744d0` | **PASS** |
| Q-MAP_12_Owner_Decision_Register_v1.5_12_Nov_26_072336.md | 16,770 | 16,770 | `0181ad506ebde6dad30034c66c03475b45192d734743011718097bdd603d666f` | `0181ad506ebde6dad30034c66c03475b45192d734743011718097bdd603d666f` | **PASS** |
| Q-MAP_13_EMA_Reference_Verification_Evidence_v1.2_12_Nov_26_072336.md | 14,698 | 14,698 | `7225e3ecf0afd91f3819625ab906b11fa015e452d9b5f8f3da868bfba1539ec0` | `7225e3ecf0afd91f3819625ab906b11fa015e452d9b5f8f3da868bfba1539ec0` | **PASS** |
| Q-MAP_ChatGPT_Handover_Note_v2.4_12_Nov_26_072336.md | 21,474 | 21,474 | `88bbbabbd62c6399b54fd751f84ff17038483319857bfce7e3c8a0ef180218bd` | `88bbbabbd62c6399b54fd751f84ff17038483319857bfce7e3c8a0ef180218bd` | **PASS** |

**15 of 15 indexed files pass both size and SHA-256.**

## 5. Outstanding Owner decisions and dependencies (unchanged)

| Item | Needed by | Effect if undecided |
|---|---|---|
| GATE-0 | Before M1a | Nothing is built |
| OD-12 — M3 before M1c? | When M2 is complete | M3 waits for M1c |
| D-EMA-11 — stale data | Before M3 | M3 cannot start |
| D-EMA-12 — precision and score storage | Before M3 | T-EMA-10 cannot pass reliably |
| G-11 — second scanner | Before M4 | M4, M5 wait |
| G-10 — profile and EMA weight | Before M5 | M5 waits |
| G-01 — inventory authorisation | Before M1c | M1c blocked |
| OD-10, P-01 | Optional | No effect |
| Owner action: verify ±15% occurrences (CONCOR 8, INFY 8, NIFTYIT 1) | When the affected history is needed | Those results stay `INVALID_DATA` |

**Sequence:** M1a → M1b → M2 → M1c → M3 → M4 → M5; M6 after M3. **No source-data item now blocks any milestone.**

## 6. Not done

- No inventory script was created or run.
- No production code was written and no repository was changed.
- No Q-MAP test was executed (0 / 0 / 0).
- No Owner decision was made or assumed.
- No G-03 occurrence was classified or unblocked.
- No source data was modified.

## 7. Final status

Claude 2's evidence and documentation work is **complete**: every EMA reference example is source-verified, and the package is consistent and verified. The package is ready for ChatGPT's independent review and your Gate 0 decision. All remaining items are Owner decisions or Owner verification actions (section 5).

> **This remains a design and preparation deliverable. It is not approval to begin production coding.**
