# Q-MAP

## Technical Blueprint & Implementation Reference

**Version 1.0 | 11 November 2026 | Fresh project handover**

# Document control and authority

| Field | Value |
| --- | --- |
| Document | Q-MAP Technical Blueprint v1.0 |
| Companion document | Q-MAP Human-Readable Blueprint v1.0 |
| Date | 11 November 2026 |
| Status | Initial handover baseline; detailed designs require approval before implementation. |
| Authority | The human-readable blueprint governs scope and business intent. This document translates it into technical direction. |
| Scope rule | P1 only is current implementation scope. P2/P3 are not authorisation to build. |

> **Implementation constraint**
>
> Do not implement deferred capabilities merely because they are mentioned here. Where a technical choice is not yet justified, mark it as a decision required and propose the simplest viable option.

# 1. System context and boundaries

Q-MAP comprises two independently maintainable components:

| Component | Responsibilities | Must not own |
| --- | --- | --- |
| Database subsystem | File discovery/import, storage organisation, metadata catalogue, validation, incremental maintenance, data retrieval. | Scanner calculations, market interpretations, scanner-specific rules. |
| Analytical subsystem | Scanner requirements, retrieval requests, calculations, scoring, output generation. | Direct manipulation of storage files, database maintenance, cloud synchronisation. |

Initial deployment is a single-user local Windows environment. The design should avoid assumptions that prevent future remote access, but must not introduce cloud infrastructure or distributed services in the initial release.

| Dataset ID (provisional) | Known source | Expected data | Schema status |
| --- | --- | --- | --- |
| NIFTY_1M | User-provided Parquet files | 1-minute OHLCV | Uninspected; verify actual schema. |
| BANKNIFTY_1M | User-provided Parquet files | 1-minute OHLCV | Uninspected; verify actual schema. |
| NIFTY_STOCKS_DAILY | User-provided text files | Daily close prices at minimum | Uninspected; determine whether OHLCV or close-only. |

The first implementation task is source inspection. Record filenames, file counts, file sizes, field names, data types, symbol representation, date/time range, timezone, row counts where practical, duplicate keys, nulls, and representative records. Do not define a rigid import schema until inspection is complete.

| Technology | Initial role | Decision |
| --- | --- | --- |
| Parquet | Primary storage for historical market data. | Use. |
| DuckDB | SQL query engine over Parquet; supports analytical retrieval. | Use. |
| SQLite | Possible metadata/configuration store. | Do not introduce initially unless a demonstrated requirement appears. |
| Cloud warehouse/service | Remote replica/query capability. | Future option only; provider not selected. |

Avoid unnecessary copies of large historical datasets. Prefer querying Parquet through DuckDB. Decide whether a DuckDB database file is needed for catalog metadata or other state after the catalogue design is specified; do not create parallel stores without a clear purpose.

The following is a logical starting model, not a mandate to create every table or column immediately.

| Logical entity | Purpose | Indicative attributes |
| --- | --- | --- |
| Dataset | One registered dataset or collection. | dataset_id, name, asset/index, timeframe, data_kind, source_format, storage_location, status. |
| Dataset coverage | Describe available records. | dataset_id, symbol, start_datetime, end_datetime, row_count if known, last_checked. |
| Field definition | Describe the fields actually present. | dataset_id, field_name, data_type, meaning, required flag. |
| Validation result | Record data-quality checks. | dataset_id, check_time, check_name, status, issue_count, report_location. |
| Update record | Track maintenance runs. | dataset_id, run_time, date_range_processed, status, records_added/changed where measurable. |

Keep the initial catalogue small. Do not add elaborate lineage, permissions, multi-tenant metadata or governance models for a local single-user system.

Analytical modules must retrieve data through a stable common interface. They must not read internal storage paths directly or embed DuckDB/Parquet file-management logic.

The detailed function signatures are to be defined in a separate API contract after the actual schemas and first scanner requirements are known. At minimum, the interface should support:

