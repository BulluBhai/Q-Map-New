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
                                     "unrecognised file name - please map it "
                                     "to an instrument")
                result.unrecognised_files.append(path)
                result.file_outcomes.append(FileOutcome(
                    path, None, ACTION_FAILED,
                    "unrecognised - please map"))
                logger.info("%s: unrecognised - please map", facts["name"])
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


def _import_instrument_file(data_root, catalogue, logger, run_id, instrument,
                            path, sha):
    """Read, standardise, validate and commit one instrument's source file as
    its first generation. Returns (FileOutcome, dates or None)."""
    instrument_id = instrument["instrument_id"]
    dataset = catalogue.dataset(instrument["dataset_id"])
    intraday = dataset["data_kind"] == "intraday_ohlcv"
    facts = _file_facts(path)
    import_id = catalogue.reserve_import_id()

    try:
        reader_result = detect_and_read(path, intraday)
    except FileImportError as exc:
        catalogue.log_import(run_id, path, facts["name"], facts["size"],
                             facts["modified"], sha, None,
                             dataset["dataset_id"], instrument_id,
                             0, 0, 0, 0, 0, 0, ACTION_FAILED, str(exc))
        logger.info("%s: FAILED - %s", facts["name"], exc)
        return FileOutcome(path, instrument_id, ACTION_FAILED, str(exc)), None

    rows_read = len(reader_result.frame)
    if reader_result.ignored_columns:
        catalogue.add_issue(IssueRecord(
            "V-SCH-02", validation.SEVERITY_INFO,
            "%s: columns ignored on import of %s: %s"
            % (instrument_id, facts["name"],
               ", ".join(reader_result.ignored_columns))),
            dataset["dataset_id"], instrument_id, run_id)

    if intraday:
        standardised = std.standardise_intraday(
            reader_result.frame,
            calendar_entries=_verified_calendar_entries(catalogue),
            owner_confirmations={},
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
        time_column = "ts"
    else:
        standardised = std.standardise_daily(reader_result.frame)
        records, quarantine, issues = validation.validate_daily(standardised,
                                                                instrument_id)
        profiles = []
        time_column = "trade_date"

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
        file_rows = storage.stage_and_validate_generation(
            data_root, dataset["dataset_id"], instrument_id,
            instrument["file_safe_name"], generation, records, import_id,
            intraday)
        storage.move_generation_into_market(
            data_root, dataset["dataset_id"], instrument["file_safe_name"],
            generation)
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

    # Volume availability for coverage (D-03: missing volume is not an error).
    if intraday:
        candles = records[records["record_type"] == std.RECORD_CANDLE]
        with_volume = candles.loc[candles["volume"].notna(), "ts"].dt.date
    else:
        with_volume = records.loc[records["volume"].notna(), "trade_date"]
    dates = (records["ts"].dt.date if intraday else records["trade_date"])

    coverage_row = {
        "dataset_id": dataset["dataset_id"],
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
    # Step 4 of the commit protocol: the single catalogue transaction.
    catalogue.activate_generation(instrument_id, generation, file_rows,
                                  coverage_row, profiles, run_id)

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
            catalogue.add_issue(IssueRecord(
                "V-CAL-02", validation.SEVERITY_WARNING,
                "%s %s: no data on a day other instruments traded "
                "(MISSING_DAY; may be a stock suspension)"
                % (instrument_id, day)),
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
