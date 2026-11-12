# Q-MAP — Quantitative Market Analytics Platform

**Repository:** [`BulluBhai/Q-Map-New`](https://github.com/BulluBhai/Q-Map-New)  
**Default branch:** `main`  
**Visibility:** Public

Q-MAP is a modular, single-user market-data and technical-analysis platform. Its purpose is to maintain a reliable local market-data foundation and provide independent analytical scanners with transparent, reproducible results.

This repository is the authoritative project reference for the approved blueprints, detailed design documents, independent verification material, implementation handover and development governance. The project is being established from approved documentation; the presence of design documents does not by itself authorise production implementation.

> **Important — public repository:** Repository contents are visible to anyone. Do not commit passwords, API keys, tokens, personal information, confidential material, production market-data archives, live databases or backups. Public users may fork the repository and propose changes, but only users and integrations with repository write access can push directly to it. All changes intended for `main` must follow the pull-request process below.

## Current project status

As recorded in the final handover material dated 12 November 2026:

- The Project Owner has approved Design Package v1.10.
- The Project Owner's separate authorisation for Claude 1 to begin production implementation (**Q-3**) is still pending.
- Technical Gate 0 checks, including exact dependency pins and the environment check, are still pending.
- No production Q-MAP application code had been written and no Q-MAP implementation tests had been executed at the time of that close-out.
- M1a, M1b and M2 are specified but must not begin until the Owner has authorised implementation and the applicable Gate 0 requirements are satisfied.
- M1c, M3, M4 and M5 remain subject to their stated prerequisites and Owner decisions. See the Consolidated Handover and the Owner Decision Register for the exact blockers.

**Do not interpret approval of the design package, repository creation or document upload as authorisation to code.** Only the Project Owner can provide Q-3. Q-3 authorises the Gate 0 preparation/checks; it does not waive Gate 0 acceptance or authorise M1a to start early. Gate 0 is complete only after the exact pins and T-ENV-01 are prepared, T-ENV-01 is run in IDLE on the Owner's PC, EV-12 is produced, and the Owner confirms the printout. M1a may start only after that confirmation.

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
├── docs/
│   ├── blueprints/
│   ├── design/
│   ├── verification/
│   └── handover/
└── tests/
    └── fixtures/
        └── source_samples/
            └── [12 approved sample files]/
```

The implementation, application and configuration folders, along with the root-level requirements.txt, will be created only when the relevant authorised milestone requires them. The sample fixture path shown above identifies the approved location; it does not authorise creating the folder or uploading the sample files before the relevant milestone. Do not create empty or speculative folders merely to fill out a software-project layout.

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
- [Stock Universe Inventory and Pilot Selection v1.6](docs/design/Q-MAP_09_Stock_Universe_Inventory_and_Pilot_Selection_v1.6_12_Nov_26_072336.md) — future pilot/universe requirements; does not authorise the G-01 inventory script.
- [EMA Scanner Design Proposal v1.7](docs/design/Q-MAP_10_EMA_Scanner_Design_Proposal_v1.7_12_Nov_26_072336.md) and [EMA Reference Verification Evidence v1.2](docs/design/Q-MAP_13_EMA_Reference_Verification_Evidence_v1.2_12_Nov_26_072336.md) — EMA design and source-verification evidence.
- [Owner Decision Register v1.5](docs/design/Q-MAP_12_Owner_Decision_Register_v1.5_12_Nov_26_072336.md) — decisions reserved for the Project Owner.
- [ChatGPT Handover Note v2.4](docs/design/Q-MAP_ChatGPT_Handover_Note_v2.4_12_Nov_26_072336.md) and [Claude 2 v1.10 Completion Report](docs/design/Q-MAP_Claude2_v1.10_Completion_Report_12_Nov_26_072336.md) — review and completion context.

### `docs/verification/` — expected results and independent evidence

- [Independent Verification Package v1.2](docs/verification/Q-MAP_Independent_Verification_Package_v1.2_12_Nov_26_124620.md)
- [Independent Reference Results v1.2](docs/verification/Q-MAP_Independent_Reference_Results_v1.2_12_Nov_26_124620.xlsx)

These materials specify expected results and evidence requirements. They are not evidence that implementation tests have already been run or passed.

### `docs/handover/` — implementation entry point and close-out

- [Consolidated Claude 1 Handover v1.0](docs/handover/Q-MAP_Claude1_Consolidated_Handover_v1.0_12_Nov_26_124620.md) — the single implementation handover for Gate 0, M1a, M1b and M2. Its Annex A identifies corrections and clarifications to outdated statements in Design Package v1.10.
- [Claude 2 Closeout Report](docs/handover/Q-MAP_Claude2_Closeout_Report_12_Nov_26_124620.md) — final groundwork status and outstanding responsibilities.
- [Final Handover Set Index](docs/handover/00_INDEX_Q-MAP_Claude2_Final_Handover_Set_12_Nov_26_124620.md) — index of the handover package and file provenance.

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

## First implementation steps — only after authorisation

Once the Owner has explicitly authorised Claude 1 to proceed, Gate 0 has been completed, and the Owner has accepted the Gate 0 evidence, follow the approved implementation order in the Consolidated Handover:

`M1a → M1b → M2 → M1c → M3 → M4 → M5` (M6 follows M3; combined-score portions follow M5).

Do not adopt the unapproved alternative sequence OD-10. Do not start a later milestone merely because its design exists. Each milestone has its own prerequisites and Owner decisions.

The root-level `requirements.txt` with exact package pins is to be prepared at Gate 0. Do not invent package versions before the Gate 0 process.

## Who does what

- **Project Owner:** final authority; approves scope, decisions, implementation start and milestone acceptance.
- **Claude Code / Claude 1:** implementation agent, but only within explicitly authorised milestones; supplies code, tests and required evidence.
- **ChatGPT:** architecture and technical review partner; independently reviews implementation, tests and evidence, and raises defects or conflicts.
- **Claude 2:** final groundwork is closed; re-engage only for a specific exceptional offline investigation.

---

This README is an orientation and navigation guide. The approved blueprints, decision records, design specifications, verification package and Consolidated Handover remain the controlling project documents.
