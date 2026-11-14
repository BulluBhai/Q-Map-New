"""L3 tests for M1b: incremental update, held revisions, failure injection,
retention, backup and restore (T-MNT-01 to 17b, T-BKP-01) and the confirmed
classification state (ACC-03). Documents 06 v1.5 section 5.6 and Verification
Package v1.2 section 8.

The failure injections run through the test hooks (the mechanism the test
strategy prescribes); T-MNT-06c injects inside the activation transaction, so
the deterministic outcome here is the not-committed branch - atomicity of the
committed branch is the DuckDB transaction guarantee.
"""

# --- Imports -----------------------------------------------------------------
import os
import shutil
import unittest
from datetime import date

import pandas as pd

import support
from qmap_database.catalogue import Catalogue
from qmap_database.maintenance import (SimulatedInterruption,
                                       approve_held_revision,
                                       confirm_cas_rule,
                                       confirm_special_session,
                                       reject_held_revision,
                                       run_initial_load, run_integrity_check,
                                       run_update, restore_from_backup)
from qmap_database.readers import sha256_of_file
from qmap_database.storage import DataRoot

# --- Constants ---------------------------------------------------------------
SHA_17A_INIT = ("e226b249691fbfc1eacc22d8f6a17d65e6423209adf4035aec9372526ec"
                "a117b")
SHA_17A_BAD = ("04a32652d426dafb332e54af3db5dfc84c546bda21fb0f0d4863270ec305"
               "5bb2")


# --- Helpers ------------------------------------------------------------------
def _concor_setup():
    """A data root with CONCOR imported from a writable copy of CONCOR.txt.
    Returns (root, source_folder, source_path)."""
    source_folder = support.new_temp_folder("mnt_src")
    source_path = os.path.join(source_folder, "CONCOR.txt")
    shutil.copyfile(support.CONCOR_TXT, source_path)
    root = support.new_temp_folder("mnt_root")
    result = run_initial_load(root, [source_path])
    assert result.file_outcomes[0].action == "NEW"
    return root, source_folder, source_path


def _concor_lines():
    with open(support.CONCOR_TXT, "rb") as handle:
        return handle.read().split(b"\r\n")


def _write_lines(path, lines):
    with open(path, "wb") as handle:
        handle.write(b"\r\n".join(lines))


def _scale_concor(source_path, factor, before_date, extra_line=None):
    """Rewrite the CONCOR copy with prices before `before_date` multiplied by
    `factor` (a synthetic revision for the held-revision tests)."""
    lines = []
    for line in _concor_lines():
        if not line:
            continue
        fields = line.decode().split(",")
        if fields[0] < before_date:
            for position in range(1, 5):
                fields[position] = "%.4f" % (float(fields[position]) * factor)
        lines.append(",".join(fields).encode())
    if extra_line is not None:
        lines.append(extra_line.encode())
    lines.append(b"")
    _write_lines(source_path, lines)


def _catalogue_facts(root, query, params=None):
    catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
    try:
        return catalogue.con.execute(query, params or []).fetchall()
    finally:
        catalogue.close()


def _active_generation(root, instrument_id):
    return _catalogue_facts(root, "SELECT active_generation FROM instrument "
                                  "WHERE instrument_id = ?",
                            [instrument_id])[0][0]


def _data_file_facts(root, instrument_id):
    return _catalogue_facts(root, "SELECT relative_path, row_count, sha256 "
                                  "FROM data_file WHERE instrument_id = ? "
                                  "ORDER BY generation, relative_path",
                            [instrument_id])


def _latest_closes(root, dataset, safe_name, n=5):
    frame = support.canonical_frame(root, dataset, safe_name)
    key = "trade_date" if "trade_date" in frame.columns else "ts"
    return frame.sort_values(key)["close"].tail(n).round(2).tolist()


