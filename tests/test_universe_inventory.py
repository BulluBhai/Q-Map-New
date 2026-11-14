"""Tests for the read-only stock-universe inventory (G-01; document 09 v1.6,
sections 3 and 8). Run on temporary copies of the approved daily fixtures;
expected figures are the source-verified values in documents 09 and 13."""

# --- Imports -----------------------------------------------------------------
import os
import shutil
import sys
import unittest
from datetime import date

import support

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "tools"))
import QMAP_Universe_Inventory as inventory  # noqa: E402


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestUniverseInventory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.folder = support.new_temp_folder("inventory_src")
        sub = os.path.join(cls.folder, "sub")
        os.makedirs(sub)
        for path in (support.CONCOR_TXT, support.CONCOR_PARQUET,
                     support.INFY_PARQUET):
            shutil.copy2(path, cls.folder)
        shutil.copy2(support.NIFTYIT_TXT, sub)
        with open(os.path.join(cls.folder, "notes.md"), "w") as handle:
            handle.write("not market data")
        cls.before = {name: inventory.sha256_of(os.path.join(cls.folder, name))
                      for name in os.listdir(cls.folder)
                      if os.path.isfile(os.path.join(cls.folder, name))}
        out_folder = support.new_temp_folder("inventory_out")
        cls.out_path = os.path.join(out_folder, "inventory.xlsx")
        cls.summary = inventory.run_inventory(cls.folder, cls.out_path,
                                              lambda kind, payload: None)
        cls.by_name = {r["file_name"]: r for r in cls.summary["records"]}

    def test_every_file_accounted_for(self):
        records = self.summary["records"]
        self.assertEqual(len(records), 5)
        self.assertEqual(self.by_name["notes.md"]["format"],
                         inventory.FORMAT_UNSUPPORTED)
        self.assertEqual(self.summary["fingerprint_changed"], [])

    def test_formats_rows_and_dates(self):
        concor = self.by_name["CONCOR.txt"]
        self.assertEqual((concor["format"], concor["rows_unique_dates"]),
                         (inventory.FORMAT_TXT7, 6860))
        self.assertEqual(concor["first_date_with_800_rows"], date(2002, 6, 6))
        infy = self.by_name["INFY_daily 02Jan98-06Nov26.parquet"]
        self.assertEqual((infy["symbol"], infy["format"],
                          infy["rows_unique_dates"]),
                         ("INFY", inventory.FORMAT_PARQUET, 7169))
        niftyit = self.by_name["Nifty IT.txt"]
        self.assertEqual((niftyit["format"], niftyit["rows_unique_dates"],
                          niftyit["ohlc_violation_rows"]),
                         (inventory.FORMAT_TXT_MIXED, 5761, 1))

    def test_large_moves_match_source_checks(self):
        concor = self.by_name["CONCOR.txt"]
        self.assertEqual((concor["large_moves_close"],
                          concor["large_moves_open_only"]), (5, 3))
        infy = self.by_name["INFY_daily 02Jan98-06Nov26.parquet"]
        self.assertEqual((infy["large_moves_close"],
                          infy["large_moves_open_only"]), (7, 1))

    def test_differing_concor_files_are_a_conflict_not_merged(self):
        self.assertTrue(self.by_name["CONCOR.txt"]["symbol_status"]
                        .startswith("DIFFERING"))
        self.assertFalse(self.by_name["CONCOR.txt"]
                         ["eligible_2_single_or_identical"])

    def test_workbook_and_sources_unchanged(self):
        import openpyxl
        workbook = openpyxl.load_workbook(self.out_path, read_only=True)
        self.assertEqual(workbook.sheetnames, [
            "Summary", "Files", "Symbols", "Format_Variants", "Problems",
            "Universe_Calendar", "Large_Moves", "Moves_By_Date",
            "Absences_For_Review", "Coverage", "Pilot_Eligibility", "Notes"])
        after = {name: inventory.sha256_of(os.path.join(self.folder, name))
                 for name in self.before}
        self.assertEqual(after, self.before)


if __name__ == "__main__":
    unittest.main()