- List available datasets and their metadata.
- Check whether a dataset contains a requested symbol, field set, timeframe and date range.
- Retrieve records for a requested dataset/symbol/date range.
- Return clear information when data is unavailable, incomplete or missing required fields.
- Return data in a documented, consistent structure with timestamps and timezone semantics explicit.
> **Important boundary**
>
> The data-access interface is the seam between the two main components. Keep it stable and small. Database internals may change without requiring scanner code to know how storage works.

The catalogue should answer practical questions: what datasets exist, which symbols are present, what fields are available, which timeframes and date ranges are covered, and when data was last checked or updated.

Initial catalogue capabilities:

- Register or discover approved datasets.
- Describe actual fields and their types.
- Track symbol and date coverage where applicable.
- Track last validation/update status.
- Allow the analytical engine to check data availability before running.
Do not build a general metadata platform. Keep metadata definitions simple and extend them only when a real scanner or maintenance need arises.

- Use a controlled import/discovery process for the supplied source files.
- Preserve original source files unless a separately approved archival policy says otherwise.
- Do not silently coerce or fabricate missing fields.
- Record import outcome and data coverage.
| Check | Minimum expected behaviour |
| --- | --- |
| Schema | Required fields exist; types are readable; unexpected schema is reported. |
| Timestamp | Parseable, timezone/session interpretation documented; invalid values reported. |
| Key duplicates | Detect duplicate symbol + timestamp or equivalent natural key. |
| OHLC consistency | Where OHLC exists, check high/low consistency and valid numeric values. |
| Volume | Where volume exists, check invalid negative values and suspicious nulls. |
| Coverage | Report first/last dates and notable gaps; distinguish expected market closures from missing data where rules are available. |
| File integrity | Unreadable or incomplete files fail visibly; no silent partial success. |

Maintenance must process only new or changed source data where feasible. Track the last successful processed coverage and validate the result. A scanner run must never trigger a full database rebuild. Recovery and retry rules should be simple and documented.

Aggregation is required only for timeframes needed by approved scanners. For OHLCV, aggregate within the correct exchange session and interval:

| Output field | Rule |
| --- | --- |
| Open | First source candle open. |
| High | Maximum source high. |
| Low | Minimum source low. |
| Close | Last source candle close. |
| Volume | Sum source volume. |

Requirements:

- Use Asia/Kolkata (IST) consistently for NSE session data; do not rely on the computer's local timezone implicitly.
- Define interval alignment and session start/end explicitly.
- Do not combine records across trading sessions.
- Handle holidays, missing source candles and incomplete current intervals.
- Do not treat an incomplete interval as a completed candle.
- Preserve source 1-minute records.
- Choose on-demand aggregation or persisted derived data after measuring actual workload; do not precompute every timeframe by default.
Each scanner is a separate Python module/package with a clear responsibility. This is modular code organisation, not a plug-in architecture.

| Contract element | Requirement |
| --- | --- |
| Identity | Stable scanner ID, name and version. |
| Requirements | Declared datasets, fields, symbols/universe, timeframe and date range needed. |
| Availability check | Check requirements against catalogue before calculation; return actionable missing-data messages. |
| Input | Receive data through the common access interface, not direct file access. |
| Calculation | Deterministic scanner-specific calculations, separated from presentation. |
| Output | Documented result structure, including run context and relevant inputs. |
| Tests | Scanner-specific unit and reference-data tests. |
| Independence | Adding a scanner should not require edits to unrelated scanners. |

The exact first two or three scanner modules are not frozen. Candidate examples discussed include MA Affinity, EMA analysis and Breakout analysis. Confirm based on source-data inspection and separately approved scanner specifications.

A basic weighted combined score is part of the planned scope and is considered moderate complexity. It is separate from the individual scanner calculations.

Proposed generic formula:

Combined Score = Σ (Scanner Score × Scanner Weight)

Initial design constraints:

- Each contributing scanner must provide a score on a common approved scale, initially proposed as 0–100.
- Weights are configuration, not hard-coded business logic; active weights must total 100%.
- Output must show scanner ID, individual score, configured weight, weighted contribution and final score.
- Define explicit behaviour for unavailable, invalid or stale scanner results. Do not silently treat missing as zero.
- Record the scoring configuration/version used for each result so it can be reproduced.
- Keep the first implementation as a transparent deterministic weighted sum.
The scoring specification must decide whether the system rejects an incomplete combination or renormalises the remaining weights. This is an open design decision and must be approved before implementation. Do not assume a policy.

Deferred: complex rule chains between scanners, market-regime-dependent/adaptive weights, automated decision engines, AI-generated weights or trade execution.

The analytical engine must be fully functional without any AI service. Provide structured, documented output that can later be supplied to Claude, ChatGPT or another AI tool.

Output should distinguish:

- Raw/source facts and retrieved data context.
- Calculated scanner results and scores.
- Combined-score calculations and configuration.
- Optional human/AI commentary or interpretation.
JSON is a suitable candidate for machine-readable interchange, but the exact output schema is to be defined with the first scanner. AI integration, provider credentials, API calls and remote access are future scope only. AI must not modify source data or calculation results.

The first release needs a simple, reliable way for the user to select/run an analysis and inspect/export results. Do not build an elaborate dashboard before the analytical workflow is proven. Prefer Windows-friendly interaction and file/folder pickers where useful; normal user tasks should not require a CLI-only workflow.

The exact UI technology is undecided. Choose the simplest maintainable option after the first scanner's workflow is clear. Keep UI code separate from data and calculation logic.

| Test layer | What it verifies |
| --- | --- |
| Data tests | Source parsing, schema, timestamp, duplicate and data-quality handling. |
| Database tests | Catalogue, retrieval, date filtering, symbol filtering and clear unavailable-data responses. |
| Aggregation tests | Known sample intervals, session boundaries, missing candles and incomplete intervals. |
| Scanner tests | Known inputs produce independently verified expected calculations and outputs. |
| Scoring tests | Weights, normalisation, missing results, reproducibility and contribution transparency. |
| Limited integration tests | Scanner can use the common data interface and complete user workflow works. |
| Regression tests | A change to one module does not break established outputs of other modules. |

Testing should be focused. Do not require a massive full-system test suite for every small change. However, test the shared interface and user workflow at meaningful milestones.

> **Acceptance principle**
>
> A program that starts or passes unit tests is not sufficient. Analytical results must be checked against hand-verified examples or another trusted calculation.

Initial local system is intended for the user's own Windows environment. Avoid unnecessary network services, credentials and exposed database endpoints. Backups and recovery expectations should be documented before real data is transformed or maintained.

Cloud security, identity management, API authentication, encryption, read-only remote access and synchronisation conflict handling are future design topics. Do not implement them in the local foundation.

| Priority | Definition | Implementation rule |
| --- | --- | --- |
| P1 | Initial essential scope. | Implement after detailed design and acceptance approval. |
| P2 | Later enhancement. | Do not implement until promoted through scope review. |
| P3 | Future idea. | Document only; no code or infrastructure. |

| Complexity | Definition |
| --- | --- |
| Low | Limited code and dependencies; straightforward tests. |
| Moderate | Several interacting rules or modules; requires a focused design and tests. |
| High | Significant infrastructure, security, operational or integration burden. |

| Milestone | Scope | Exit evidence |
| --- | --- | --- |
| M0 – Source inspection | Inspect all starting files and produce an inventory/quality report. | Verified schemas, fields, dates, issues and import recommendations. |
| M1 – Local data foundation | Parquet/DuckDB access, simple catalogue, basic validation. | Runnable local query and catalogue demonstration. |
| M2 – Stable data interface | Document and test scanner-facing data retrieval. | Example client retrieves correct records without knowing storage internals. |
| M3 – Scanner 1 | Implement one approved scanner. | Verified output and reproducible tests. |
| M4 – Scanner 2/3 | Add up to two more independent scanners. | Independent tests; no regressions in earlier modules. |
| M5 – Weighted scoring | Implement simple combined scoring. | Transparent, reproducible combined result and approved missing-data policy. |
| M6 – Practical output | Provide user-friendly run and review workflow. | User can run and inspect results without developer intervention. |