def _nifty_17b_setup():
    """17b fixtures: NIFTY without 06-Nov-26 for the initial load, and the
    full fixture content for the update, both at one path."""
    source_folder = support.new_temp_folder("mnt17b_src")
    source_path = os.path.join(source_folder, "Nifty_1min_sample.parquet")
    full = pd.read_parquet(support.NIFTY_1MIN)[
        ["datetime", "open", "high", "low", "close", "Volume"]]
    init = full[full["datetime"].dt.date != date(2026, 11, 6)]
    assert len(init) == 168262
    init.to_parquet(source_path)
    root = support.new_temp_folder("mnt17b_root")
    result = run_initial_load(root, [source_path])
    assert result.file_outcomes[0].action == "NEW"
    return root, source_folder, source_path, full


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestIncrementalUpdate(unittest.TestCase):

    def test_t_mnt_01_unchanged_file_skipped(self):
        root, folder, _ = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["SKIPPED_UNCHANGED"])
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)

    def test_t_mnt_02_append(self):
        root, folder, source_path = _concor_setup()
        with open(source_path, "ab") as handle:
            handle.write(b"2026-11-09,440.00,442.00,438.00,441.00,100000,"
                         b"50000\r\n")
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        self.assertEqual(_active_generation(root, "CONCOR"), 2)
        rows = {generation: row_count for _, row_count, _ in []}
        facts = _catalogue_facts(root, "SELECT generation, row_count FROM "
                                       "data_file WHERE instrument_id = "
                                       "'CONCOR' ORDER BY generation")
        self.assertEqual(facts, [(1, 6860), (2, 6861)])
        # The previous generation's folder is retained on disk.
        self.assertTrue(os.path.isdir(os.path.join(
            root, "market", "NSE_EQ_DAILY", "CONCOR", "gen_000001")))

    def test_t_mnt_03_uniform_factor_revision_held(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        _scale_concor(source_path, 0.8, "2025-07-04")
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["HELD_REVISION"])
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)
        self.assertEqual(_active_generation(root, "CONCOR"), 1)
        issue = _catalogue_facts(root, "SELECT evidence FROM data_issue "
                                       "WHERE check_code = 'V-REV-01'")[0][0]
        self.assertIn("uniform factor 0.8000", issue)
        self.assertIn("candidate corporate action - not verified", issue)
        self.assertIn("2025-07-04", str(issue))
        held_folder = os.path.join(root, "held", "NSE_EQ_DAILY")
        self.assertEqual(len(os.listdir(held_folder)), 1)

    def test_t_mnt_03b_false_positive_uniform_factor_held(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        _scale_concor(source_path, 10.0, "2020-01-01")   # vendor unit error
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["HELD_REVISION"])
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)
        issue = _catalogue_facts(root, "SELECT evidence FROM data_issue "
                                       "WHERE check_code = 'V-REV-01'")[0][0]
        self.assertIn("uniform factor 10.0000", issue)
        self.assertIn("not verified", issue)

    def test_t_mnt_03c_owner_approves_held_revision(self):
        root, folder, source_path = _concor_setup()
        _scale_concor(source_path, 0.8, "2025-07-04")
        run_update(root, [folder])
        generation = approve_held_revision(root, "CONCOR")
        self.assertEqual(generation, 2)
        self.assertEqual(_active_generation(root, "CONCOR"), 2)
        frame = support.canonical_frame(root, "NSE_EQ_DAILY", "CONCOR")
        old_row = frame[frame["trade_date"].astype(str) == "1998-11-26"]
        self.assertAlmostEqual(old_row["close"].iloc[0], 29.44 * 0.8,
                               places=3)
        # The previous generation stays readable on disk.
        gen1 = os.path.join(root, "market", "NSE_EQ_DAILY", "CONCOR",
                            "gen_000001")
        self.assertTrue(os.path.isdir(gen1))
        actions = [row[0] for row in _catalogue_facts(
            root, "SELECT action FROM import_log ORDER BY import_id")]
        self.assertIn("APPLIED_APPROVED_REVISION", actions)

    def test_t_mnt_03d_owner_rejects_held_revision(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        _scale_concor(source_path, 10.0, "2020-01-01")
        run_update(root, [folder])
        reject_held_revision(root, "CONCOR", "vendor unit error")
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)
        result = run_update(root, [folder])   # same fingerprint again
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["REJECTED_REVISION"])
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)

    def test_t_mnt_04_unexplained_revision_held(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        lines = _concor_lines()
        for position, line in enumerate(lines):
            if line.startswith(b"2020-01-01,"):
                fields = line.decode().split(",")
                fields[4] = "%.2f" % (float(fields[4]) + 1.0)
                lines[position] = ",".join(fields).encode()
        _write_lines(source_path, lines)
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["HELD_REVISION"])
        issue = _catalogue_facts(root, "SELECT evidence FROM data_issue "
                                       "WHERE check_code = 'V-REV-01'")[0][0]
        self.assertIn("not uniform", issue)
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)

    def test_t_mnt_05_removed_rows_held(self):
        root, folder, source_path = _concor_setup()
        lines = [line for line in _concor_lines() if line]
        _write_lines(source_path, lines[10:] + [b""])
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["HELD_REVISION"])
        facts = _catalogue_facts(root, "SELECT rows_removed FROM import_log "
                                       "WHERE action = 'HELD_REVISION'")
        self.assertEqual(facts, [(10,)])
        self.assertEqual(_catalogue_facts(
            root, "SELECT row_count FROM data_file WHERE instrument_id = "
                  "'CONCOR'"), [(6860,)])

    def test_t_mnt_12_conflicting_sources_not_imported(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        second_path = os.path.join(folder, "CONCOR_daily_v2.txt")
        shutil.copyfile(source_path, second_path)
        lines = _concor_lines()
        lines[100] = lines[100].replace(b",", b",", 1)  # keep first file as is
        with open(second_path, "rb") as handle:
            second_lines = handle.read().split(b"\r\n")
        fields = second_lines[50].decode().split(",")
        fields[4] = "%.2f" % (float(fields[4]) + 5.0)
        second_lines[50] = ",".join(fields).encode()
        _write_lines(second_path, second_lines)
        # Make the registered file changed too, so both are fresh content.
        with open(source_path, "ab") as handle:
            handle.write(b"2026-11-09,440.00,442.00,438.00,441.00,100000,"
                         b"50000\r\n")
        result = run_update(root, [folder])
        actions = sorted(o.action for o in result.file_outcomes)
        self.assertEqual(actions, ["SOURCE_CONFLICT", "SOURCE_CONFLICT"])
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)

    def test_t_mnt_13_moved_unchanged_file_not_imported_twice(self):
        root, _, source_path = _concor_setup()
        other_folder = support.new_temp_folder("mnt13_new")
        shutil.copyfile(source_path, os.path.join(other_folder, "CONCOR.txt"))
        result = run_update(root, [other_folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["SKIPPED_UNCHANGED"])
        self.assertEqual(_active_generation(root, "CONCOR"), 1)

    def test_t_mnt_14_held_revision_holds_new_rows_visibly(self):
        root, folder, source_path = _concor_setup()
        _scale_concor(source_path, 0.8, "2025-07-04",
                      extra_line="2026-11-09,440.00,442.00,438.00,441.00,"
                                 "100000,50000")
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes],
                         ["HELD_REVISION"])
        last_ts = _catalogue_facts(root, "SELECT last_ts FROM coverage WHERE "
                                         "instrument_id = 'CONCOR'")[0][0]
        self.assertEqual(str(last_ts), "2026-11-06 00:00:00")
        self.assertEqual(_latest_closes(root, "NSE_EQ_DAILY", "CONCOR"),
                         [417.85, 419.15, 425.10, 440.85, 439.80])

    def test_t_mnt_15_inaccessible_registered_source_reported(self):
        root, folder, source_path = _concor_setup()
        before = _data_file_facts(root, "CONCOR")
        os.replace(source_path, os.path.join(folder, "CONCOR_renamed.txt"))
        result = run_update(root, [folder])
        self.assertEqual(result.inaccessible_sources, [source_path])
        self.assertIn(os.path.join(folder, "CONCOR_renamed.txt"),
                      result.unrecognised_files)
        self.assertEqual(_data_file_facts(root, "CONCOR"), before)
        issues = _catalogue_facts(root, "SELECT description FROM data_issue "
                                        "WHERE check_code = 'G-09'")
        self.assertEqual(len(issues), 1)
        self.assertIn("SOURCE_INACCESSIBLE", issues[0][0])
        self.assertIn(source_path, issues[0][0])

    def test_t_mnt_16_only_selected_folders_in_scope(self):
        folder_a = support.new_temp_folder("mnt16_a")
        folder_b = support.new_temp_folder("mnt16_b")
        concor_path = os.path.join(folder_a, "CONCOR.txt")
        infy_path = os.path.join(folder_b, "INFY_daily.parquet")
        shutil.copyfile(support.CONCOR_TXT, concor_path)
        shutil.copyfile(support.INFY_PARQUET, infy_path)
        root = support.new_temp_folder("mnt16_root")
        run_initial_load(root, [concor_path, infy_path])
        infy_before = _data_file_facts(root, "INFY")
        # Change both files; select only folder A.
        with open(concor_path, "ab") as handle:
            handle.write(b"2026-11-09,440.00,442.00,438.00,441.00,100000,"
                         b"50000\r\n")
        with open(infy_path, "ab") as handle:
            handle.write(b"junk")
        result = run_update(root, [folder_a])
        examined = {o.instrument_id for o in result.file_outcomes}
        self.assertEqual(examined, {"CONCOR"})
        self.assertEqual(result.out_of_scope_sources, 1)
        self.assertEqual(_data_file_facts(root, "INFY"), infy_before)

    def test_t_mnt_07_integrity_mismatch_detected(self):
        root, _, _ = _concor_setup()
        gen_folder = os.path.join(root, "market", "NSE_EQ_DAILY", "CONCOR",
                                  "gen_000001")
        file_path = os.path.join(gen_folder, "CONCOR.parquet")
        frame = pd.read_parquet(file_path)
        frame.iloc[0, frame.columns.get_loc("close")] += 1.0
        frame.to_parquet(file_path)
        problems = run_integrity_check(root)
        self.assertTrue(problems)
        self.assertIn("INTEGRITY_MISMATCH", problems[0])

    def test_t_mnt_08_pre_run_backup(self):
        root, folder, source_path = _concor_setup()
        with open(source_path, "ab") as handle:
            handle.write(b"2026-11-09,440.00,442.00,438.00,441.00,100000,"
                         b"50000\r\n")
        run_update(root, [folder])
        rows = _catalogue_facts(root, "SELECT started_at, "
                                      "catalogue_backup_path FROM "
                                      "maintenance_run WHERE run_type = "
                                      "'INCREMENTAL'")
        started_at, backup_path = rows[0]
        self.assertTrue(os.path.exists(backup_path))
        backup_mtime = pd.Timestamp(os.path.getmtime(backup_path), unit="s")
        self.assertLessEqual(backup_mtime.to_pydatetime().timestamp(),
                             started_at.timestamp() + 1)
        # The backup predates the update: it does not contain run 2.
        backup_con = Catalogue(backup_path, read_only=True)
        try:
            runs = backup_con.con.execute(
                "SELECT count(*) FROM maintenance_run WHERE run_type = "
                "'INCREMENTAL'").fetchone()[0]
        finally:
            backup_con.close()
        self.assertEqual(runs, 0)

    def test_t_mnt_09_reader_never_rebuilds(self):
        """M2 form of T-MNT-09: reading through QMapData creates no
        maintenance run and writes no data file. The scanner-run form is
        re-tested at M3 when the engine exists."""
        from qmap_database.access import QMapData
        root, _, _ = _concor_setup()
        runs_before = _catalogue_facts(root, "SELECT count(*) FROM "
                                             "maintenance_run")[0][0]
        files_before = _data_file_facts(root, "CONCOR")
        db = QMapData(root)
        try:
            db.get_bars("CONCOR", "1D", latest_n=5)
            db.get_bars("CONCOR", "1MO")
        finally:
            db.close()
        self.assertEqual(_catalogue_facts(root, "SELECT count(*) FROM "
                                                "maintenance_run")[0][0],
                         runs_before)
        self.assertEqual(_data_file_facts(root, "CONCOR"), files_before)

    def test_t_mnt_10_retention_never_removes_needed_generation(self):
        folder = support.new_temp_folder("mnt10_src")
        source_path = os.path.join(folder, "CONCOR.txt")
        days = ["2026-10-%02d" % d for d in range(1, 16)]
        with open(source_path, "w") as handle:
            for day in days[:3]:
                handle.write("%s,100,101,99,100.5,10\n" % day)
        root = support.new_temp_folder("mnt10_root")
        run_initial_load(root, [source_path])
        for extra in range(3, 15):   # 12 update runs
            with open(source_path, "a") as handle:
                handle.write("%s,100,101,99,100.5,10\n" % days[extra])
            result = run_update(root, [folder])
            self.assertEqual([o.action for o in result.file_outcomes],
                             ["APPEND"])
        backups_folder = os.path.join(root, "backups", "catalogue")
        backups = sorted(os.listdir(backups_folder))[-10:]
        needed = set()
        for name in backups:
            con = Catalogue(os.path.join(backups_folder, name),
                            read_only=True)
            try:
                for (generation,) in con.con.execute(
                        "SELECT active_generation FROM instrument WHERE "
                        "active_generation IS NOT NULL").fetchall():
                    needed.add(generation)
            finally:
                con.close()
        on_disk = {int(name.split("_")[1]) for name in os.listdir(
            os.path.join(root, "market", "NSE_EQ_DAILY", "CONCOR"))}
        for generation in needed:
            self.assertIn(generation, on_disk)
        # Generations older than every retained backup are pruned.
        self.assertNotIn(1, on_disk)


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestFailureInjection(unittest.TestCase):
    """T-MNT-06a to 06c and T-MNT-17a/17b, actually run through test hooks."""

    def test_t_mnt_06a_interrupted_during_staging(self):
        root, folder, source_path, full = _nifty_17b_setup()
        before = _data_file_facts(root, "NIFTY")
        full.to_parquet(source_path)
        staged = []

        def hook(file_path, period):
            staged.append(period)
            raise SimulatedInterruption("killed after the first staged file")

        with self.assertRaises(SimulatedInterruption):
            run_update(root, [folder], test_hooks={"after_stage": hook})
        self.assertEqual(len(staged), 1)
        self.assertEqual(_active_generation(root, "NIFTY"), 1)
        self.assertEqual(_data_file_facts(root, "NIFTY"), before)
        staging = os.path.join(root, "staging", "NSE_INDEX_1M", "NIFTY")
        self.assertTrue(os.path.isdir(staging))   # leftover from the "kill"
        # The next start recovers: staging deleted, then the update succeeds.
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        self.assertEqual(_active_generation(root, "NIFTY"), 2)

    def test_t_mnt_06b_interrupted_after_rename_before_activation(self):
        root, folder, source_path, full = _nifty_17b_setup()
        before = _data_file_facts(root, "NIFTY")
        full.to_parquet(source_path)

        def hook():
            raise SimulatedInterruption("killed after the folder rename")

        with self.assertRaises(SimulatedInterruption):
            run_update(root, [folder], test_hooks={"after_rename": hook})
        self.assertEqual(_active_generation(root, "NIFTY"), 1)
        self.assertEqual(_data_file_facts(root, "NIFTY"), before)
        gen2 = os.path.join(root, "market", "NSE_INDEX_1M", "NIFTY",
                            "gen_000002")
        self.assertTrue(os.path.isdir(gen2))   # renamed but never activated
        result = run_update(root, [folder])    # recovery removes it, then OK
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        self.assertEqual(_active_generation(root, "NIFTY"), 2)

    def test_t_mnt_06c_interrupted_inside_activation(self):
        root, folder, source_path, full = _nifty_17b_setup()
        before = _data_file_facts(root, "NIFTY")
        full.to_parquet(source_path)

        def hook():
            raise SimulatedInterruption("killed inside the activation "
                                        "transaction")

        with self.assertRaises(SimulatedInterruption):
            run_update(root, [folder], test_hooks={"in_activation": hook})
        # The transaction did not commit, so the previous generation is fully
        # active and no mixture is possible (the commit point is atomic).
        self.assertEqual(_active_generation(root, "NIFTY"), 1)
        self.assertEqual(_data_file_facts(root, "NIFTY"), before)
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        self.assertEqual(_active_generation(root, "NIFTY"), 2)
        facts = _catalogue_facts(root, "SELECT period, row_count FROM "
                                       "data_file WHERE instrument_id = "
                                       "'NIFTY' AND generation = 2 "
                                       "ORDER BY period")
        self.assertEqual(facts, [("2025", 90811), ("2026", 77812)])

    def test_t_mnt_17a_update_fails_reading(self):
        # Step 1: initial load with the byte-exact 6,859-line prefix.
        source_folder = support.new_temp_folder("mnt17a_src")
        source_path = os.path.join(source_folder, "CONCOR.txt")
        lines = [line for line in _concor_lines() if line]
        _write_lines(source_path, lines[:6859] + [b""])
        self.assertEqual(sha256_of_file(source_path), SHA_17A_INIT)
        root = support.new_temp_folder("mnt17a_root")
        result = run_initial_load(root, [source_path])
        self.assertEqual(result.file_outcomes[0].action, "NEW")
        self.assertEqual(result.file_outcomes[0].rows_stored, 6859)
        baseline = _data_file_facts(root, "CONCOR")
        self.assertEqual(_latest_closes(root, "NSE_EQ_DAILY", "CONCOR"),
                         [413.85, 417.85, 419.15, 425.10, 440.85])

        # Steps 2-4: the bad file fails at file level, naming line 6,860.
        _write_lines(source_path, lines[:6859]
                     + [b"2026-11-06,437.00,439.80,430.00", b""])
        self.assertEqual(sha256_of_file(source_path), SHA_17A_BAD)
        result = run_update(root, [source_folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["FAILED"])
        self.assertIn("line 6860 has 4 fields", result.file_outcomes[0].message)
        self.assertEqual(result.status, "FAILED")
        log_row = _catalogue_facts(
            root, "SELECT source_sha256, message FROM import_log WHERE "
                  "action = 'FAILED'")[0]
        self.assertEqual(log_row[0], SHA_17A_BAD)
        self.assertIn("CONCOR.txt", log_row[1])
        quality = _catalogue_facts(root, "SELECT quality_status FROM coverage "
                                         "WHERE instrument_id = 'CONCOR'")
        self.assertEqual(quality, [("FAIL",)])

        # Steps 5-6: the active generation and its data are untouched.
        self.assertEqual(_data_file_facts(root, "CONCOR"), baseline)
        self.assertEqual(_latest_closes(root, "NSE_EQ_DAILY", "CONCOR"),
                         [413.85, 417.85, 419.15, 425.10, 440.85])

        # Step 7: the same bad file fails again, never SKIPPED_UNCHANGED.
        result = run_update(root, [source_folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["FAILED"])

        # Step 8: the follow-up valid update runs as an ordinary APPEND.
        shutil.copyfile(support.CONCOR_TXT, source_path)
        result = run_update(root, [source_folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        self.assertEqual(_active_generation(root, "CONCOR"), 2)
        facts = _catalogue_facts(root, "SELECT generation, row_count FROM "
                                       "data_file WHERE instrument_id = "
                                       "'CONCOR' ORDER BY generation")
        self.assertEqual(facts, [(1, 6859), (2, 6860)])
        self.assertEqual(_latest_closes(root, "NSE_EQ_DAILY", "CONCOR"),
                         [417.85, 419.15, 425.10, 440.85, 439.80])
        quality = _catalogue_facts(root, "SELECT quality_status FROM coverage "
                                         "WHERE instrument_id = 'CONCOR'")
        self.assertEqual(quality, [("PASS_WITH_WARNINGS",)])

    def test_t_mnt_17b_staged_generation_validation_fails(self):
        root, folder, source_path, full = _nifty_17b_setup()
        baseline = _data_file_facts(root, "NIFTY")
        day_rows = _catalogue_facts(
            root, "SELECT present_candles + CAST(has_closing_auction AS "
                  "INTEGER) FROM day_profile WHERE instrument_id = 'NIFTY' "
                  "AND trade_date = DATE '2026-11-05'")
        self.assertEqual(day_rows, [(361,)])
        full.to_parquet(source_path)

        def corrupt(file_path, period):
            if period == "2026":
                frame = pd.read_parquet(file_path)
                frame.iloc[:-1].to_parquet(file_path)   # drop one row

        result = run_update(root, [folder],
                            test_hooks={"after_stage": corrupt})
        self.assertEqual([o.action for o in result.file_outcomes], ["FAILED"])
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(_data_file_facts(root, "NIFTY"), baseline)
        self.assertEqual(_active_generation(root, "NIFTY"), 1)
        self.assertFalse(os.path.isdir(os.path.join(
            root, "staging", "NSE_INDEX_1M", "NIFTY")))   # staging discarded
        quality = _catalogue_facts(root, "SELECT quality_status FROM coverage "
                                         "WHERE instrument_id = 'NIFTY'")
        self.assertEqual(quality, [("FAIL",)])
        # No 06-Nov-26 row is ever readable.
        frame = support.canonical_frame(root, "NSE_INDEX_1M", "NIFTY")
        self.assertEqual((frame["ts"].dt.date == date(2026, 11, 6)).sum(), 0)
        # Re-run without the hook: APPEND of the 361 rows of 06-Nov-26.
        result = run_update(root, [folder])
        self.assertEqual([o.action for o in result.file_outcomes], ["APPEND"])
        rows_new = _catalogue_facts(root, "SELECT rows_new FROM import_log "
                                          "WHERE action = 'APPEND'")[0][0]
        self.assertEqual(rows_new, 361)
        facts = _catalogue_facts(root, "SELECT period, row_count FROM "
                                       "data_file WHERE instrument_id = "
                                       "'NIFTY' AND generation = 2 "
                                       "ORDER BY period")
        self.assertEqual(facts, [("2025", 90811), ("2026", 77812)])


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestBackupRestore(unittest.TestCase):

    def test_t_bkp_01_restore_consistent(self):
        root, folder, source_path = _concor_setup()
        before_facts = _data_file_facts(root, "CONCOR")
        before_closes = _latest_closes(root, "NSE_EQ_DAILY", "CONCOR")
        with open(source_path, "ab") as handle:
            handle.write(b"2026-11-09,440.00,442.00,438.00,441.00,100000,"
                         b"50000\r\n")
        run_update(root, [folder])
        self.assertEqual(_active_generation(root, "CONCOR"), 2)
        backups_folder = os.path.join(root, "backups", "catalogue")
        backup_path = os.path.join(backups_folder,
                                   sorted(os.listdir(backups_folder))[-1])
        problems = restore_from_backup(root, backup_path)
        self.assertEqual(problems, [])   # integrity check passes
        self.assertEqual(_active_generation(root, "CONCOR"), 1)
        self.assertEqual(_data_file_facts(root, "CONCOR"), before_facts)
        self.assertEqual(_latest_closes(root, "NSE_EQ_DAILY", "CONCOR"),
                         before_closes)
        # The newer, now-unactivated generation was reported and removed.
        self.assertFalse(os.path.isdir(os.path.join(
            root, "market", "NSE_EQ_DAILY", "CONCOR", "gen_000002")))


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestConfirmationsAndRevalidate(unittest.TestCase):
    """ACC-03's confirmed state, via the Owner confirmation workflow."""

    def test_acc_03_confirmed_state(self):
        from datetime import time
        root = support.new_temp_folder("acc03_root")
        run_initial_load(root, [support.NIFTY_1MIN, support.BANKNIFTY_1MIN])
        confirm_cas_rule(root, "NIFTY", "Owner confirmation of the CAS "
                         "detection list", "Owner, 14-Nov-26")
        confirm_cas_rule(root, "BANKNIFTY", "Owner confirmation",
                         "Owner, 14-Nov-26")
        confirm_special_session(root, "NIFTY", date(2025, 10, 21), "SPECIAL",
                                time(13, 45), time(14, 45), "Muhurat",
                                "Owner, 14-Nov-26")
        confirm_special_session(root, "NIFTY", date(2025, 2, 1), "SPECIAL",
                                time(9, 15), time(15, 30), "Budget day",
                                "Owner, 14-Nov-26")
        confirm_special_session(root, "NIFTY", date(2026, 2, 1), "SPECIAL",
                                time(9, 15), time(15, 30), "Budget day",
                                "Owner, 14-Nov-26")
        confirm_special_session(root, "BANKNIFTY", date(2026, 11, 8),
                                "SPECIAL_CAS", time(14, 20), None, "Muhurat",
                                "Owner, 14-Nov-26")
        nifty = support.canonical_frame(root, "NSE_INDEX_1M", "NIFTY")
        banknifty = support.canonical_frame(root, "NSE_INDEX_1M", "BANKNIFTY")
        # 02 section 6.3: counts after the Owner confirms the special days.
        self.assertEqual(nifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 168555, "CLOSING_AUCTION": 68})
        self.assertEqual(banknifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 21293, "AUCTION_PHASE": 43,
                          "CLOSING_AUCTION": 60})
        for frame in (nifty, banknifty):
            flags = frame["quality_flags"].fillna("")
            self.assertEqual(int(flags.str.contains("SESSION_UNCONFIRMED")
                                 .sum()), 0)
            self.assertEqual(int(flags.str.contains("CAS_CANDIDATE").sum()),
                             0)
        statuses = _catalogue_facts(root, "SELECT DISTINCT session_status "
                                          "FROM day_profile")
        self.assertEqual(sorted(row[0] for row in statuses),
                         ["CANDIDATE", "CONFIRMED_BY_OWNER"])
        # Candidates that remain are only pre-CAS regular weekdays.
        remaining = _catalogue_facts(root, "SELECT DISTINCT session_type "
                                           "FROM day_profile WHERE "
                                           "session_status = 'CANDIDATE'")
        self.assertEqual([row[0] for row in remaining], ["REGULAR"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
