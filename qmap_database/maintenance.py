"""Maintenance: the initial load (M1a scope) with logging, the Excel
validation report and the machine-readable M1a evidence export.

Initial preparation and incremental maintenance are separate activities
(document 02 v1.6, section 9.1); the incremental update, held revisions,
approve/reject and backup-restore workflows arrive with M1b. A scanner run
never triggers anything here.
"""

# --- Imports -----------------------------------------------------------------
import fnmatch
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from openpyxl import Workbook

from . import catalogue as cat_mod
from . import session_rules as sr
from . import standardise as std
from . import storage
from . import validation
from .catalogue import Catalogue
from .errors import FileImportError
from .readers import detect_and_read, sha256_of_file
from .validation import IssueRecord

# --- Constants ---------------------------------------------------------------
ACTION_NEW = "NEW"
ACTION_FAILED = "FAILED"
ACTION_DUPLICATE_SOURCE = "DUPLICATE_SOURCE"
ACTION_SOURCE_CONFLICT = "SOURCE_CONFLICT"

EVIDENCE_TS_FORMAT = "%Y-%m-%d %H:%M:%S"   # TS-01: IST wall clock, no offset


# --- Result structures ----------------------------------------------------------
@dataclass
class FileOutcome:
    path: str
    instrument_id: str
    action: str
    message: str = ""
    rows_stored: int = 0
    rows_quarantined: int = 0


@dataclass
class InitialLoadResult:
    run_id: int = None
    status: str = ""
    file_outcomes: list = field(default_factory=list)
    unrecognised_files: list = field(default_factory=list)
    report_path: str = ""
    log_path: str = ""
    summary: str = ""


# --- Helpers ----------------------------------------------------------------------
def timestamp_suffix(now=None):
    """The Owner's dd_mmm_yy_hhmmss file-name suffix."""
    return (now or datetime.now()).strftime("%d_%b_%y_%H%M%S")


def human_date(value):
    """Human-readable date, dd mmm yy (Owner's style)."""
    if value is None:
        return ""
    return value.strftime("%d %b %y")


def _make_logger(log_path, live_callback):
    logger = logging.getLogger("qmap_data_manager_%s" % id(log_path))
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s",
                                           datefmt="%d-%b-%y %H:%M:%S"))
    logger.addHandler(handler)
    if live_callback is not None:
        class _Live(logging.Handler):
            def emit(self, record):
                live_callback(record.getMessage())
        logger.addHandler(_Live())
    return logger


def match_instrument(file_path, instruments):
    """Map a file to an instrument by its name alias, never by guessing.

    Matching is case-insensitive on the file stem. None means unrecognised,
    and the Data Manager asks the Owner instead of assuming anything."""
    stem = os.path.splitext(os.path.basename(file_path))[0]
    for instrument in instruments:
        for alias in instrument["source_aliases"]:
            if fnmatch.fnmatchcase(stem.lower(), alias.lower()):
                return instrument
    return None


def _file_facts(path):
    stat = os.stat(path)
    return {"name": os.path.basename(path), "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime)}


def _verified_calendar_entries(catalogue):
    entries = {}
    for (trade_date, day_type, session_open, session_close, description,
         source, verified) in catalogue.calendar_entries():
        if verified and source == sr.CAL_SOURCE_OFFICIAL:
            entries[trade_date] = sr.CalendarEntry(
                trade_date, day_type, session_open, session_close,
                description, source, verified)
    return entries


def _cas_rule_confirmed(catalogue, instrument_id):
    row = catalogue.con.execute(
        "SELECT count(*) FROM instrument_rule WHERE instrument_id = ? AND "
        "rule_type = 'SESSION_PATTERN' AND value = 'CAS' AND source IN "
        "('OWNER_CONFIRMED', 'OFFICIAL_REFERENCE')", [instrument_id]
    ).fetchone()
    return bool(row[0])


# --- Main logic: the initial load ---------------------------------------------------
def run_initial_load(data_root_path, selected_files, calendar_file=None,
                     live_log=None, progress=None):
    """Create the data root and catalogue, import the selected source files,
    derive the calendar, validate, and write the report (02 section 9.1).

    `selected_files`: the exact files the Owner picked. Only they are
    examined (G-09). `progress(step, total, text)` feeds a progress bar."""
    now = datetime.now()
    suffix = timestamp_suffix(now)
    data_root = storage.DataRoot(data_root_path)
    data_root.ensure_layout()
    log_path = data_root.folder("logs", "qmap_data_manager_%s.log" % suffix)
    logger = _make_logger(log_path, live_log)
    result = InitialLoadResult(log_path=log_path)

    def report_progress(step, total, text):
        if progress is not None:
            progress(step, total, text)

    # A catalogue backup is taken before every maintenance run (02 section 10);
    # on the very first load there is nothing to back up yet.
    backup_path = None
    if os.path.exists(data_root.catalogue_path):
        backup_path = data_root.folder(
            "backups", "catalogue", "qmap_catalogue_%s.duckdb" % suffix)
        shutil.copy2(data_root.catalogue_path, backup_path)
        logger.info("catalogue backed up to %s", backup_path)

    catalogue = Catalogue(data_root.catalogue_path)
    try:
        catalogue.ensure_schema()
        catalogue.register_initial_content()

        for message in storage.startup_recovery(data_root, catalogue):
            logger.info(message)
        integrity_problems = storage.integrity_check(data_root, catalogue)
        for problem in integrity_problems:
            logger.info(problem)
        if integrity_problems:
            raise RuntimeError(
                "The stored data does not match the catalogue. Restore a "
                "catalogue backup and run Check integrity before loading. "
                "Details: %s" % "; ".join(integrity_problems))

        run_id = catalogue.start_run("INITIAL", log_path, backup_path)
        result.run_id = run_id
        logger.info("initial load started (run %d), %d file(s) selected",
                    run_id, len(selected_files))

        instruments = catalogue.instruments()
        total_steps = len(selected_files) + 3
        step = 0

        # --- Map every selected file to an instrument, by alias only. ---------
        by_instrument = {}
        for path in selected_files:
            step += 1
            report_progress(step, total_steps, "Examining %s"
                            % os.path.basename(path))
            if not os.path.exists(path):
                facts = {"name": os.path.basename(path), "size": None,
                         "modified": None}
                catalogue.log_import(run_id, path, facts["name"], None, None,
                                     None, None, None, None, 0, 0, 0, 0, 0, 0,
                                     ACTION_FAILED, "file not found")
                result.file_outcomes.append(FileOutcome(
                    path, None, ACTION_FAILED, "file not found"))
                logger.info("%s: not found", path)
                continue
            sha = sha256_of_file(path)
            instrument = match_instrument(path, instruments)
            if instrument is None:
                facts = _file_facts(path)
                catalogue.log_import(run_id, path, facts["name"],
                                     facts["size"], facts["modified"], sha,
                                     None, None, None, 0, 0, 0, 0, 0, 0,
                                     ACTION_FAILED,
                                     "unrecognised file name - not a "
                                     "registered instrument")
                result.unrecognised_files.append(path)
                result.file_outcomes.append(FileOutcome(
                    path, None, ACTION_FAILED,
                    "unrecognised - not a registered instrument"))
                logger.info("%s: not imported - file name is not a registered "
                            "instrument", facts["name"])
                continue
            by_instrument.setdefault(instrument["instrument_id"],
                                     []).append((path, sha, instrument))

        # --- G-16: several files for one symbol. ------------------------------
        dates_by_instrument = {}
        for instrument_id, entries in sorted(by_instrument.items()):
            distinct_shas = {sha for _, sha, _ in entries}
            instrument = entries[0][2]
            if len(distinct_shas) > 1:
                _record_source_conflict(catalogue, logger, run_id,
                                        instrument_id, instrument, entries,
                                        result)
                continue
            import_path, sha, instrument = entries[0]
            # Byte-identical copies are the same content: imported once, every
            # further path recorded (G-16).
            for extra_path, extra_sha, _ in entries[1:]:
                facts = _file_facts(extra_path)
                catalogue.log_import(run_id, extra_path, facts["name"],
                                     facts["size"], facts["modified"],
                                     extra_sha, None,
                                     instrument["dataset_id"], instrument_id,
                                     0, 0, 0, 0, 0, 0,
                                     ACTION_DUPLICATE_SOURCE,
                                     "byte-identical copy of %s"
                                     % os.path.basename(import_path))
                result.file_outcomes.append(FileOutcome(
                    extra_path, instrument_id, ACTION_DUPLICATE_SOURCE,
                    "byte-identical copy"))
                logger.info("%s: duplicate of %s", facts["name"],
                            os.path.basename(import_path))

            step += 1
            report_progress(min(step, total_steps), total_steps,
                            "Importing %s" % instrument_id)
            outcome, instrument_dates = _import_instrument_file(
                data_root, catalogue, logger, run_id, instrument, import_path,
                sha)
            result.file_outcomes.append(outcome)
            if instrument_dates is not None:
                dates_by_instrument[instrument_id] = instrument_dates

        # --- Calendar: derive, then the optional official file (G-02). --------
        step = total_steps - 1
        report_progress(step, total_steps, "Deriving the calendar")
        derived = sr.derive_calendar(dates_by_instrument)
        catalogue.upsert_derived_calendar(derived)
        logger.info("derived calendar: %d row(s), all unverified",
                    len(derived))
        if calendar_file:
            _import_calendar_file(catalogue, logger, run_id, calendar_file)

        # --- Daily completeness, V-CAL checks and coverage roll-up. ------------
        _missing_day_checks(catalogue, logger, run_id, dates_by_instrument)
        _rollup_coverage(catalogue)

        # --- Report and run closure. -------------------------------------------
        report_progress(total_steps, total_steps, "Writing the report")
        report_path = data_root.folder(
            "reports", "Q-MAP_Validation_Report_%s.xlsx" % suffix)
        write_validation_report(catalogue, report_path, run_id)
        imported = sum(1 for o in result.file_outcomes if o.action == ACTION_NEW)
        failed = sum(1 for o in result.file_outcomes
                     if o.action in (ACTION_FAILED, ACTION_SOURCE_CONFLICT))
        open_warnings = catalogue.con.execute(
            "SELECT count(*) FROM data_issue WHERE severity = 'WARNING' AND "
            "status = 'OPEN'").fetchone()[0]
        status = (cat_mod.RUN_STATUS_SUCCESS
                  if failed == 0 and open_warnings == 0
                  else cat_mod.RUN_STATUS_SUCCESS_WITH_WARNINGS)
        if imported == 0 and failed > 0:
            status = cat_mod.RUN_STATUS_FAILED
        summary = ("%d file(s) imported, %d not imported, %d open warning(s)"
                   % (imported, failed, open_warnings))
        catalogue.finish_run(run_id, status, len(selected_files), summary,
                             report_path)
        result.status = status
        result.summary = summary
        result.report_path = report_path
        logger.info("initial load finished: %s - %s", status, summary)
        return result
    finally:
        catalogue.close()


def _record_source_conflict(catalogue, logger, run_id, instrument_id,
                            instrument, entries, result):
    """G-16: any fingerprint difference is a conflict for the Owner. Nothing
    is imported for the symbol until the Owner chooses; no content comparison,
    no merging, no automatic selection."""
    details = []
    for path, sha, _ in entries:
        facts = _file_facts(path)
        extra = _describe_file_for_conflict(path, instrument)
        details.append("%s (size %d bytes%s, sha256 %s)"
                       % (facts["name"], facts["size"], extra, sha))
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha, None,
                             instrument["dataset_id"], instrument_id,
                             0, 0, 0, 0, 0, 0, ACTION_SOURCE_CONFLICT,
                             "conflicting source files for %s - the Owner "
                             "must choose" % instrument_id)
        result.file_outcomes.append(FileOutcome(
            path, instrument_id, ACTION_SOURCE_CONFLICT,
            "conflicting sources - Owner must choose"))
    issue = IssueRecord(
        "G-16", validation.SEVERITY_WARNING,
        "%s: %d source files with different fingerprints were selected. "
        "Nothing was imported for this instrument. Please choose which file "
        "is its source." % (instrument_id, len(entries)),
        evidence=" | ".join(details))
    catalogue.add_issue(issue, instrument["dataset_id"], instrument_id, run_id)
    logger.info("%s: SOURCE_CONFLICT - %d files, nothing imported",
                instrument_id, len(entries))