Cloud, remote AI integration, sophisticated decision logic and broad scanner expansion are not milestones in this initial plan.

- No production code before the relevant design is approved.
- Every milestone must be runnable and testable.
- Prefer clear, purpose-driven variable and function names.
- Each function should perform one clear task.
- Comments should explain WHY, not restate obvious code.
- Organise modules consistently: imports, constants, helpers, main logic, execution.
- Handle edge cases explicitly; no silent failures.
- Avoid unnecessary frameworks, dependencies and abstractions.
- Use small changes and preserve working functionality.
- Provide beginner-friendly run instructions suitable for Windows and Python IDLE where practical.
- Use GUI file/folder selection for user-facing file workflows when appropriate.
- Do not create unrequested helper files or documentation.
| Future capability | Why deferred / trigger to reconsider |
| --- | --- |
| Cloud replica and local-to-cloud sync | Adds connectivity, storage cost, integrity, retry, recovery and security requirements. Reconsider after local use proves value. |
| Remote query API for Python apps | Requires service deployment, authentication, authorisation and operational support. |
| Claude/ChatGPT direct integration | Optional; first deliver structured outputs. Reconsider when repeated manual interpretation becomes a real bottleneck. |
| Sophisticated multi-scanner decision engine | Weighted sum is included; conditional dependencies, adaptive logic and regime-aware decisions need separate requirements. |
| Adaptive weights | Requires evidence, validation and governance to avoid unstable or misleading scores. |
| Advanced dashboard and automation | Wait until scanner outputs and user workflow are stable. |
| More asset classes / markets / data sources | Add based on specific use cases and verified source availability. |
| Advanced catalogue governance and data lineage | Not justified for the initial local single-user system. |

| Decision | Required input / timing |
| --- | --- |
| Actual source schemas | Inspect files at M0. |
| First two or three scanners | Choose after source inspection and scanner requirement comparison. |
| Scanner-specific formulas and parameters | Separate specification and approval for each scanner. |
| Timeframe list and persistence policy | Derive from scanner needs; benchmark if necessary. |
| Catalogue implementation details | Choose simplest adequate approach during M1 design. |
| Combined-score missing-result policy | Approve before M5 implementation. |
| Score calibration method | Define per scanner so scores are comparable; do not assume raw outputs are directly comparable. |
| Output schema and report format | Define with first scanner; include machine-readable output. |
| UI technology | Choose after workflow is demonstrated. |
| Backup and restore method | Define before routine maintenance of the local database. |
| Cloud provider/security architecture | Future design only. |
| AI provider/API integration | Future design only. |

The project is to be created as a fresh GitHub repository named Q-MAP. The repository should initially contain the approved human-readable and technical blueprints, a concise project status/decision record if useful, and a simple source-code structure only when implementation begins.

Do not create application code, frameworks, dependencies or large directory structures merely to make the repository look complete. Keep the initial repository small. Use version control for the approved documents and subsequent implementation.

Implement a local-first Q-MAP with two independent subsystems: a reusable Parquet/DuckDB database and an analytical engine containing independent scanner modules. Inspect actual input files before fixing schemas. Keep the catalogue and data-access interface small and stable. Start with two or three approved scanners. Include a deterministic, transparent weighted combined score with common score scale, configurable weights and explicit missing-result policy. Ensure the engine works without AI. Defer cloud synchronisation, remote APIs, direct AI integration, advanced dashboards and sophisticated decision logic. Follow gated milestones with verified, usable outputs. The human-readable blueprint controls scope; this technical blueprint is its implementation translation.
