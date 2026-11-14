"""Run the complete Q-MAP test suite (open in IDLE and press F5).

Per T-ENV-01 and G-15, the runner first prints the Python and package versions
and compares them with requirements.txt. Any difference is reported at the top
of the summary as an untested environment, and such a run is not milestone
evidence. Real-data tests skip with a clear message when the sample files are
absent.
"""

# --- Imports -----------------------------------------------------------------
import os
import platform
import sys
import unittest

_TESTS_FOLDER = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TESTS_FOLDER, os.pardir))
for path in (_REPO_ROOT, _TESTS_FOLDER):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- Constants ---------------------------------------------------------------
EXPECTED_PYTHON = "3.12.10"
REQUIRED_PACKAGES = ("duckdb", "pandas", "pyarrow", "openpyxl")


# --- Helpers ------------------------------------------------------------------
def check_environment():
    """Compare the running environment with the Gate 0 pins (T-ENV-01)."""
    problems = []
    if platform.python_version() != EXPECTED_PYTHON:
        problems.append("Python is %s, expected %s"
                        % (platform.python_version(), EXPECTED_PYTHON))
    pins = {}
    requirements_path = os.path.join(_REPO_ROOT, "requirements.txt")
    try:
        with open(requirements_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if "==" in line:
                    name, version = line.strip().split("==", 1)
                    pins[name.strip().lower()] = version.strip()
    except OSError as exc:
        problems.append("requirements.txt could not be read: %s" % exc)
    print("Environment (T-ENV-01):")
    print("  python: %s (pinned: %s)" % (platform.python_version(),
                                         EXPECTED_PYTHON))
    for package_name in REQUIRED_PACKAGES:
        try:
            module = __import__(package_name)
            installed = getattr(module, "__version__", "unknown")
        except ImportError:
            installed = "NOT INSTALLED"
        pinned = pins.get(package_name, "(no pin)")
        marker = "" if installed == pinned else "   <-- differs"
        print("  %s: %s (pinned: %s)%s" % (package_name, installed, pinned,
                                           marker))
        if installed != pinned:
            problems.append("%s is %s, pinned %s" % (package_name, installed,
                                                     pinned))
    return problems


# --- Main logic ----------------------------------------------------------------
def main():
    problems = check_environment()
    print()
    loader = unittest.TestLoader()
    suite = loader.discover(_TESTS_FOLDER, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    print()
    print("=" * 60)
    if problems:
        print("UNTESTED ENVIRONMENT - this run is NOT milestone evidence "
              "(G-15):")
        for problem in problems:
            print("  - %s" % problem)
    else:
        print("Environment matches the Gate 0 pins.")
    print("Tests run: %d | failures: %d | errors: %d | skipped: %d"
          % (result.testsRun, len(result.failures), len(result.errors),
             len(result.skipped)))
    for test, _ in result.failures:
        print("FAILED: %s" % test)
    for test, _ in result.errors:
        print("ERROR: %s" % test)
    for test, reason in result.skipped:
        print("skipped: %s (%s)" % (test, reason))
    return result


# --- Execution -------------------------------------------------------------------
if __name__ == "__main__":
    main()
