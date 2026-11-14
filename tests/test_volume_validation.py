"""L2 tests: row-level volume validation V-VOL-01 / V-VOL-02 (document 02
v1.6, section 7). Missing volume is accepted as null; non-numeric, negative
and fractional volumes quarantine only the offending row, with the original
value and reason kept as evidence, and valid rows in the same file import."""

# --- Imports -----------------------------------------------------------------
import glob
import os
import unittest
from datetime import date

import pandas as pd

import support
from qmap_database import standardise as std
from qmap_database import validation
from qmap_database.readers import detect_and_read

# --- Constants ---------------------------------------------------------------
# Headerless daily text (reader R3). Prices are steady so no G-03 issue arises.
_DAILY_LINES = [
    "2024-01-01,100,101,99,100.5,1000",
    "2024-01-02,100,101,99,100.5,",        # blank volume: missing, accepted
    "2024-01-03,100,101,99,100.5,abc",     # non-numeric
    "2024-01-04,100,101,99,100.5,-50",     # negative
    "2024-01-05,100,101,99,100.5,12.5",    # fractional
    "2024-01-08,100,101,99,100.5,2000",
]


# --- Helpers ------------------------------------------------------------------
def _write_daily_text(folder, name="CONCOR.txt"):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(_DAILY_LINES) + "\n")
    return path


def _validate_daily_file(path):
    result = detect_and_read(path, expect_intraday=False)
    standardised = std.standardise_daily(result.frame)
    return validation.validate_daily(standardised, "TEST")


def _quarantined_row(quarantine, day):
    rows = quarantine[quarantine["trade_date"] == day]
    if len(rows) != 1:
        raise AssertionError("expected one quarantined row for %s, found %d"
                             % (day, len(rows)))
    return rows.iloc[0]


class TestVolumeValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        folder = support.new_temp_folder("vol")
        cls.path = _write_daily_text(folder)
        cls.records, cls.quarantine, cls.issues = _validate_daily_file(cls.path)

    def test_t_vol_01_blank_volume_kept_as_null_and_accepted(self):
        row = self.records[self.records["trade_date"] == date(2024, 1, 2)]
        self.assertEqual(len(row), 1)
        self.assertTrue(pd.isna(row["volume"].iloc[0]))
        self.assertNotIn(date(2024, 1, 2),
                         list(self.quarantine["trade_date"]))

    def test_t_vol_02_non_numeric_volume_quarantined(self):
        row = _quarantined_row(self.quarantine, date(2024, 1, 3))
        self.assertEqual(row["reason_code"], validation.REASON_BAD_VOLUME)
        self.assertEqual(row["volume_invalid_text"], "abc")
        self.assertEqual(int(row["source_row"]), 3)
        self.assertEqual(float(row["close"]), 100.5)

    def test_t_vol_03_negative_volume_quarantined(self):
        row = _quarantined_row(self.quarantine, date(2024, 1, 4))
        self.assertEqual(row["reason_code"], validation.REASON_BAD_VOLUME)
        self.assertEqual(row["volume_invalid_text"], "-50")

    def test_t_vol_04_fractional_volume_quarantined(self):
        row = _quarantined_row(self.quarantine, date(2024, 1, 5))
        self.assertEqual(row["reason_code"], validation.REASON_BAD_VOLUME)
        self.assertEqual(row["volume_invalid_text"], "12.5")

    def test_t_vol_05_valid_rows_in_same_file_imported(self):
        # Reader/validation level: exactly the three valid rows survive.
        self.assertEqual(sorted(self.records["trade_date"]),
                         [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 8)])
        self.assertNotIn("volume_invalid_text", self.records.columns)
        self.assertEqual(len(self.quarantine), 3)

        # Full import: the file is imported (not failed), three rows stored,
        # three rows in the quarantine evidence with the original values.
        from qmap_database.maintenance import run_initial_load
        root = support.new_temp_folder("vol_load")
        source_folder = support.new_temp_folder("vol_src")
        path = _write_daily_text(source_folder)
        result = run_initial_load(root, [path])
        stored = support.canonical_frame(root, "NSE_EQ_DAILY", "CONCOR")
        self.assertEqual(sorted(stored["trade_date"]),
                         [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 8)])
        self.assertEqual(stored.loc[stored["trade_date"] == date(2024, 1, 8),
                                    "volume"].iloc[0], 2000)
        quarantine_files = glob.glob(os.path.join(root, "quarantine", "*",
                                                  "*.parquet"))
        self.assertEqual(len(quarantine_files), 1)
        evidence = pd.read_parquet(quarantine_files[0])
        self.assertEqual(sorted(evidence["volume_invalid_text"]),
                         ["-50", "12.5", "abc"])
        self.assertEqual(set(evidence["reason_code"]), {"BAD_VOLUME"})
        self.assertTrue(result is not None)

    def test_t_vol_06_intraday_csv_volume_row_level(self):
        # R2 previously failed the whole file on a non-numeric volume.
        folder = support.new_temp_folder("vol_csv")
        path = os.path.join(folder, "TEST_1.csv")
        lines = ["time,open,high,low,close,Volume"]
        for minute in range(40):
            volume = {5: "x1", 6: "", 7: "-3", 8: "1.5"}.get(minute, "10")
            lines.append("2024-01-02T09:%02d:00+05:30,100,101,99,100,%s"
                         % (15 + minute, volume))
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(lines) + "\n")
        result = detect_and_read(path, expect_intraday=True)
        frame = result.frame
        self.assertEqual(len(frame), 40)
        self.assertTrue(pd.isna(frame["volume"].iloc[6]))
        self.assertIsNone(frame["volume_invalid_text"].iloc[6])
        self.assertEqual(list(frame["volume_invalid_text"].iloc[[5, 7, 8]]),
                         ["x1", "-3", "1.5"])


if __name__ == "__main__":
    unittest.main()
