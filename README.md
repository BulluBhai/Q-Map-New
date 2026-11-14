# Q-MAP — Quantitative Market Analytics Platform

**Repository:** [`BulluBhai/Q-Map-New`](https://github.com/BulluBhai/Q-Map-New)  
**Default branch:** `main`  
**Visibility:** Public

Q-MAP is a modular, single-user market-data and technical-analysis platform. Its purpose is to maintain a reliable local market-data foundation and provide independent analytical scanners with transparent, reproducible results.

This repository holds both the authoritative project reference (approved blueprints, detailed design documents, independent verification material, implementation handover and development governance) and the implemented Q-MAP code. The presence of a design document does not by itself authorise implementing it: each milestone still needs its stated prerequisites and Owner decisions.

**Using Q-MAP:** start with the [Owner's User Guide v1.0](docs/user_guides/Q-MAP_Owners_User_Guide_v1.0_14_Nov_26.md). It explains installation from IDLE, the environment check, the Data Manager, the M2 example, the Universe Inventory and the EMA Scanner.

> **Important — public repository:** Repository contents are visible to anyone. Do not commit passwords, API keys, tokens, personal information, confidential material, production market-data archives, live databases or backups. Public users may fork the repository and propose changes, but only users and integrations with repository write access can push directly to it. All changes intended for `main` must follow the pull-request process below.

## Current project status

Status as of 14 November 2026, `main` at `6f3d0c3cdf861f2ad5129dcb14202c6df111b80e`. The historical close-out position of 12 November 2026 (Q-3 pending, no code written) is superseded: the Owner authorised implementation and the work below has been merged.

### Implemented and merged

| Pull request | Merge commit | What it delivered |
|---|---|---|
| #7 | `10d125975d04f19ab59f31460c06acaac1fa3f65` | Gate 0 files (`requirements.txt` with exact pins; T-ENV-01 environment check), M1a database foundation and initial load, M1b incremental maintenance / held revisions / generations / backup and restore, M2 `QMapData` data-access interface and timeframe aggregation, and the V-VOL-01 row-level volume correction |
| #8 | `a6b7f180e02f6171e081717f7b54546ee5e71d66` | Data Manager readiness: Owner verification of G-03 continuity issues (`VERIFIED_OK`, preserved when unchanged data is processed again), data-summary export, IDLE package installer, M2 example covering every timeframe |
| #10 | `15985070cd0676aecb21e3064feb198b31a9c2c2` | M3 EMA Trend Alignment scanner (version 0.9.0) with the analytical engine contract, registry, run coordinator and JSON/Excel output |
| #9 | `001e03a5ee1a03527b595876b2d4f0beaee92e9c` | G-01 read-only Stock Universe Inventory tool |
| #11 | `6f3d0c3cdf861f2ad5129dcb14202c6df111b80e` | Owner's User Guide v1.0 (documentation only) |

### Testing status

- The complete test suite (`tests/run_all_tests.py`, `unittest`) last ran on the updated PR #9 branch, whose tree is identical to `main` after PR #9: **181 tests, 0 failures, 0 errors, 0 skipped**. Environment: **Linux**, Python 3.12.10, duckdb 1.5.6, pandas 2.3.3, pyarrow 26.0.1, openpyxl 3.1.5. PR #11 changed documentation only.
- These are development-environment results. Under G-15 they are **not** milestone evidence.
- **Windows testing on the Owner's PC is still outstanding**, including the T-ENV-01 run in IDLE and EV-12 confirmation (which closes Gate 0), and the end-to-end application checks.

### Outstanding decisions and work

- **D-EMA-11** (stale data) and **D-EMA-12** (numeric precision) are proposals awaiting the Owner's decision. The EMA scanner applies them provisionally and labels every result as provisional; they are not approved.
- **M1c** (pilot load) needs the Owner's run of the Universe Inventory on the local stock folder and the Owner's approval of the actual pilot list.
- **M4** (second scanner) is not implemented and not approved for development; it needs the Owner's scanner selection (G-11).
- **M5** (combined scoring) is not implemented; it needs the Owner's approved scoring profile and weights (G-10).
- The Owner's individual verification of each ±15% occurrence (G-03), CAS and special-session confirmations remain Owner actions.

### Not available

ORB backtesting is future work. There is no broker connectivity, automatic trading or order placement, no cloud synchronisation and no AI interpretation in the current application. None of these may be represented as available.

## Approved project direction

The approved initial direction is:

- Local, offline, single-user operation on the Owner's Windows PC.
- Python **3.12.10**, with third-party dependencies pinned to exact versions at Gate 0.
- Parquet for canonical market-data storage and DuckDB for querying and the catalogue.
- Two separately maintained components: the Q-MAP Database and the Q-MAP Analytical Engine.
- Analytical modules obtain data only through the approved common data-access interface; scanners must not manipulate storage files directly.
- Independent, deterministic scanners and transparent calculations. The analytical engine must work without an AI service.
- A simple Windows-friendly user interface, following the approved GUI requirements.

P1 is the current implementation scope. P2 and P3 are deferred and are not permission to build. Cloud infrastructure, remote APIs, AI integration, servers, plug-in frameworks, SQLite or a second metadata store, precomputed timeframes and other deferred capabilities must not be introduced unless separately approved.

## Repository map

```text
Q-Map-New/
├── README.md
├── CLAUDE.md
├── .gitignore
├── requirements.txt          exact pins for duckdb, pandas, pyarrow, openpyxl
├── apps/                     IDLE applications (F5)
│   ├── QMAP_Data_Manager.py      import, update, validation, decisions, backup/restore
│   ├── QMAP_M2_Example.py        read-only data-access and timeframe demonstration
│   └── QMAP_EMA_Scanner.py       EMA Trend Alignment scanner (provisional)
├── qmap_database/            database subsystem: readers, standardisation, validation,
│                             storage, catalogue, maintenance, QMapData access interface
├── qmap_engine/              analytical engine: contract, registry, runner, output
├── qmap_scanners/            independent scanner modules (ema_trend_alignment)
├── tools/
│   ├── QMAP_Install_Requirements.py   installs the exact pins from IDLE
│   └── QMAP_Universe_Inventory.py     read-only stock-folder inventory (G-01)
├── docs/
│   ├── blueprints/
│   ├── design/
│   ├── verification/
│   ├── handover/
│   └── user_guides/
└── tests/
    ├── run_all_tests.py, t_env_01_environment_check.py, test_*.py
    └── fixtures/
        └── source_samples/
            └── [12 approved sample files]
```

The database subsystem (`qmap_database`) and the analytical subsystem (`qmap_engine`, `qmap_scanners`) are separate. Scanners obtain data only through the read-only `QMapData` interface and never read Parquet files, storage folders or the catalogue directly. The Owner has approved the 12 sample files for public distribution and test use; they are committed under `tests/fixtures/source_samples/` with their original filenames and contents. Do not create empty or speculative folders.

### `docs/user_guides/` — how to use the current applications

- [Owner's User Guide v1.0](docs/user_guides/Q-MAP_Owners_User_Guide_v1.0_14_Nov_26.md) — installation, environment check and use of every current application.

### `docs/blueprints/` — what the project is and its technical direction

- [Human-Readable Blueprint v1.0](docs/blueprints/Q-MAP_Human_Readable_Blueprint_v1.docx) — governs project scope and business intent.
- [Technical Blueprint v1.0](docs/blueprints/Q-MAP_Technical_Blueprint_v1.md) — translates the approved intent into technical direction.

### `docs/design/` — detailed design and decisions

- [Design Package Master Index v1.10](docs/design/Q-MAP_00_Design_Package_Master_Index_v1.10_12_Nov_26_072336.md) — master contents list, version register and package guide.
- [Data Inventory and Quality Report v1.4](docs/design/Q-MAP_01_Data_Inventory_and_Quality_Report_v1.4_12_Nov_26_072336.md) and [Data Inventory Workbook v1.1](docs/design/Q-MAP_Data_Inventory_Workbook_v1.1_11_Nov_26_183420.xlsx) — inspected source-data findings.
- [Database and Catalogue Architecture v1.6](docs/design/Q-MAP_02_Database_and_Catalogue_Architecture_v1.6_12_Nov_26_072336.md) — storage, catalogue, import, validation, maintenance, generations and backup.
- [Data Access and Timeframe Aggregation Specification v1.2](docs/design/Q-MAP_03_Data_Access_and_Timeframe_Aggregation_Specification_v1.2_11_Nov_26_225736.md) — common data interface and aggregation rules.
- [Analytical Engine and Scanner Architecture v1.3](docs/design/Q-MAP_04_Analytical_Engine_and_Scanner_Architecture_v1.3_11_Nov_26_232056.md) — engine and scanner contracts.
- [Combined Scoring and Output Design v1.1](docs/design/Q-MAP_05_Combined_Scoring_and_Output_Design_v1.1_11_Nov_26_225736.md) — score and output requirements.
- [Testing and Validation Strategy v1.5](docs/design/Q-MAP_06_Testing_and_Validation_Strategy_v1.5_12_Nov_26_072336.md) — test catalogue and acceptance approach.
- [Decision and Future Ideas Register v1.6](docs/design/Q-MAP_07_Decision_and_Future_Ideas_Register_v1.6_12_Nov_26_072336.md) — recorded decisions, open matters and deferred ideas.
- [Claude 1 Implementation Handover v1.7](docs/design/Q-MAP_08_Claude1_Implementation_Handover_v1.7_12_Nov_26_072336.md) and [Implementation Readiness Checklist v1.7](docs/design/Q-MAP_11_Claude1_Implementation_Readiness_Checklist_v1.7_12_Nov_26_072336.md) — milestone specifications and readiness criteria.
- [Stock Universe Inventory and Pilot Selection v1.6](docs/design/Q-MAP_09_Stock_Universe_Inventory_and_Pilot_Selection_v1.6_12_Nov_26_072336.md) — pilot/universe requirements and the inventory specification (the G-01 inventory tool has since been authorised and implemented).
- [EMA Scanner Design Proposal v1.7](docs/design/Q-MAP_10_EMA_Scanner_Design_Proposal_v1.7_12_Nov_26_072336.md) and [EMA Reference Verification Evidence v1.2](docs/design/Q-MAP_13_EMA_Reference_Verification_Evidence_v1.2_12_Nov_26_072336.md) — EMA design and source-verification evidence.
- [Owner Decision Register v1.5](docs/design/Q-MAP_12_Owner_Decision_Register_v1.5_12_Nov_26_072336.md) — decisions reserved for the Project Owner.
- [ChatGPT Handover Note v2.4](docs/design/Q-MAP_ChatGPT_Handover_Note_v2.4_12_Nov_26_072336.md) and [Claude 2 v1.10 Completion Report](docs/design/Q-MAP_Claude2_v1.10_Completion_Report_12_Nov_26_072336.md) — review and completion context.

### `docs/verification/` — expected results and independent evidence

- [Independent Verification Package v1.2](docs/verification/Q-MAP_Independent_Verification_Package_v1.2_12_Nov_26_124620.md)
- [Independent Reference Results v1.2](docs/verification/Q-MAP_Independent_Reference_Results_v1.2_12_Nov_26_124620.xlsx)

These materials specify expected results and evidence requirements. They are not themselves evidence that implementation tests have been run or passed; that evidence is recorded in each pull request.

### `docs/handover/` — implementation entry point and close-out

- [Consolidated Claude 1 Handover v1.0](docs/handover/Q-MAP_Claude1_Consolidated_Handover_v1.0_12_Nov_26_124620.md) — the single implementation handover for Gate 0, M1a, M1b and M2. Its Annex A identifies corrections and clarifications to outdated statements in Design Package v1.10.
- [Claude 2 Closeout Report](docs/handover/Q-MAP_Claude2_Closeout_Report_12_Nov_26_124620.md) — final groundwork status and outstanding responsibilities.
- [Final Handover Set Index](docs/handover/00_INDEX_Q-MAP_Claude2_Final_Handover_Set_12_Nov_26_124620.md) — index of the handover package and file provenance.
- [Claude 1 Session Handover 14-Nov-26](docs/handover/Q-MAP_Claude1_Session_Handover_14_Nov_26.md) — session note written after M2. It predates PRs #8 to #11; the status section above is current.

## Document authority

When project documents disagree, apply the following order from the Consolidated Handover:

1. Human-Readable Blueprint v1.0.
2. Technical Blueprint v1.0.
3. Project Owner decisions, including later Owner instructions recorded through ChatGPT and Annex A of the Consolidated Handover.
4. ChatGPT technical rulings S-1 to S-6 and T-DA-12, as recorded in the Consolidated Handover.
5. Design Package v1.10.
6. Consolidated Handover and Independent Verification Package v1.2, which interpret the higher-authority material and must not contradict it.

The Design Package Master Index identifies the current version of each design document. **Use the current version actually stored in this repository, not older version numbers quoted in historical passages.** Where the Consolidated Handover Annex A marks a Design Package v1.10 statement as outdated, follow the correction in Annex A. Do not silently resolve any other conflict; raise it with ChatGPT and the Project Owner.

## Data and security rules

- The live data root must be selected by the Owner and kept **outside this repository**.
- Do not commit production or full-universe market data, live DuckDB databases, database journals, backups, generated logs, reports, scanner outputs or evidence exports.
- The Owner has explicitly approved public distribution of the following 12 historical sample files for test use under `tests/fixtures/source_samples/` only. Preserve their original filenames and contents. Tests must treat them as read-only. No other market-data files are permitted by this exception:
  1. `Nifty_1min_09Jan25-06Nov26.parquet`
  2. `NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet`
  3. `NSE_BANKNIFTY_1.csv`
  4. `CONCOR.txt`
  5. `CONCOR_daily 26Nov98-06Nov26.parquet`
  6. `INFY_daily 02Jan98-06Nov26.parquet`
  7. `Nifty IT.txt`
  8. `Nifty_3min_02Jan23-30Oct26.parquet`
  9. `Nifty_5min_02Jan23-30Oct26.parquet`
  10. `Nifty_15min_02Jan23-30Oct26.parquet`
  11. `Nifty_daily_02Jan23-30Oct26.parquet`
  12. `Nifty_monthly_02Jan23-30Oct26.parquet`
- `INFY.txt` was not supplied and is not an approved fixture. The approved sample fixtures are test inputs and reference/acceptance material, not the live database. Their SHA-256 fingerprints are recorded in Annex B of the Consolidated Handover; tests should assert those fingerprints.
- `.gitignore` is a safety aid, not a security boundary. Check staged files before every commit.
- Never commit credentials, tokens, passwords, private keys, `.env` files or confidential information.

## Development and review workflow

- Work on a dedicated feature or fix branch; never commit directly to `main`.
- Submit changes to `main` through a focused pull request.
- Include a clear summary, tests actually run, evidence and known limitations in the pull request.
- Use **Squash and merge** as the normal merge method unless the Project Owner directs otherwise.
- Do not merge automatically. Wait for the required review and the Project Owner's approval.
- For the three initial root guidance files (`README.md`, `CLAUDE.md` and `.gitignore`), an independent second-AI review is required before merge, in addition to ChatGPT's review and the Project Owner's approval.
- ChatGPT reviews Claude 1's implementation and milestone evidence. The Project Owner retains final authority over scope, decisions, implementation authorisation and milestone acceptance.

## Milestone sequence

The approved implementation order from the Consolidated Handover is:

`M1a → M1b → M2 → M1c → M3 → M4 → M5` (M6 follows M3; combined-score portions follow M5).

M1a, M1b and M2 are implemented (PR #7). M3 was implemented while M1c remains blocked, on the Owner's explicit instruction of 14-Nov-26, and stays provisional until D-EMA-11 and D-EMA-12 are decided (PR #10). Do not adopt the unapproved alternative sequence OD-10. Do not start a later milestone merely because its design exists. Each milestone has its own prerequisites and Owner decisions.

The root-level `requirements.txt` holds the exact Gate 0 package pins. Do not change them or add packages without the Owner's approval.

## Who does what

- **Project Owner:** final authority; approves scope, decisions, implementation start and milestone acceptance.
- **Claude Code / Claude 1:** implementation agent, but only within explicitly authorised milestones; supplies code, tests and required evidence.
- **ChatGPT:** architecture and technical review partner; independently reviews implementation, tests and evidence, and raises defects or conflicts.
- **Claude 2:** final groundwork is closed; re-engage only for a specific exceptional offline investigation.

---

This README is an orientation and navigation guide. The approved blueprints, decision records, design specifications, verification package and Consolidated Handover remain the controlling project documents.
