"""Q-MAP EMA Scanner - run the EMA Trend Alignment scanner from IDLE (F5).

Choose the Q-MAP data root (the folder loaded with the Data Manager), the
stocks, one or more analysis dates and an output folder, then press Run.
Writes Q-MAP_Run_<dd_mmm_yy_hhmmss>.json and
Q-MAP_Run_Report_<dd_mmm_yy_hhmmss>.xlsx (document 05 section 7.2).

Optional: the reference check runs the documented CONCOR and INFY cases
(document 10 section B9.3, source-verified in document 13) and adds a
Reference_Check sheet comparing the scanner's values with the reference.

Data is read only through the read-only QMapData interface. D-EMA-11 and
D-EMA-12 are Owner proposals; results are labelled provisional.
"""

# --- Imports -----------------------------------------------------------------
import os
import queue
import sys
import threading
import time
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(
    __file__)), os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pandas as pd                                          # noqa: E402

from qmap_database import settings as settings_mod          # noqa: E402
from qmap_database.access import QMapData                   # noqa: E402
from qmap_engine import output, runner                      # noqa: E402

# --- Constants ---------------------------------------------------------------
WINDOW_TITLE = "Q-MAP EMA Scanner (provisional: D-EMA-11/12 pending)"
POLL_MS = 100
SCANNER_ID = "ema_trend_alignment"
DAILY_STOCK_DATASET = "NSE_EQ_DAILY"

# Reference cases (document 10 v1.7 B9.3; document 13 v1.2). "default" is
# the expected status while the G-03 occurrence is unverified; "conditional"
# holds the values that apply only after the Owner verifies it.
REFERENCE_CASES = [
    ("T-EMA-02", "CONCOR", "2026-11-06", "INVALID_DATA",
     dict(close=439.80, ema_short=432.7297, ema_medium=452.6585,
          ema_long=486.4492, ema_medium_lookback=466.7276, score=16.67,
          state="BEARISH"), "04-Jun-24 must be verified for OK"),
    ("T-EMA-03", "INFY", "2026-11-06", "OK",
     dict(close=1181.40, ema_short=1132.2614, ema_medium=1108.5365,
          ema_long=1203.8765, ema_medium_lookback=1084.5193, score=66.67,
          state="NEUTRAL"), ""),
    ("T-EMA-04", "INFY", "2026-02-03", "OK",
     dict(close=1656.00, ema_short=1646.1038, ema_medium=1617.6051,
          ema_long=1589.1800, ema_medium_lookback=1598.2591, score=100.0,
          state="BULLISH"), ""),
    ("T-EMA-05", "CONCOR", "2026-09-09", "INVALID_DATA",
     dict(close=510.00, ema_short=509.8872, ema_medium=504.0989,
          ema_long=506.0167, ema_medium_lookback=502.3052, score=83.33,
          state="BULLISH"), "04-Jun-24 must be verified for OK"),
    ("T-EMA-06", "CONCOR", "2001-12-31", "INSUFFICIENT_DATA", None,
     "690 bars available, 800 needed"),
    ("T-EMA-07", "CONCOR", "2002-06-06", "OK", None,
     "first analysis date with status OK"),
    ("T-EMA-08", "CONCOR", "2014-06-30", "INVALID_DATA", None,
     "06-Sep-13 issue in the window"),
    ("T-EMA-09a", "CONCOR", "2016-12-07", "INVALID_DATA", None,
     "window still contains 06-Sep-13"),
    ("T-EMA-09b", "CONCOR", "2016-12-08", "OK", None,
     "window starts 10-Sep-13"),
    ("T-EMA-17", "CONCOR", "2026-11-10", "INSUFFICIENT_DATA", None,
     "stale data, proposed D-EMA-11"),
    ("T-EMA-18", "CONCOR", "2007-12-31", "INVALID_DATA",
     dict(close=246.61, ema_short=236.3180, ema_medium=241.2234,
          ema_long=252.5792, ema_medium_lookback=244.1076, score=33.33,
          state="NEUTRAL"), "15-May-06 must be verified for OK"),
]
VALUE_FIELDS = ("close", "ema_short", "ema_medium", "ema_long",
                "ema_medium_lookback")