def _describe_file_for_conflict(path, instrument):
    """Best-effort row count and date range for the conflict issue evidence."""
    try:
        intraday = instrument["dataset_id"] == "NSE_INDEX_1M"
        reader_result = detect_and_read(path, intraday)
        frame = reader_result.frame
        column = "ts" if reader_result.is_intraday else "trade_date"
        return (", rows %d, %s to %s"
                % (len(frame), frame[column].min(), frame[column].max()))
    except (FileImportError, Exception):
        return ""


def _read_standardise_validate(catalogue, instrument, path):
    """The shared pipeline: read a source file, standardise it with the
    current confirmations, and validate it. Raises FileImportError for a
    file-level failure. Returns a dict with everything later steps need."""
    instrument_id = instrument["instrument_id"]
    dataset = catalogue.dataset(instrument["dataset_id"])
    intraday = dataset["data_kind"] == "intraday_ohlcv"
    reader_result = detect_and_read(path, intraday)

    if intraday:
        standardised = std.standardise_intraday(
            reader_result.frame,
            calendar_entries=_verified_calendar_entries(catalogue),
            owner_confirmations=catalogue.session_confirmations(instrument_id),
            cas_rule_confirmed=_cas_rule_confirmed(catalogue, instrument_id))
        records, quarantine, issues = validation.validate_intraday(
            standardised, instrument_id,
            tick_rules=catalogue.get_tick_rules(instrument_id))
        profiles, profile_issues = validation.build_day_profiles(
            records, quarantine, standardised.day_classes, instrument_id)
        issues.extend(profile_issues)
        for day in reader_result.resolution_suspect_days:
            issues.append(IssueRecord(
                "RESOLUTION_SUSPECT", validation.SEVERITY_WARNING,
                "%s %s: most records on this day are coarser than 1 minute "
                "inside a 1-minute file; kept unchanged" % (instrument_id,
                                                            day)))
    else:
        standardised = std.standardise_daily(reader_result.frame)
        records, quarantine, issues = validation.validate_daily(standardised,
                                                                instrument_id)
        profiles = []

    return {"dataset": dataset, "intraday": intraday,
            "reader_result": reader_result, "standardised": standardised,
            "records": records, "quarantine": quarantine, "issues": issues,
            "profiles": profiles,
            "time_column": "ts" if intraday else "trade_date"}


def _import_instrument_file(data_root, catalogue, logger, run_id, instrument,
                            path, sha):
    """Read, standardise, validate and commit one instrument's source file as
    its first generation. Returns (FileOutcome, dates or None)."""
    instrument_id = instrument["instrument_id"]
    dataset = catalogue.dataset(instrument["dataset_id"])
    facts = _file_facts(path)
    import_id = catalogue.reserve_import_id()

    try:
        processed = _read_standardise_validate(catalogue, instrument, path)
    except FileImportError as exc:
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha, None,
                             dataset["dataset_id"], instrument_id,
                             0, 0, 0, 0, 0, 0, ACTION_FAILED, str(exc))
        logger.info("%s: FAILED - %s", facts["name"], exc)
        return FileOutcome(path, instrument_id, ACTION_FAILED, str(exc)), None

    reader_result = processed["reader_result"]
    standardised = processed["standardised"]
    records = processed["records"]
    quarantine = processed["quarantine"]
    issues = processed["issues"]
    profiles = processed["profiles"]
    intraday = processed["intraday"]
    time_column = processed["time_column"]
    rows_read = len(reader_result.frame)

    if reader_result.ignored_columns:
        catalogue.add_issue(IssueRecord(
            "V-SCH-02", validation.SEVERITY_INFO,
            "%s: columns ignored on import of %s: %s"
            % (instrument_id, facts["name"],
               ", ".join(reader_result.ignored_columns))),
            dataset["dataset_id"], instrument_id, run_id)
    for note in standardised.info_notes + reader_result.notes:
        catalogue.add_issue(IssueRecord("V-TS-03", validation.SEVERITY_INFO,
                                        "%s: %s" % (instrument_id, note)),
                            dataset["dataset_id"], instrument_id, run_id)

    quarantine_path = storage.write_quarantine(
        data_root, dataset["dataset_id"], instrument["file_safe_name"],
        import_id, quarantine, intraday)
    if quarantine_path:
        logger.info("%s: %d row(s) quarantined to %s", instrument_id,
                    len(quarantine), quarantine_path)
        catalogue.add_issue(IssueRecord(
            "QUARANTINE", validation.SEVERITY_WARNING,
            "%s: %d row(s) failed validation and were quarantined "
            "(reasons: %s)" % (instrument_id, len(quarantine),
                               ", ".join(sorted(
                                   quarantine["reason_code"].unique())))),
            dataset["dataset_id"], instrument_id, run_id)

    generation = (instrument["active_generation"] or 0) + 1
    try:
        _commit_generation(data_root, catalogue, instrument, generation,
                           records, profiles, import_id, intraday, run_id)
    except SimulatedInterruption:
        raise
    except Exception as exc:
        storage.discard_staging(data_root, dataset["dataset_id"],
                                instrument["file_safe_name"], generation)
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha, reader_result.reader_id,
                             dataset["dataset_id"], instrument_id, rows_read,
                             0, len(quarantine), 0, 0, 0, ACTION_FAILED,
                             "generation validation failed: %s" % exc)
        logger.info("%s: FAILED - generation validation: %s", instrument_id,
                    exc)
        return (FileOutcome(path, instrument_id, ACTION_FAILED, str(exc)),
                None)
    dates = (records["ts"].dt.date if intraday else records["trade_date"])

    for issue in issues:
        catalogue.add_issue(issue, dataset["dataset_id"], instrument_id,
                            run_id)
    catalogue.log_import(run_id, path, facts["name"], facts["size"],
                         facts["modified"], sha, reader_result.reader_id,
                         dataset["dataset_id"], instrument_id, rows_read,
                         len(records), len(quarantine), len(records), 0, 0,
                         ACTION_NEW, "initial import", import_id=import_id)
    logger.info("%s: imported %d row(s), %d quarantined, generation %d active",
                instrument_id, len(records), len(quarantine), generation)
    outcome = FileOutcome(path, instrument_id, ACTION_NEW,
                          "imported", len(records), len(quarantine))
    return outcome, set(dates)


