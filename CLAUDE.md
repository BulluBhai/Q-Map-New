# Q-MAP — Instructions for Claude Code

## 1. Role and authority

Act as the Q-MAP implementation agent (Claude 1) and follow the approved repository documents. The Project Owner is the final decision-maker. ChatGPT is the architecture, technical-review and milestone-evidence reviewer.

These instructions are operational guidance. They do not override the approved documents or grant permission to start implementation.

## 2. Authorisation status and current baseline

The Project Owner has approved Design Package v1.10. Approval of a design is **not** by itself authorisation to implement it; every milestone still needs its own prerequisites and Owner decisions.

- **Q-3 — explicit Owner authorisation: GIVEN.** The Owner authorised Claude 1 to implement, and on 14-Nov-26 directed the M1a–M3 work, the G-01 inventory and the laptop-readiness work listed below. Do not infer authorisation for anything further from repository access, an approved design, a prior chat or a request to review the repository.
- **Gate 0:** the files are prepared (root `requirements.txt` with exact `==` pins for `duckdb`, `pandas`, `pyarrow` and `openpyxl`; the IDLE-friendly T-ENV-01 script `tests/t_env_01_environment_check.py`; the installer `tools/QMAP_Install_Requirements.py`). **Gate 0 acceptance is still outstanding:** the Owner must run T-ENV-01 in IDLE on the Owner's PC; `duckdb`, `pandas`, `pyarrow`, `openpyxl` and `tkinter` must import; the printed versions must match `requirements.txt`; the EV-12 evidence (`EV12_environment_<ts>.txt` plus `requirements.txt`) must be produced; and the Owner must confirm the printout came from the Owner's PC. Until then no milestone is accepted (G-15).

### Current implementation baseline (`main` at `6f3d0c3cdf861f2ad5129dcb14202c6df111b80e`)

| PR | Merge commit | Content |
|---|---|---|
| #7 | `10d125975d04f19ab59f31460c06acaac1fa3f65` | Gate 0 files, M1a, M1b, M2 (`QMapData` interface and timeframe aggregation), V-VOL-01 row-level volume correction |
| #8 | `a6b7f180e02f6171e081717f7b54546ee5e71d66` | Data Manager G-03 verification (`VERIFIED_OK` preserved on unchanged reprocessing), data-summary export, IDLE installer, M2 example for every timeframe |
| #10 | `15985070cd0676aecb21e3064feb198b31a9c2c2` | M3 EMA Trend Alignment scanner v0.9.0, engine contract, registry, run coordinator, JSON/Excel output |
| #9 | `001e03a5ee1a03527b595876b2d4f0beaee92e9c` | G-01 read-only Stock Universe Inventory tool |
| #11 | `6f3d0c3cdf861f2ad5129dcb14202c6df111b80e` | Owner's User Guide v1.0 (`docs/user_guides/`) |

Full test runs: 181 tests, 0 failures, 0 errors, 0 skipped on the PR #9 branch (tree identical to `main` after PR #9), and 181 tests with 1 intermittent failure (T-MNT-10, see the open defect below) on `main` at `6f3d0c3`. Both were on **Linux** with Python 3.12.10 and the exact pins. This is development evidence only. **No test has been run on Windows yet.**

### Outstanding

- **D-EMA-11 and D-EMA-12 are proposals, not approved.** The scanner applies them provisionally, labels every result and stays below version 1.0.0. Never treat them as approved without the Owner's decision.
- **M1c** is blocked until the Owner runs the inventory on the local stock folder, the inventory is reviewed (V-04) and the Owner approves the actual pilot list.
- **M4** is not implemented and not approved for development (needs G-11). **M5** is not implemented (needs the approved scoring profile and weights, G-10).
- ORB backtesting is future work. Broker connectivity, automatic trading, cloud synchronisation and AI interpretation are not available and must not be represented as available.
- Owner actions: Windows testing, T-ENV-01/EV-12, verification of each ±15% occurrence (G-03), CAS and special-session confirmations.
- **Fixed (backup-name PR):** catalogue backup names used to collide when two maintenance runs started within the same second, overwriting an earlier backup and making T-MNT-10 fail intermittently. Backups are now created only through `storage.create_catalogue_backup` (a `_002`, `_003`... suffix within one second) and ordered chronologically by `storage.catalogue_backup_sort_key` for retention. Do not weaken T-MNT-10 or `tests/test_catalogue_backups.py`.

