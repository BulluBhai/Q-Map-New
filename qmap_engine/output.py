"""Output writer (document 04 v1.3, M-06; document 05 v1.1, section 7).

Writes Q-MAP_Run_<suffix>.json and Q-MAP_Run_Report_<suffix>.xlsx to the
folder the user picks. Values are never altered: the JSON holds full
precision; the report only formats them. Each file is written under a
temporary name and then renamed, so no partial file is left behind.
"""

# --- Imports -----------------------------------------------------------------
import hashlib
import json
import os
from datetime import date, datetime

from . import contract
from .runner import QMAP_VERSION

# --- Constants ---------------------------------------------------------------
OUTPUT_VERSION = "1.0"
SCHEMA_NOTES = {
    "timestamps": "IST (Asia/Kolkata) wall-clock; intraday times are interval "
                  "START; dates ISO YYYY-MM-DD",
    "sections": "1 run_context, 2 data_references, 3 scanner_results, "
                "4 combined_scores are calculated by Python and are "
                "authoritative. 5 interpretation is optional commentary and "
                "never changes 1-4.",
    "missing_values": "null means not available; it never means zero",
    "scores": "0-100; meaning defined per scanner (score.calibration)",
}
DATE_FMT = "dd-mmm-yy"


# --- Helpers ------------------------------------------------------------------------
def _suffix(moment):
    return moment.strftime("%d_%b_%y_%H%M%S")