def _import_calendar_file(catalogue, logger, run_id, calendar_file):
    """G-02 step 1: import the reference calendar as unconfirmed rows."""
    try:
        entries = sr.read_official_calendar_file(calendar_file)
    except FileImportError as exc:
        catalogue.log_import(run_id, calendar_file,
                             os.path.basename(calendar_file), None, None,
                             None, None, None, None, 0, 0, 0, 0, 0, 0,
                             ACTION_FAILED, str(exc))
        logger.info("calendar file not loaded: %s", exc)
        return
    catalogue.import_reference_calendar(entries)
    facts = _file_facts(calendar_file)
    catalogue.log_import(run_id, calendar_file, facts["name"], facts["size"],
                         facts["modified"], sha256_of_file(calendar_file),
                         "CAL", None, None, len(entries), len(entries), 0,
                         len(entries), 0, 0, ACTION_NEW,
                         "reference calendar imported as "
                         "REFERENCE_FILE_UNCONFIRMED (G-02); recording "
                         "provenance is a separate Owner step")
    logger.info("calendar file imported: %d row(s), unconfirmed until the "
                "Owner records provenance", len(entries))


def _missing_day_checks(catalogue, logger, run_id, dates_by_instrument):
    """V-CAL-02: a trading day missing for one instrument inside its own date
    range may be a stock suspension - reported, never filled. A trading day
    here is any date on which some instrument has data (derived calendar)."""
    all_dates = set()
    for dates in dates_by_instrument.values():
        all_dates.update(dates)
    # Expected trading days are weekdays only: a derived weekend session is a
    # SPECIAL day, not a TRADING day, so an instrument without data on it is
    # not reported as missing (02 section 8).
    trading_days = {d for d in all_dates if d.weekday() < 5}
    for instrument in catalogue.instruments():
        instrument_id = instrument["instrument_id"]
        own = dates_by_instrument.get(instrument_id)
        if not own:
            continue
        first, last = min(own), max(own)
        missing = sorted(d for d in trading_days
                         if first <= d <= last and d not in own)
        for day in missing:
            day_ts = datetime.combine(day, datetime.min.time())
            catalogue.add_issue(IssueRecord(
                "V-CAL-02", validation.SEVERITY_WARNING,
                "%s %s: no data on a day other instruments traded "
                "(MISSING_DAY; may be a stock suspension)"
                % (instrument_id, day), ts_from=day_ts, ts_to=day_ts),
                instrument["dataset_id"], instrument_id, run_id)
        if missing:
            logger.info("%s: %d missing day(s) inside its range",
                        instrument_id, len(missing))


def _rollup_coverage(catalogue):
    """Set quality and completeness status per instrument (02 section 5.4).

    Completeness stays PROVISIONAL_DERIVED_CALENDAR until an official calendar
    with recorded provenance covers the range (G-02)."""
    for instrument in catalogue.instruments():
        instrument_id = instrument["instrument_id"]
        if instrument["active_generation"] is None:
            continue
        warnings, errors = catalogue.open_issue_counts(instrument_id)
        missing_candles = catalogue.con.execute(
            "SELECT coalesce(sum(missing_candles), 0) FROM day_profile WHERE "
            "instrument_id = ?", [instrument_id]).fetchone()[0]
        missing_days = catalogue.con.execute(
            "SELECT count(*) FROM data_issue WHERE instrument_id = ? AND "
            "check_code = 'V-CAL-02' AND status = 'OPEN'",
            [instrument_id]).fetchone()[0]
        unconfirmed = catalogue.con.execute(
            "SELECT count(*) FROM day_profile WHERE instrument_id = ? AND "
            "session_status IN ('UNRECOGNISED_SESSION_SHAPE', 'CANDIDATE')",
            [instrument_id]).fetchone()[0]
        completeness = (cat_mod.COMPLETENESS_GAPS
                        if (missing_candles or missing_days)
                        else cat_mod.COMPLETENESS_COMPLETE)
        quality = (cat_mod.QUALITY_PASS_WITH_WARNINGS
                   if (warnings or unconfirmed)
                   else cat_mod.QUALITY_PASS)
        catalogue.update_coverage_status(
            instrument_id, completeness, cat_mod.BASIS_PROVISIONAL, quality,
            warnings, errors)


# --- Main logic: Excel validation report ---------------------------------------------
def write_validation_report(catalogue, report_path, run_id):
    """One Excel validation report per run (02 section 11): Summary, Coverage,
    Issues, Day_Profiles, Imports, Revisions."""
    book = Workbook()

    summary = book.active
    summary.title = "Summary"
    run = catalogue.con.execute(
        "SELECT run_type, started_at, status, files_examined, summary FROM "
        "maintenance_run WHERE run_id = ?", [run_id]).fetchone()
    summary.append(["Q-MAP Validation Report"])
    summary.append(["Run", run_id])
    if run:
        summary.append(["Type", run[0]])
        summary.append(["Started", run[1].strftime("%d %b %y, %I:%M %p")
                        if run[1] else ""])
        summary.append(["Status", run[2]])
        summary.append(["Files examined", run[3]])
        summary.append(["Summary", run[4]])
    issue_counts = catalogue.con.execute(
        "SELECT severity, count(*) FROM data_issue WHERE status = 'OPEN' "
        "GROUP BY severity ORDER BY severity").fetchall()
    summary.append([])
    summary.append(["Open issues by severity"])
    for severity, count in issue_counts:
        summary.append([severity, count])

    def add_sheet(title, headers, rows, date_columns=()):
        sheet = book.create_sheet(title)
        sheet.append(headers)
        for row in rows:
            formatted = []
            for position, value in enumerate(row):
                if position in date_columns and value is not None:
                    formatted.append(human_date(value))
                elif hasattr(value, "strftime") and value is not None:
                    formatted.append(str(value))
                else:
                    formatted.append(value)
            sheet.append(formatted)

    add_sheet("Coverage",
              ["Dataset", "Instrument", "Generation", "First", "Last",
               "Trading days", "Rows", "Volume from", "Volume to", "Quality",
               "Completeness", "Basis", "Open warnings", "Open errors"],
              catalogue.coverage_table(), date_columns=(7, 8))
    add_sheet("Issues",
              ["Issue", "Dataset", "Instrument", "From", "To", "Check",
               "Severity", "Description", "Evidence", "Blocks continuity",
               "Status", "Note"],
              catalogue.get_issues(min_severity="INFO", status=None))
    add_sheet("Day_Profiles",
              ["Instrument", "Date", "First record", "Last candle",
               "Shape", "Status", "Type", "Expected", "Basis", "Present",
               "Missing", "Missing ranges", "Auction phase", "Closing auction",
               "Volume", "Quarantined"],
              catalogue.con.execute(
                  "SELECT instrument_id, trade_date, first_record, "
                  "last_continuous_candle, observed_shape, session_status, "
                  "session_type, expected_candles, expected_basis, "
                  "present_candles, missing_candles, missing_ranges, "
                  "has_auction_phase, has_closing_auction, has_volume, "
                  "quarantined_rows FROM day_profile ORDER BY instrument_id, "
                  "trade_date").fetchall(), date_columns=(1,))
    add_sheet("Imports",
              ["Import", "Run", "Path", "Name", "Size", "Modified", "SHA-256",
               "Reader", "Dataset", "Instrument", "Read", "Stored",
               "Quarantined", "New", "Changed", "Removed", "Action", "Message"],
              catalogue.con.execute(
                  "SELECT * FROM import_log ORDER BY import_id").fetchall())
    add_sheet("Revisions",
              ["Instrument", "Detected", "Status", "Evidence"],
              [])  # Held revisions arrive with M1b.

    book.save(report_path)
    return report_path


# --- Main logic: M1a machine-readable evidence (EV-01 to EV-04) -----------------------
def export_m1a_evidence(data_root_path, output_folder):
    """Write the EV-01 to EV-04 evidence files (Verification Package v1.2,
    section 10). Timestamps follow TS-01: YYYY-MM-DD HH:MM:SS, IST wall clock,
    never converted; booleans TRUE/FALSE; nulls empty."""
    data_root = storage.DataRoot(data_root_path)
    catalogue = Catalogue(data_root.catalogue_path, read_only=True)
    os.makedirs(output_folder, exist_ok=True)
    suffix = timestamp_suffix()
    written = []
    try:
        def write_csv(name, frame):
            path = os.path.join(output_folder, name)
            for column in frame.columns:
                if pd.api.types.is_datetime64_any_dtype(frame[column]):
                    frame[column] = frame[column].dt.strftime(
                        EVIDENCE_TS_FORMAT)
                elif frame[column].dtype == object:
                    frame[column] = frame[column].map(
                        lambda v: ("TRUE" if v is True else
                                   "FALSE" if v is False else v))
                elif pd.api.types.is_bool_dtype(frame[column]):
                    frame[column] = frame[column].map(
                        lambda v: "TRUE" if v else "FALSE")
            frame.to_csv(path, index=False)
            written.append(path)

        write_csv("EV01_source_fingerprints_%s.csv" % suffix,
                  catalogue.con.execute(
                      "SELECT source_name, source_path, source_size, "
                      "source_sha256, reader_used, dataset_id, instrument_id, "
                      "rows_read, rows_stored, rows_quarantined, action, "
                      "message FROM import_log ORDER BY import_id").df())
        for instrument_id in ("NIFTY", "BANKNIFTY"):
            write_csv("EV02_day_profiles_%s_%s.csv" % (instrument_id, suffix),
                      catalogue.con.execute(
                          "SELECT * FROM day_profile WHERE instrument_id = ? "
                          "ORDER BY trade_date", [instrument_id]).df())
        write_csv("EV03_record_counts_%s.csv" % suffix,
                  _record_counts_frame(data_root, catalogue))
        write_csv("EV04_issues_%s.csv" % suffix,
                  catalogue.con.execute(
                      "SELECT * FROM data_issue ORDER BY issue_id").df())
        write_csv("EV04_quarantine_%s.csv" % suffix,
                  _quarantine_frame(data_root))
        return written
    finally:
        catalogue.close()