## 3. Read the authoritative documents before acting

At the start of a new session, read this file and `README.md`, then consult the repository documents relevant to the task. Before implementation work, read at least:

1. `docs/blueprints/Q-MAP_Human_Readable_Blueprint_v1.docx`.
2. `docs/blueprints/Q-MAP_Technical_Blueprint_v1.md`.
3. `docs/design/Q-MAP_00_Design_Package_Master_Index_v1.10_12_Nov_26_072336.md`.
4. `docs/handover/Q-MAP_Claude1_Consolidated_Handover_v1.0_12_Nov_26_124620.md` in full, including Annex A and Annex B.
5. The current-version design documents and the v1.2 verification package/workbook that apply to the authorised milestone.
6. `docs/handover/Q-MAP_Claude2_Closeout_Report_12_Nov_26_124620.md` and the Owner Decision Register when checking outstanding decisions or responsibilities.
7. `docs/user_guides/Q-MAP_Owners_User_Guide_v1.0_14_Nov_26.md` whenever a change affects what the Owner sees or does. Keep the guide consistent with the applications; a change to a screen, prompt, file name or behaviour needs a matching guide update.

Do not rely on old chat context or stale copies of documents. The repository copy is the working reference. Preserve the supplied source documents unchanged. Never use, copy, inspect for implementation reuse, or rely on `old-Q-MAP-ignore` or any earlier Q-MAP repository/codebase. This is a fresh project and repository.

## 4. Document precedence and conflict handling

When documents disagree, use this authority order:

1. Human-Readable Blueprint v1.0.
2. Technical Blueprint v1.0.
3. Project Owner decisions, including later Owner instructions recorded through ChatGPT and the corrections in Consolidated Handover Annex A.
4. ChatGPT technical rulings S-1 to S-6 and T-DA-12, as recorded in the Consolidated Handover.
5. Design Package v1.10.
6. Consolidated Handover and Independent Verification Package v1.2, which interpret the higher-authority material and must not contradict it.

The Design Package Master Index identifies current document versions. Use the current versions in this repository. Where Consolidated Handover Annex A explicitly marks a v1.10 statement as outdated, follow Annex A. For any other conflict, ambiguity, missing decision or apparent contradiction:

- Do not choose an interpretation silently.
- Do not alter an approved requirement to make implementation easier.
- Record the exact documents/sections involved, the impact and the smallest decision needed.
- Raise it with ChatGPT and the Project Owner, and wait where the issue blocks the work.

## 5. Scope and milestone controls

- Implement **P1 only**, and only work that the Owner has authorised (section 2).
- P2/P3 items, future ideas and examples are not implementation authorisation.
- Follow the approved sequence: `M1a → M1b → M2 → M1c → M3 → M4 → M5`. M6 follows M3; combined-score output portions follow M5.
- OD-10 (M2 before M1b) is not adopted. Do not change the approved sequence without an explicit Owner decision.
- M1c remains blocked until the V-04 inventory has been run by the Owner on the local stock folder (G-01 is authorised and the tool is merged), the results are reviewed, and the Owner approves the actual pilot list.
- M3 is implemented provisionally on the Owner's instruction of 14-Nov-26 while M1c is blocked. It cannot be accepted until D-EMA-11 and D-EMA-12 are decided and Gate 0 is accepted.
- M4 requires the Owner's scanner selection (G-11). M5 requires the approved scoring profile and weights (G-10).
- Never start a milestone because its design document exists. Check its readiness conditions and required Owner decisions first.

## 6. Non-negotiable architecture and technology boundaries

Follow the current approved technical blueprint and Design Package v1.10 as corrected by the Consolidated Handover.

