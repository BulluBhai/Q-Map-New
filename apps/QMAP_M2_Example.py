"""Q-MAP M2 example - the data-access interface from IDLE (document 08,
section 7, M2 runnable outcome).

Open this file in IDLE on the Owner's PC and press F5. It asks for the Q-MAP
data root (the folder loaded with the Data Manager), then prints:
1. list_instruments();
2. NIFTY 5-minute bars for 17-Aug-26;
3. BANKNIFTY 19-Aug-26 with its incomplete 13:25 bar;
4. the CONCOR latest 5 closes;
5. one deliberate error, showing its plain message.

This script only reads. It is part of the M2 evidence.
"""

# --- Imports -----------------------------------------------------------------
import os
import sys

import pandas as pd

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qmap_database import settings as settings_mod          # noqa: E402
from qmap_database.access import QMapData                   # noqa: E402
from qmap_database.errors import (QMapDataError,            # noqa: E402
                                  UnsupportedTimeframeError)

# --- Constants ---------------------------------------------------------------
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)


# --- Helpers ------------------------------------------------------------------
def choose_data_root():
    """The saved data root, or a folder picker when none is saved."""
    saved = settings_mod.load_settings().get("data_root", "")
    if saved and os.path.isdir(saved):
        print("Using the saved data root: %s\n" % saved)
        return saved
    import tkinter
    from tkinter import filedialog
    hidden = tkinter.Tk()
    hidden.withdraw()
    chosen = filedialog.askdirectory(title="Choose the Q-MAP data root")
    hidden.destroy()
    return chosen


def heading(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# --- Main logic -----------------------------------------------------------------
def main():
    data_root = choose_data_root()
    if not data_root:
        print("No data root chosen - nothing to show.")
        return
    with QMapData(data_root) as db:
        heading("1. list_instruments()")
        print(db.list_instruments().to_string(index=False))

        heading("2. NIFTY 5-minute bars, 17 Aug 26 (CAS day)")
        result = db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17")
        print("status:", result.status,
              "| bars:", result.meta["bar_count"],
              "| notes:", ", ".join(result.meta["notes"]))
        print("\nFirst three and last three rows:")
        print(result.bars.head(3).to_string(index=False))
        print("...")
        print(result.bars.tail(3).to_string(index=False))

        heading("3. BANKNIFTY 5-minute bars, 19 Aug 26 - the incomplete "
                "13:25 bar")
        result = db.get_bars("BANKNIFTY", "5m", "2026-08-19", "2026-08-19")
        print("status:", result.status, "| warnings:",
              ", ".join(w["code"] for w in result.meta["warnings"]))
        bar = result.bars[result.bars["ts"]
                          == pd.Timestamp("2026-08-19 13:25:00")]
        print("\nThe 13:25 bar (3 of 5 minutes present; 13:28 and 13:29 are "
              "missing in the source and are never filled):")
        print(bar.to_string(index=False))

        heading("4. CONCOR latest 5 closes")
        result = db.get_bars("CONCOR", "1D", latest_n=5, fields=["close"])
        print(result.bars[["ts", "close"]].to_string(index=False))

        heading("5. A deliberate error - its plain message")
        try:
            db.get_bars("CONCOR", "15m")
        except UnsupportedTimeframeError as error:
            print("UnsupportedTimeframeError:", error)

    print("\nDone. The interface is read-only: nothing was changed.")


# --- Execution --------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except QMapDataError as error:
        print("Q-MAP error:", error)