def _record_counts_frame(data_root, catalogue):
    rows = []
    for instrument in catalogue.instruments():
        if instrument["active_generation"] is None:
            continue
        folder = data_root.market_generation(instrument["dataset_id"],
                                             instrument["file_safe_name"],
                                             instrument["active_generation"])
        files = [os.path.join(folder, f) for f in sorted(os.listdir(folder))]
        frame = pd.concat([pd.read_parquet(f) for f in files],
                          ignore_index=True)
        if "record_type" in frame.columns:
            counts = frame.groupby("record_type").size()
            flagged = frame["quality_flags"].fillna("").str.contains(
                "SESSION_UNCONFIRMED").sum()
            for record_type, count in counts.items():
                rows.append({"instrument_id": instrument["instrument_id"],
                             "record_type": record_type, "count": int(count),
                             "session_unconfirmed_rows": int(flagged)})
        else:
            rows.append({"instrument_id": instrument["instrument_id"],
                         "record_type": "DAILY", "count": len(frame),
                         "session_unconfirmed_rows": 0})
    return pd.DataFrame(rows)


def _quarantine_frame(data_root):
    folder = data_root.folder("quarantine")
    frames = []
    for dataset_id in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        dataset_folder = os.path.join(folder, dataset_id)
        for name in sorted(os.listdir(dataset_folder)):
            frame = pd.read_parquet(os.path.join(dataset_folder, name))
            frame.insert(0, "file", name)
            frame.insert(0, "dataset_id", dataset_id)
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["dataset_id", "file", "reason_code"])
    return pd.concat(frames, ignore_index=True)


# =============================================================================
# M1b - incremental maintenance, held revisions, backup and restore
# (document 02 v1.6, sections 9.2, 9.3, 9.6 and 10)
# =============================================================================

class SimulatedInterruption(BaseException):
    """Failure injection for T-MNT-06a/b/c: simulates the process being killed
    at a defined point. It derives from BaseException so that no ordinary
    error handling or rollback code runs - exactly as a real kill would leave
    things - and recovery at the next start must cope."""


@dataclass
class UpdateResult:
    run_id: int = None
    status: str = ""
    file_outcomes: list = field(default_factory=list)
    unrecognised_files: list = field(default_factory=list)
    inaccessible_sources: list = field(default_factory=list)
    out_of_scope_sources: int = 0
    report_path: str = ""
    log_path: str = ""
    summary: str = ""


# --- Helpers shared by every generation-writing run ----------------------------
def _build_coverage_row(records, intraday, dataset_id, import_id):
    """Coverage facts from the canonical records (D-03: volume availability is
    recorded, never an error)."""
    time_column = "ts" if intraday else "trade_date"
    if intraday:
        candles = records[records["record_type"] == std.RECORD_CANDLE]
        with_volume = candles.loc[candles["volume"].notna(), "ts"].dt.date
        dates = records["ts"].dt.date
    else:
        with_volume = records.loc[records["volume"].notna(), "trade_date"]
        dates = records["trade_date"]
    return {
        "dataset_id": dataset_id,
        "first_ts": pd.Timestamp(records[time_column].min()).to_pydatetime(),
        "last_ts": pd.Timestamp(records[time_column].max()).to_pydatetime(),
        "trading_days": int(dates.nunique()),
        "row_count": len(records),
        "volume_first_date": (with_volume.min() if len(with_volume) else None),
        "volume_last_date": (with_volume.max() if len(with_volume) else None),
        "last_import_id": import_id,
        "quality_status": cat_mod.QUALITY_UNVALIDATED,
        "completeness_status": cat_mod.COMPLETENESS_UNKNOWN,
        "completeness_basis": cat_mod.BASIS_PROVISIONAL,
        "open_warning_count": 0,
        "open_error_count": 0,
    }


def _commit_generation(data_root, catalogue, instrument, generation, records,
                       profiles, import_id, intraday, run_id,
                       test_hooks=None):
    """Steps 1-5 of the commit protocol for one instrument (02 section 9.4).
    Raises on a staged-validation failure, leaving the previous generation
    active; the caller discards staging and records the failure."""
    hooks = test_hooks or {}
    dataset_id = instrument["dataset_id"]
    file_rows = storage.stage_and_validate_generation(
        data_root, dataset_id, instrument["instrument_id"],
        instrument["file_safe_name"], generation, records, import_id,
        intraday, after_stage_hook=hooks.get("after_stage"))
    storage.move_generation_into_market(
        data_root, dataset_id, instrument["file_safe_name"], generation)
    if hooks.get("after_rename") is not None:
        hooks["after_rename"]()
    coverage_row = _build_coverage_row(records, intraday, dataset_id,
                                       import_id)
    catalogue.activate_generation(
        instrument["instrument_id"], generation, file_rows, coverage_row,
        profiles, run_id, in_transaction_hook=hooks.get("in_activation"))
    for message in storage.prune_generations(
            data_root, catalogue, data_root.folder("backups", "catalogue")):
        pass  # pruning messages go to the run log via the caller's logger
    return file_rows


def _stored_canonical(data_root, catalogue, instrument):
    """Every canonical row of the instrument's active generation."""
    folder = data_root.market_generation(instrument["dataset_id"],
                                         instrument["file_safe_name"],
                                         instrument["active_generation"])
    files = [os.path.join(folder, name) for name in sorted(os.listdir(folder))]
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _compare_with_active(stored, new_records, intraday):
    """Full-overlap comparison by key (02 section 9.2): every row is NEW,
    UNCHANGED, CHANGED or REMOVED. Comparing the whole overlap, not only the
    latest date, is what catches silent history revisions."""
    key = "ts" if intraday else "trade_date"
    value_columns = ["open", "high", "low", "close", "volume"]
    stored_frame = stored[[key] + value_columns].copy()
    new_frame = new_records[[key] + value_columns].copy()
    merged = stored_frame.merge(new_frame, on=key, how="outer",
                                suffixes=("_old", "_new"), indicator=True)

    new_mask = merged["_merge"] == "right_only"
    # REMOVED means any stored key absent from the newer file. The inspected
    # sources always deliver an instrument's complete history in one file, so
    # a key the new file no longer carries is a removal of stored history -
    # at the start (T-MNT-05), in the middle, or at the end - and is held.
    removed_mask = merged["_merge"] == "left_only"
    both = merged[merged["_merge"] == "both"]
    changed_mask = pd.Series(False, index=both.index)
    for column in value_columns:
        old_values, new_values = both[column + "_old"], both[column + "_new"]
        differs = (old_values != new_values) & ~(old_values.isna()
                                                 & new_values.isna())
        changed_mask |= differs

    changed = both[changed_mask]
    result = {
        "key": key,
        "new_count": int(new_mask.sum()),
        "changed_count": int(len(changed)),
        "removed_count": int(removed_mask.sum()),
        "changed_keys": changed[key].tolist(),
        "sample_differences": [],
        "uniform_factor": None,
        "uniform_effective": None,
    }
    for _, row in changed.head(20).iterrows():
        result["sample_differences"].append(
            "%s: old O/H/L/C/V %s/%s/%s/%s/%s -> new %s/%s/%s/%s/%s"
            % tuple([row[key]]
                    + [row[c + "_old"] for c in value_columns]
                    + [row[c + "_new"] for c in value_columns]))

    # Uniform-factor test: all changed rows lie before one date and new/old
    # equals one factor within 0.01%. The same pattern arises from a genuine
    # corporate action AND from an erroneous vendor change, so it is only ever
    # a *candidate*, never proof (02 section 9.3).
    if len(changed) and result["removed_count"] == 0:
        ratios = []
        for column in ("open", "high", "low", "close"):
            old_values = changed[column + "_old"].astype(float)
            new_values = changed[column + "_new"].astype(float)
            ratios.append(new_values / old_values)
        ratio_frame = pd.concat(ratios)
        factor = float(ratio_frame.median())
        if factor > 0 and ((ratio_frame - factor).abs()
                           <= abs(factor) * 0.0001).all():
            last_changed = max(result["changed_keys"])
            later_stored = stored_frame.loc[stored_frame[key] > last_changed,
                                            key]
            if len(later_stored):
                result["uniform_factor"] = factor
                result["uniform_effective"] = later_stored.min()
    return result


