# Q-MAP — Claude 1 Session Handover (14 Nov 26)

**For the next Claude 1 session.** Read `CLAUDE.md`, then the Consolidated
Handover v1.0 (docs/handover), then this. The Owner has explicitly authorised
Q-3 (production implementation); do not report it as pending.

## Done (branch `claude/elegant-pasteur-9dlxgw`, 3 commits, pushed)

- **Gate 0:** `requirements.txt` pins — duckdb==1.5.6, pandas==2.3.3,
  pyarrow==26.0.1, openpyxl==3.1.5 (duckdb kept below 2.0.0 per 08 §6).
  T-ENV-01 script: `tests/t_env_01_environment_check.py` (writes EV-12).
- **M1a:** full `qmap_database` package — 11-table catalogue, readers R1–R4
  (TC-26), session/record/completeness classification, validation and
  quarantine, generation commit protocol, derived calendar (G-02), Excel
  report, EV-01–EV-04 export, Data Manager GUI. All source-verified counts
  match exactly (T-SES-06/09, 17 G-03 issues, ACC-02/04/06/08).
- **M1b:** incremental update (G-09, G-16), held revisions with evidence and
  uniform-factor candidate test, approve/reject, failure injection actually
  run (T-MNT-06a–c, T-MNT-17a/17b on the byte-exact R3 fixtures), T-BKP-01
  restore, retention, Owner confirmations + REVALIDATE (ACC-03 state exact).
- **M2:** `access.py` (ten functions, interface 1.1 + rulings S-1–S-6,
  T-DA-12) and `aggregation.py`. **ACC-01: zero differences at all five
  timeframes** (55,648/33,414/11,180/448 matched; 21 months Feb-25–Oct-26
  per Q-1). ACC-07 = 16 of 67. DA-1–DA-24 pass. EV-05–EV-10 export; EV-09 =
  the 38 reference incomplete bars. IDLE demo: `apps/QMAP_M2_Example.py`.
- **Tests: 136, 0 failures, 0 skips** (`tests/run_all_tests.py`), run on the
  pins but under Python 3.13 in the dev container — per G-15 the Owner's
  3.12.10 IDLE runs are the milestone evidence.

## Left to do

- **Owner:** T-ENV-01 + suite on his PC; E2E-01 (Initial load of the 5
  source files), E2E-02 (Update), ACC-10 timing; confirm CAS rules and the 4
  special sessions; verify each ±15% occurrence (CONCOR 04-Jun-24 blocks the
  CONCOR EMA). A consolidated decision request is pending with the Owner:
  OD-12 / D-EMA-11 / D-EMA-12 (gate M3), G-01 (gates M1c), G-11 (M4),
  G-10 (M5). No PR opened yet (needs ChatGPT review before merge).
- **M3** (start when OD-12, D-EMA-11, D-EMA-12 are decided): engine core
  (`qmap_engine`: contract/registry/runner/output), EMA scanner per doc 10
  D-EMA-01–10, minimal Analysis Runner, T-SCC/T-EMA tests; copy the spec to
  `docs/scanners/`. Then **M6** (full Analysis Runner, Excel report), **M4**
  (after G-11), **M5** (after G-10). **M1c** after G-01 + V-04 + pilot-list
  approval.
- **Loose ends to close:** T-CAL-03 and the completeness-basis switch to
  OFFICIAL_CALENDAR after provenance (wire into REVALIDATE before the Owner
  supplies a calendar file); EV-11 CSV assembly for the M1b evidence pack;
  two documented choices awaiting ChatGPT review — the ±50% close move maps
  to LEVEL_BREAK_UNVERIFIED, and `maintenance_run.status` values (X-5);
  Q-1/Q-2 implemented per the verification package's interim positions.
