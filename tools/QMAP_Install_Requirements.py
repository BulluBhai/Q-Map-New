"""Install the exact Q-MAP package pins from requirements.txt (IDLE, F5).

Open this file in IDLE on the Owner's PC and press F5. It runs pip for the
same Python that IDLE uses, so no command line is needed, and prints pip's
output. Afterwards run tests/t_env_01_environment_check.py (also F5).

Only the four approved packages are listed in requirements.txt; pip also
installs their own dependencies (for example numpy), which are not pinned.
"""

# --- Imports -----------------------------------------------------------------
import os
import platform
import subprocess
import sys

# --- Constants ---------------------------------------------------------------
EXPECTED_PYTHON = "3.12.10"
REQUIREMENTS_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "requirements.txt"))


# --- Helpers -----------------------------------------------------------------
def console_python():
    """IDLE on Windows may run under pythonw.exe; pip is run with the
    python.exe next to it (same installation) when that exists."""
    folder, name = os.path.split(sys.executable)
    if name.lower() == "pythonw.exe":
        candidate = os.path.join(folder, "python.exe")
        if os.path.exists(candidate):
            return candidate
    return sys.executable


# --- Main logic --------------------------------------------------------------
def main():
    print("Python used by IDLE: %s (%s)" % (platform.python_version(),
                                            sys.executable))
    if platform.python_version() != EXPECTED_PYTHON:
        print("WARNING: Q-MAP requires Python %s. Install it from python.org "
              "and open this file with that version's IDLE." % EXPECTED_PYTHON)
        return
    print("Installing from %s ...\n" % REQUIREMENTS_PATH)
    process = subprocess.Popen(
        [console_python(), "-m", "pip", "install",
         "--disable-pip-version-check", "-r", REQUIREMENTS_PATH],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    for line in process.stdout:
        print(line.rstrip())
    code = process.wait()
    if code == 0:
        print("\nDone. Now run tests/t_env_01_environment_check.py (F5).")
    else:
        print("\npip finished with exit code %d - see the messages above."
              % code)


# --- Execution ---------------------------------------------------------------
if __name__ == "__main__":
    main()
