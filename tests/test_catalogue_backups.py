"""Regression tests: catalogue backup names are never reused and backups are
ordered chronologically (document 02 v1.6 section 10; TC-15).

Before the fix, backups were named to the second, so maintenance runs that
started within the same second overwrote each other's backup, and "the last
10 backups" was chosen by text order of dd_mmm_yy names, which is not
chronological across days or months.
"""

# --- Imports -----------------------------------------------------------------
import os
import unittest
from datetime import datetime
from unittest import mock

import support
from qmap_database import storage
from qmap_database.maintenance import run_initial_load, run_update

# --- Constants ---------------------------------------------------------------
FIXED_MOMENT = datetime(2026, 11, 14, 10, 40, 29)


class _FrozenDateTime(datetime):
    """datetime whose now() is fixed, so every backup falls in one second."""

    @classmethod
    def now(cls, tz=None):
        return FIXED_MOMENT


def _write_source(folder, days):
    path = os.path.join(folder, "CONCOR.txt")
    with open(path, "w") as handle:
        for day in days:
            handle.write("%s,100,101,99,100.5,10\n" % day)
    return path


class TestCatalogueBackupNames(unittest.TestCase):

    def test_same_second_backups_are_all_kept(self):
        root = support.new_temp_folder("bkp_unit")
        data_root = storage.DataRoot(root)
        data_root.ensure_layout()
        with open(data_root.catalogue_path, "wb") as handle:
            handle.write(b"catalogue v1")
        paths = []
        for version in (1, 2, 3):
            with open(data_root.catalogue_path, "wb") as handle:
                handle.write(b"catalogue v%d" % version)
            paths.append(storage.create_catalogue_backup(data_root,
                                                         now=FIXED_MOMENT))
        self.assertEqual([os.path.basename(p) for p in paths], [
            "qmap_catalogue_14_Nov_26_104029.duckdb",
            "qmap_catalogue_14_Nov_26_104029_002.duckdb",
            "qmap_catalogue_14_Nov_26_104029_003.duckdb"])
        # Each backup holds the catalogue as it was when it was taken.
        for version, path in enumerate(paths, start=1):
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"catalogue v%d" % version)

    def test_rapid_maintenance_runs_create_one_backup_each(self):
        # Every run_update in the same second must leave its own backup.
        source_folder = support.new_temp_folder("bkp_src")
        days = ["2026-10-%02d" % d for d in range(1, 10)]
        _write_source(source_folder, days[:3])
        root = support.new_temp_folder("bkp_root")
        run_initial_load(root, [os.path.join(source_folder, "CONCOR.txt")])
        runs = 6
        with mock.patch.object(storage, "datetime", _FrozenDateTime):
            for extra in range(3, 3 + runs):
                _write_source(source_folder, days[:extra + 1])
                result = run_update(root, [source_folder])
                self.assertEqual([o.action for o in result.file_outcomes],
                                 ["APPEND"])
        backups = os.listdir(os.path.join(root, "backups", "catalogue"))
        self.assertEqual(len(backups), runs)
        self.assertEqual(len(set(backups)), runs)

    def test_backups_are_ordered_chronologically(self):
        names = [
            "qmap_catalogue_14_Nov_26_104029_002.duckdb",
            "qmap_catalogue_02_Dec_26_090000.duckdb",
            "qmap_catalogue_14_Nov_26_104029.duckdb",
            "qmap_catalogue_30_Nov_26_235959.duckdb",
            "qmap_catalogue_14_Nov_26_104029_010.duckdb",
            "unexpected_file.txt",
        ]
        ordered = sorted(names, key=storage.catalogue_backup_sort_key)
        self.assertEqual(ordered, [
            "unexpected_file.txt",
            "qmap_catalogue_14_Nov_26_104029.duckdb",
            "qmap_catalogue_14_Nov_26_104029_002.duckdb",
            "qmap_catalogue_14_Nov_26_104029_010.duckdb",
            "qmap_catalogue_30_Nov_26_235959.duckdb",
            "qmap_catalogue_02_Dec_26_090000.duckdb",
        ])
        folder = support.new_temp_folder("bkp_order")
        for name in names:
            open(os.path.join(folder, name), "w").close()
        self.assertEqual(storage.latest_catalogue_backups(folder, 2), [
            "qmap_catalogue_30_Nov_26_235959.duckdb",
            "qmap_catalogue_02_Dec_26_090000.duckdb"])


if __name__ == "__main__":
    unittest.main()
