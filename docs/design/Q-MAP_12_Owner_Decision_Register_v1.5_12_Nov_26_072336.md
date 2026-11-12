# Q-MAP — Owner Decision Register

**Package document 12 | Version 1.5 | 12-Nov-26 | Status: Decisions of 11-Nov-26 recorded; remaining open items for the Project Owner (v1.10 package). No new decision required by the v1.10 evidence update.**

| Field | Value |
|---|---|
| Purpose | One place showing (1) the Owner decisions now recorded, (2) the status of every new rule introduced in v1.5–v1.8, and (3) the few decisions still open, each with a recommendation and one question |
| Prepared by | Claude 2 |
| Written record of earlier decisions | D-01 to D-13; OD-01 to OD-09; I-01, I-02 — document 11 v1.3 §1.1–§1.2. Decisions of 11-Nov-26 — document 11 v1.3 §1.3. |

> **This package is a design and preparation deliverable. It is not approval to begin production coding.**

**Change log**

| Version | Change |
|---|---|
| 1.0 | First issue (v1.5 package) |
| 1.1 | Owner decisions of 11-Nov-26 recorded (G-03, G-04, G-16, D-EMA-01 to 10, pilot method; G-01 not authorised) and no longer asked. New §2 classifies every rule introduced in v1.5–v1.6. G-03's open-only exception withdrawn and kept only as proposal P-01. D-EMA-11, OD-10 and P-01 presented as proposals. |
| 1.2 | Targeted correction (v1.7 package): GATE-0 refers to v1.7; G-01 entry states that V-04 blocks M1c only and that the actual pilot list needs your separate approval. No decision changed. |
| 1.3 | Final groundwork cycle: GATE-0 refers to v1.8; two new items from the final verification and sequence review — **D-EMA-12** (numeric precision, before M3) and **OD-12** (M3 while M1c is blocked, after M2); §5 rewritten as one table showing for every open item what is needed, why, by when, and what happens if undecided. No earlier decision changed. |
| 1.4 | v1.9 evidence update: GATE-0 refers to v1.9; Owner actions updated — CONCOR source files received and verified; **INFY file still needed**; the eight CONCOR G-03 occurrences now awaiting your verification are listed (three newly identified). All open decisions unchanged and still pending. |
| 1.5 | v1.10 evidence update: GATE-0 refers to v1.10; the INFY file was received and the INFY values are verified, so that action is closed; the INFY ±15% occurrences awaiting your verification are listed (seven newly identified). All open decisions unchanged and still pending. |

---

## 1. Decisions recorded on 11-Nov-26 — not asked again

| ID | Your decision | What it means in practice |
|---|---|---|
| G-03 | Every price move beyond ±15% blocks until you verify that occurrence and mark it `VERIFIED_OK` | Long-window results (e.g. the 200-day EMA) for an affected stock are shown as "invalid data" until you review the move. Open-only and close moves are treated alike. |
| G-04 | A tick rule needs supporting evidence and effective dates before it is "verified"; until then off-tick values are flagged, not removed | Suspected filled-in candles stay visible and flagged until you confirm a rule with evidence |
| G-16 | Only files with identical SHA-256 fingerprints are duplicates; any other difference comes to you; no automatic merging or selection | `CONCOR.txt` and the CONCOR Parquet are different files, so you will be asked to choose one |
| D-EMA-01 to 10 | EMA methodology approved, subject to G-03; combined-score weight deferred | The first scanner's rules are fixed; its weight is set with the first profile (G-10) |
| Pilot | Stratified 30 + 10 + 10 method approved; CONCOR and INFY included within about 50 | The actual list comes to you after the inventory |
| G-01 | Inventory script **not authorised** | Nothing is created until you give explicit further approval. Gate 0, M1a, M1b and M2 do **not** need it (they use the inspected sample files); only the pilot (M1c) waits |

---

## 2. Every new rule introduced in v1.5–v1.8, and its status

This table answers ChatGPT's finding 9: which additions are technical clarifications within the approved design, which carry out your instructions, and which need your decision. **None of the "proposal" items is treated as approved anywhere in the package.**

