"""Q-MAP Data Manager (M1a: Initial load).

Open this file in IDLE on the Owner's PC and press F5. Pick the data root
folder and the source files, then run the Initial load. Progress, a live log,
the validation report location, and the CAS and unrecognised-day confirmation
lists are shown. Only this program writes to the Q-MAP database.

Recording CAS and special-session confirmations (which re-validates data into
a new generation) arrives with M1b; this version shows the lists the Owner
will confirm.
"""

# --- Imports -----------------------------------------------------------------
import os
import queue
import sys
import threading
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qmap_database import settings as settings_mod          # noqa: E402
from qmap_database.errors import DatabaseUnavailableError   # noqa: E402
from qmap_database.maintenance import run_initial_load      # noqa: E402

# --- Constants ---------------------------------------------------------------
POLL_MILLISECONDS = 100
WINDOW_TITLE = "Q-MAP Data Manager"
SOURCE_FILE_TYPES = [("Market data files", "*.parquet *.csv *.txt"),
                     ("All files", "*.*")]


# --- Helpers ------------------------------------------------------------------
class ScrollableFrame(tk.Frame):
    """A vertically scrollable container, so every control stays reachable on
    a normal screen without resizing."""

    def __init__(self, parent):
        super().__init__(parent)
        self._canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical",
                                 command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas)
        self.inner.bind("<Configure>", lambda event: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._window = self._canvas.create_window((0, 0), window=self.inner,
                                                  anchor="nw")
        self._canvas.bind("<Configure>", lambda event: self._canvas.itemconfig(
            self._window, width=event.width))
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def destroy_canvas_first(self):
        """Destroy the internal canvas before hiding the window (prevents the
        ghost-window issue on Windows)."""
        try:
            self._canvas.destroy()
        except tk.TclError:
            pass


# --- Main logic -----------------------------------------------------------------
class DataManagerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("860x720")
        self.minsize(720, 560)
        self._closing = False
        self._worker = None
        self._queue = queue.Queue()
        self._run_started_at = None
        self.settings = settings_mod.load_settings()

        self._scroll_frame = ScrollableFrame(self)
        self._scroll_frame.pack(fill="both", expand=True)
        body = self._scroll_frame.inner

        self._build_input_section(body)
        self._build_output_section(body)
        self._build_options_section(body)
        self._build_run_section(body)
        self._build_progress_section(body)
        self._build_log_section(body)
        self._build_confirmation_section(body)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(POLL_MILLISECONDS, self._poll_queue)

    # --- interface sections ------------------------------------------------------
    def _build_input_section(self, body):
        frame = tk.LabelFrame(body, text="1. Input - source data files",
                              padx=6, pady=4)
        frame.pack(fill="x", padx=8, pady=(8, 2))
        row = tk.Frame(frame)
        row.pack(fill="x")
        tk.Button(row, text="Add files...", command=self._add_files).pack(
            side="left")
        tk.Button(row, text="Remove selected",
                  command=self._remove_selected).pack(side="left", padx=4)
        tk.Button(row, text="Clear", command=self._clear_files).pack(
            side="left")
        self.file_count_label = tk.Label(row, text="0 file(s) selected")
        self.file_count_label.pack(side="right")
        self.file_list = tk.Listbox(frame, height=6, selectmode="extended")
        self.file_list.pack(fill="x", pady=(4, 0))
        for path in self.settings.get("last_source_files", []):
            if os.path.exists(path):
                self.file_list.insert("end", path)
        self._update_file_count()

    def _build_output_section(self, body):
        frame = tk.LabelFrame(body, text="2. Output - Q-MAP data root folder",
                              padx=6, pady=4)
        frame.pack(fill="x", padx=8, pady=2)
        row = tk.Frame(frame)
        row.pack(fill="x")
        self.data_root_var = tk.StringVar(
            value=self.settings.get("data_root", ""))
        tk.Entry(row, textvariable=self.data_root_var).pack(
            side="left", fill="x", expand=True)
        tk.Button(row, text="Browse...", command=self._pick_data_root).pack(
            side="left", padx=(4, 0))
        tk.Label(frame, anchor="w", fg="grey25",
                 text="The data root holds the catalogue, market data, "
                      "quarantine, reports and logs. Keep it outside the "
                      "program folder.").pack(fill="x")

    def _build_options_section(self, body):
        frame = tk.LabelFrame(body, text="3. Options", padx=6, pady=4)
        frame.pack(fill="x", padx=8, pady=2)
        row = tk.Frame(frame)
        row.pack(fill="x")
        tk.Label(row, text="Official NSE calendar file (optional):").pack(
            side="left")
        self.calendar_var = tk.StringVar(value="")
        tk.Entry(row, textvariable=self.calendar_var).pack(
            side="left", fill="x", expand=True, padx=4)
        tk.Button(row, text="Browse...", command=self._pick_calendar).pack(
            side="left")
        tk.Label(frame, anchor="w", fg="grey25",
                 text="An imported calendar stays unconfirmed until you "
                      "record its official source (G-02).").pack(fill="x")

    def _build_run_section(self, body):
        frame = tk.Frame(body)
        frame.pack(fill="x", padx=8, pady=4)
        self.run_button = tk.Button(frame, text="Run initial load",
                                    font=("TkDefaultFont", 10, "bold"),
                                    command=self._start_initial_load)
        self.run_button.pack(side="left")
        tk.Label(frame, text="Imports the selected files into a fresh or "
                             "existing data root.").pack(side="left", padx=8)

    def _build_progress_section(self, body):
        frame = tk.LabelFrame(body, text="Progress / Status", padx=6, pady=4)
        frame.pack(fill="x", padx=8, pady=2)
        self.progress_bar = ttk.Progressbar(frame, mode="determinate")
        self.progress_bar.pack(fill="x")
        self.status_label = tk.Label(frame, text="Ready.", anchor="w")
        self.status_label.pack(fill="x")
        self.timing_label = tk.Label(frame, text="", anchor="w")
        self.timing_label.pack(fill="x")

    def _build_log_section(self, body):
        frame = tk.LabelFrame(body, text="Live log", padx=6, pady=4)
        frame.pack(fill="both", expand=True, padx=8, pady=2)
        self.log_text = tk.Text(frame, height=12, state="disabled",
                                wrap="none", font=("Courier New", 9))
        log_scroll = tk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def _build_confirmation_section(self, body):
        frame = tk.LabelFrame(
            body, text="Sessions awaiting your confirmation "
                       "(recording confirmations arrives with M1b)",
            padx=6, pady=4)
        frame.pack(fill="both", padx=8, pady=(2, 8))
        self.confirmation_text = tk.Text(frame, height=8, state="disabled",
                                         wrap="word")
        self.confirmation_text.pack(fill="both", expand=True)

    # --- input handlers ------------------------------------------------------------
    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Select source data files",
                                            filetypes=SOURCE_FILE_TYPES)
        existing = set(self.file_list.get(0, "end"))
        for path in paths:
            if path not in existing:
                self.file_list.insert("end", path)
        self._update_file_count()

    def _remove_selected(self):
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
        self._update_file_count()

    def _clear_files(self):
        self.file_list.delete(0, "end")
        self._update_file_count()

    def _update_file_count(self):
        count = self.file_list.size()
        self.file_count_label.config(text="%d file(s) selected" % count)

    def _pick_data_root(self):
        path = filedialog.askdirectory(title="Choose the Q-MAP data root "
                                             "folder")
        if path:
            self.data_root_var.set(path)

    def _pick_calendar(self):
        path = filedialog.askopenfilename(
            title="Select the official NSE calendar file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.calendar_var.set(path)

    # --- run -------------------------------------------------------------------------
    def _start_initial_load(self):
        if self._worker is not None and self._worker.is_alive():
            messagebox.showinfo(WINDOW_TITLE, "A run is already in progress.")
            return
        files = list(self.file_list.get(0, "end"))
        data_root = self.data_root_var.get().strip()
        if not data_root:
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root "
                                               "folder first.")
            return
        if not files:
            messagebox.showerror(WINDOW_TITLE, "Please add at least one "
                                               "source data file.")
            return
        calendar_file = self.calendar_var.get().strip() or None

        self.settings["data_root"] = data_root
        self.settings["last_source_files"] = files
        settings_mod.save_settings(self.settings)

        self.run_button.config(state="disabled")
        self._run_started_at = datetime.now()
        self._set_status("Starting the initial load...")
        self._append_log("=== Initial load started %s ==="
                         % self._run_started_at.strftime("%d %b %y, %I:%M %p"))

        self._worker = threading.Thread(
            target=self._initial_load_worker,
            args=(data_root, files, calendar_file), daemon=True)
        self._worker.start()

    def _initial_load_worker(self, data_root, files, calendar_file):
        """Runs off the main thread; talks to the window only via the queue."""
        try:
            result = run_initial_load(
                data_root, files, calendar_file=calendar_file,
                live_log=lambda message: self._queue.put(("log", message)),
                progress=lambda step, total, text: self._queue.put(
                    ("progress", (step, total, text))))
            self._queue.put(("done", result))
        except DatabaseUnavailableError as exc:
            self._queue.put(("error", str(exc)))
        except Exception:
            self._queue.put(("error", "Unexpected error:\n%s"
                             % traceback.format_exc()))

    # --- queue polling ------------------------------------------------------------------
    def _poll_queue(self):
        if getattr(self, "_closing", False):
            return
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "progress":
                    step, total, text = payload
                    self.progress_bar.configure(maximum=total, value=step)
                    self._set_status("%s  (%d of %d)" % (text, step, total))
                elif kind == "done":
                    self._finish_run(payload)
                elif kind == "error":
                    self._fail_run(payload)
        except queue.Empty:
            pass
        if self._run_started_at is not None:
            elapsed = datetime.now() - self._run_started_at
            self.timing_label.config(
                text="Started %s   -   elapsed %s"
                     % (self._run_started_at.strftime("%I:%M:%S %p"),
                        str(elapsed).split(".")[0]))
        self.after(POLL_MILLISECONDS, self._poll_queue)

    def _finish_run(self, result):
        if getattr(self, "_closing", False):
            return
        self._run_started_at = None
        self.run_button.config(state="normal")
        self._set_status("Finished: %s - %s" % (result.status, result.summary))
        self._append_log("=== Finished: %s ===" % result.status)
        if result.report_path:
            self._append_log("Validation report: %s" % result.report_path)
        if result.unrecognised_files:
            self._append_log("Unrecognised files (please map them to "
                             "instruments):")
            for path in result.unrecognised_files:
                self._append_log("  %s" % path)
        self._show_confirmation_lists(result)

    def _fail_run(self, message):
        if getattr(self, "_closing", False):
            return
        self._run_started_at = None
        self.run_button.config(state="normal")
        self._set_status("The run failed. See the log for details.")
        self._append_log(message)
        messagebox.showerror(WINDOW_TITLE, message.splitlines()[0])

    def _show_confirmation_lists(self, result):
        """The CAS-candidate and unrecognised-day lists (02 section 6.2)."""
        lines = []
        try:
            from qmap_database.catalogue import Catalogue
            from qmap_database.storage import DataRoot
            data_root = DataRoot(self.data_root_var.get().strip())
            catalogue = Catalogue(data_root.catalogue_path, read_only=True)
            try:
                for (instrument_id, count, first, last) in \
                        catalogue.cas_confirmation_list():
                    lines.append("%s: CAS shape on %d day(s) from %s to %s - "
                                 "please confirm the CAS rule."
                                 % (instrument_id, count,
                                    first.strftime("%d %b %y"),
                                    last.strftime("%d %b %y")))
                for (instrument_id, day, first_record, last_candle, present,
                     missing) in catalogue.unrecognised_days():
                    lines.append("%s %s: records %s-%s only (%s present). "
                                 "Special session, or truncated data?"
                                 % (instrument_id, day.strftime("%d %b %y"),
                                    first_record, last_candle, present))
            finally:
                catalogue.close()
        except Exception as exc:
            lines.append("The confirmation lists could not be read: %s" % exc)
        if not lines:
            lines.append("Nothing awaits confirmation.")
        self.confirmation_text.config(state="normal")
        self.confirmation_text.delete("1.0", "end")
        self.confirmation_text.insert("end", "\n".join(lines))
        self.confirmation_text.config(state="disabled")

    # --- small widgets -------------------------------------------------------------------
    def _set_status(self, text):
        if not getattr(self, "_closing", False):
            self.status_label.config(text=text)

    def _append_log(self, message):
        if getattr(self, "_closing", False):
            return
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # --- clean shutdown --------------------------------------------------------------------
    def _on_closing(self):
        """Exact shutdown order for Windows/IDLE: closing flag, stdout,
        scroll-frame canvas, withdraw, cancel after-callbacks, destroy."""
        self._closing = True
        try:
            sys.stdout = sys.__stdout__
        except Exception:
            pass
        try:
            self._scroll_frame.destroy_canvas_first()
            self._scroll_frame.pack_forget()
            self._scroll_frame.destroy()
        except Exception:
            pass
        try:
            self.withdraw()
        except Exception:
            pass
        try:
            for callback in self.tk.call("after", "info"):
                try:
                    self.after_cancel(callback)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass


# --- Execution ---------------------------------------------------------------------
if __name__ == "__main__":
    app = DataManagerApp()
    app.mainloop()
