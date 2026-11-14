"""Q-MAP Data Manager (M1a initial load + M1b maintenance).

Open this file in IDLE on the Owner's PC and press F5. Pick the data root
folder and the source files, then run the Initial load. For maintenance, pick
the folders holding changed source files and run Update: unchanged files are
skipped, new rows are appended, and every change to stored history is HELD
for your approve/reject decision. The confirmation list records your answers
on CAS days and unrecognised sessions and re-validates the data. Check
integrity and Restore follow document 02 section 10.

Only this program writes to the Q-MAP database.
"""

# --- Imports -----------------------------------------------------------------
import os
import queue
import sys
import threading
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qmap_database import settings as settings_mod          # noqa: E402
from qmap_database.errors import DatabaseUnavailableError   # noqa: E402
from qmap_database.maintenance import (                     # noqa: E402
    approve_held_revision, confirm_cas_rule, confirm_special_session,
    export_m1a_evidence, reject_held_revision, run_initial_load,
    run_integrity_check, run_update, restore_from_backup,
    verify_continuity_issue)

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


def _is_inside(path, folder):
    """True when path is folder or lies inside it. Case-insensitive on
    Windows, and a sibling such as D:\\QMAP_DATA_out is not 'inside'."""
    path = os.path.normcase(os.path.abspath(path))
    folder = os.path.normcase(os.path.abspath(folder))
    try:
        return os.path.commonpath([path, folder]) == folder
    except ValueError:                     # different drives on Windows
        return False


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
        self._build_maintenance_section(body)
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

    def _build_maintenance_section(self, body):
        frame = tk.LabelFrame(body, text="4. Maintenance (M1b)", padx=6,
                              pady=4)
        frame.pack(fill="x", padx=8, pady=2)
        row = tk.Frame(frame)
        row.pack(fill="x")
        tk.Button(row, text="Add update folder...",
                  command=self._add_update_folder).pack(side="left")
        tk.Button(row, text="Clear folders",
                  command=lambda: self.folder_list.delete(0, "end")).pack(
            side="left", padx=4)
        self.update_button = tk.Button(row, text="Run update",
                                       font=("TkDefaultFont", 10, "bold"),
                                       command=self._start_update)
        self.update_button.pack(side="left", padx=12)
        tk.Button(row, text="Check integrity",
                  command=self._start_integrity_check).pack(side="left",
                                                            padx=4)
        tk.Button(row, text="Restore catalogue backup...",
                  command=self._start_restore).pack(side="left", padx=4)
        tk.Button(row, text="Export data summary...",
                  command=self._start_export).pack(side="left", padx=4)
        self.folder_list = tk.Listbox(frame, height=3, selectmode="extended")
        self.folder_list.pack(fill="x", pady=(4, 0))
        for folder in self.settings.get("last_source_folders", []):
            if os.path.isdir(folder):
                self.folder_list.insert("end", folder)
        tk.Label(frame, anchor="w", fg="grey25",
                 text="An Update examines only the folders listed here "
                      "(G-09). Changes to stored history are HELD for your "
                      "decision; nothing is applied automatically.").pack(
            fill="x")

    def _build_confirmation_section(self, body):
        frame = tk.LabelFrame(
            body, text="Awaiting your decision - sessions, held revisions "
                       "and continuity issues (G-03)",
            padx=6, pady=4)
        frame.pack(fill="both", padx=8, pady=(2, 8))
        self.pending_list = tk.Listbox(frame, height=10)
        self.pending_list.pack(fill="both", expand=True)
        self._pending_items = []
        row = tk.Frame(frame)
        row.pack(fill="x", pady=(4, 0))
        tk.Button(row, text="Confirm selected...",
                  command=self._confirm_selected).pack(side="left")
        tk.Button(row, text="Approve held revision",
                  command=lambda: self._decide_revision(True)).pack(
            side="left", padx=4)
        tk.Button(row, text="Reject held revision",
                  command=lambda: self._decide_revision(False)).pack(
            side="left")
        tk.Button(row, text="Refresh list",
                  command=self._refresh_pending).pack(side="right")

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
                elif kind == "action_done":
                    self._finish_action(payload)
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
        self.update_button.config(state="normal")
        self._set_status("Finished: %s - %s" % (result.status, result.summary))
        self._append_log("=== Finished: %s ===" % result.status)
        if result.report_path:
            self._append_log("Validation report: %s" % result.report_path)
        self._report_unrecognised(result.unrecognised_files)
        self._refresh_pending()

    def _finish_action(self, outcome):
        """Completion of an update, decision, confirmation, integrity check
        or restore (anything run through _run_in_background)."""
        if getattr(self, "_closing", False):
            return
        self._run_started_at = None
        self.run_button.config(state="normal")
        self.update_button.config(state="normal")
        if hasattr(outcome, "status"):          # an UpdateResult
            self._set_status("Finished: %s - %s" % (outcome.status,
                                                    outcome.summary))
            self._append_log("=== Finished: %s ===" % outcome.status)
            if outcome.report_path:
                self._append_log("Validation report: %s" % outcome.report_path)
            self._report_unrecognised(outcome.unrecognised_files)
        elif isinstance(outcome, list):         # integrity / restore problems
            if outcome:
                self._set_status("Integrity problems found - see the log.")
                for problem in outcome:
                    self._append_log(problem)
            else:
                self._set_status("Done. Integrity check PASSED.")
                self._append_log("Integrity check PASSED.")
        else:
            self._set_status("Done.")
            self._append_log("=== Done ===")
        self._refresh_pending()

    def _report_unrecognised(self, paths):
        """Explain files whose name matches no registered instrument. They
        were not imported and nothing else changed. New instruments are
        registered in the pilot stage (M1c), after the Owner approves the
        pilot list, so the Data Manager cannot map them yet."""
        if not paths:
            return
        registered = "the registered instruments"
        try:
            from qmap_database.catalogue import Catalogue
            from qmap_database.storage import DataRoot
            catalogue = Catalogue(DataRoot(
                self.data_root_var.get().strip()).catalogue_path,
                read_only=True)
            try:
                registered = ", ".join(sorted(
                    i["instrument_id"] for i in catalogue.instruments()))
            finally:
                catalogue.close()
        except Exception:
            pass
        self._append_log("NOT IMPORTED - %d file(s) whose name is not a "
                         "registered instrument. Nothing was changed for "
                         "them:" % len(paths))
        for path in paths:
            self._append_log("  %s" % path)
        self._append_log("Q-MAP can load only these instruments at present: "
                         "%s. Other stocks are added in the pilot stage, "
                         "after you approve the pilot list." % registered)

    def _fail_run(self, message):
        if getattr(self, "_closing", False):
            return
        self._run_started_at = None
        self.run_button.config(state="normal")
        self.update_button.config(state="normal")
        self._set_status("The run failed. See the log for details.")
        self._append_log(message)
        messagebox.showerror(WINDOW_TITLE, message.splitlines()[0])

    def _refresh_pending(self):
        """The CAS-candidate, unrecognised-day and held-revision lists
        awaiting the Owner (02 sections 6.2 and 9.3)."""
        self.pending_list.delete(0, "end")
        self._pending_items = []
        try:
            from qmap_database.catalogue import Catalogue
            from qmap_database.storage import DataRoot
            data_root = DataRoot(self.data_root_var.get().strip())
            catalogue = Catalogue(data_root.catalogue_path, read_only=True)
            try:
                for (instrument_id, count, first, last) in \
                        catalogue.cas_confirmation_list():
                    self._pending_items.append(("cas", instrument_id, None))
                    self.pending_list.insert(
                        "end", "%s: CAS shape on %d day(s) from %s to %s - "
                               "confirm the CAS rule?"
                               % (instrument_id, count,
                                  first.strftime("%d %b %y"),
                                  last.strftime("%d %b %y")))
                for (instrument_id, day, first_record, last_candle, present,
                     missing) in catalogue.unrecognised_days():
                    self._pending_items.append(("day", instrument_id, day))
                    self.pending_list.insert(
                        "end", "%s %s: records %s-%s only (%s present). "
                               "Special session, or truncated data?"
                               % (instrument_id, day.strftime("%d %b %y"),
                                  first_record, last_candle, present))
                for (issue_id, instrument_id, ts_from, check_code,
                     description) in \
                        catalogue.continuity_issues_awaiting_owner():
                    self._pending_items.append(("continuity", instrument_id,
                                                (issue_id, ts_from,
                                                 description)))
                    self.pending_list.insert(
                        "end", "G-03 BLOCKING - %s %s: %s"
                               % (instrument_id,
                                  ts_from.strftime("%d %b %y"),
                                  description[:140]))
                for (issue_id, instrument_id, description, _) in \
                        catalogue.held_revisions():
                    self._pending_items.append(("revision", instrument_id,
                                                issue_id))
                    self.pending_list.insert(
                        "end", "HELD REVISION - %s: %s"
                               % (instrument_id, description[:160]))
            finally:
                catalogue.close()
        except Exception as exc:
            self.pending_list.insert("end",
                                     "The lists could not be read: %s" % exc)
        if not self._pending_items:
            self.pending_list.insert("end", "Nothing awaits your decision.")

    def _selected_pending(self):
        selection = self.pending_list.curselection()
        if not selection or selection[0] >= len(self._pending_items):
            messagebox.showinfo(WINDOW_TITLE, "Please select an item in the "
                                              "list first.")
            return None
        return self._pending_items[selection[0]]

    def _confirm_selected(self):
        item = self._selected_pending()
        if item is None:
            return
        kind, instrument_id, payload = item
        data_root = self.data_root_var.get().strip()
        if kind == "cas":
            evidence = simpledialog.askstring(
                WINDOW_TITLE, "You are confirming the CAS rule for %s from "
                              "03 Aug 26 (D-06).\nPlease state your basis "
                              "(e.g. the NSE circular):" % instrument_id)
            if not evidence:
                return
            self._run_in_background(
                "Confirming the CAS rule for %s and re-validating..."
                % instrument_id,
                lambda: confirm_cas_rule(data_root, instrument_id, evidence,
                                         "Owner, %s"
                                         % datetime.now().strftime("%d %b %y")))
        elif kind == "day":
            answer = simpledialog.askstring(
                WINDOW_TITLE,
                "Confirm %s %s as a special session.\nEnter: TYPE OPEN CLOSE"
                "\nTYPE is SPECIAL or SPECIAL_CAS; times are HH:MM"
                " (CLOSE may be blank when unknown).\nExample: SPECIAL 13:45 "
                "14:45" % (instrument_id, payload.strftime("%d %b %y")))
            if not answer:
                return
            parts = answer.split()
            if len(parts) < 2 or parts[0] not in ("SPECIAL", "SPECIAL_CAS"):
                messagebox.showerror(WINDOW_TITLE, "Please enter TYPE OPEN "
                                                   "[CLOSE], e.g. SPECIAL "
                                                   "13:45 14:45")
                return
            def parse_time(text):
                hour, minute = text.split(":")
                import datetime as dt
                return dt.time(int(hour), int(minute))
            session_open = parse_time(parts[1])
            session_close = parse_time(parts[2]) if len(parts) > 2 else None
            self._run_in_background(
                "Confirming %s %s and re-validating..."
                % (instrument_id, payload),
                lambda: confirm_special_session(
                    data_root, instrument_id, payload, parts[0], session_open,
                    session_close, "Owner confirmation",
                    "Owner, %s" % datetime.now().strftime("%d %b %y")))
        elif kind == "continuity":
            issue_id, ts_from, description = payload
            note = simpledialog.askstring(
                WINDOW_TITLE,
                "G-03: mark this occurrence VERIFIED_OK only after you have "
                "personally verified it as a genuine move.\n\n%s %s\n%s\n\n"
                "It will no longer block continuity-dependent calculations "
                "(e.g. the EMA scanner). Other occurrences stay blocking.\n\n"
                "State your basis (kept as evidence):"
                % (instrument_id, ts_from.strftime("%d %b %y"),
                   description[:300]))
            if not note or not note.strip():
                return
            self._run_in_background(
                "Recording your verification of %s %s..."
                % (instrument_id, ts_from.strftime("%d %b %y")),
                lambda: verify_continuity_issue(
                    data_root, issue_id,
                    "%s (Owner, %s)" % (note.strip(),
                                        datetime.now().strftime("%d %b %y"))))
        else:
            messagebox.showinfo(WINDOW_TITLE, "Use the Approve/Reject "
                                              "buttons for a held revision.")

    def _decide_revision(self, approve):
        item = self._selected_pending()
        if item is None:
            return
        kind, instrument_id, _ = item
        if kind != "revision":
            messagebox.showinfo(WINDOW_TITLE, "Please select a held revision.")
            return
        data_root = self.data_root_var.get().strip()
        if approve:
            if not messagebox.askyesno(
                    WINDOW_TITLE, "Apply the held revision for %s? The "
                                  "previous data generation is retained."
                    % instrument_id):
                return
            self._run_in_background(
                "Applying the approved revision for %s..." % instrument_id,
                lambda: approve_held_revision(data_root, instrument_id))
        else:
            note = simpledialog.askstring(
                WINDOW_TITLE, "Reason for rejecting the %s revision "
                              "(kept as evidence):" % instrument_id) or ""
            self._run_in_background(
                "Rejecting the held revision for %s..." % instrument_id,
                lambda: reject_held_revision(data_root, instrument_id, note))

    # --- maintenance handlers ------------------------------------------------------
    def _add_update_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder of changed "
                                               "source files")
        if folder and folder not in self.folder_list.get(0, "end"):
            self.folder_list.insert("end", folder)

    def _start_update(self):
        if self._worker is not None and self._worker.is_alive():
            messagebox.showinfo(WINDOW_TITLE, "A run is already in progress.")
            return
        folders = list(self.folder_list.get(0, "end"))
        data_root = self.data_root_var.get().strip()
        if not data_root or not folders:
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root "
                                               "and at least one update "
                                               "folder.")
            return
        self.settings["data_root"] = data_root
        self.settings["last_source_folders"] = folders
        settings_mod.save_settings(self.settings)
        self._run_in_background(
            "Running the update...",
            lambda: run_update(
                data_root, folders,
                live_log=lambda m: self._queue.put(("log", m)),
                progress=lambda s, t, x: self._queue.put(("progress",
                                                          (s, t, x)))))

    def _start_integrity_check(self):
        data_root = self.data_root_var.get().strip()
        if not data_root:
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root "
                                               "first.")
            return
        self._run_in_background(
            "Checking integrity...",
            lambda: run_integrity_check(
                data_root, live_log=lambda m: self._queue.put(("log", m))))

    def _start_restore(self):
        data_root = self.data_root_var.get().strip()
        if not data_root:
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root "
                                               "first.")
            return
        backup = filedialog.askopenfilename(
            title="Choose the catalogue backup to restore",
            initialdir=os.path.join(data_root, "backups", "catalogue"),
            filetypes=[("Catalogue backups", "*.duckdb")])
        if not backup:
            return
        if not messagebox.askyesno(
                WINDOW_TITLE, "Restore the catalogue from\n%s?\n\nEvery "
                              "other Q-MAP program must be closed. Check "
                              "integrity runs afterwards." % backup):
            return
        self._run_in_background(
            "Restoring the catalogue backup...",
            lambda: restore_from_backup(
                data_root, backup,
                live_log=lambda m: self._queue.put(("log", m))))

    def _start_export(self):
        """Write the catalogue summary CSVs (sources and fingerprints, record
        counts, all issues, all quarantined rows) to a chosen folder for
        inspection in Excel. Read-only for the database."""
        data_root = self.data_root_var.get().strip()
        if not data_root:
            messagebox.showerror(WINDOW_TITLE, "Please choose the data root "
                                               "first.")
            return
        folder = filedialog.askdirectory(
            title="Choose a folder for the summary files (outside the data "
                  "root)")
        if not folder:
            return
        if _is_inside(folder, data_root):
            messagebox.showerror(WINDOW_TITLE, "Please choose a folder "
                                               "outside the data root.")
            return

        def action():
            for path in export_m1a_evidence(data_root, folder):
                self._queue.put(("log", "Written: %s" % path))
            return None
        self._run_in_background("Exporting the data summary...", action)

    def _run_in_background(self, status_text, action):
        """Run one maintenance action off the main thread, with the usual
        queue-based completion handling."""
        if self._worker is not None and self._worker.is_alive():
            messagebox.showinfo(WINDOW_TITLE, "A run is already in progress.")
            return
        self.run_button.config(state="disabled")
        self.update_button.config(state="disabled")
        self._run_started_at = datetime.now()
        self._set_status(status_text)
        self._append_log("=== %s ===" % status_text)

        def worker():
            try:
                outcome = action()
                self._queue.put(("action_done", outcome))
            except DatabaseUnavailableError as exc:
                self._queue.put(("error", str(exc)))
            except Exception:
                self._queue.put(("error", "Unexpected error:\n%s"
                                 % traceback.format_exc()))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

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
