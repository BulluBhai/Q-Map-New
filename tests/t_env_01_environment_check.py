"""T-ENV-01 — Environment check for Gate 0 (run from IDLE with F5).

Prints the Python and third-party package versions, compares them with the
exact pins in requirements.txt, checks that tkinter is importable, and writes
the machine-readable evidence file EV12_environment_<ts>.txt next to this
script (per the Consolidated Handover section 9.1 and 11).

No command line is needed: open this file in IDLE on the Owner's PC and
press F5. The printed versions must equal requirements.txt for Gate 0.
"""

# --- Imports -----------------------------------------------------------------
import os
import platform
import sys
from datetime import datetime

# --- Constants ---------------------------------------------------------------
REQUIRED_PACKAGES = ("duckdb", "pandas", "pyarrow", "openpyxl")
EXPECTED_PYTHON = "3.12.10"
REQUIREMENTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 os.pardir, "requirements.txt")


# --- Helpers -----------------------------------------------------------------
def read_pins(path):
    """Read the exact '==' pins from requirements.txt into a dict."""
    pins = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "==" not in line:
                continue
            name, version = line.split("==", 1)
            pins[name.strip().lower()] = version.strip()
    return pins


def timestamp_suffix(now):
    """Return the Owner's dd_mmm_yy_hhmmss file-name suffix."""
    return now.strftime("%d_%b_%y_%H%M%S")


# --- Main logic --------------------------------------------------------------
def run_check():
    now = datetime.now()
    lines = []

    def record(text):
        print(text)
        lines.append(text)

    record("T-ENV-01 environment check")
    # Evidence timestamps use IST wall-clock time with no conversion (TS-01).
    record("checked_at: %s" % now.strftime("%Y-%m-%d %H:%M:%S"))
    record("computer: %s (%s)" % (platform.node(), platform.platform()))
    python_version = platform.python_version()
    python_matches = python_version == EXPECTED_PYTHON
    record("python_version: %s" % python_version)
    record("python_expected: %s" % EXPECTED_PYTHON)
    record("python_match: %s" % ("TRUE" if python_matches else "FALSE"))

    try:
        pins = read_pins(REQUIREMENTS_PATH)
        record("requirements_txt: FOUND")
    except OSError as exc:
        pins = {}
        record("requirements_txt: MISSING (%s)" % exc)

    # Gate 0 requires the exact Python version as well as matching packages.
    all_match = python_matches
    for package_name in REQUIRED_PACKAGES:
        try:
            module = __import__(package_name)
            installed = getattr(module, "__version__", "unknown")
            record("%s_installed: %s" % (package_name, installed))
            pinned = pins.get(package_name, "(no pin)")
            record("%s_pinned: %s" % (package_name, pinned))
            match = installed == pinned
            record("%s_match: %s" % (package_name, "TRUE" if match else "FALSE"))
            all_match = all_match and match
        except ImportError as exc:
            record("%s_installed: IMPORT FAILED (%s)" % (package_name, exc))
            all_match = False

    try:
        import tkinter
        record("tkinter_installed: %s" % tkinter.TkVersion)
    except ImportError as exc:
        record("tkinter_installed: IMPORT FAILED (%s)" % exc)
        all_match = False

    record("all_environment_checks_match: %s" % ("TRUE" if all_match else "FALSE"))
    if not all_match:
        record("note: Python or package versions differ from the required environment, "
               "or tkinter is unavailable - this environment is untested and its "
               "runs are not milestone evidence (G-15)")

    evidence_name = "EV12_environment_%s.txt" % timestamp_suffix(now)
    evidence_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 evidence_name)
    with open(evidence_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\nEvidence written to: %s" % evidence_path)
    print("Done. Please confirm this printout came from your own PC.")


# --- Execution ---------------------------------------------------------------
if __name__ == "__main__":
    run_check()
