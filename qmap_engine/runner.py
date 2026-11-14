"""Run coordinator (document 04 v1.3, M-01; run configuration section 6).

Validates the run configuration, opens the read-only data interface, and for
each instrument and scanner: checks availability, calls the scanner, and
validates its result. A scanner's unexpected exception becomes that result's
ERROR status and the run continues. Combined scoring (M5) is not part of P1
yet, so a scoring profile must not be named.
"""

# --- Imports -----------------------------------------------------------------
import traceback
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from qmap_database.access import QMapData
from qmap_database.errors import QMapDataError

from . import contract, registry

# --- Constants ---------------------------------------------------------------
RUN_CONFIG_VERSION = "1.0"
QMAP_VERSION = "0.9.0"


# --- Structures -----------------------------------------------------------------
@dataclass
class RunConfig:
    data_root: str
    instruments: list
    analysis_end: object
    scanners: list                      # [{"scanner_id": ..., "parameters": {}}]
    analysis_start: object = None
    output_folder: str = ""
    scoring_profile_id: object = None
    options: dict = field(default_factory=lambda: {
        "include_auction_records": True, "exclude_flagged": False})

    def as_dict(self):
        return contract.to_jsonable({
            "run_config_version": RUN_CONFIG_VERSION,
            "data_root": self.data_root, "output_folder": self.output_folder,
            "instruments": list(self.instruments),
            "analysis_start": self.analysis_start,
            "analysis_end": self.analysis_end,
            "scanners": self.scanners,
            "scoring_profile_id": self.scoring_profile_id,
            "options": self.options})


class RunConfigError(Exception):
    """A configuration problem found before any scanner starts."""


@dataclass
class RunResult:
    run_id: str
    created_at: datetime
    config: dict
    scanner_results: list
    combined_scores: list = field(default_factory=list)


# --- Helpers ------------------------------------------------------------------------
def _parse_day(value, name):
    if value is None:
        return None
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError):
        raise RunConfigError("%s %r is not a valid date (use YYYY-MM-DD)."
                             % (name, value))


def validate_config(config, db):
    """Section 6 checks. Fills missing parameters from default_parameters()
    (SC-12) and returns the resolved scanner list [(module, params)]."""
    problems = []
    known = set(db.list_instruments()["instrument_id"])
    for instrument_id in config.instruments:
        if instrument_id not in known:
            problems.append("instrument %s does not exist" % instrument_id)
    if not config.instruments:
        problems.append("no instrument was chosen")
    _parse_day(config.analysis_end, "analysis_end")
    _parse_day(config.analysis_start, "analysis_start")
    if config.scoring_profile_id is not None:
        problems.append("combined scoring profiles are not available yet "
                        "(M5, G-10)")
    resolved = []
    for entry in config.scanners:
        module = registry.SCANNERS.get(entry.get("scanner_id"))
        if module is None:
            problems.append("scanner %s is not registered"
                            % entry.get("scanner_id"))
            continue
        params = dict(module.default_parameters(),
                      **(entry.get("parameters") or {}))
        param_problems = module.validate_parameters(params)
        problems.extend("%s: %s" % (module.INFO.scanner_id, p)
                        for p in param_problems)
        resolved.append((module, params))
    if not config.scanners:
        problems.append("no scanner was chosen")
    if problems:
        raise RunConfigError("The run cannot start: " + "; ".join(problems))
    return resolved


# --- Main logic ---------------------------------------------------------------------
def run_analysis(config, progress=None):
    """Run one analysis. progress(message, done, total) is optional."""
    registry.check_registry()
    created_at = datetime.now()
    run_id = "RUN_%s" % created_at.strftime("%d_%b_%y_%H%M%S")
    results = []
    with QMapData(config.data_root) as db:
        resolved = validate_config(config, db)
        # The resolved parameter sets are recorded in full (SC-12).
        config.scanners = [{"scanner_id": m.INFO.scanner_id,
                            "scanner_version": m.INFO.version,
                            "parameters": dict(p)} for m, p in resolved]
        total = len(config.instruments) * len(resolved)
        done = 0
        for instrument_id in config.instruments:
            for module, params in resolved:
                if progress:
                    progress("%s - %s" % (instrument_id, module.INFO.name),
                             done, total)
                results.append(_run_one(db, run_id, config, instrument_id,
                                        module, params))
                done += 1
        if progress:
            progress("finished", done, total)
    return RunResult(run_id=run_id, created_at=created_at,
                     config=config.as_dict(), scanner_results=results)


def _run_one(db, run_id, config, instrument_id, module, params):
    info = module.INFO
    timeframe = info.timeframes[0]
    requirements = module.data_requirements(instrument_id, params,
                                            config.analysis_start,
                                            config.analysis_end)
    pairs = []
    for requirement in requirements:
        try:
            report = db.check_availability(requirement)
        except QMapDataError as exc:
            context = contract.ScannerContext(
                run_id, instrument_id, params, config.analysis_start,
                config.analysis_end, [])
            result = contract.new_result(info, context, timeframe)
            result["status"] = contract.STATUS_NOT_APPLICABLE
            result["status_messages"].append(str(exc))
            return result
        pairs.append((requirement, report))
    context = contract.ScannerContext(
        run_id=run_id, instrument_id=instrument_id, parameters=params,
        analysis_start=config.analysis_start,
        analysis_end=config.analysis_end, requirements=pairs, _data=db,
        include_auction_records=config.options.get(
            "include_auction_records", True))
    try:
        result = module.run(context)
    except Exception as exc:                  # SC-11: the runner records ERROR
        return contract.error_result(
            info, context, timeframe,
            ["Unexpected error in %s: %s" % (info.scanner_id, exc),
             traceback.format_exc()])
    problems = contract.validate_result(result, info)
    if problems:
        return contract.error_result(
            info, context, timeframe,
            ["The result failed contract validation: %s" % "; ".join(problems)])
    return result