- Initial environment: local, offline, single-user Windows PC; Python **3.12.10**.
- Storage: Parquet. Querying and the single catalogue store: DuckDB. Do not introduce SQLite or a second metadata store.
- Keep the database subsystem (`qmap_database`) separate from the analytical subsystem (`qmap_engine`, `qmap_scanners`).
- The database subsystem owns discovery/import, storage organisation, catalogue, validation, maintenance and data retrieval.
- The analytical engine must use the approved common read-only `QMapData` interface (through the approved context/fetch contract). It must not read Parquet files, storage folders or database internals directly.
- Keep scanner modules independent and deterministic. Do not introduce a plug-in or automatic-discovery framework.
- Aggregation must follow the approved OHLCV, IST, exchange-session, holiday, gap and incomplete-interval rules. Preserve 1-minute source records. Do not precompute timeframes in P1.
- The analytical engine must work without AI. No AI API calls, cloud, remote services, servers or trading/execution integration in P1.
- Do not fabricate fields, candles or prices. Do not silently repair, interpolate, fill or auto-adjust historical data. Do not import indicator columns.
- Historical source revisions are held for Owner review; never apply a revision automatically.
- Apply the approved validation, issue, continuity and source-conflict rules. In particular, G-03 continuity-blocking ±15% issues and G-16 SHA-256 duplicate/source-conflict handling must not be weakened.
- **Auction-volume safeguards (Consolidated Handover §8.5 and R-5):** keep auction records separate; never add auction volume to daily volume; preserve auction-volume values exactly as supplied; never infer, copy, correct, fill or de-duplicate any volume; retain `VOLUME_SEMANTICS_UNVERIFIED`, `VOLUME_EXCLUDES_AUCTION`, `DAILY_VOLUME_EXCLUDES_AUCTION` and the specified `volume_complete` status/warnings; do not build logic on the unconfirmed meaning of auction-volume patterns.
- **Session safeguards:** an observed record shape must never create a `SPECIAL` session. Use only the approved authoritative sources and confirmation rules for session status. Do not treat derived calendar rows or weekend shapes as confirmation.
- **Tick-size safeguard (G-04):** quarantine an off-tick row only when the applicable tick rule is verified and supported by evidence/effective dates. Otherwise retain the row with `OFF_TICK_RULE_UNVERIFIED`; do not guess a tick rule.
- Do not add dependencies, architecture layers, caches, background services or features without a specific approved requirement.

## 7. Dependencies and environment

- Use the Owner's Python 3.12.10 environment.
- The approved third-party package set is `duckdb`, `pandas`, `pyarrow` and `openpyxl`, pinned exactly in `requirements.txt` (duckdb 1.5.6, pandas 2.3.3, pyarrow 26.0.1, openpyxl 3.1.5). `numpy` and other transitive dependencies are installed by pip and are not pinned; pinning them would need the Owner's approval.
- Use the approved standard-library modules where needed. Do not add third-party packages without the Owner's approval and an explicit design justification.
- Tests run only against the exact pinned versions. Results from a different Python or package version are not acceptance evidence.
- `requirements.txt` is at the repository root. Do not change a pin or add a package without the Owner's approval. The Owner's IDLE T-ENV-01 run and EV-12 confirmation are required to close Gate 0.

## 8. Data handling, sample fixtures and repository hygiene

- The Owner-selected live data root must remain outside the repository.
- The only approved market-data exception is the following exact 12-file set under `tests/fixtures/source_samples/`. The Project Owner has explicitly approved these public data files for public distribution. No wildcard or extension-based expansion of this list is permitted:
  - `Nifty_1min_09Jan25-06Nov26.parquet`
  - `NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet`
  - `NSE_BANKNIFTY_1.csv`
  - `CONCOR.txt`
  - `CONCOR_daily 26Nov98-06Nov26.parquet`
  - `INFY_daily 02Jan98-06Nov26.parquet`
  - `Nifty IT.txt`
  - `Nifty_3min_02Jan23-30Oct26.parquet`
  - `Nifty_5min_02Jan23-30Oct26.parquet`
  - `Nifty_15min_02Jan23-30Oct26.parquet`
  - `Nifty_daily_02Jan23-30Oct26.parquet`
  - `Nifty_monthly_02Jan23-30Oct26.parquet`