def _canonical_sha256(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_run_json(runs):
    """One JSON document for one or more runs (one per analysis date)."""
    sections = {
        "1_run_context": [{"run_id": r.run_id,
                           "created_at": r.created_at.strftime(
                               "%Y-%m-%d %H:%M:%S"),
                           "qmap_version": QMAP_VERSION,
                           "contract_version": contract.CONTRACT_VERSION,
                           "run_config": r.config} for r in runs],
        "2_data_references": [ref for r in runs for res in r.scanner_results
                              for ref in res["data_references"]],
        "3_scanner_results": [res for r in runs for res in r.scanner_results],
        "4_combined_scores": [],
    }
    payload = {"qmap_run_output_version": OUTPUT_VERSION,
               "schema_notes": SCHEMA_NOTES}
    payload.update(sections)
    payload["5_interpretation"] = None
    payload["integrity"] = {
        "content_sha256": _canonical_sha256(sections),
        "note": "SHA-256 of sections 1-4 serialised with sorted keys and no "
                "spaces. Any change to sections 1-4 changes this value."}
    return payload


def _to_date(text):
    if isinstance(text, str) and len(text) == 10 and text[4] == "-":
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return text
    return text


def _write_sheet(wb, title, headers, rows):
    from openpyxl.styles import Font
    sheet = wb.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    for column in sheet.iter_cols(min_row=2):
        for cell in column:
            if isinstance(cell.value, (date, datetime)):
                cell.number_format = DATE_FMT
    sheet.freeze_panes = "A2"
    for index, header in enumerate(headers, start=1):
        letter = sheet.cell(row=1, column=index).column_letter
        sheet.column_dimensions[letter].width = min(max(len(header) + 2, 11), 60)
    return sheet


def _result_row(res):
    facts = res.get("facts") or {}
    calc = res.get("calculations") or {}
    answers = calc.get("answers") or {}
    score = res.get("score") or {}
    return [
        res["subject"]["instrument_id"], _to_date(res["subject"]["analysis_end"]),
        _to_date(facts.get("analysis_date")), res["status"], score.get("value"),
        calc.get("state"), calc.get("net"),
        answers.get("Q1"), answers.get("Q2"), answers.get("Q3"),
        answers.get("Q4"), answers.get("Q5"), answers.get("Q6"),
        facts.get("close"), facts.get("ema_short"), facts.get("ema_medium"),
        facts.get("ema_long"), facts.get("ema_medium_lookback"),
        _to_date(facts.get("window_start_date")), facts.get("window_bars"),
        res["scanner"]["scanner_id"], res["scanner"]["version"],
        " | ".join(m for m in res["status_messages"]
                   if not m.startswith("Traceback"))[:3000],
    ]


RESULT_HEADERS = [
    "instrument", "requested_analysis_date", "analysis_date", "status",
    "score", "state", "net", "Q1 close>EMA20", "Q2 close>EMA50",
    "Q3 close>EMA200", "Q4 EMA20>EMA50", "Q5 EMA50>EMA200",
    "Q6 EMA50 rising", "close", "ema_short", "ema_medium", "ema_long",
    "ema_medium_lookback", "window_start", "window_bars", "scanner",
    "scanner_version", "messages",
]


def build_workbook(runs, extra_sheets=None, include_detail=True):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    results = [res for r in runs for res in r.scanner_results]
    counts = {}
    for res in results:
        counts[res["status"]] = counts.get(res["status"], 0) + 1
    summary = [
        ["Runs", len(runs)],
        ["Run IDs", ", ".join(r.run_id for r in runs)],
        ["Results", len(results)],
    ] + [["Status %s" % k, v] for k, v in sorted(counts.items())] + [
        ["Combined scores", "Not produced: combined scoring is M5 (G-10)"],
        ["Provisional rules", "D-EMA-11 and D-EMA-12 are proposals awaiting "
                              "the Owner's decision; results are provisional"],
        ["Interpretation", "None - Python never writes interpretation"],
    ]
    _write_sheet(wb, "Summary", ["Item", "Value"], summary)
    wb["Summary"].column_dimensions["B"].width = 90
    _write_sheet(wb, "Scanner_Results", RESULT_HEADERS,
                 [_result_row(res) for res in results])
    for sheet_title, headers, rows in (extra_sheets or []):
        _write_sheet(wb, sheet_title, headers, rows)
    warn_rows = []
    for res in results:
        for ref in res["data_references"]:
            for w in ref.get("warnings", []):
                warn_rows.append([res["subject"]["instrument_id"],
                                  _to_date(res["subject"]["analysis_end"]),
                                  w["code"], w["message"]])
            for issue in ref.get("issues", []):
                warn_rows.append([res["subject"]["instrument_id"],
                                  _to_date(res["subject"]["analysis_end"]),
                                  "ISSUE %s %s" % (issue["issue_id"],
                                                   issue["check_code"]),
                                  "%s | affects_continuity=%s | status=%s"
                                  % (issue["description"],
                                     issue["affects_continuity"],
                                     issue["status"])])
    _write_sheet(wb, "Data_Warnings", ["instrument", "analysis_date", "code",
                                       "message"], warn_rows)
    settings = []
    for r in runs:
        for entry in r.config["scanners"]:
            for name, value in sorted(entry["parameters"].items()):
                settings.append([r.run_id, entry["scanner_id"], name, value])
        for name in ("data_root", "analysis_end", "options"):
            settings.append([r.run_id, "run", name, json.dumps(r.config[name])])
    _write_sheet(wb, "Run_Settings", ["run_id", "scope", "setting", "value"],
                 settings)
    if include_detail:
        for res in results:
            table = (res.get("detail_tables") or {}).get("ema_window")
            if not table:
                continue
            title = ("EMA_%s_%s" % (res["subject"]["instrument_id"],
                                    res["facts"]["analysis_date"]))[:31]
            if title in wb.sheetnames:
                continue
            _write_sheet(wb, title, ["date", "close", "ema_short",
                                     "ema_medium", "ema_long"],
                         [[_to_date(row["date"]), row["close"],
                           row["ema_short"], row["ema_medium"],
                           row["ema_long"]] for row in table])
    return wb


# --- Main logic ---------------------------------------------------------------------
def write_outputs(runs, output_folder, extra_sheets=None, include_detail=True,
                  moment=None):
    """Write the run JSON and the Excel report; return their paths."""
    if not os.path.isdir(output_folder):
        raise OSError("The output folder %s does not exist." % output_folder)
    suffix = _suffix(moment or datetime.now())
    json_path = os.path.join(output_folder, "Q-MAP_Run_%s.json" % suffix)
    xlsx_path = os.path.join(output_folder,
                             "Q-MAP_Run_Report_%s.xlsx" % suffix)
    payload = build_run_json(runs)
    temp_json = json_path + ".partial"
    temp_xlsx = xlsx_path + ".partial"
    try:
        with open(temp_json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, allow_nan=False)
        build_workbook(runs, extra_sheets, include_detail).save(temp_xlsx)
        os.replace(temp_json, json_path)
        os.replace(temp_xlsx, xlsx_path)
    finally:
        for temp in (temp_json, temp_xlsx):
            if os.path.exists(temp):
                os.remove(temp)
    return json_path, xlsx_path
