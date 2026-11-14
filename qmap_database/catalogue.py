"""The Q-MAP catalogue: one DuckDB file holding only metadata (document 02
v1.6, section 5). Exactly the 11 approved tables exist, no others.

Only the Data Manager writes here. Every multi-table change that must be
all-or-nothing runs inside one transaction; generation activation (section
9.4 step 4) is the single commit point for an instrument's data change.
"""

# --- Imports -----------------------------------------------------------------
from datetime import datetime

import duckdb

from .errors import DatabaseUnavailableError

# --- Constants ---------------------------------------------------------------
QUALITY_UNVALIDATED = "UNVALIDATED"
QUALITY_PASS = "PASS"
QUALITY_PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
QUALITY_FAIL = "FAIL"

COMPLETENESS_COMPLETE = "COMPLETE"
COMPLETENESS_GAPS = "GAPS_REPORTED"
COMPLETENESS_UNKNOWN = "UNKNOWN"

BASIS_OFFICIAL = "OFFICIAL_CALENDAR"
BASIS_PROVISIONAL = "PROVISIONAL_DERIVED_CALENDAR"

ISSUE_OPEN = "OPEN"
ISSUE_ACKNOWLEDGED = "ACKNOWLEDGED"
ISSUE_VERIFIED_OK = "VERIFIED_OK"
ISSUE_RESOLVED = "RESOLVED"

RUN_STATUS_RUNNING = "RUNNING"
RUN_STATUS_SUCCESS = "SUCCESS"
RUN_STATUS_SUCCESS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"
# maintenance_run.status for a failed run. Document 02 section 5.2 does not
# enumerate status values; this value is documented per Verification Package
# v1.2 item X-5.
RUN_STATUS_FAILED = "FAILED"

# The three approved datasets (02 section 3.1). Storage folders are stored as
# portable relative paths; os.path.join applies the platform separator.
INITIAL_DATASETS = [
    ("NSE_INDEX_1M", "NSE index intraday candles", "intraday_ohlcv", "1m",
     "market/NSE_INDEX_1M", "Asia/Kolkata"),
    ("NSE_EQ_DAILY", "NSE equity daily bars", "daily_ohlcv", "1D",
     "market/NSE_EQ_DAILY", "Asia/Kolkata"),
    ("NSE_SECTOR_INDEX_DAILY", "NSE sector index daily bars (D-13)",
     "daily_ohlcv", "1D", "market/NSE_SECTOR_INDEX_DAILY", "Asia/Kolkata"),
]

# Instruments at start, with the file-name aliases of 02 section 3.2. Identity
# comes only from file names, so unknown files are never guessed.
INITIAL_INSTRUMENTS = [
    ("NIFTY", "NSE_INDEX_1M", "NIFTY 50", "INDEX", "NSE", "NIFTY",
     ["Nifty_1min*"]),
    ("BANKNIFTY", "NSE_INDEX_1M", "NIFTY Bank", "INDEX", "NSE", "BANKNIFTY",
     ["NSE_BANKNIFTY*"]),
    ("CONCOR", "NSE_EQ_DAILY", "Container Corporation of India", "EQUITY",
     "NSE", "CONCOR", ["CONCOR", "CONCOR_daily*"]),
    ("INFY", "NSE_EQ_DAILY", "Infosys", "EQUITY", "NSE", "INFY",
     ["INFY", "INFY_daily*"]),
    ("NIFTYIT", "NSE_SECTOR_INDEX_DAILY", "NIFTY IT", "SECTOR_INDEX", "NSE",
     "NIFTYIT", ["Nifty IT", "Nifty_IT*"]),
]