def _hold_revision(data_root, catalogue, logger, run_id, instrument, path,
                   sha, facts, processed, comparison, import_id):
    """OD-04 / V-REV-01: the whole revised file is held, including its new
    rows, with the revision evidence; the active generation is untouched."""
    instrument_id = instrument["instrument_id"]
    folder = data_root.folder("held", instrument["dataset_id"])
    os.makedirs(folder, exist_ok=True)
    held_path = os.path.join(folder, "%s_imp%06d.parquet"
                             % (instrument["file_safe_name"], import_id))
    records = processed["records"].copy()
    records["quality_flags"] = storage.flags_to_text(records["quality_flags"])
    records["import_id"] = import_id
    records.to_parquet(held_path)

    if comparison["uniform_factor"] is not None:
        factor_text = ("uniform factor %.4f, effective %s, candidate "
                       "corporate action - not verified"
                       % (comparison["uniform_factor"],
                          comparison["uniform_effective"]))
    else:
        factor_text = "not uniform"
    changed_keys = comparison["changed_keys"]
    evidence = ("new=%d changed=%d removed=%d | changed range: %s to %s | "
                "%s | source sha256 %s | samples: %s"
                % (comparison["new_count"], comparison["changed_count"],
                   comparison["removed_count"],
                   min(changed_keys) if changed_keys else "-",
                   max(changed_keys) if changed_keys else "-",
                   factor_text, sha,
                   " ; ".join(comparison["sample_differences"][:20])))
    catalogue.add_issue(IssueRecord(
        "V-REV-01", validation.SEVERITY_WARNING,
        "%s: a newer source file changes stored history (%d changed, %d "
        "removed, %d new row(s)). The revision is HELD for your review; "
        "active data is unchanged and stops advancing until you approve or "
        "reject it." % (instrument_id, comparison["changed_count"],
                        comparison["removed_count"], comparison["new_count"]),
        evidence=evidence), instrument["dataset_id"], instrument_id, run_id)
    catalogue.log_import(run_id, path, facts["name"], facts["size"],
                         facts["modified"], sha,
                         processed["reader_result"].reader_id,
                         instrument["dataset_id"], instrument_id,
                         len(processed["reader_result"].frame),
                         0, len(processed["quarantine"]),
                         comparison["new_count"], comparison["changed_count"],
                         comparison["removed_count"], "HELD_REVISION",
                         "revision held for Owner review (%s)" % factor_text,
                         import_id=import_id)
    logger.info("%s: HELD_REVISION (%d changed, %d removed, %d new; %s)",
                instrument_id, comparison["changed_count"],
                comparison["removed_count"], comparison["new_count"],
                factor_text)
    return held_path


# --- Main logic: the incremental update (02 section 9.2) -------------------------
def run_update(data_root_path, selected_folders, live_log=None, progress=None,
               test_hooks=None, owner_chosen_paths=None):
    """Find changed source files in the folders the Owner selected for THIS
    update (G-09), import only what is new, hold every history revision, and
    report. `owner_chosen_paths` are files the Owner explicitly chose after a
    SOURCE_CONFLICT; they go through the ordinary update path."""
    now = datetime.now()
    suffix = timestamp_suffix(now)
    data_root = storage.DataRoot(data_root_path)
    data_root.ensure_layout()
    log_path = data_root.folder("logs", "qmap_data_manager_%s.log" % suffix)
    logger = _make_logger(log_path, live_log)
    result = UpdateResult(log_path=log_path)
    chosen = {os.path.abspath(p) for p in (owner_chosen_paths or [])}

    if not os.path.exists(data_root.catalogue_path):
        raise RuntimeError("No Q-MAP catalogue exists at this data root yet. "
                           "Please run Initial load first.")
    backup_path = data_root.folder("backups", "catalogue",
                                   "qmap_catalogue_%s.duckdb" % suffix)
    shutil.copy2(data_root.catalogue_path, backup_path)
    logger.info("catalogue backed up to %s", backup_path)

    catalogue = Catalogue(data_root.catalogue_path)
    try:
        catalogue.ensure_schema()
        for message in storage.startup_recovery(data_root, catalogue):
            logger.info(message)
        integrity_problems = storage.integrity_check(data_root, catalogue)
        for problem in integrity_problems:
            logger.info(problem)
        if integrity_problems:
            raise RuntimeError(
                "INTEGRITY_MISMATCH: the stored data does not match the "
                "catalogue. Restore a catalogue backup and run Check "
                "integrity. Details: %s" % "; ".join(integrity_problems))

        run_id = catalogue.start_run("INCREMENTAL", log_path, backup_path)
        result.run_id = run_id
        logger.info("update started (run %d), %d folder(s) selected",
                    run_id, len(selected_folders))

        instruments = catalogue.instruments()
        by_id = {i["instrument_id"]: i for i in instruments}
        registered = catalogue.registered_sources()
        registered_paths = {}
        for source_path, _, instrument_id, _ in registered:
            registered_paths.setdefault(instrument_id, set()).add(
                os.path.abspath(source_path))

        # G-09: only the selected folders are in scope; files directly inside
        # them with a supported extension. Registered sources outside them are
        # counted, never examined, never removed.
        selected = [os.path.abspath(f) for f in selected_folders]
        found_files = []
        for folder in selected:
            if not os.path.isdir(folder):
                logger.info("selected folder not accessible: %s", folder)
                continue
            for name in sorted(os.listdir(folder)):
                path = os.path.join(folder, name)
                if os.path.isfile(path) and os.path.splitext(name)[1].lower() \
                        in (".parquet", ".txt", ".csv"):
                    found_files.append(path)

        def inside_selected(path):
            parent = os.path.dirname(os.path.abspath(path))
            return parent in selected

        found_set = {os.path.abspath(p) for p in found_files}
        for source_path, _, instrument_id, _ in registered:
            absolute = os.path.abspath(source_path)
            if inside_selected(absolute):
                if not os.path.exists(absolute) or not os.access(absolute,
                                                                 os.R_OK):
                    catalogue.add_issue(IssueRecord(
                        "G-09", validation.SEVERITY_WARNING,
                        "%s: registered source is missing or unreadable: %s. "
                        "The registration is kept and the stored data is "
                        "unchanged (SOURCE_INACCESSIBLE)."
                        % (instrument_id, source_path)),
                        by_id[instrument_id]["dataset_id"], instrument_id,
                        run_id)
                    result.inaccessible_sources.append(source_path)
                    logger.info("%s: SOURCE_INACCESSIBLE %s", instrument_id,
                                source_path)
            elif absolute not in found_set:
                result.out_of_scope_sources += 1
        if result.out_of_scope_sources:
            logger.info("%d registered source(s) not in scope for this "
                        "update", result.out_of_scope_sources)

        # Map found files to instruments and group for G-16.
        by_instrument = {}
        for path in found_files:
            instrument = match_instrument(path, instruments)
            if instrument is None:
                sha = sha256_of_file(path)
                facts = _file_facts(path)
                catalogue.log_import(run_id, path, facts["name"],
                                     facts["size"], facts["modified"], sha,
                                     None, None, None, 0, 0, 0, 0, 0, 0,
                                     ACTION_FAILED,
                                     "unrecognised file name - not a "
                                     "registered instrument")
                result.unrecognised_files.append(path)
                result.file_outcomes.append(FileOutcome(
                    path, None, ACTION_FAILED,
                    "unrecognised - not a registered instrument"))
                continue
            by_instrument.setdefault(instrument["instrument_id"],
                                     []).append((path, instrument))

        run_failed = False
        for instrument_id, entries in sorted(by_instrument.items()):
            instrument = entries[0][1]
            history = catalogue.sha_history(instrument_id)
            fresh = []
            for path, _ in entries:
                sha = sha256_of_file(path)
                facts = _file_facts(path)
                absolute = os.path.abspath(path)
                if sha in history["known"]:
                    catalogue.log_import(
                        run_id, path, facts["name"], facts["size"],
                        facts["modified"], sha, None,
                        instrument["dataset_id"], instrument_id,
                        0, 0, 0, 0, 0, 0, "SKIPPED_UNCHANGED",
                        "fingerprint unchanged since the last import")
                    result.file_outcomes.append(FileOutcome(
                        path, instrument_id, "SKIPPED_UNCHANGED", ""))
                    logger.info("%s: SKIPPED_UNCHANGED (%s)", instrument_id,
                                facts["name"])
                elif sha in history["rejected"]:
                    catalogue.log_import(
                        run_id, path, facts["name"], facts["size"],
                        facts["modified"], sha, None,
                        instrument["dataset_id"], instrument_id,
                        0, 0, 0, 0, 0, 0, "REJECTED_REVISION",
                        "this revision was rejected earlier; it is not "
                        "offered again")
                    result.file_outcomes.append(FileOutcome(
                        path, instrument_id, "REJECTED_REVISION", ""))
                elif sha in history["held"]:
                    catalogue.log_import(
                        run_id, path, facts["name"], facts["size"],
                        facts["modified"], sha, None,
                        instrument["dataset_id"], instrument_id,
                        0, 0, 0, 0, 0, 0, "HELD_REVISION",
                        "already held and awaiting your approve/reject "
                        "decision")
                    result.file_outcomes.append(FileOutcome(
                        path, instrument_id, "HELD_REVISION",
                        "already held"))
                else:
                    fresh.append((path, sha, facts, absolute))

            if not fresh:
                continue
            if len({sha for _, sha, _, _ in fresh}) > 1:
                _record_source_conflict(catalogue, logger, run_id,
                                        instrument_id, instrument,
                                        [(p, s, instrument)
                                         for p, s, _, _ in fresh], result)
                continue
            path, sha, facts, absolute = fresh[0]
            known_paths = registered_paths.get(instrument_id, set())
            if instrument["active_generation"] is None:
                outcome, _ = _import_instrument_file(
                    data_root, catalogue, logger, run_id, instrument, path,
                    sha)
                result.file_outcomes.append(outcome)
                if outcome.action == ACTION_FAILED:
                    run_failed = True
                continue
            if known_paths and absolute not in known_paths \
                    and absolute not in chosen:
                # G-16: a different file at a different path is a conflict for
                # the Owner, even when the prices might be the same.
                _record_source_conflict(
                    catalogue, logger, run_id, instrument_id, instrument,
                    [(path, sha, instrument)], result)
                continue

            outcome = _update_one_instrument(data_root, catalogue, logger,
                                             run_id, instrument, path, sha,
                                             facts, test_hooks)
            result.file_outcomes.append(outcome)
            if outcome.action == ACTION_FAILED:
                run_failed = True

        _rollup_coverage(catalogue)
        for outcome in result.file_outcomes:
            # 02 section 5.4: FAIL means the latest update for the instrument
            # was not activated; the previous generation stays readable.
            if outcome.action == ACTION_FAILED and outcome.instrument_id:
                catalogue.con.execute(
                    "UPDATE coverage SET quality_status = ? WHERE "
                    "instrument_id = ?",
                    [cat_mod.QUALITY_FAIL, outcome.instrument_id])

        report_path = data_root.folder(
            "reports", "Q-MAP_Validation_Report_%s.xlsx" % suffix)
        write_validation_report(catalogue, report_path, run_id)
        open_warnings = catalogue.con.execute(
            "SELECT count(*) FROM data_issue WHERE severity = 'WARNING' AND "
            "status = 'OPEN'").fetchone()[0]
        if run_failed:
            status = cat_mod.RUN_STATUS_FAILED
        elif open_warnings:
            status = cat_mod.RUN_STATUS_SUCCESS_WITH_WARNINGS
        else:
            status = cat_mod.RUN_STATUS_SUCCESS
        summary = "; ".join("%s %s" % (o.instrument_id or "?", o.action)
                            for o in result.file_outcomes) or "nothing to do"
        catalogue.finish_run(run_id, status, len(found_files), summary,
                             report_path)
        result.status = status
        result.summary = summary
        result.report_path = report_path
        logger.info("update finished: %s - %s", status, summary)
        return result
    finally:
        catalogue.close()


