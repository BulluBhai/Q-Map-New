"""EMA Trend Alignment scanner (document 10 v1.7, Part B).

Methodology D-EMA-01 to D-EMA-10, approved by the Owner on 11-Nov-26:
daily closes of NSE stocks; EMA 20/50/200 over a fixed 800-bar window with a
simple-average seed; six comparison questions (+1 / -1 / 0 for an exact tie);
net count, score = 50 + 50 x net / 6, and five state bands. Any
continuity-blocking issue (G-03) overlapping the window gives INVALID_DATA.

Two rules are Owner PROPOSALS, not approved, and are applied provisionally so
that results can be inspected. Every result says so in status_messages and
calculations.provisional_rules, and the version stays below 1.0.0 until the
Owner decides:
- D-EMA-11 (proposed): data ending before the analysis date (signalled by
  RANGE_TRUNCATED_END) gives INSUFFICIENT_DATA with both dates; no score.
- D-EMA-12 (proposed): closes and EMA values are rounded to 6 decimal places
  before each comparison; the stored score is rounded to 2 decimal places.

Only data from context.fetch is used (SC-02). Nothing is written (SC-03).
"""

# --- Imports -----------------------------------------------------------------
import math
from decimal import ROUND_HALF_UP, Decimal

from qmap_engine.contract import (STATUS_INSUFFICIENT_DATA,
                                  STATUS_INVALID_DATA, STATUS_NOT_APPLICABLE,
                                  STATUS_OK, DataRequirement, ScannerInfo,
                                  new_result, to_jsonable)

# --- Constants ---------------------------------------------------------------
INFO = ScannerInfo(
    scanner_id="ema_trend_alignment",
    name="EMA Trend Alignment",
    # 1.0.0 is reserved for the version issued once D-EMA-11 and D-EMA-12 are
    # decided (document 10 section B1: "1.0.0 (on approval)").
    version="0.9.0",
    spec_reference="docs/design/Q-MAP_10_EMA_Scanner_Design_Proposal_v1.7"
                   "_12_Nov_26_072336.md",
    timeframes=("1D",),
    produces_score=True,
    score_meaning="Consistency of bullish daily EMA trend alignment: 0 = all "
                  "six signals bearish, 50 = evenly mixed, 100 = all six "
                  "bullish. Not a probability, forecast or recommendation.",
)

TIMEFRAME = "1D"
APPLICABLE_DATASET = "NSE_EQ_DAILY"          # D-EMA-01
CALIBRATION = "rule-based alignment count v1 (D-EMA-06)"
AUCTION_RECORD_TYPES = ("AUCTION_PHASE", "CLOSING_AUCTION")

# Proposed precision rule D-EMA-12 (not yet approved by the Owner).
COMPARISON_DECIMALS = 6
SCORE_DECIMALS = 2

PROVISIONAL_RULES = [
    "D-EMA-11 (PROPOSED, not yet approved): data ending before the analysis "
    "date -> INSUFFICIENT_DATA, no score",
    "D-EMA-12 (PROPOSED, not yet approved): values rounded to 6 dp before "
    "comparison; score stored to 2 dp",
]

QUESTIONS = (
    ("Q1", "close vs EMA short"),
    ("Q2", "close vs EMA medium"),
    ("Q3", "close vs EMA long"),
    ("Q4", "EMA short vs EMA medium"),
    ("Q5", "EMA medium vs EMA long"),
    ("Q6", "EMA medium vs its value slope_lookback bars earlier"),
)

# Warnings that let the calculation proceed but are reported (section B2).
REPORTED_WARNINGS = ("FLAGGED_ROWS_INCLUDED", "HELD_REVISION_EXISTS",
                     "UNRECOGNISED_SESSION_IN_RANGE", "INCOMPLETE_BARS",
                     "FORMING_BAR")


# --- Contract functions ----------------------------------------------------------
def default_parameters():
    return {"short_period": 20, "medium_period": 50, "long_period": 200,
            "slope_lookback": 10, "window_bars": 800, "tie_band_pct": 0.0}


