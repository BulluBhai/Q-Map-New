"""Scanner registry (document 04 v1.3, M-03; TC-18): one explicit dictionary,
no automatic discovery and no plug-in loading. Adding a scanner adds one
line."""

# --- Imports -----------------------------------------------------------------
from qmap_scanners.ema_trend_alignment import scanner as ema_trend_alignment

# --- Constants ---------------------------------------------------------------
SCANNERS = {
    "ema_trend_alignment": ema_trend_alignment,
}

REQUIRED_MEMBERS = ("INFO", "default_parameters", "validate_parameters",
                    "data_requirements", "run")


# --- Main logic --------------------------------------------------------------
def check_registry(scanners=None):
    """Stop start-up with a clear message if the registry is inconsistent."""
    scanners = SCANNERS if scanners is None else scanners
    problems = []
    for key, module in scanners.items():
        missing = [m for m in REQUIRED_MEMBERS if not hasattr(module, m)]
        if missing:
            problems.append("scanner %s lacks: %s" % (key, ", ".join(missing)))
        elif module.INFO.scanner_id != key:
            problems.append("scanner key %s differs from INFO.scanner_id %s"
                            % (key, module.INFO.scanner_id))
    if problems:
        raise RuntimeError("Scanner registry problem: " + "; ".join(problems))
    return [module.INFO for module in scanners.values()]