_FIELD_DEFINITIONS = {
    "intraday_ohlcv": [
        ("ts", "TIMESTAMP", False, "IST wall clock", "minute start (interval start)"),
        ("record_type", "VARCHAR", False, "", "CANDLE / AUCTION_PHASE / CLOSING_AUCTION"),
        ("open", "DOUBLE", False, "price", "as supplied, never adjusted"),
        ("high", "DOUBLE", False, "price", "as supplied"),
        ("low", "DOUBLE", False, "price", "as supplied"),
        ("close", "DOUBLE", False, "price", "as supplied"),
        ("volume", "BIGINT", True, "units", "missing is normal (D-03)"),
        ("source_ts", "TIMESTAMP", False, "IST wall clock", "timestamp exactly as supplied (D-09)"),
        ("quality_flags", "VARCHAR", True, "", "semicolon list of flags"),
    ],
    "daily_ohlcv": [
        ("trade_date", "DATE", False, "", "exchange trading date"),
        ("open", "DOUBLE", False, "price", "as supplied, never adjusted"),
        ("high", "DOUBLE", False, "price", "as supplied"),
        ("low", "DOUBLE", False, "price", "as supplied"),
        ("close", "DOUBLE", False, "price", "as supplied"),
        ("volume", "BIGINT", True, "units", "missing is normal (D-03)"),
        ("quality_flags", "VARCHAR", True, "", "semicolon list of flags"),
    ],
}

_SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS dataset (
        dataset_id VARCHAR PRIMARY KEY, name VARCHAR, data_kind VARCHAR,
        base_timeframe VARCHAR, storage_folder VARCHAR, timezone VARCHAR,
        provenance_note VARCHAR, status VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS instrument (
        instrument_id VARCHAR PRIMARY KEY, dataset_id VARCHAR,
        display_name VARCHAR, instrument_type VARCHAR, exchange VARCHAR,
        file_safe_name VARCHAR, source_aliases VARCHAR[], active BOOLEAN,
        active_generation INTEGER, previous_generation INTEGER)""",
    """CREATE TABLE IF NOT EXISTS field_definition (
        dataset_id VARCHAR, field_name VARCHAR, data_type VARCHAR,
        nullable BOOLEAN, unit VARCHAR, meaning VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS coverage (
        dataset_id VARCHAR, instrument_id VARCHAR, generation INTEGER,
        first_ts TIMESTAMP, last_ts TIMESTAMP, trading_days INTEGER,
        row_count BIGINT, volume_first_date DATE, volume_last_date DATE,
        last_import_id INTEGER, last_update_at TIMESTAMP,
        last_validated_at TIMESTAMP, quality_status VARCHAR,
        completeness_status VARCHAR, completeness_basis VARCHAR,
        open_warning_count INTEGER, open_error_count INTEGER)""",
    """CREATE TABLE IF NOT EXISTS day_profile (
        instrument_id VARCHAR, trade_date DATE, generation INTEGER,
        observed_shape VARCHAR, session_status VARCHAR, session_type VARCHAR,
        first_record TIME, last_continuous_candle TIME,
        expected_candles INTEGER, expected_basis VARCHAR,
        present_candles INTEGER, missing_candles INTEGER,
        missing_ranges VARCHAR, has_auction_phase BOOLEAN,
        has_closing_auction BOOLEAN, has_volume BOOLEAN,
        quarantined_rows INTEGER)""",
    """CREATE TABLE IF NOT EXISTS market_calendar (
        trade_date DATE PRIMARY KEY, day_type VARCHAR, session_open TIME,
        session_close TIME, description VARCHAR, source VARCHAR,
        verified BOOLEAN, evidence VARCHAR, confirmed_at VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS data_file (
        relative_path VARCHAR, dataset_id VARCHAR, instrument_id VARCHAR,
        generation INTEGER, period VARCHAR, row_count BIGINT,
        min_ts TIMESTAMP, max_ts TIMESTAMP, sha256 VARCHAR,
        written_at TIMESTAMP, written_by_run INTEGER)""",
    """CREATE TABLE IF NOT EXISTS import_log (
        import_id INTEGER PRIMARY KEY, run_id INTEGER, source_path VARCHAR,
        source_name VARCHAR, source_size BIGINT, source_modified TIMESTAMP,
        source_sha256 VARCHAR, reader_used VARCHAR, dataset_id VARCHAR,
        instrument_id VARCHAR, rows_read BIGINT, rows_stored BIGINT,
        rows_quarantined BIGINT, rows_new BIGINT, rows_changed BIGINT,
        rows_removed BIGINT, action VARCHAR, message VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS maintenance_run (
        run_id INTEGER PRIMARY KEY, run_type VARCHAR, started_at TIMESTAMP,
        finished_at TIMESTAMP, status VARCHAR, files_examined INTEGER,
        summary VARCHAR, report_path VARCHAR, log_path VARCHAR,
        catalogue_backup_path VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS data_issue (
        issue_id INTEGER PRIMARY KEY, dataset_id VARCHAR,
        instrument_id VARCHAR, ts_from TIMESTAMP, ts_to TIMESTAMP,
        check_code VARCHAR, severity VARCHAR, description VARCHAR,
        evidence VARCHAR, affects_continuity BOOLEAN, status VARCHAR,
        first_seen_run INTEGER, last_seen_run INTEGER, user_note VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS instrument_rule (
        instrument_id VARCHAR, rule_type VARCHAR, value VARCHAR,
        effective_from DATE, effective_to DATE, verified BOOLEAN,
        source VARCHAR, evidence VARCHAR, confirmed_at VARCHAR)""",
    "CREATE SEQUENCE IF NOT EXISTS seq_import_id START 1",
    "CREATE SEQUENCE IF NOT EXISTS seq_run_id START 1",
    "CREATE SEQUENCE IF NOT EXISTS seq_issue_id START 1",
]


# --- Main logic ----------------------------------------------------------------
class Catalogue:
    """Wrapper around the one DuckDB catalogue file."""

    def __init__(self, path, read_only=False):
        self.path = path
        try:
            self.con = duckdb.connect(path, read_only=read_only)
        except duckdb.Error as exc:
            raise DatabaseUnavailableError(
                "The Q-MAP catalogue could not be opened. It may be in use by "
                "another Q-MAP program. Please close the other program and "
                "try again. (%s)" % exc)

    def close(self):
        self.con.close()

    # --- schema and registration ---------------------------------------------
    def ensure_schema(self):
        for statement in _SCHEMA_STATEMENTS:
            self.con.execute(statement)

    def register_initial_content(self):
        """Register the approved datasets, instruments and field definitions,
        and the observed (unverified) index tick rules, once."""
        count = self.con.execute("SELECT count(*) FROM dataset").fetchone()[0]
        if count:
            return
        for row in INITIAL_DATASETS:
            self.con.execute(
                "INSERT INTO dataset VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                list(row) + ["registered at initial setup", "ACTIVE"])
            data_kind = row[2]
            for f in _FIELD_DEFINITIONS[data_kind]:
                self.con.execute(
                    "INSERT INTO field_definition VALUES (?, ?, ?, ?, ?, ?)",
                    [row[0]] + list(f))
        for (iid, did, name, itype, exch, safe, aliases) in INITIAL_INSTRUMENTS:
            self.con.execute(
                "INSERT INTO instrument VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [iid, did, name, itype, exch, safe, aliases, True, None, None])
        # The 0.05 index grid is an *observed* property of the inspected data,
        # not an established exchange rule (Deliverable 1 section 4), so the
        # rule is recorded unverified: off-tick rows are flagged, never
        # quarantined, until the Owner verifies it under G-04.
        for index_id in ("NIFTY", "BANKNIFTY"):
            self.add_instrument_rule(index_id, "TICK_SIZE", "0.05", None, None,
                                     False, "OBSERVED_IN_DATA",
                                     "Observed on all inspected 1-minute "
                                     "records (Deliverable 1 v1.4, section 4)",
                                     None)

    # --- small helpers ---------------------------------------------------------
    def _next(self, sequence):
        return self.con.execute("SELECT nextval('%s')" % sequence).fetchone()[0]

    def begin(self):
        self.con.execute("BEGIN TRANSACTION")

    def commit(self):
        self.con.execute("COMMIT")

    def rollback(self):
        self.con.execute("ROLLBACK")

    # --- maintenance runs ------------------------------------------------------
    def start_run(self, run_type, log_path, backup_path):
        run_id = self._next("seq_run_id")
        self.con.execute(
            "INSERT INTO maintenance_run VALUES (?, ?, ?, NULL, ?, 0, '', "
            "NULL, ?, ?)",
            [run_id, run_type, datetime.now(), RUN_STATUS_RUNNING, log_path,
             backup_path])
        return run_id

    def finish_run(self, run_id, status, files_examined, summary, report_path):
        self.con.execute(
            "UPDATE maintenance_run SET finished_at = ?, status = ?, "
            "files_examined = ?, summary = ?, report_path = ? WHERE run_id = ?",
            [datetime.now(), status, files_examined, summary, report_path,
             run_id])

    # --- import log ------------------------------------------------------------
    def reserve_import_id(self):
        """Hand out the next import_id before the canonical rows are written,
        so the stored rows can carry their provenance link (02 section 4.1)."""
        return self._next("seq_import_id")

    def log_import(self, run_id, source_path, source_name, source_size,
                   source_modified, source_sha256, reader_used, dataset_id,
                   instrument_id, rows_read, rows_stored, rows_quarantined,
                   rows_new, rows_changed, rows_removed, action, message,
                   import_id=None):
        if import_id is None:
            import_id = self._next("seq_import_id")
        self.con.execute(
            "INSERT INTO import_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?)",
            [import_id, run_id, source_path, source_name, source_size,
             source_modified, source_sha256, reader_used, dataset_id,
             instrument_id, rows_read, rows_stored, rows_quarantined, rows_new,
             rows_changed, rows_removed, action, message])
        return import_id

    # --- issues ------------------------------------------------------------------
    def add_issue(self, issue, dataset_id, instrument_id, run_id):
        """Insert an IssueRecord; re-raising the same open issue on a later run
        only moves last_seen_run instead of duplicating it."""
        existing = self.con.execute(
            "SELECT issue_id FROM data_issue WHERE dataset_id IS NOT DISTINCT "
            "FROM ? AND instrument_id IS NOT DISTINCT FROM ? AND check_code = ? "
            "AND description = ? AND status IN (?, ?)",
            [dataset_id, instrument_id, issue.check_code, issue.description,
             ISSUE_OPEN, ISSUE_ACKNOWLEDGED]).fetchone()
        if existing:
            self.con.execute(
                "UPDATE data_issue SET last_seen_run = ? WHERE issue_id = ?",
                [run_id, existing[0]])
            return existing[0]
        issue_id = self._next("seq_issue_id")
        self.con.execute(
            "INSERT INTO data_issue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, NULL)",
            [issue_id, dataset_id, instrument_id, issue.ts_from, issue.ts_to,
             issue.check_code, issue.severity, issue.description,
             issue.evidence, issue.affects_continuity, ISSUE_OPEN, run_id,
             run_id])
        return issue_id

    def mark_issue_verified_ok(self, issue_id, user_note=""):
        """G-03: the Owner, after personally verifying an occurrence, marks it
        VERIFIED_OK; affects_continuity turns false in the same transaction."""
        self.begin()
        try:
            self.con.execute(
                "UPDATE data_issue SET status = ?, affects_continuity = false, "
                "user_note = ? WHERE issue_id = ?",
                [ISSUE_VERIFIED_OK, user_note, issue_id])
            self.commit()
        except Exception:
            self.rollback()
            raise

    def acknowledge_issue(self, issue_id, user_note=""):
        """The Owner confirms a real break or error: affects_continuity stays
        true and the status becomes ACKNOWLEDGED (02 section 5.2)."""
        self.begin()
        try:
            self.con.execute(
                "UPDATE data_issue SET status = ?, user_note = ? "
                "WHERE issue_id = ?", [ISSUE_ACKNOWLEDGED, user_note, issue_id])
            self.commit()
        except Exception:
            self.rollback()
            raise

    # --- instrument rules (G-04) --------------------------------------------------
    def add_instrument_rule(self, instrument_id, rule_type, value,
                            effective_from, effective_to, verified, source,
                            evidence, confirmed_at):
        if verified:
            self._check_g04(evidence, effective_from, confirmed_at)
        self.con.execute(
            "INSERT INTO instrument_rule VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [instrument_id, rule_type, value, effective_from, effective_to,
             verified, source, evidence, confirmed_at])

    def set_rule_verified(self, instrument_id, rule_type, value, evidence,
                          effective_from, confirmed_at, effective_to=None):
        """Set a rule verified only when the complete G-04 record is present."""
        self._check_g04(evidence, effective_from, confirmed_at)
        self.con.execute(
            "UPDATE instrument_rule SET verified = true, evidence = ?, "
            "effective_from = ?, effective_to = COALESCE(?, effective_to), "
            "confirmed_at = ? WHERE instrument_id = ? AND rule_type = ? AND "
            "value = ?",
            [evidence, effective_from, effective_to, confirmed_at,
             instrument_id, rule_type, value])

    @staticmethod
    def _check_g04(evidence, effective_from, confirmed_at):
        missing = [name for name, value in
                   [("evidence", evidence), ("effective_from", effective_from),
                    ("confirmed_at", confirmed_at)] if not value]
        if missing:
            raise ValueError(
                "A rule may be verified only with evidence, effective_from "
                "and confirmed_at recorded (G-04). Missing: %s"
                % ", ".join(missing))

    def get_tick_rules(self, instrument_id):
        rows = self.con.execute(
            "SELECT value, effective_from, effective_to, verified FROM "
            "instrument_rule WHERE instrument_id = ? AND rule_type = "
            "'TICK_SIZE'", [instrument_id]).fetchall()
        return [{"value": r[0], "effective_from": r[1], "effective_to": r[2],
                 "verified": r[3]} for r in rows]

    # --- instruments and datasets --------------------------------------------------
    def instruments(self):
        rows = self.con.execute(
            "SELECT instrument_id, dataset_id, instrument_type, "
            "file_safe_name, source_aliases, active_generation, "
            "previous_generation FROM instrument").fetchall()
        return [{"instrument_id": r[0], "dataset_id": r[1],
                 "instrument_type": r[2], "file_safe_name": r[3],
                 "source_aliases": r[4] or [], "active_generation": r[5],
                 "previous_generation": r[6]} for r in rows]

    def dataset(self, dataset_id):
        row = self.con.execute(
            "SELECT dataset_id, name, data_kind, base_timeframe, "
            "storage_folder, timezone FROM dataset WHERE dataset_id = ?",
            [dataset_id]).fetchone()
        if row is None:
            return None
        return {"dataset_id": row[0], "name": row[1], "data_kind": row[2],
                "base_timeframe": row[3], "storage_folder": row[4],
                "timezone": row[5]}

    # --- generation activation (the single commit point, 02 section 9.4) -----------
    def activate_generation(self, instrument_id, generation, data_file_rows,
                            coverage_row, day_profile_rows, run_id):
        """One catalogue transaction: data_file rows, coverage, day profiles
        and the generation pointer switch, all or nothing."""
        self.begin()
        try:
            for f in data_file_rows:
                self.con.execute(
                    "INSERT INTO data_file VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "
                    "?, ?)",
                    [f["relative_path"], f["dataset_id"], instrument_id,
                     generation, f["period"], f["row_count"], f["min_ts"],
                     f["max_ts"], f["sha256"], datetime.now(), run_id])
            self.con.execute("DELETE FROM coverage WHERE instrument_id = ?",
                             [instrument_id])
            self.con.execute(
                "INSERT INTO coverage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "?, ?, ?, ?, ?, ?)",
                [coverage_row["dataset_id"], instrument_id, generation,
                 coverage_row["first_ts"], coverage_row["last_ts"],
                 coverage_row["trading_days"], coverage_row["row_count"],
                 coverage_row["volume_first_date"],
                 coverage_row["volume_last_date"],
                 coverage_row["last_import_id"], datetime.now(),
                 datetime.now(), coverage_row["quality_status"],
                 coverage_row["completeness_status"],
                 coverage_row["completeness_basis"],
                 coverage_row["open_warning_count"],
                 coverage_row["open_error_count"]])
            self.con.execute("DELETE FROM day_profile WHERE instrument_id = ?",
                             [instrument_id])
            for p in day_profile_rows:
                self.con.execute(
                    "INSERT INTO day_profile VALUES (?, ?, ?, ?, ?, ?, ?, ?, "
                    "?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [p["instrument_id"], p["trade_date"], generation,
                     p["observed_shape"], p["session_status"],
                     p["session_type"], p["first_record"],
                     p["last_continuous_candle"], p["expected_candles"],
                     p["expected_basis"], p["present_candles"],
                     p["missing_candles"], p["missing_ranges"],
                     p["has_auction_phase"], p["has_closing_auction"],
                     p["has_volume"], p["quarantined_rows"]])
            self.con.execute(
                "UPDATE instrument SET previous_generation = "
                "active_generation, active_generation = ? WHERE "
                "instrument_id = ?", [generation, instrument_id])
            self.commit()
        except Exception:
            self.rollback()
            raise

    # --- calendar (G-02) -------------------------------------------------------------
    def upsert_derived_calendar(self, entries):
        """Store derived calendar rows without touching reference or user rows,
        and without ever setting verified = true (G-02)."""
        for e in entries:
            existing = self.con.execute(
                "SELECT source FROM market_calendar WHERE trade_date = ?",
                [e.trade_date]).fetchone()
            if existing is None:
                self.con.execute(
                    "INSERT INTO market_calendar VALUES (?, ?, ?, ?, ?, ?, "
                    "false, NULL, NULL)",
                    [e.trade_date, e.day_type, e.session_open, e.session_close,
                     e.description, e.source])
            # A derived row never replaces a reference or user row.

    def import_reference_calendar(self, entries):
        """G-02 step 1: store the file's rows as REFERENCE_FILE_UNCONFIRMED.
        Importing never, by itself, makes anything official. Re-importing a
        changed file returns its dates to unconfirmed."""
        self.begin()
        try:
            for e in entries:
                self.con.execute("DELETE FROM market_calendar WHERE "
                                 "trade_date = ?", [e.trade_date])
                self.con.execute(
                    "INSERT INTO market_calendar VALUES (?, ?, ?, ?, ?, ?, "
                    "false, NULL, NULL)",
                    [e.trade_date, e.day_type, e.session_open, e.session_close,
                     e.description, e.source])
            self.commit()
        except Exception:
            self.rollback()
            raise

    def record_calendar_provenance(self, years, evidence, confirmed_at):
        """G-02 step 2: only now do the confirmed years become official."""
        if not evidence or not confirmed_at:
            raise ValueError("Recording provenance needs the official source "
                             "(evidence) and who confirmed it (confirmed_at) "
                             "- G-02.")
        self.begin()
        try:
            for year in years:
                self.con.execute(
                    "UPDATE market_calendar SET source = 'OFFICIAL_REFERENCE', "
                    "verified = true, evidence = ?, confirmed_at = ? WHERE "
                    "year(trade_date) = ? AND source = "
                    "'REFERENCE_FILE_UNCONFIRMED'",
                    [evidence, confirmed_at, year])
            self.commit()
        except Exception:
            self.rollback()
            raise

    def calendar_entries(self):
        rows = self.con.execute(
            "SELECT trade_date, day_type, session_open, session_close, "
            "description, source, verified FROM market_calendar").fetchall()
        return rows

    # --- queries used by maintenance, reports and the GUI ----------------------------
    def coverage_table(self):
        return self.con.execute(
            "SELECT dataset_id, instrument_id, generation, first_ts, last_ts, "
            "trading_days, row_count, volume_first_date, volume_last_date, "
            "quality_status, completeness_status, completeness_basis, "
            "open_warning_count, open_error_count FROM coverage "
            "ORDER BY dataset_id, instrument_id").fetchall()

    def update_coverage_status(self, instrument_id, completeness_status,
                               completeness_basis, quality_status,
                               open_warning_count, open_error_count):
        self.con.execute(
            "UPDATE coverage SET completeness_status = ?, completeness_basis "
            "= ?, quality_status = ?, open_warning_count = ?, "
            "open_error_count = ?, last_validated_at = ? WHERE "
            "instrument_id = ?",
            [completeness_status, completeness_basis, quality_status,
             open_warning_count, open_error_count, datetime.now(),
             instrument_id])

    def open_issue_counts(self, instrument_id):
        row = self.con.execute(
            "SELECT count(*) FILTER (WHERE severity = 'WARNING'), "
            "count(*) FILTER (WHERE severity = 'ERROR') FROM data_issue WHERE "
            "instrument_id = ? AND status = 'OPEN'", [instrument_id]).fetchone()
        return int(row[0]), int(row[1])

    def get_issues(self, instrument_id=None, min_severity="WARNING",
                   status="OPEN"):
        order = {"INFO": 0, "WARNING": 1, "ERROR": 2}
        severities = [s for s, rank in order.items()
                      if rank >= order.get(min_severity, 0)]
        query = ("SELECT issue_id, dataset_id, instrument_id, ts_from, ts_to, "
                 "check_code, severity, description, evidence, "
                 "affects_continuity, status, user_note FROM data_issue "
                 "WHERE severity IN (%s)"
                 % ",".join("'%s'" % s for s in severities))
        params = []
        if instrument_id:
            query += " AND instrument_id = ?"
            params.append(instrument_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY issue_id"
        return self.con.execute(query, params).fetchall()

    def cas_confirmation_list(self):
        """Detected CAS candidates, grouped per instrument for the Owner."""
        return self.con.execute(
            "SELECT instrument_id, count(*), min(trade_date), max(trade_date) "
            "FROM day_profile WHERE session_status = 'CANDIDATE' AND "
            "session_type = 'CAS' GROUP BY instrument_id "
            "ORDER BY instrument_id").fetchall()

    def unrecognised_days(self):
        """Unrecognised days, one row each, for the Owner's review."""
        return self.con.execute(
            "SELECT instrument_id, trade_date, first_record, "
            "last_continuous_candle, present_candles, missing_ranges "
            "FROM day_profile WHERE session_status = "
            "'UNRECOGNISED_SESSION_SHAPE' ORDER BY instrument_id, trade_date"
        ).fetchall()

    def active_data_files(self):
        """Every file of every active generation, for V-INT-01."""
        return self.con.execute(
            "SELECT f.relative_path, f.row_count, f.sha256, f.instrument_id "
            "FROM data_file f JOIN instrument i ON i.instrument_id = "
            "f.instrument_id AND i.active_generation = f.generation"
        ).fetchall()

    def registered_sources(self):
        """Paths and fingerprints already recorded for imported content."""
        return self.con.execute(
            "SELECT source_path, source_sha256, instrument_id, action FROM "
            "import_log WHERE action IN ('NEW', 'APPEND', "
            "'APPLIED_APPROVED_REVISION', 'DUPLICATE_SOURCE', "
            "'SKIPPED_UNCHANGED')").fetchall()