def validate_parameters(params):
    """Section B3 ranges; an empty list means valid."""
    problems = []
    expected = default_parameters()
    unknown = sorted(set(params) - set(expected))
    if unknown:
        problems.append("unknown parameter(s): %s" % ", ".join(unknown))
    p = dict(expected, **params)

    def is_int(name):
        value = p[name]
        if isinstance(value, bool) or not isinstance(value, int):
            problems.append("%s must be a whole number" % name)
            return False
        return True

    if all(is_int(n) for n in ("short_period", "medium_period", "long_period",
                               "slope_lookback", "window_bars")):
        if not 2 <= p["short_period"] <= 100:
            problems.append("short_period must be 2-100")
        if not p["short_period"] < p["medium_period"] < p["long_period"]:
            problems.append("periods must satisfy short < medium < long")
        if p["long_period"] > 400:
            problems.append("long_period must be 400 or less")
        if not 1 <= p["slope_lookback"] <= 50:
            problems.append("slope_lookback must be 1-50")
        if p["window_bars"] < 4 * p["long_period"]:
            problems.append("window_bars must be at least 4 x long_period")
    band = p["tie_band_pct"]
    if isinstance(band, bool) or not isinstance(band, (int, float)) \
            or not 0.0 <= band <= 1.0:
        problems.append("tie_band_pct must be 0.0-1.0")
    return problems


def data_requirements(instrument_id, params, analysis_start, analysis_end):
    """Section B2: the latest window_bars daily closes ending at analysis_end."""
    return [DataRequirement(
        instrument_id=instrument_id, timeframe=TIMEFRAME, start=None,
        end=analysis_end, required_fields=("close",), optional_fields=(),
        min_bars=params["window_bars"], require_complete_bars=True,
        exclude_flagged=False, latest_n=params["window_bars"])]


# --- Helpers: calculation (section B4) ----------------------------------------------
def ema_series(closes, period):
    """EMA with a simple-average seed at index period-1; None before it."""
    alpha = 2.0 / (period + 1)
    values = [None] * len(closes)
    if len(closes) < period:
        return values
    values[period - 1] = math.fsum(closes[:period]) / period
    for i in range(period, len(closes)):
        values[i] = alpha * closes[i] + (1.0 - alpha) * values[i - 1]
    return values


def compare(value, reference, tie_band_pct):
    """sgn(value - reference) with the D-EMA-07 band (0 by default) applied
    to values rounded per the proposed D-EMA-12."""
    a = round(value, COMPARISON_DECIMALS)
    b = round(reference, COMPARISON_DECIMALS)
    threshold = tie_band_pct / 100.0 * abs(b) if tie_band_pct else 0.0
    difference = a - b
    if difference > threshold:
        return 1
    if difference < -threshold:
        return -1
    return 0


def state_for(net):
    """D-EMA-05: every net count from -6 to +6 falls into exactly one band."""
    if net >= 4:
        return "BULLISH"
    if net == 3:
        return "NEUTRAL_LEANING_BULLISH"
    if net >= -2:
        return "NEUTRAL"
    if net == -3:
        return "NEUTRAL_LEANING_BEARISH"
    return "BEARISH"


def score_for(net):
    """D-EMA-06 score, stored to 2 dp half-up (proposed D-EMA-12). Computed
    exactly in Decimal so the stored value does not depend on formula order
    (finding EMA-F2)."""
    exact = Decimal(50) + Decimal(50) * Decimal(net) / Decimal(6)
    return float(exact.quantize(Decimal(1).scaleb(-SCORE_DECIMALS),
                                rounding=ROUND_HALF_UP))


def _day(ts):
    return ts.date() if hasattr(ts, "date") else ts


def _human(day):
    return day.strftime("%d-%b-%y")