def _update_one_instrument(data_root, catalogue, logger, run_id, instrument,
                           path, sha, facts, test_hooks):
    """One changed source file for an instrument with active data: read,
    standardise, compare the whole overlap, then APPEND or HOLD."""
    instrument_id = instrument["instrument_id"]
    import_id = catalogue.reserve_import_id()
    try:
        processed = _read_standardise_validate(catalogue, instrument, path)
    except FileImportError as exc:
        # T-MNT-17a: a failed file gives FAILED, the active generation and
        # its rows stay exactly as they were, and quality_status turns FAIL.
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha, None,
                             instrument["dataset_id"], instrument_id,
                             0, 0, 0, 0, 0, 0, ACTION_FAILED, str(exc))
        logger.info("%s: FAILED - %s", instrument_id, exc)
        return FileOutcome(path, instrument_id, ACTION_FAILED, str(exc))

    stored = _stored_canonical(data_root, catalogue, instrument)
    comparison = _compare_with_active(stored, processed["records"],
                                      processed["intraday"])

    if comparison["changed_count"] or comparison["removed_count"]:
        _hold_revision(data_root, catalogue, logger, run_id, instrument, path,
                       sha, facts, processed, comparison, import_id)
        return FileOutcome(path, instrument_id, "HELD_REVISION",
                           "revision held for review",
                           rows_quarantined=len(processed["quarantine"]))

    generation = instrument["active_generation"] + 1
    try:
        storage.write_quarantine(data_root, instrument["dataset_id"],
                                 instrument["file_safe_name"], import_id,
                                 processed["quarantine"],
                                 processed["intraday"])
        _commit_generation(data_root, catalogue, instrument, generation,
                           processed["records"], processed["profiles"],
                           import_id, processed["intraday"], run_id,
                           test_hooks)
    except SimulatedInterruption:
        raise
    except Exception as exc:
        # T-MNT-17b: the staged generation failed validation. Staging is
        # discarded, nothing was renamed or activated, the previous
        # generation stays active, and the instrument is FAIL.
        storage.discard_staging(data_root, instrument["dataset_id"],
                                instrument["file_safe_name"], generation)
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha,
                             processed["reader_result"].reader_id,
                             instrument["dataset_id"], instrument_id,
                             len(processed["reader_result"].frame), 0,
                             len(processed["quarantine"]), 0, 0, 0,
                             ACTION_FAILED,
                             "staged generation validation failed: %s" % exc)
        logger.info("%s: FAILED - staged validation: %s", instrument_id, exc)
        return FileOutcome(path, instrument_id, ACTION_FAILED, str(exc))

    for issue in processed["issues"]:
        catalogue.add_issue(issue, instrument["dataset_id"], instrument_id,
                            run_id)
    catalogue.log_import(run_id, path, facts["name"], facts["size"],
                         facts["modified"], sha,
                         processed["reader_result"].reader_id,
                         instrument["dataset_id"], instrument_id,
                         len(processed["reader_result"].frame),
                         len(processed["records"]),
                         len(processed["quarantine"]),
                         comparison["new_count"], 0, 0, "APPEND",
                         "appended %d new row(s)" % comparison["new_count"],
                         import_id=import_id)
    logger.info("%s: APPEND %d new row(s), generation %d active",
                instrument_id, comparison["new_count"], generation)
    return FileOutcome(path, instrument_id, "APPEND", "",
                       rows_stored=len(processed["records"]),
                       rows_quarantined=len(processed["quarantine"]))


