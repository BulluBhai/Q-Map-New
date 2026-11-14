"""Scanner contract version 1.0 (document 04 v1.3, section 7).

The single definition of what a scanner receives (ScannerContext) and returns
(a ScannerResult dictionary), plus validate_result(), which every result must
pass before it is accepted. Data is obtained only through
ScannerContext.fetch, which calls the read-only QMapData interface; a scanner
never sees a path, a file or SQL (SC-02).
"""

# --- Imports -----------------------------------------------------------------
import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

from qmap_database.access import DataRequirement  # noqa: F401  (re-exported)

# --- Constants ---------------------------------------------------------------
CONTRACT_VERSION = "1.0"
RESULT_SCHEMA_VERSION = "1.0"

STATUS_OK = "OK"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
STATUS_INVALID_DATA = "INVALID_DATA"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_ERROR = "ERROR"
ALL_STATUSES = (STATUS_OK, STATUS_INSUFFICIENT_DATA, STATUS_INVALID_DATA,
                STATUS_NOT_APPLICABLE, STATUS_ERROR)

REQUIRED_KEYS = ("result_schema_version", "scanner", "subject", "parameters",
                 "status", "status_messages", "data_references", "facts",
                 "calculations", "detail_tables", "score", "interpretation")


# --- Data classes -----------------------------------------------------------------
@dataclass(frozen=True)
class ScannerInfo:
    scanner_id: str
    name: str
    version: str
    spec_reference: str
    timeframes: tuple
    produces_score: bool
    score_meaning: str


class UndeclaredRequirementError(Exception):
    """SC-02: a scanner asked for data it did not declare."""


@dataclass
class ScannerContext:
    run_id: str
    instrument_id: str
    parameters: dict
    analysis_start: object
    analysis_end: object
    requirements: list                    # [(DataRequirement, AvailabilityReport)]
    _data: object = field(repr=False, default=None)        # QMapData
    include_auction_records: bool = True
    data_references: list = field(default_factory=list)

    def fetch(self, requirement):
        """The only way a scanner obtains data (document 04 section 7.2)."""
        declared = [req for req, _ in self.requirements]
        if requirement not in declared:
            raise UndeclaredRequirementError(
                "Requirement %r was not declared through data_requirements()."
                % (requirement,))
        fields = tuple(requirement.required_fields) \
            + tuple(requirement.optional_fields)
        result = self._data.get_bars(
            requirement.instrument_id, requirement.timeframe,
            requirement.start, requirement.end, fields=list(fields),
            latest_n=requirement.latest_n,
            include_auction_records=self.include_auction_records,
            exclude_flagged=requirement.exclude_flagged)
        meta = result.meta
        self.data_references.append(to_jsonable({
            "request": {"instrument_id": requirement.instrument_id,
                        "timeframe": requirement.timeframe,
                        "start": requirement.start, "end": requirement.end,
                        "latest_n": requirement.latest_n,
                        "fields": list(fields)},
            "dataset_id": meta.get("dataset_id"),
            "data_version": meta.get("data_version"),
            "returned_first_ts": meta.get("returned_first_ts"),
            "returned_last_ts": meta.get("returned_last_ts"),
            "bar_count": meta.get("bar_count"),
            "timezone": meta.get("timezone"),
            "ts_meaning": meta.get("ts_meaning"),
            "status": result.status,
            "warnings": meta.get("warnings", []),
            "notes": meta.get("notes", []),
            "issues": meta.get("issues", []),
        }))
        return result


# --- Helpers ------------------------------------------------------------------------
def to_jsonable(value):
    """Convert dates, timestamps and numpy scalars to JSON-safe values.
    Dates become ISO YYYY-MM-DD (document 05 section 7.2)."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.time() == datetime.min.time():
            return value.date().isoformat()
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "item"):                 # numpy scalar
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def new_result(info, context, timeframe):
    """An empty result skeleton with every required section."""
    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "scanner": {"scanner_id": info.scanner_id, "name": info.name,
                    "version": info.version,
                    "spec_reference": info.spec_reference},
        "subject": to_jsonable({"instrument_id": context.instrument_id,
                                "timeframe": timeframe,
                                "analysis_start": context.analysis_start,
                                "analysis_end": context.analysis_end}),
        "parameters": dict(context.parameters),
        "status": None,
        "status_messages": [],
        "data_references": context.data_references,
        "facts": {},
        "calculations": {},
        "detail_tables": {},
        "score": None,
        "interpretation": None,
    }


# --- Main logic: contract validation (section 7.7) -----------------------------------
def validate_result(result, info):
    """Return a list of problems; an empty list means the result is valid."""
    problems = []
    if not isinstance(result, dict):
        return ["result is not a dictionary"]
    missing = [key for key in REQUIRED_KEYS if key not in result]
    if missing:
        problems.append("missing keys: %s" % ", ".join(missing))
        return problems
    if result["result_schema_version"] != RESULT_SCHEMA_VERSION:
        problems.append("unknown result_schema_version %r"
                        % result["result_schema_version"])
    scanner = result["scanner"] or {}
    if scanner.get("scanner_id") != info.scanner_id \
            or scanner.get("version") != info.version:
        problems.append("scanner_id/version do not match the registered INFO")
    status = result["status"]
    if status not in ALL_STATUSES:
        problems.append("status %r is not one of the five codes" % status)
    score = result["score"]
    if score is not None:
        if status != STATUS_OK or not info.produces_score:
            problems.append("a score is present although status is %s" % status)
        value = score.get("value") if isinstance(score, dict) else None
        if not isinstance(value, (int, float)) or isinstance(value, bool) \
                or not math.isfinite(value) or not 0 <= value <= 100:
            problems.append("score value %r is not a finite number in [0, 100]"
                            % (value,))
    elif status == STATUS_OK and info.produces_score:
        problems.append("status OK but no score")
    if status == STATUS_OK and not result["data_references"]:
        problems.append("status OK but data_references is empty")
    if result["interpretation"] is not None:
        problems.append("interpretation must be null (Python never writes it)")
    try:
        json.dumps(result, allow_nan=False)
    except (TypeError, ValueError) as exc:
        problems.append("result is not JSON-serialisable: %s" % exc)
    return problems


def error_result(info, context, timeframe, messages):
    """The replacement result for an exception or a failed validation."""
    result = new_result(info, context, timeframe)
    result["status"] = STATUS_ERROR
    result["status_messages"] = list(messages)
    result["facts"] = {}
    result["calculations"] = {}
    result["detail_tables"] = {}
    result["score"] = None
    return result