# --- Main logic ---------------------------------------------------------------------
def run(context):
    params = context.parameters
    result = new_result(INFO, context, TIMEFRAME)
    result["calculations"]["provisional_rules"] = list(PROVISIONAL_RULES)
    messages = result["status_messages"]
    messages.append("Provisional result: D-EMA-11 and D-EMA-12 are proposals "
                    "awaiting the Owner's decision.")

    requirement = context.requirements[0][0]
    bar_result = context.fetch(requirement)
    meta = bar_result.meta

    if meta.get("dataset_id") != APPLICABLE_DATASET:
        result["status"] = STATUS_NOT_APPLICABLE
        messages.append("The EMA scanner applies to daily NSE stocks (%s); %s "
                        "is in %s (D-EMA-01)."
                        % (APPLICABLE_DATASET, context.instrument_id,
                           meta.get("dataset_id")))
        return result

    warning_codes = [w["code"] for w in meta.get("warnings", [])]
    for warning in meta.get("warnings", []):
        if warning["code"] in REPORTED_WARNINGS:
            messages.append("%s: %s" % (warning["code"], warning["message"]))
    for report_reason in (context.requirements[0][1].reasons
                          if context.requirements[0][1] else []):
        if report_reason["code"] == "MISSING_DAY":
            messages.append("MISSING_DAY: %s" % report_reason["message"])

    bars = bar_result.bars
    if "record_type" in bars.columns:
        # Auction records are not price bars of the series (document 03 A5).
        bars = bars[~bars["record_type"].isin(AUCTION_RECORD_TYPES)]
    # A forming or incomplete bar is never used (SC-06, section B2).
    complete = bars[bars["is_complete"].astype(bool)
                    & ~bars["is_forming"].astype(bool)]
    window = params["window_bars"]

    if "RANGE_TRUNCATED_END" in warning_codes and len(complete):
        last_day = _day(complete["ts"].iloc[-1])
        result["status"] = STATUS_INSUFFICIENT_DATA
        messages.append("data ends %s; analysis date %s (D-EMA-11, proposed)"
                        % (_human(last_day),
                           _human(_day(_as_date(context.analysis_end)))))
        result["facts"] = to_jsonable({"last_data_date": last_day,
                                       "bars_available": len(complete)})
        return result

    if len(complete) < window:
        result["status"] = STATUS_INSUFFICIENT_DATA
        messages.append("needs %d complete daily bars; %d available"
                        % (window, len(complete)))
        result["facts"] = {"bars_available": int(len(complete)),
                           "bars_required": window}
        return result

    complete = complete.tail(window).reset_index(drop=True)
    window_start = _day(complete["ts"].iloc[0])
    analysis_day = _day(complete["ts"].iloc[-1])

    # SC-07 / D-EMA-09 / G-03: affects_continuity alone decides.
    blocking = []
    for issue in meta.get("issues", []):
        if not issue.get("affects_continuity"):
            continue
        issue_from = _day(issue["ts_from"])
        issue_to = _day(issue.get("ts_to") or issue["ts_from"])
        if issue_from <= analysis_day and issue_to >= window_start:
            blocking.append(issue)
    if blocking:
        result["status"] = STATUS_INVALID_DATA
        for issue in blocking:
            messages.append("continuity-blocking issue %s (%s, %s) lies in the "
                            "window %s to %s: %s"
                            % (issue["issue_id"], issue["check_code"],
                               _human(_day(issue["ts_from"])),
                               _human(window_start), _human(analysis_day),
                               issue["description"]))
        result["facts"] = to_jsonable({
            "analysis_date": analysis_day, "window_start_date": window_start,
            "window_bars": window,
            "blocking_issue_ids": [i["issue_id"] for i in blocking]})
        return result

    closes = [float(c) for c in complete["close"]]
    s, m, L = (params["short_period"], params["medium_period"],
               params["long_period"])
    k = params["slope_lookback"]
    band = params["tie_band_pct"]
    ema_s, ema_m, ema_l = (ema_series(closes, s), ema_series(closes, m),
                           ema_series(closes, L))
    last = window - 1
    close = closes[last]
    answers = {
        "Q1": compare(close, ema_s[last], band),
        "Q2": compare(close, ema_m[last], band),
        "Q3": compare(close, ema_l[last], band),
        "Q4": compare(ema_s[last], ema_m[last], band),
        "Q5": compare(ema_m[last], ema_l[last], band),
        "Q6": compare(ema_m[last], ema_m[last - k], band),
    }
    net = sum(answers.values())
    state = state_for(net)

    result["status"] = STATUS_OK
    result["facts"] = to_jsonable({
        "analysis_date": analysis_day, "window_start_date": window_start,
        "window_bars": window, "close": close,
        "ema_short": ema_s[last], "ema_medium": ema_m[last],
        "ema_long": ema_l[last], "ema_medium_lookback": ema_m[last - k]})
    result["calculations"].update({
        "distance_to_short_pct": (close / ema_s[last] - 1.0) * 100.0,
        "distance_to_medium_pct": (close / ema_m[last] - 1.0) * 100.0,
        "distance_to_long_pct": (close / ema_l[last] - 1.0) * 100.0,
        "answers": answers,
        "answer_names": dict(QUESTIONS),
        "net": net, "state": state})
    result["score"] = {
        "value": score_for(net), "scale": "0-100", "calibration": CALIBRATION,
        "components": [{"name": "%s %s" % (q, name), "value": answers[q],
                        "weight_in_scanner": 1.0 / 6.0}
                       for q, name in QUESTIONS]}
    result["detail_tables"] = {"ema_window": [
        to_jsonable({"date": _day(ts), "close": c, "ema_short": a,
                     "ema_medium": b, "ema_long": d})
        for ts, c, a, b, d in zip(complete["ts"], closes, ema_s, ema_m, ema_l)]}
    return result


def _as_date(value):
    import pandas as pd
    return pd.Timestamp(value).to_pydatetime()