# --- Main logic: the Owner's approve / reject decision (02 section 9.3) ----------
def approve_held_revision(data_root_path, instrument_id, live_log=None):
    """APPLY_APPROVED_REVISION: build a new generation from the held data,
    validate it and activate it. The previous generation is retained."""
    suffix = timestamp_suffix()
    data_root = storage.DataRoot(data_root_path)
    log_path = data_root.folder("logs", "qmap_data_manager_%s.log" % suffix)
    logger = _make_logger(log_path, live_log)
    backup_path = data_root.folder("backups", "catalogue",
                                   "qmap_catalogue_%s.duckdb" % suffix)
    shutil.copy2(data_root.catalogue_path, backup_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        held = catalogue.held_import(instrument_id)
        if held is None:
            raise RuntimeError("No held revision exists for %s."
                               % instrument_id)
        held_import_id, source_path, source_sha = held
        instrument = [i for i in catalogue.instruments()
                      if i["instrument_id"] == instrument_id][0]
        dataset = catalogue.dataset(instrument["dataset_id"])
        intraday = dataset["data_kind"] == "intraday_ohlcv"
        held_path = data_root.folder(
            "held", instrument["dataset_id"],
            "%s_imp%06d.parquet" % (instrument["file_safe_name"],
                                    held_import_id))
        held_frame = pd.read_parquet(held_path)

        run_id = catalogue.start_run("APPLY_APPROVED_REVISION", log_path,
                                     backup_path)
        import_id = catalogue.reserve_import_id()
        held_frame["quality_flags"] = held_frame["quality_flags"].map(
            lambda text: set(text.split(";")) if text else set())
        if intraday:
            # Rebuild the raw rows and re-run the full pipeline, so profiles
            # and classifications are recomputed for the revised data.
            raw = pd.DataFrame({
                "ts": held_frame["source_ts"],
                "open": held_frame["open"], "high": held_frame["high"],
                "low": held_frame["low"], "close": held_frame["close"],
                "volume": held_frame["volume"].astype("Int64"),
                "source_row": range(1, len(held_frame) + 1)})
            standardised = std.standardise_intraday(
                raw, calendar_entries=_verified_calendar_entries(catalogue),
                owner_confirmations=catalogue.session_confirmations(
                    instrument_id),
                cas_rule_confirmed=_cas_rule_confirmed(catalogue,
                                                       instrument_id))
            records, quarantine, issues = validation.validate_intraday(
                standardised, instrument_id,
                tick_rules=catalogue.get_tick_rules(instrument_id))
            profiles, profile_issues = validation.build_day_profiles(
                records, quarantine, standardised.day_classes, instrument_id)
            issues.extend(profile_issues)
        else:
            records = held_frame[["trade_date", "open", "high", "low",
                                  "close", "volume"]].copy()
            records["volume"] = records["volume"].astype("Int64")
            records["source_row"] = range(1, len(records) + 1)
            standardised = std.standardise_daily(records)
            records, quarantine, issues = validation.validate_daily(
                standardised, instrument_id)
            profiles = []

        generation = instrument["active_generation"] + 1
        storage.write_quarantine(data_root, instrument["dataset_id"],
                                 instrument["file_safe_name"], import_id,
                                 quarantine, intraday)
        _commit_generation(data_root, catalogue, instrument, generation,
                           records, profiles, import_id, intraday, run_id)
        for issue in issues:
            catalogue.add_issue(issue, instrument["dataset_id"],
                                instrument_id, run_id)
        catalogue.resolve_issues(instrument_id, "V-REV-01",
                                 "approved by the Owner")
        catalogue.log_import(run_id, source_path,
                             os.path.basename(source_path), None, None,
                             source_sha, None, instrument["dataset_id"],
                             instrument_id, len(records), len(records),
                             len(quarantine), 0, 0, 0,
                             "APPLIED_APPROVED_REVISION",
                             "held revision approved and activated as "
                             "generation %d" % generation,
                             import_id=import_id)
        _rollup_coverage(catalogue)
        report_path = data_root.folder(
            "reports", "Q-MAP_Validation_Report_%s.xlsx" % suffix)
        write_validation_report(catalogue, report_path, run_id)
        catalogue.finish_run(run_id, cat_mod.RUN_STATUS_SUCCESS_WITH_WARNINGS,
                             1, "%s: approved revision activated"
                             % instrument_id, report_path)
        logger.info("%s: approved revision active as generation %d",
                    instrument_id, generation)
        return generation
    finally:
        catalogue.close()


def reject_held_revision(data_root_path, instrument_id, note="", live_log=None):
    """The held data is kept as evidence, marked REJECTED_REVISION, and the
    same source fingerprint is not offered again. Active data unchanged."""
    data_root = storage.DataRoot(data_root_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        held = catalogue.held_import(instrument_id)
        if held is None:
            raise RuntimeError("No held revision exists for %s."
                               % instrument_id)
        _, source_path, source_sha = held
        instrument = [i for i in catalogue.instruments()
                      if i["instrument_id"] == instrument_id][0]
        catalogue.log_import(None, source_path,
                             os.path.basename(source_path), None, None,
                             source_sha, None, instrument["dataset_id"],
                             instrument_id, 0, 0, 0, 0, 0, 0,
                             "REJECTED_REVISION",
                             "held revision rejected by the Owner. %s" % note)
        catalogue.resolve_issues(instrument_id, "V-REV-01",
                                 "rejected by the Owner. %s" % note)
    finally:
        catalogue.close()


# --- Main logic: re-validation after Owner confirmations --------------------------
def run_revalidate(data_root_path, instrument_ids=None, live_log=None):
    """REVALIDATE: re-classify stored intraday data under the current
    confirmations (CAS rule, special sessions, official calendar) into a new
    generation. Prices are rebuilt from the stored records' own source
    timestamps and values; nothing is read from source files."""
    suffix = timestamp_suffix()
    data_root = storage.DataRoot(data_root_path)
    log_path = data_root.folder("logs", "qmap_data_manager_%s.log" % suffix)
    logger = _make_logger(log_path, live_log)
    backup_path = data_root.folder("backups", "catalogue",
                                   "qmap_catalogue_%s.duckdb" % suffix)
    shutil.copy2(data_root.catalogue_path, backup_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        run_id = catalogue.start_run("REVALIDATE", log_path, backup_path)
        for instrument in catalogue.instruments():
            instrument_id = instrument["instrument_id"]
            if instrument_ids and instrument_id not in instrument_ids:
                continue
            dataset = catalogue.dataset(instrument["dataset_id"])
            if dataset["data_kind"] != "intraday_ohlcv" \
                    or instrument["active_generation"] is None:
                continue
            stored = _stored_canonical(data_root, catalogue, instrument)
            raw = pd.DataFrame({
                "ts": stored["source_ts"],
                "open": stored["open"], "high": stored["high"],
                "low": stored["low"], "close": stored["close"],
                "volume": stored["volume"].astype("Int64"),
                "source_row": range(1, len(stored) + 1)})
            standardised = std.standardise_intraday(
                raw, calendar_entries=_verified_calendar_entries(catalogue),
                owner_confirmations=catalogue.session_confirmations(
                    instrument_id),
                cas_rule_confirmed=_cas_rule_confirmed(catalogue,
                                                       instrument_id))
            records, quarantine, issues = validation.validate_intraday(
                standardised, instrument_id,
                tick_rules=catalogue.get_tick_rules(instrument_id))
            profiles, profile_issues = validation.build_day_profiles(
                records, quarantine, standardised.day_classes, instrument_id)
            issues.extend(profile_issues)

            import_id = catalogue.reserve_import_id()
            generation = instrument["active_generation"] + 1
            storage.write_quarantine(data_root, instrument["dataset_id"],
                                     instrument["file_safe_name"], import_id,
                                     quarantine, True)
            _commit_generation(data_root, catalogue, instrument, generation,
                               records, profiles, import_id, True, run_id)
            # Session findings are recomputed from scratch for this
            # instrument; stale ones are closed first, then re-added.
            for check_code in ("V-SES-01", "V-SES-02"):
                catalogue.resolve_issues(instrument_id, check_code,
                                         "superseded by re-validation run %d"
                                         % run_id)
            for issue in issues:
                catalogue.add_issue(issue, instrument["dataset_id"],
                                    instrument_id, run_id)
            catalogue.log_import(run_id, "(stored data)", "(stored data)",
                                 None, None, None, None,
                                 instrument["dataset_id"], instrument_id,
                                 len(stored), len(records), len(quarantine),
                                 0, 0, 0, "APPEND",
                                 "re-validated under current confirmations "
                                 "as generation %d" % generation,
                                 import_id=import_id)
            logger.info("%s: re-validated as generation %d", instrument_id,
                        generation)
        _rollup_coverage(catalogue)
        report_path = data_root.folder(
            "reports", "Q-MAP_Validation_Report_%s.xlsx" % suffix)
        write_validation_report(catalogue, report_path, run_id)
        catalogue.finish_run(run_id, cat_mod.RUN_STATUS_SUCCESS_WITH_WARNINGS,
                             0, "re-validation completed", report_path)
    finally:
        catalogue.close()


# --- Main logic: Owner confirmations ------------------------------------------------
def confirm_cas_rule(data_root_path, instrument_id, evidence, confirmed_at):
    """Record the Owner's confirmation of an instrument's CAS rule (D-06) and
    re-validate the instrument."""
    data_root = storage.DataRoot(data_root_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        from datetime import date as date_type
        catalogue.record_session_confirmation(
            instrument_id, "CAS", date_type(2026, 8, 3), None, evidence,
            confirmed_at)
    finally:
        catalogue.close()
    run_revalidate(data_root_path, [instrument_id])


def confirm_special_session(data_root_path, instrument_id, trade_date,
                            session_type, session_open, session_close,
                            evidence, confirmed_at):
    """Record the Owner's confirmation of one special session and re-validate
    the instrument."""
    from . import session_rules as sr
    data_root = storage.DataRoot(data_root_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        value = sr.encode_session_confirmation(session_type, session_open,
                                               session_close)
        catalogue.record_session_confirmation(instrument_id, value,
                                              trade_date, trade_date,
                                              evidence, confirmed_at)
    finally:
        catalogue.close()
    run_revalidate(data_root_path, [instrument_id])


def verify_continuity_issue(data_root_path, issue_id, owner_note):
    """G-03: the Owner, after personally verifying one occurrence, marks that
    issue VERIFIED_OK (affects_continuity becomes false in the same
    transaction, 02 section 5.2). A catalogue backup is taken first. Only an
    OPEN continuity-blocking issue can be verified; nothing else changes."""
    if not owner_note or not owner_note.strip():
        raise ValueError("A verification note (your basis) is required.")
    data_root = storage.DataRoot(data_root_path)
    backup_path = data_root.folder("backups", "catalogue",
                                   "qmap_catalogue_%s.duckdb"
                                   % timestamp_suffix())
    shutil.copy2(data_root.catalogue_path, backup_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        open_ids = {row[0] for row in
                    catalogue.continuity_issues_awaiting_owner()}
        if issue_id not in open_ids:
            raise ValueError("Issue %s is not an open continuity-blocking "
                             "issue." % issue_id)
        catalogue.mark_issue_verified_ok(issue_id, owner_note.strip())
    finally:
        catalogue.close()
    return backup_path


# --- Main logic: integrity check and restore (02 section 10) ------------------------
def run_integrity_check(data_root_path, live_log=None):
    """Check integrity: every active-generation file exists and matches its
    catalogue fingerprint and row count; unactivated generations are handled
    by the start-up recovery. Returns the problem list (empty = PASS)."""
    data_root = storage.DataRoot(data_root_path)
    catalogue = Catalogue(data_root.catalogue_path)
    try:
        messages = storage.startup_recovery(data_root, catalogue)
        problems = storage.integrity_check(data_root, catalogue)
    finally:
        catalogue.close()
    if live_log:
        for message in messages + (problems or ["Integrity check PASSED."]):
            live_log(message)
    return problems


def restore_from_backup(data_root_path, backup_path, live_log=None):
    """Restore procedure of 02 section 10: copy the chosen catalogue backup
    over the live catalogue, then run Check integrity. Every Q-MAP program
    must be closed first."""
    data_root = storage.DataRoot(data_root_path)
    storage.restore_catalogue_backup(data_root, backup_path)
    if live_log:
        live_log("catalogue restored from %s" % backup_path)
    return run_integrity_check(data_root_path, live_log=live_log)


# =============================================================================
# M2 - machine-readable evidence EV-05 to EV-10 (Verification Package v1.2
# section 10). Timestamps follow TS-01; nulls are empty fields; booleans are
# TRUE/FALSE; prices keep full precision with no thousands separators.
# =============================================================================

def _evidence_bars_csv(result, path):
    """Write a BarResult's bars in the evidence format."""
    frame = result.bars.copy()
    for column in ("ts", "source_ts"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column]).dt.strftime(
                EVIDENCE_TS_FORMAT)
    for column in ("is_complete", "is_forming", "session_truncated",
                   "volume_complete"):
        if column in frame.columns:
            frame[column] = frame[column].map(
                lambda value: "TRUE" if bool(value) else "FALSE")
    frame.to_csv(path, index=False)


def _evidence_meta_json(result, path):
    import json

    def plain(value):
        if hasattr(value, "strftime"):
            return value.strftime(EVIDENCE_TS_FORMAT)
        if isinstance(value, (list, tuple)):
            return [plain(item) for item in value]
        if isinstance(value, dict):
            return {key: plain(item) for key, item in value.items()}
        if hasattr(value, "item"):
            return value.item()
        return value

    with open(path, "w", encoding="utf-8") as handle:
        json.dump({key: plain(value) for key, value in result.meta.items()},
                  handle, indent=2)


def export_m2_evidence(data_root_path, output_folder):
    """Write EV-05 to EV-10. Returns the list of files written."""
    from .access import DataRequirement, QMapData
    from .errors import QMapDataError

    os.makedirs(output_folder, exist_ok=True)
    suffix = timestamp_suffix()
    written = []

    def out(name):
        path = os.path.join(output_folder, name)
        written.append(path)
        return path

    incomplete_frames = []

    def export_bars(file_stem, result, collect_incomplete=False):
        _evidence_bars_csv(result, out("%s_%s.csv" % (file_stem, suffix)))
        _evidence_meta_json(result, out("%s_meta_%s.json"
                                        % (file_stem, suffix)))
        if collect_incomplete:
            bars = result.bars
            candles = bars[~bars["record_type"].isin(["AUCTION_PHASE",
                                                      "CLOSING_AUCTION"])]
            incomplete = candles[~candles["is_complete"].astype(bool)].copy()
            if len(incomplete):
                incomplete.insert(0, "timeframe", result.meta["timeframe"])
                incomplete.insert(0, "instrument_id",
                                  result.meta["instrument_id"])
                incomplete_frames.append(incomplete)

    with QMapData(data_root_path) as db:
        # EV-05 and EV-06: the four reference days.
        for instrument_id, day, ev in (("NIFTY", "2026-08-17", "EV05"),
                                       ("BANKNIFTY", "2026-08-19", "EV06")):
            for timeframe in ("5m", "15m"):
                result = db.get_bars(instrument_id, timeframe, day, day)
                export_bars("%s_bars_%s_%s_%s"
                            % (ev, instrument_id, timeframe,
                               day.replace("-", "")), result)

        # EV-07: full daily output per instrument.
        for row in db.list_instruments().itertuples():
            result = db.get_bars(row.instrument_id, "1D")
            export_bars("EV07_bars_%s_1D_all" % row.instrument_id, result)

        # EV-08: whole-sample aggregation (and EV-09's inputs).
        for instrument_id, timeframes in (("NIFTY", ("3m", "5m", "15m",
                                                     "1MO")),
                                          ("BANKNIFTY", ("5m", "15m"))):
            for timeframe in timeframes:
                result = db.get_bars(instrument_id, timeframe)
                export_bars("EV08_bars_%s_%s_all" % (instrument_id,
                                                     timeframe), result,
                            collect_incomplete=timeframe in ("5m", "15m"))

        # EV-09: every incomplete 5m/15m bar in the whole sample.
        if incomplete_frames:
            frame = pd.concat(incomplete_frames, ignore_index=True)
            frame["ts"] = pd.to_datetime(frame["ts"]).dt.strftime(
                EVIDENCE_TS_FORMAT)
            frame.to_csv(out("EV09_incomplete_bars_%s.csv" % suffix),
                         index=False)

        # EV-10: the DA-1 to DA-24 results.
        rows = []

        def record(case_id, call_text, outcome, detail=""):
            rows.append({"case": case_id, "call": call_text,
                         "outcome": outcome, "detail": detail})

        def bars_case(case_id, call_text, **kwargs):
            try:
                result = db.get_bars(**kwargs)
                record(case_id, call_text,
                       result.status,
                       "rows=%d; warnings=%s; notes=%s"
                       % (len(result.bars),
                          "|".join(sorted(w["code"]
                                          for w in result.meta["warnings"])),
                          "|".join(result.meta["notes"])))
            except QMapDataError as error:
                record(case_id, call_text, type(error).__name__, str(error))

        bars_case("DA-1", "NIFTY 5m 2026-08-17", instrument_id="NIFTY",
                  timeframe="5m", start="2026-08-17", end="2026-08-17")
        bars_case("DA-2", "DA-1 without auction rows", instrument_id="NIFTY",
                  timeframe="5m", start="2026-08-17", end="2026-08-17",
                  include_auction_records=False)
        bars_case("DA-3", "BANKNIFTY 5m 2026-08-19",
                  instrument_id="BANKNIFTY", timeframe="5m",
                  start="2026-08-19", end="2026-08-19")
        bars_case("DA-4", "BANKNIFTY 15m 2026-08-19",
                  instrument_id="BANKNIFTY", timeframe="15m",
                  start="2026-08-19", end="2026-08-19")
        bars_case("DA-5", "CONCOR 1D latest_n=5 close",
                  instrument_id="CONCOR", timeframe="1D", latest_n=5,
                  fields=["close"])
        try:
            db.get_bars("NIFTI", "5m")
        except QMapDataError as error:
            record("DA-6", "NIFTI", type(error).__name__, str(error))
        try:
            db.list_instruments(dataset_id="NSE_FUT_1M")
        except QMapDataError as error:
            record("DA-7", "list_instruments(NSE_FUT_1M)",
                   type(error).__name__, str(error))
        bars_case("DA-8", "NIFTY 5m 2026-01-26", instrument_id="NIFTY",
                  timeframe="5m", start="2026-01-26", end="2026-01-26")
        bars_case("DA-9", "NIFTY 5m 2024-06-03..07", instrument_id="NIFTY",
                  timeframe="5m", start="2024-06-03", end="2024-06-07")
        bars_case("DA-10", "BANKNIFTY 1D Aug-26", instrument_id="BANKNIFTY",
                  timeframe="1D", start="2026-08-01", end="2026-08-31")
        bars_case("DA-11", "NIFTY 1D Jan-25 close+volume",
                  instrument_id="NIFTY", timeframe="1D", start="2025-01-09",
                  end="2025-01-31", fields=["close", "volume"])
        try:
            db.get_bars("CONCOR", "1D", fields=["oi"])
        except QMapDataError as error:
            record("DA-12", "CONCOR fields oi", type(error).__name__,
                   str(error))

        def availability_case(case_id, call_text, requirement):
            report = db.check_availability(requirement)
            record(case_id, call_text, report.status,
                   "reasons=%s; missing=%s; estimated_bars=%d"
                   % ("|".join(sorted(reason["code"]
                                      for reason in report.reasons)),
                      ",".join(report.missing_fields),
                      report.estimated_bars))
            _evidence_availability_json(report, out(
                "EV10_%s_availability_%s.json" % (case_id, suffix)))

        availability_case("DA-13", "NIFTY 5m Jan-25 volume required",
                          DataRequirement("NIFTY", "5m", "2025-01-09",
                                          "2025-01-31",
                                          required_fields=("close",
                                                           "volume")))
        try:
            db.get_bars("CONCOR", "15m")
        except QMapDataError as error:
            record("DA-14", "CONCOR 15m", type(error).__name__, str(error))
        try:
            db.get_bars("NIFTY", "7m")
        except QMapDataError as error:
            record("DA-15", "NIFTY 7m", type(error).__name__, str(error))
        try:
            db.get_bars("NIFTY", "5m", "2026-09-30", "2026-09-01")
        except QMapDataError as error:
            record("DA-16", "start after end", type(error).__name__,
                   str(error))
        bars_case("DA-17", "NIFTY 5m 2025-10-21", instrument_id="NIFTY",
                  timeframe="5m", start="2025-10-21", end="2025-10-21")
        bars_case("DA-18", "BANKNIFTY 5m 2026-11-08",
                  instrument_id="BANKNIFTY", timeframe="5m",
                  start="2026-11-08", end="2026-11-08")
        bars_case("DA-19", "BANKNIFTY 15m 2026-11-08",
                  instrument_id="BANKNIFTY", timeframe="15m",
                  start="2026-11-08", end="2026-11-08")
        bars_case("DA-20", "NIFTY 5m 2026-08-14..17", instrument_id="NIFTY",
                  timeframe="5m", start="2026-08-14", end="2026-08-17")
        availability_case("DA-21", "NIFTY 1D 10-21 Aug volume required",
                          DataRequirement("NIFTY", "1D", "2026-08-10",
                                          "2026-08-21",
                                          required_fields=("close",
                                                           "volume")))
        availability_case("DA-22", "NIFTY 1D 17-21 Aug volume required",
                          DataRequirement("NIFTY", "1D", "2026-08-17",
                                          "2026-08-21",
                                          required_fields=("close",
                                                           "volume")))
        availability_case("DA-23", "NIFTY 1D Jan-25 volume optional",
                          DataRequirement("NIFTY", "1D", "2025-01-09",
                                          "2025-01-31"))
        instruments = db.list_instruments(dataset_id="NSE_INDEX_1M")
        record("DA-24", "list_instruments(NSE_INDEX_1M)", "OK",
               ",".join(instruments["instrument_id"].tolist()))

        pd.DataFrame(rows).to_csv(out("EV10_da_results_%s.csv" % suffix),
                                  index=False)
    return written


def _evidence_availability_json(report, path):
    import json

    def plain(value):
        if hasattr(value, "strftime"):
            return value.strftime(EVIDENCE_TS_FORMAT)
        if hasattr(value, "item"):
            return value.item()
        return value

    payload = {"status": report.status, "reasons": report.reasons,
               "available_start": plain(report.available_start),
               "available_end": plain(report.available_end),
               "estimated_bars": int(report.estimated_bars),
               "missing_fields": list(report.missing_fields),
               "continuity_issues": [
                   {key: plain(value) for key, value in issue.items()}
                   for issue in report.continuity_issues]}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
