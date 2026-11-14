"""L1 tests: file discovery, readers and schema (T-FILE-01 to 09, T-IMP-01
to 04). Document 06 v1.5, sections 5.1 and 5.2."""

# --- Imports -----------------------------------------------------------------
import os
import unittest
from datetime import date, datetime, timedelta

import pandas as pd

import support
from qmap_database import standardise as std
from qmap_database import validation
from qmap_database.errors import FileImportError
from qmap_database.readers import (READER_R1, READER_R2, READER_R3, READER_R4,
                                   detect_and_read)


# --- Helpers ------------------------------------------------------------------
def _write_minutes_parquet(path, rows):
    """rows: list of (ts, o, h, l, c, volume or None)."""
    frame = pd.DataFrame(rows, columns=["datetime", "open", "high", "low",
                                        "close", "Volume"])
    frame["Volume"] = frame["Volume"].astype("Int64")
    frame.to_parquet(path)


class TestReaders(unittest.TestCase):

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_file_01_recognise_each_format(self):
        cases = [
            (support.NIFTY_1MIN, True, READER_R1),
            (support.BANKNIFTY_CSV, True, READER_R2),
            (support.NIFTYIT_TXT, False, READER_R3),   # 6- and 7-field lines
            (support.CONCOR_TXT, False, READER_R3),    # 7-field lines
            (support.INFY_PARQUET, False, READER_R4),
        ]
        for path, intraday, expected_reader in cases:
            result = detect_and_read(path, intraday)
            self.assertEqual(result.reader_id, expected_reader,
                             os.path.basename(path))

    @unittest.skipUnless(os.path.exists(support.NIFTY_1MIN), "sample absent")
    def test_t_file_02_missing_required_column(self):
        folder = support.new_temp_folder("tfile02")
        raw = pd.read_parquet(support.NIFTY_1MIN).drop(columns=["close"])
        path = os.path.join(folder, "Nifty_1min_noclose.parquet")
        raw.head(5000).to_parquet(path)
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(path, True)
        self.assertIn("close", str(ctx.exception))

    @unittest.skipUnless(os.path.exists(support.NIFTY_1MIN), "sample absent")
    def test_t_file_03_indicator_columns_ignored(self):
        result = support.read_raw(support.NIFTY_1MIN)
        self.assertGreaterEqual(len(result.ignored_columns), 18)
        self.assertEqual(list(result.frame.columns),
                         ["ts", "open", "high", "low", "close", "volume",
                          "volume_invalid_text", "source_row"])

    @unittest.skipUnless(os.path.exists(support.NIFTY_1MIN), "sample absent")
    def test_t_file_04_unreadable_file(self):
        folder = support.new_temp_folder("tfile04")
        path = os.path.join(folder, "Nifty_1min_truncated.parquet")
        with open(support.NIFTY_1MIN, "rb") as source:
            data = source.read(1000)
        with open(path, "wb") as target:
            target.write(data)
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(path, True)
        self.assertIn("not imported", str(ctx.exception))

    def test_t_file_05_unknown_file_name(self):
        from qmap_database.catalogue import INITIAL_INSTRUMENTS
        from qmap_database.maintenance import match_instrument
        instruments = [{"instrument_id": row[0], "source_aliases": row[6]}
                       for row in INITIAL_INSTRUMENTS]
        self.assertIsNone(match_instrument("C:/data/XYZ_data.txt",
                                           instruments))
        self.assertEqual(match_instrument("C:/data/CONCOR.txt",
                                          instruments)["instrument_id"],
                         "CONCOR")

    @unittest.skipUnless(os.path.exists(support.NIFTY_3MIN), "sample absent")
    def test_t_file_06_derived_file_rejected(self):
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(support.NIFTY_3MIN, True)
        self.assertIn("most common time step is 3 minutes", str(ctx.exception))
        self.assertIn("1-minute data required", str(ctx.exception))

    @unittest.skipUnless(os.path.exists(support.BANKNIFTY_1MIN),
                         "sample absent")
    def test_t_file_07_missing_minutes_accepted(self):
        result = support.read_raw(support.BANKNIFTY_1MIN)
        self.assertEqual(result.reader_id, READER_R1)
        self.assertEqual(len(result.frame), 21396)
        self.assertEqual(result.resolution_suspect_days, [])

    def test_t_file_08_resolution_not_established(self):
        folder = support.new_temp_folder("tfile08")
        rows = [(datetime(2026, 1, 1, 9, 15) + timedelta(days=i),
                 100.0, 101.0, 99.0, 100.5, None) for i in range(40)]
        path = os.path.join(folder, "one_record_per_day.parquet")
        _write_minutes_parquet(path, rows)
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(path, True)
        self.assertIn("cannot establish 1-minute resolution",
                      str(ctx.exception))

    def test_t_file_09_coarser_day_flagged_not_changed(self):
        folder = support.new_temp_folder("tfile09")
        rows = []
        for day in range(5):   # five clean 1-minute days
            base = datetime(2026, 1, 5 + day, 9, 15)
            for minute in range(60):
                rows.append((base + timedelta(minutes=minute),
                             100.0, 101.0, 99.0, 100.5, None))
        coarse_base = datetime(2026, 1, 12, 9, 15)   # one 3-minute day
        for bar in range(125):
            rows.append((coarse_base + timedelta(minutes=3 * bar),
                         100.0, 101.0, 99.0, 100.5, None))
        path = os.path.join(folder, "mixed_resolution.parquet")
        _write_minutes_parquet(path, rows)
        result = detect_and_read(path, True)
        self.assertEqual(len(result.frame), 5 * 60 + 125)  # nothing removed
        self.assertEqual(result.resolution_suspect_days, [date(2026, 1, 12)])


