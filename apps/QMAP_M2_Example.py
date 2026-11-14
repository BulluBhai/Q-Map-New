"""Q-MAP M2 example - the data-access interface from IDLE (document 08,
section 7, M2 runnable outcome).

Open this file in IDLE on the Owner's PC and press F5. It asks for the Q-MAP
data root (the folder loaded with the Data Manager), then prints:
1. list_instruments();
2. NIFTY 5-minute bars for 17-Aug-26;
3. BANKNIFTY 19-Aug-26 with its incomplete 13:25 bar;
4. the CONCOR latest 5 closes;
5. one deliberate error, showing its plain message;
6. one NIFTY day and one CONCOR period at every supported timeframe.

A section whose instrument is not loaded prints its message and the
example continues.

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


def show_every_timeframe(db, instrument_id, start, end):
    """Bar count and first/last bar for every supported timeframe."""
    print("%s, %s to %s" % (instrument_id, start, end))
    print("%-5s %6s  %-19s %10s %10s %10s %10s  %s"
          % ("tf", "bars", "first bar", "open", "high", "low", "close",
             "status"))
    for timeframe in db.supported_timeframes(instrument_id):
        result = db.get_bars(instrument_id, timeframe, start, end,
                             fields=["open", "high", "low", "close"])
        if result.meta["bar_count"] == 0:
            print("%-5s %6d  (no bars)" % (timeframe, 0))
            continue
        first = result.bars.iloc[0]
        print("%-5s %6d  %-19s %10.2f %10.2f %10.2f %10.2f  %s"
              % (timeframe, result.meta["bar_count"],
                 str(first["ts"])[:19], first["open"], first["high"],
                 first["low"], first["close"], result.status))


def heading(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def section_nifty_5m(db):
    result = db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17")
    print("status:", result.status,
          "| bars:", result.meta["bar_count"],
          "| notes:", ", ".join(result.meta["notes"]))
    print("\nFirst three and last three rows:")
    print(result.bars.head(3).to_string(index=False))
    print("...")
    print(result.bars.tail(3).to_string(index=False))


def section_banknifty(db):
    result = db.get_bars("BANKNIFTY", "5m", "2026-08-19", "2026-08-19")
    print("status:", result.status, "| warnings:",
          ", ".join(w["code"] for w in result.meta["warnings"]))
    bar = result.bars[result.bars["ts"] == pd.Timestamp("2026-08-19 13:25:00")]
    print("\nThe 13:25 bar (3 of 5 minutes present; 13:28 and 13:29 are "
          "missing in the source and are never filled):")
    print(bar.to_string(index=False))


def section_error(db):
    try:
        db.get_bars("CONCOR", "15m")
    except UnsupportedTimeframeError as error:
        print("UnsupportedTimeframeError:", error)


# --- Main logic -----------------------------------------------------------------
def main():
    data_root = choose_data_root()
    if not data_root:
        print("No data root chosen - nothing to show.")
        return
    with QMapData(data_root) as db:
        sections = [
            ("1. list_instruments()", lambda: print(
                db.list_instruments().to_string(index=False))),
            ("2. NIFTY 5-minute bars, 17 Aug 26 (CAS day)",
             lambda: section_nifty_5m(db)),
            ("3. BANKNIFTY 5-minute bars, 19 Aug 26 - the incomplete 13:25 "
             "bar", lambda: section_banknifty(db)),
            ("4. CONCOR latest 5 closes", lambda: print(
                db.get_bars("CONCOR", "1D", latest_n=5, fields=["close"])
                .bars[["ts", "close"]].to_string(index=False))),
            ("5. A deliberate error - its plain message",
             lambda: section_error(db)),
            ("6a. Timeframe aggregation - NIFTY 18 Aug 26, every timeframe "
             "(1-minute source records, aggregated on request)",
             lambda: show_every_timeframe(db, "NIFTY", "2026-08-18",
                                          "2026-08-18")),
            ("6b. Timeframe aggregation - NIFTY Aug-Oct 26 (weekly and "
             "monthly bars need a range covering whole weeks/months)",
             lambda: show_every_timeframe(db, "NIFTY", "2026-08-01",
                                          "2026-10-31")),
            ("6c. Timeframe aggregation - CONCOR Sep-Oct 26 (daily source)",
             lambda: show_every_timeframe(db, "CONCOR", "2026-09-01",
                                          "2026-10-31")),
        ]
        for title, show in sections:
            heading(title)
            try:
                show()
            except QMapDataError as error:
                print("Not shown - %s: %s" % (type(error).__name__, error))

    print("\nDone. The interface is read-only: nothing was changed.")


# --- Execution --------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except QMapDataError as error:
        print("Q-MAP error:", error)