- `INFY.txt` was never supplied and is not approved. Preserve approved fixture filenames and contents exactly. Tests must read fixtures in place or use a temporary copy; never modify the originals. Verify fixture SHA-256 values against Annex B of the Consolidated Handover.
- Do not commit production/full-universe market data, live DuckDB files or journals, backups, logs, generated reports, scanner run outputs, inventory workbooks, `EV12_environment_*.txt` files or evidence exports.
- The applications save local settings (including the Owner's data-root path) in `config/settings.json` inside the program folder. That file is local to each PC and must never be committed.
- Evidence exports are submitted to ChatGPT with milestone evidence; they do not belong in the repository.
- Machine-readable evidence timestamps must use `YYYY-MM-DD HH:MM:SS` as IST wall-clock time, with no UTC conversion or offset, as approved by the Owner.
- Never commit passwords, API keys, tokens, `.env` files, private keys, credentials or confidential information. This repository is public.
- `.gitignore` is not a substitute for checking the staged change. Inspect the complete file list before every commit and pull request.

## 9. Coding and testing standards

When implementation is authorised:

- Use clear names that state purpose; keep each function focused on one task.
- Add comments to explain why a non-obvious choice is made, not to restate the code.
- Organise each file as: Imports → Constants → Helpers → Main logic → Execution.
- Handle errors explicitly and visibly. Do not silently swallow exceptions or report partial success as complete.
- Make small, focused changes. Do not add unrequested files or refactor unrelated modules.
- Keep calculations deterministic and reproducible. Preserve full precision in stored results where the specifications require it; apply display rounding only as specified.
- Use the approved `unittest` approach and test catalogue. Add or update focused tests for changed behaviour, plus relevant regression tests.
- Run tests on the exact pinned environment with `python tests/run_all_tests.py` (it prints the environment and flags any mismatch). State exactly which tests were executed, the Python version and the operating system, and the results. Never claim a test passed if it was not run on the implementation, and never present Linux results as Windows validation.
- A program that starts or passes unit tests is not sufficient. Compare required calculations against the independently verified reference results and provide the specified evidence.
- Do not modify original fixtures or source data during tests.

## 10. Git and pull-request governance

- Never commit directly to `main`, bypass branch protection, force-push, or change repository security/ruleset settings.
- Make work on a dedicated, short-lived feature/fix branch created from the latest `main`.
- Keep each pull request focused on one approved task or milestone. Do not bundle unrelated work.
- Before opening a pull request, inspect the full diff and confirm that only intended files changed and no secrets, production data, generated outputs or temporary files are included.
- A pull request must state: purpose, scope, files changed, tests actually run, evidence supplied, known limitations and any unresolved decision.
- Do not merge your own pull request automatically. Wait for ChatGPT's review and the Project Owner's explicit acceptance/merge direction. Use **Squash and merge** as the normal method unless the Owner says otherwise.
- For the initial `README.md`, `CLAUDE.md` and `.gitignore` change, an independent second-AI review is mandatory before merge, in addition to ChatGPT review and Owner approval.
- Never alter or delete approved project documents without explicit Owner instruction. Preserve original filenames and versions; propose a new version rather than silently replacing an approved baseline.

## 11. Roles and reporting

- **Project Owner:** final authority for project scope, decisions, implementation authorisation, exceptions and milestone acceptance.
- **Claude Code / Claude 1:** implements only authorised work and supplies reproducible code, tests and evidence.
- **ChatGPT:** reviews architecture, code, tests and milestone evidence; identifies defects and conflicts; provides corrective instructions. ChatGPT's review does not replace Owner approval.
- **Claude 2:** its assigned groundwork is closed and it is inactive for routine development; re-engage only for a specific exceptional offline investigation.

Report progress factually. Separate completed work, pending work, test results, assumptions and blockers. If evidence is missing, say so; do not infer success.