# --- Helpers ------------------------------------------------------------------
def parse_dates(text):
    """Comma-separated dates as YYYY-MM-DD or dd-mmm-yy; returns ISO text."""
    dates = []
    for part in [p.strip() for p in text.split(",") if p.strip()]:
        for fmt in ("%Y-%m-%d", "%d-%b-%y", "%d %b %y", "%d-%b-%Y"):
            try:
                dates.append(datetime.strptime(part, fmt).date().isoformat())
                break
            except ValueError:
                continue
        else:
            raise ValueError("'%s' is not a date (use 06-Nov-26 or 2026-11-06)"
                             % part)
    return dates


def reference_rows(results_by_case):
    """Reference_Check sheet rows: expected versus actual, per case."""
    rows = []
    for case_id, instrument, day, default_status, conditional, note in \
            REFERENCE_CASES:
        res = results_by_case.get(case_id)
        if res is None:
            continue
        status = res["status"]
        facts = res.get("facts") or {}
        score = (res.get("score") or {}).get("value")
        state = (res.get("calculations") or {}).get("state")
        if status == default_status and (default_status != "OK"
                                         or conditional is None):
            verdict = "MATCH"
            expected = None
        elif status == default_status == "OK":
            expected = conditional
            verdict = "MATCH"
        elif status == "OK" and conditional is not None:
            expected = conditional
            verdict = "MATCH (after Owner verification)"
        else:
            expected = None
            verdict = "DIFFERENT"
        differences = []
        if expected is not None:
            for name in VALUE_FIELDS:
                if round(facts.get(name, float("nan")), 4) != expected[name]:
                    differences.append("%s %s vs %s" % (name, facts.get(name),
                                                        expected[name]))
            if score != expected["score"]:
                differences.append("score %s vs %s" % (score, expected["score"]))
            if state != expected["state"]:
                differences.append("state %s vs %s" % (state, expected["state"]))
            if differences:
                verdict = "DIFFERENT"
        rows.append([case_id, instrument, datetime.strptime(day, "%Y-%m-%d"),
                     default_status, status, verdict, score,
                     expected["score"] if expected else None, state,
                     "; ".join(differences) or note,
                     " | ".join(m for m in res["status_messages"][1:3])[:500]])
    return ("Reference_Check",
            ["case", "instrument", "analysis_date",
             "expected_status_while_unverified", "actual_status", "verdict",
             "score", "reference_score", "state", "differences_or_note",
             "messages"], rows)


def run_job(data_root, instruments, dates, output_folder, with_reference,
            include_detail, report):
    runs = []
    total = len(dates) + (len(REFERENCE_CASES) if with_reference else 0)
    done = 0
    for day in dates:
        report("progress", (done, total, "Analysis date %s" % day))
        run = runner.run_analysis(runner.RunConfig(
            data_root, list(instruments), day,
            [{"scanner_id": SCANNER_ID}], output_folder=output_folder))
        for res in run.scanner_results:
            score = (res.get("score") or {}).get("value")
            report("log", "%s %s: %s%s" % (
                res["subject"]["instrument_id"], day, res["status"],
                "" if score is None else " score %.2f %s" % (
                    score, res["calculations"]["state"])))
        runs.append(run)
        done += 1
    extra = []
    if with_reference:
        by_case = {}
        for case_id, instrument, day, *_ in REFERENCE_CASES:
            report("progress", (done, total, "Reference %s" % case_id))
            run = runner.run_analysis(runner.RunConfig(
                data_root, [instrument], day, [{"scanner_id": SCANNER_ID}],
                output_folder=output_folder))
            by_case[case_id] = run.scanner_results[0]
            runs.append(run)
            done += 1
        sheet = reference_rows(by_case)
        for row in sheet[2]:
            report("log", "Reference %s %s %s: %s" % (row[0], row[1],
                                                      row[2].strftime("%d-%b-%y"),
                                                      row[5]))
        extra.append(sheet)
    report("progress", (done, total, "Writing the output files..."))
    return output.write_outputs(runs, output_folder, extra_sheets=extra,
                                include_detail=include_detail)


# --- GUI -----------------------------------------------------------------------------
class ScrollFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self._window = self.canvas.create_window((0, 0), window=self.body,
                                                 anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._window, width=e.width))
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

    def destroy_canvas_first(self):
        try:
            self.canvas.destroy()
        except tk.TclError:
            pass


class EmaScannerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("880x720")
        self._closing = False
        self._queue = queue.Queue()
        self._started = None
        self._scroll_frame = ScrollFrame(self)
        self._scroll_frame.pack(fill="both", expand=True)
        body = self._scroll_frame.body
        pad = {"padx": 6, "pady": 3}
        saved = settings_mod.load_settings()

        box = tk.LabelFrame(body, text="1. Input - Q-MAP data root and stocks",
                            padx=6, pady=4)
        box.pack(fill="x", **pad)
        row = tk.Frame(box)
        row.pack(fill="x")
        self.root_var = tk.StringVar(value=saved.get("data_root", ""))
        tk.Entry(row, textvariable=self.root_var).pack(side="left", fill="x",
                                                       expand=True)
        tk.Button(row, text="Browse...", command=self._pick_root).pack(
            side="left", padx=4)
        tk.Button(row, text="Load stock list",
                  command=self._load_instruments).pack(side="left")
        row = tk.Frame(box)
        row.pack(fill="x", pady=(4, 0))
        self.instrument_list = tk.Listbox(row, height=6, selectmode="extended",
                                          exportselection=False)
        self.instrument_list.pack(side="left", fill="x", expand=True)
        self.instrument_list.bind("<<ListboxSelect>>",
                                  lambda e: self._update_badge())
        side = tk.Frame(row)
        side.pack(side="left", padx=4)
        tk.Button(side, text="Select all", command=self._select_all).pack(
            fill="x")
        self.badge = tk.Label(side, text="0 selected")
        self.badge.pack(fill="x")

        box = tk.LabelFrame(body, text="2. Output - folder for the run files",
                            padx=6, pady=4)
        box.pack(fill="x", **pad)
        self.out_var = tk.StringVar()
        tk.Entry(box, textvariable=self.out_var).pack(side="left", fill="x",
                                                      expand=True)
        tk.Button(box, text="Browse...", command=self._pick_output).pack(
            side="left", padx=4)

        box = tk.LabelFrame(body, text="3. Options", padx=6, pady=4)
        box.pack(fill="x", **pad)
        row = tk.Frame(box)
        row.pack(fill="x")
        tk.Label(row, text="Analysis date(s), comma-separated "
                           "(e.g. 06-Nov-26, 03-Feb-26):").pack(side="left")
        self.dates_var = tk.StringVar()
        tk.Entry(row, textvariable=self.dates_var, width=36).pack(
            side="left", padx=4)
        self.reference_var = tk.BooleanVar(value=True)
        tk.Checkbutton(box, variable=self.reference_var, anchor="w",
                       text="Add the reference check (documented CONCOR/INFY "
                            "cases, doc 10 B9.3 / doc 13)").pack(fill="x")
        self.detail_var = tk.BooleanVar(value=True)
        tk.Checkbutton(box, variable=self.detail_var, anchor="w",
                       text="Add the 800-row EMA table per result (for Excel "
                            "verification, doc 10 B9.2)").pack(fill="x")
        tk.Label(box, anchor="w", justify="left", fg="grey25",
                 text="Parameters are the approved defaults (20/50/200, slope "
                      "10, window 800, no tie band). D-EMA-11/12 are applied "
                      "provisionally and labelled in every result.").pack(
            fill="x")

        self.run_button = tk.Button(body, text="Run EMA scanner", width=22,
                                    font=("TkDefaultFont", 10, "bold"),
                                    command=self._start)
        self.run_button.pack(**pad)

        box = tk.LabelFrame(body, text="Progress / Status", padx=6, pady=4)
        box.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(box, mode="determinate")
        self.progress.pack(fill="x")
        self.status_label = tk.Label(box, text="Ready.", anchor="w")
        self.status_label.pack(fill="x")
        self.timing_label = tk.Label(box, text="", anchor="w")
        self.timing_label.pack(fill="x")

        box = tk.LabelFrame(body, text="Live log", padx=6, pady=4)
        box.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(box, height=16, bg="black", fg="#d0d0d0",
                           font=("Consolas", 9))
        scroll = tk.Scrollbar(box, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(POLL_MS, self._poll)
        if self.root_var.get() and os.path.isdir(self.root_var.get()):
            self.after(200, self._load_instruments)

    # --- input handlers ---------------------------------------------------------
    def _pick_root(self):
        folder = filedialog.askdirectory(title="Choose the Q-MAP data root")
        if folder:
            self.root_var.set(folder)
            self._load_instruments()

    def _pick_output(self):
        folder = filedialog.askdirectory(title="Choose the output folder")
        if folder:
            self.out_var.set(folder)

    def _load_instruments(self):
        root = self.root_var.get().strip()
        try:
            with QMapData(root) as db:
                table = db.list_instruments()
        except Exception as exc:
            messagebox.showerror(WINDOW_TITLE, "The data root could not be "
                                               "opened:\n%s" % exc)
            return
        stocks = table[table["dataset_id"] == DAILY_STOCK_DATASET]
        self.instrument_list.delete(0, "end")
        for instrument_id in stocks["instrument_id"]:
            self.instrument_list.insert("end", instrument_id)
        self._select_all()
        if len(stocks) and not self.dates_var.get().strip():
            latest = pd.Timestamp(stocks["last_ts"].max())
            self.dates_var.set(latest.strftime("%d-%b-%y"))
        self._append("%d daily stock(s) in %s" % (len(stocks), root))

    def _select_all(self):
        self.instrument_list.select_set(0, "end")
        self._update_badge()

    def _update_badge(self):
        self.badge.config(text="%d selected"
                          % len(self.instrument_list.curselection()))

    # --- run ---------------------------------------------------------------------
    def _start(self):
        root = self.root_var.get().strip()
        out = self.out_var.get().strip()
        instruments = [self.instrument_list.get(i)
                       for i in self.instrument_list.curselection()]
        try:
            dates = parse_dates(self.dates_var.get())
        except ValueError as exc:
            messagebox.showerror(WINDOW_TITLE, str(exc))
            return
        if not os.path.isdir(root):
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root.")
            return
        if not os.path.isdir(out):
            messagebox.showerror(WINDOW_TITLE, "Please choose an output "
                                               "folder.")
            return
        if os.path.abspath(out).startswith(os.path.abspath(root)):
            messagebox.showerror(WINDOW_TITLE, "Choose an output folder "
                                               "outside the data root.")
            return
        if not instruments or not dates:
            messagebox.showerror(WINDOW_TITLE, "Choose at least one stock and "
                                               "one analysis date.")
            return
        self.run_button.config(state="disabled")
        self.status_label.config(fg="black")
        self._started = time.time()
        self._append("=== Run started %s ==="
                     % datetime.now().strftime("%d-%b-%y %H:%M:%S"))
        args = (root, instruments, dates, out, self.reference_var.get(),
                self.detail_var.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _worker(self, *args):
        def report(kind, payload):
            self._queue.put((kind, payload))
        try:
            paths = run_job(*args, report=report)
            self._queue.put(("done", paths))
        except runner.RunConfigError as exc:
            self._queue.put(("error", str(exc)))
        except Exception:
            self._queue.put(("error", "Unexpected error:\n%s"
                             % traceback.format_exc()))

    def _poll(self):
        if getattr(self, "_closing", False):
            return
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                self._handle(kind, payload)
        except queue.Empty:
            pass
        if self._started:
            elapsed = int(time.time() - self._started)
            self.timing_label.config(text="Started %s   elapsed %02d:%02d" % (
                datetime.fromtimestamp(self._started).strftime("%H:%M:%S"),
                elapsed // 60, elapsed % 60))
        self.after(POLL_MS, self._poll)

    def _handle(self, kind, payload):
        if getattr(self, "_closing", False):
            return
        if kind == "progress":
            done, total, text = payload
            self.progress.config(maximum=max(total, 1), value=done)
            self.status_label.config(text="%s   (%d of %d)" % (text, done,
                                                               total))
        elif kind == "log":
            self._append(payload)
        elif kind == "done":
            self._started = None
            self.run_button.config(state="normal")
            self.progress.config(value=self.progress.cget("maximum"))
            self.status_label.config(text="Finished. Files saved.")
            for path in payload:
                self._append("Saved: %s" % path)
        elif kind == "error":
            self._started = None
            self.run_button.config(state="normal")
            self.status_label.config(text="The run failed - see the log.",
                                     fg="red")
            self._append(payload)

    def _append(self, text):
        if getattr(self, "_closing", False):
            return
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def _on_closing(self):
        self._closing = True
        try:
            self._scroll_frame.destroy_canvas_first()
            self._scroll_frame.pack_forget()
            self._scroll_frame.destroy()
        except tk.TclError:
            pass
        self.withdraw()
        try:
            for callback in self.tk.call("after", "info"):
                try:
                    self.after_cancel(callback)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass


# --- Execution ------------------------------------------------------------------------
if __name__ == "__main__":
    EmaScannerApp().mainloop()