| Item | What it is | Type | Status |
|---|---|---|---|
| Weekend full sessions (G-17) | A full-length Saturday or Sunday session waits for your confirmation, like any special session (accepted rule A3) | Technical clarification | In the design; reviewer to confirm. Session counts were **calculated**, not re-run. |
| `latest_n` in a data request (G-18, TC-27) | Lets a scanner ask for "the last 800 bars" through the common interface | Technical clarification (interface 1.1, additive) | In the design |
| `RANGE_TRUNCATED_END` definition | The interface warns when a stock's data stops before the requested date | Technical clarification | In the design |
| Held revision also holds new rows | Already implied by OD-04; now stated with its visible effects | Clarification of OD-04 | In the design |
| Resolution test (TC-26, revised v1.6) | Recognises 1-minute data by the **most common** time step, so missing minutes never cause rejection; coarser days flagged | Technical clarification (answers ChatGPT finding 11) | In the design |
| Continuity rule on `affects_continuity` (TC-28) | `VERIFIED_OK` from you is the only thing that unblocks | Implements your G-03 decision | In the design |
| `DUPLICATE_SOURCE`, `SOURCE_CONFLICT` | Labels recording what happened to each file | Implements your G-16 decision | In the design |
| Update scope (TC-25, revised v1.6) | Only folders you select; unreachable registered sources reported, never removed | Implements ChatGPT finding 7 (G-09) | In the design |
| Calendar provenance (TC-29, revised v1.6) | An imported calendar is official only after you record its source; adds two fields (`evidence`, `confirmed_at`) to the existing calendar table | Implements ChatGPT finding 6 (G-02) | In the design; reviewer to confirm the two fields |
| **OD-10** build order | Build data access (M2) before update machinery (M1b) | **Proposal — your decision** | Not adopted; baseline order applies |
| **D-EMA-11** stale data | What the EMA scanner does when a stock's data stops before the analysis date | **Proposal — your decision** | Not adopted |
| **P-01** open-only moves | Treat open-only ±15% moves as non-blocking for close-only scanners | **Proposal — your decision (optional)** | Not adopted; your G-03 rule applies |
| **D-EMA-12** numeric precision | Round to 6 dp before comparisons; store the score to 2 dp | **Proposal — your decision** (found in the final verification) | Not adopted |
| **OD-12** M3 before M1c | Allow the EMA scanner to start while the pilot is blocked | **Proposal — your decision** | Not adopted; approved sequence applies |

---

## 3. Decisions still open

### GATE-0 — Approval of the package