class TestImportParsing(unittest.TestCase):

    def _csv_file(self, time_text):
        folder = support.new_temp_folder("timp")
        path = os.path.join(folder, "NSE_BANKNIFTY_sample.csv")
        header = "time,open,high,low,close,Volume\n"
        lines = [header]
        # 35 rows so the file passes the 30-gap resolution minimum.
        base = datetime(2026, 8, 17, 9, 15)
        for offset in range(35):
            ts = base + timedelta(minutes=offset)
            stamp = ts.strftime("%Y-%m-%dT%H:%M:%S") + time_text
            lines.append("%s,100.0,101.0,99.0,100.5,10\n" % stamp)
        with open(path, "w", encoding="utf-8") as handle:
            handle.writelines(lines)
        return path

    def test_t_imp_01_ist_offset_removed(self):
        result = detect_and_read(self._csv_file("+05:30"), True)
        self.assertEqual(result.frame["ts"].iloc[0],
                         pd.Timestamp("2026-08-17 09:15:00"))

    def test_t_imp_02_wrong_offset_rejected(self):
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(self._csv_file("+00:00"), True)
        self.assertIn("+00:00", str(ctx.exception))
        self.assertIn("+05:30", str(ctx.exception))

    def test_t_imp_03_six_and_seven_field_lines(self):
        folder = support.new_temp_folder("timp03")
        path = os.path.join(folder, "MIXED.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("2026-11-06,33270.15,33616.2,32727.05,32977.9,"
                         "49068677\r\n")
            handle.write("2003-08-25,13933.45,14193.35,13142.6,13522.95,"
                         "30749892,30749892\r\n")
        result = detect_and_read(path, False)
        self.assertEqual(len(result.frame), 2)
        self.assertEqual(sorted(result.frame["volume"].tolist()),
                         [30749892, 49068677])

    def test_t_imp_03b_wrong_field_count_fails_file(self):
        folder = support.new_temp_folder("timp03b")
        path = os.path.join(folder, "BROKEN.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("2026-11-06,33270.15,33616.2,32727.05,32977.9,1\n")
            handle.write("2026-11-07,437.00,439.80,430.00\n")
        with self.assertRaises(FileImportError) as ctx:
            detect_and_read(path, False)
        self.assertIn("line 2 has 4 fields; expected 6 or 7",
                      str(ctx.exception))

    @unittest.skipUnless(os.path.exists(support.NIFTY_1MIN), "sample absent")
    def test_t_imp_04_missing_volume_accepted(self):
        raw = support.read_raw(support.NIFTY_1MIN).frame
        day = raw[raw["ts"].dt.date == date(2025, 1, 9)]
        first = day[day["ts"].dt.time.astype(str) == "09:15:00"]
        self.assertEqual(len(first), 1)
        self.assertTrue(pd.isna(first["volume"].iloc[0]))
        standardised = std.standardise_intraday(day.reset_index(drop=True))
        records, quarantine, issues = validation.validate_intraday(
            standardised, "NIFTY")
        self.assertEqual(len(records), len(day))
        self.assertEqual(len(quarantine), 0)
        volume_issues = [i for i in issues if "volume" in i.description.lower()
                         and i.check_code != "V-VOL-03"]
        self.assertEqual(volume_issues, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