> **Question GATE-0 (after ChatGPT's final review):** Do you approve design package v1.10, with any corrections ChatGPT requires, as the baseline that Claude 1 builds from? (This does not answer the questions below, and it does not authorise the inventory script.)

### D-EMA-11 — EMA result when a stock's data stops early (needed before M3)

**The issue.** You ask for EMA results "as of 10-Nov-26", but a stock's data ends on 06-Nov-26 — because it was suspended or delisted, or its file has not been updated. The approved methodology does not say what to do. If the scanner quietly used 06-Nov-26, a stock whose data stopped in 2019 could appear in a 2026 list with a 2019 result.

**Recommended:** give **no score** for that stock, with the message "data ends 06-Nov-26; analysis date 10-Nov-26". Holidays and weekends do not trigger this; only missing **trading** days do.

**Alternative:** calculate as of the last available date and show that date. More results, but a list would mix dates.

**Consequence:** with the recommendation, stale stocks appear as "insufficient data" until their files are updated; under OD-03 they also get no combined score.

> **Question D-EMA-11:** Should the EMA scanner give no score when a stock's data ends before the analysis date (recommended)?

### D-EMA-12 — Numerical precision of EMA comparisons and the stored score (needed before M3)

**The issue.** The final check (document 13) found that ordinary computer arithmetic introduces tiny errors. With 800 identical closes of 100.00, the 200-day EMA comes out as 100.0000000000001 instead of exactly 100, so "is the close above the 200-day EMA?" answers "no" instead of "tie", and the result changes from score 50 to 33.33. Similarly, equivalent ways of writing the score formula give 16.666666666666664, 16.66666666666667 or 16.666666666666668. Real share prices rarely produce such exact ties, but the rule must be fixed so that every run gives the same answer.

**Recommended:** before comparing, round closes and EMA values to **6 decimal places**; store the score rounded to **2 decimal places** (as the approved score table already shows). Six decimals are 10,000 times finer than the ₹0.05 price step, so this does not add any "near the line" allowance — your approved exact-comparison rule (D-EMA-07) is kept.

**Alternative:** use exact decimal arithmetic throughout. Slower and more complex, with no practical benefit.

**If undecided:** M3 cannot be accepted, because test T-EMA-10 cannot pass reliably.

> **Question D-EMA-12:** Do you approve rounding to 6 decimal places before comparisons and storing the score to 2 decimal places?

### OD-12 — May the EMA scanner (M3) start while the pilot (M1c) is blocked? (needed only after M2)

**The issue.** The approved sequence is M1a → M1b → M2 → M1c → M3. M1c cannot start until you authorise the inventory script (G-01), which you have not done. M3 needs only CONCOR and INFY, which are already in the database after M1a, so it does not technically need the pilot.

**Recommended:** if M1c is still blocked when M2 is finished, allow M3 to proceed on CONCOR and INFY without waiting. M1c then follows whenever its prerequisites are met.

**If undecided:** M3 waits for M1c, so the first scanner result (the original "Day 5" target) waits for your G-01 authorisation and the pilot.

> **Question OD-12 (answer when M2 is complete):** If the pilot is still blocked, may Claude 1 build the EMA scanner (M3) before the pilot (M1c)?

### OD-10 — Build order (optional; needed only if you want the faster route)

**The issue.** The baseline plan builds the safe-update machinery (M1b: updates, held revisions, backups, failure tests) before the common data-access door (M2). Building M2 first would let you query real data sooner — closer to the original "Day 3" target — without dropping anything from M1b.

**Recommended:** M1a → M2 → M1b. **Not adopted. If you do not decide, the approved sequence M1a → M1b → M2 → M1c → M3 applies.**

> **Question OD-10:** Do you approve building M2 before M1b?

### G-11 — The second (and third) scanner (needed before M4)

**The issue.** A combined score needs at least two scanners; only EMA is chosen.

**Recommended:** **Breakout Analysis on daily stocks** as the second — moderate effort, same data as EMA, and it measures a different condition (price leaving a recent range), which makes the combined score more informative. MA Affinity (more complex) as the third, later.

> **Question G-11:** Which scanner should be second — Breakout Analysis on daily stocks (recommended), MA Affinity, or decide later?

### G-10 — The first combined-score profile, including the EMA weight (needed before M5)

**The issue.** You approved that the EMA score may enter the combined score but deferred its weight. The profile needs its scanners and weights (totalling 100%).

**Recommended:** decide when two scanners exist; a sensible start is EMA 50% and the second scanner 50%.

> **Question G-10 (answer at M5):** Which scanners go into the first profile, and with what weights?

### P-01 — Open-only moves for close-based scanners (optional proposal)

**The issue.** Under your G-03 rule, a bad *opening* price (open more than 15% from the previous close, close normal) blocks the close-based EMA too. In the inspected data this affects four old dates (CONCOR 26-May-04, 27-May-04, 15-May-06; INFY 24-Oct-03), making several years of *historical* EMA results unavailable. Current results are not affected by these four dates.

**Options.** (a) Keep your rule as it is and verify such dates individually when you want those years (no change). (b) Adopt P-01: an open-only move would still be flagged and listed for you, but would not block scanners that use only closing prices.

**Recommendation:** keep your rule (a) for now; revisit after the inventory shows how many open-only cases exist. Nothing in the package assumes (b).

> **Question P-01 (optional; no answer means "keep the current rule"):** Do you want open-only moves to stop blocking close-based scanners?

### G-01 — Inventory script (no question now)

Recorded as **not authorised**. The full stock-universe inventory (V-04) depends on this script, so V-04 cannot be done yet. **This blocks only the pilot (M1c)**; Gate 0, M1a, M1b and M2 go ahead on the files already inspected. When you want to move towards the pilot, give explicit approval and Claude 2 will write the script exactly as specified in 09 v1.4 §8. After the inventory is reviewed, the proposed pilot list will be presented to you, and **M1c starts only after you approve that actual list**.

---

## 4. Actions for you (not decisions)

| Action | Why | When |
|---|---|---|
| Re-send `QMAP_M0_Exploratory_Data_Inspection.py` and `QMAP_Exploratory_Benchmark.py`, or confirm they are lost | They were never in the ZIP received; needed only to reproduce Deliverable 1 and the benchmark (00 v1.10 §3.2) | Before any reproduction check |
| Verify the ±15% occurrences in the Data Manager, starting with those you need. CONCOR has eight: 26-May-04, 27-May-04, 15-May-06, **31-Jan-08**, 06-Sep-13, **20-Mar-20**, **10-Aug-20**, 04-Jun-24 (bold: newly identified on 12-Nov-26). INFY has eight: **08-Aug-00, 11-Apr-01, 18-Apr-01, 10-Apr-03**, 24-Oct-03, **11-Jan-13, 12-Apr-13, 22-Oct-19** (bold: newly identified on 12-Nov-26). Also NIFTYIT 28-May-04. **04-Jun-24 matters most:** until it is verified, CONCOR has no current EMA result. | Each blocks long-window calculations until you mark it `VERIFIED_OK` (G-03). Blocked periods: document 13 §4 (CONCOR) and §6 (INFY). | In the Data Manager, during M1b/M3 |
| ~~Send the INFY daily Parquet~~ — **done** (received and verified 12-Nov-26; document 13 v1.2) | — | — |
| Optional: an NSE holiday list as a CSV, with its official source | Turns completeness from provisional to official for those years | Any time |
| Optional: the current Nifty 50 constituent list | Group A of the pilot | Before the pilot list is proposed |
| Confirm the CAS days and special sessions shown in the Data Manager | Existing D-06 process; includes 01-Feb-25 and 01-Feb-26 | During M1a |

---

## 5. All open items — one table

| # | ID | Decision needed | Why | Needed by | If undecided |
|---|---|---|---|---|---|
| 1 | GATE-0 | Approve package v1.10 as Claude 1's baseline | Required before any coding or repository work | Before M1a | Nothing is built |
| 2 | OD-12 | May M3 start before M1c while M1c is blocked? | The approved sequence places M3 after M1c, which waits for G-01 | When M2 is complete | M3 waits for M1c |
| 3 | D-EMA-11 | No EMA score when a stock's data ends before the analysis date? | Behaviour not defined by the approved methodology | Before M3 | M3 cannot start (behaviour undefined) |
| 4 | D-EMA-12 | Round to 6 dp before comparisons; store the score to 2 dp? | Floating-point drift breaks exact ties (document 13) | Before M3 | M3 cannot pass T-EMA-10 |
| 5 | G-11 | Second (and third) scanner | A combined score needs two scanners | Before M4 | M4, M5 and the Day 7 target wait |
| 6 | G-10 | First combined profile and weights, including the EMA weight | The weight was deferred when the EMA was approved | Before M5 | M5 waits |
| 7 | G-01 | Authorise the inventory script (no question now) | V-04 and the pilot need it | Before M1c | M1c stays blocked (and M3 too, unless OD-12 is approved) |
| 8 | OD-10 | Build M2 before M1b (optional proposal, not adopted) | Earlier data access | After M1a | Approved sequence applies |
| 9 | P-01 | Open-only moves non-blocking for close-based scanners (optional proposal, not adopted) | Historical EMA availability | Optional | Your G-03 rule applies unchanged |

**Recommended answers:** GATE-0 yes (after ChatGPT's review); OD-12 yes; D-EMA-11 yes; D-EMA-12 yes; G-11 Breakout Analysis on daily stocks; G-10 EMA and the second scanner at 50 / 50; OD-10 and P-01 — no change needed.

*End of document 12, v1.5.*
