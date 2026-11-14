"""L4 tests: the QMapData interface (T-DA-01 to 15) and the final expected
results DA-1 to DA-24 (Verification Package v1.2, section 7; rulings S-1 to
S-6 and T-DA-12 applied: every warning list is a minimum set, and expressly
prohibited codes must be absent)."""

# --- Imports -----------------------------------------------------------------
import os
import shutil
import unittest
from datetime import date, datetime

import pandas as pd

import support
from qmap_database.access import DataRequirement, QMapData
from qmap_database.errors import (DatabaseUnavailableError,
                                  InvalidRequestError, UnknownInstrumentError,
                                  UnsupportedTimeframeError)

# --- Constants ---------------------------------------------------------------
META_KEYS = ["instrument_id", "dataset_id", "timeframe", "timezone",
             "ts_meaning", "requested_start", "requested_end",
             "returned_first_ts", "returned_last_ts", "bar_count",
             "incomplete_bar_count", "forming_bar_count",
             "volume_available_from", "volume_available_to", "quality_status",
             "completeness_status", "completeness_basis", "session_summary",
             "notes", "data_version", "warnings", "issues"]


# --- Helpers ------------------------------------------------------------------
def _db():
    root, _ = support.shared_initial_load()
    return QMapData(root)


def _codes(result):
    return {w["code"] for w in result.meta["warnings"]}


class TestDataAccess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not support.fixtures_present():
            raise unittest.SkipTest("sample files absent")
        cls.db = _db()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    # --- T-DA cases -----------------------------------------------------------
    def test_t_da_01_unknown_instrument(self):
        with self.assertRaises(UnknownInstrumentError) as ctx:
            self.db.get_bars("NIFTI", "1D")
        self.assertIn("NIFTY", str(ctx.exception))

    def test_t_da_02_unsupported_timeframe(self):
        with self.assertRaises(UnsupportedTimeframeError) as ctx:
            self.db.get_bars("CONCOR", "15m")
        for code in ("1D", "1W", "1MO"):
            self.assertIn(code, str(ctx.exception))

    def test_t_da_03_bad_range(self):
        with self.assertRaises(InvalidRequestError):
            self.db.get_bars("NIFTY", "1m", "2026-09-30", "2026-09-01")

    def test_t_da_04_holiday_only_range(self):
        result = self.db.get_bars("NIFTY", "1m", "2026-01-26", "2026-01-26")
        self.assertEqual(result.status, "EMPTY")
        self.assertIn("NO_DATA_IN_RANGE", _codes(result))

    def test_t_da_05_volume_unavailable(self):
        result = self.db.get_bars("NIFTY", "1D", "2025-01-09", "2025-01-31",
                                  fields=["close", "volume"])
        self.assertEqual(result.status, "PARTIAL")
        self.assertIn("VOLUME_UNAVAILABLE", _codes(result))
        self.assertTrue(result.bars["volume"].isna().all())

    def test_t_da_06_continuity_warning(self):
        result = self.db.get_bars("NIFTYIT", "1D", "2004-01-01", "2004-12-31")
        self.assertIn("CONTINUITY_ISSUE_IN_RANGE", _codes(result))
        referenced = [issue for issue in result.meta["issues"]
                      if issue["affects_continuity"]
                      and str(issue["ts_from"]).startswith("2004-05-28")]
        self.assertTrue(referenced)

    def test_t_da_07_latest_bars(self):
        result = self.db.get_bars("CONCOR", "1D", latest_n=5,
                                  fields=["close"])
        self.assertEqual(result.bars["close"].round(2).tolist(),
                         [417.85, 419.15, 425.10, 440.85, 439.80])
        self.assertEqual([str(ts.date()) for ts in result.bars["ts"]],
                         ["2026-11-02", "2026-11-03", "2026-11-04",
                          "2026-11-05", "2026-11-06"])

    def test_t_da_08_database_locked(self):
        # A dedicated data root, so the only open handle is the writer's -
        # exactly the state while the Data Manager runs an update.
        from qmap_database.catalogue import Catalogue
        from qmap_database.maintenance import run_initial_load
        from qmap_database.storage import DataRoot
        folder = support.new_temp_folder("tda08_src")
        source = os.path.join(folder, "CONCOR.txt")
        with open(source, "w") as handle:
            for day in ("2026-11-04", "2026-11-05", "2026-11-06"):
                handle.write("%s,100,101,99,100.5,10\n" % day)
        root = support.new_temp_folder("tda08_root")
        run_initial_load(root, [source])
        writer = Catalogue(DataRoot(root).catalogue_path)   # write handle
        try:
            with self.assertRaises(DatabaseUnavailableError):
                QMapData(root)
        finally:
            writer.close()

    def test_t_da_09_meta_always_present(self):
        result = self.db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17")
        for key in META_KEYS:
            self.assertIn(key, result.meta, key)
        self.assertEqual(result.meta["timezone"], "Asia/Kolkata")
        self.assertEqual(result.meta["ts_meaning"],
                         "interval_start_ist_wallclock")
        self.assertTrue(result.meta["data_version"].startswith("run_"))

    def test_t_da_10_availability_report(self):
        report = self.db.check_availability(DataRequirement(
            "NIFTYIT", "1D", "2003-01-01", "2005-12-31", min_bars=200))
        self.assertEqual(report.status, "PARTIAL")
        codes = {reason["code"] for reason in report.reasons}
        self.assertIn("RANGE_TRUNCATED_START", codes)
        self.assertIn("CONTINUITY_ISSUE_IN_RANGE", codes)
        self.assertIn("MISSING_DAY", codes)
        self.assertTrue(any("2005-07-01" in reason["message"]
                            for reason in report.reasons
                            if reason["code"] == "MISSING_DAY"))
        self.assertEqual(str(report.available_start), "2003-08-25 00:00:00")
        self.assertTrue(report.continuity_issues)

    def test_t_da_11_provisional_completeness(self):
        result = self.db.get_bars("NIFTY", "1D", "2026-08-17", "2026-08-21")
        self.assertEqual(result.meta["completeness_basis"],
                         "PROVISIONAL_DERIVED_CALENDAR")
        self.assertIn("COMPLETENESS_PROVISIONAL", result.meta["notes"])

    def test_t_da_12_unrecognised_session_reported(self):
        result = self.db.get_bars("NIFTY", "5m", "2025-10-21", "2025-10-21")
        self.assertEqual(result.status, "PARTIAL")
        self.assertIn("UNRECOGNISED_SESSION_IN_RANGE", _codes(result))
        self.assertTrue(result.bars["quality_flags"].str.contains(
            "SESSION_UNCONFIRMED").all())

    def test_t_da_13_held_revision_reported(self):
        # A dedicated root with a held CONCOR revision (as T-MNT-03).
        from qmap_database.maintenance import run_initial_load, run_update
        folder = support.new_temp_folder("tda13_src")
        source = os.path.join(folder, "CONCOR.txt")
        shutil.copyfile(support.CONCOR_TXT, source)
        root = support.new_temp_folder("tda13_root")
        run_initial_load(root, [source])
        with open(support.CONCOR_TXT, "rb") as handle:
            lines = handle.read().split(b"\r\n")
        changed = []
        for line in lines:
            if not line:
                continue
            fields = line.decode().split(",")
            if fields[0] < "2025-07-04":
                for position in range(1, 5):
                    fields[position] = "%.4f" % (float(fields[position])
                                                 * 0.8)
            changed.append(",".join(fields).encode())
        with open(source, "wb") as handle:
            handle.write(b"\r\n".join(changed + [b""]))
        run_update(root, [folder])
        db = QMapData(root)
        try:
            result = db.get_bars("CONCOR", "1D", latest_n=5,
                                 fields=["close"])
            self.assertEqual(result.bars["close"].round(2).tolist(),
                             [417.85, 419.15, 425.10, 440.85, 439.80])
            self.assertIn("HELD_REVISION_EXISTS", _codes(result))
        finally:
            db.close()

    def test_t_da_14_latest_n_through_a_requirement(self):
        report = self.db.check_availability(DataRequirement(
            "CONCOR", "1D", end="2026-11-06", required_fields=("close",),
            latest_n=5))
        self.assertEqual(report.status, "AVAILABLE")
        self.assertEqual(report.estimated_bars, 5)

    def test_t_da_15_range_truncated_end_only_for_real_staleness(self):
        result = self.db.get_bars("CONCOR", "1D", "2026-10-01", "2026-11-08")
        self.assertNotIn("RANGE_TRUNCATED_END", _codes(result))
        result = self.db.get_bars("CONCOR", "1D", "2026-10-01", "2026-11-10")
        self.assertIn("RANGE_TRUNCATED_END", _codes(result))
        message = [w["message"] for w in result.meta["warnings"]
                   if w["code"] == "RANGE_TRUNCATED_END"][0]
        self.assertIn("06-Nov-26", message)
        self.assertIn("10-Nov-26", message)


class TestDAExpected(unittest.TestCase):
    """DA-1 to DA-24: status exact, every must-contain code present, every
    must-not-contain code absent, key values equal (section 7.2 pass rule)."""

    @classmethod
    def setUpClass(cls):
        if not support.fixtures_present():
            raise unittest.SkipTest("sample files absent")
        cls.db = _db()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def _check_bars(self, case_id, result, rows, status, must, must_not):
        self.assertEqual(len(result.bars), rows, "%s row count" % case_id)
        self.assertEqual(result.status, status, "%s status" % case_id)
        codes = _codes(result)
        for code in must:
            self.assertIn(code, codes, "%s must contain %s" % (case_id, code))
        for code in must_not:
            self.assertNotIn(code, codes,
                             "%s must not contain %s" % (case_id, code))

    def test_da_01(self):
        result = self.db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17")
        self._check_bars("DA-1", result, 73, "OK", [],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE",
                          "FLAGGED_ROWS_INCLUDED", "INCOMPLETE_BARS"])

    def test_da_02(self):
        result = self.db.get_bars("NIFTY", "5m", "2026-08-17", "2026-08-17",
                                  include_auction_records=False)
        self._check_bars("DA-2", result, 72, "OK", [],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE",
                          "FLAGGED_ROWS_INCLUDED", "INCOMPLETE_BARS"])

    def test_da_03(self):
        result = self.db.get_bars("BANKNIFTY", "5m", "2026-08-19",
                                  "2026-08-19")
        self._check_bars("DA-3", result, 74, "PARTIAL",
                         ["INCOMPLETE_BARS", "FLAGGED_ROWS_INCLUDED"],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE"])

    def test_da_04(self):
        result = self.db.get_bars("BANKNIFTY", "15m", "2026-08-19",
                                  "2026-08-19")
        self._check_bars("DA-4", result, 26, "PARTIAL",
                         ["INCOMPLETE_BARS", "FLAGGED_ROWS_INCLUDED"],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE"])

    def test_da_05(self):
        result = self.db.get_bars("CONCOR", "1D", latest_n=5,
                                  fields=["close"])
        self._check_bars("DA-5", result, 5, "OK", [],
                         ["RANGE_TRUNCATED_END", "CONTINUITY_ISSUE_IN_RANGE",
                          "FLAGGED_ROWS_INCLUDED"])
        self.assertEqual(result.bars["close"].round(2).tolist(),
                         [417.85, 419.15, 425.10, 440.85, 439.80])

    def test_da_06(self):
        with self.assertRaises(UnknownInstrumentError) as ctx:
            self.db.get_bars("NIFTI", "5m")
        self.assertIn("NIFTY", str(ctx.exception))

    def test_da_07(self):
        with self.assertRaises(InvalidRequestError) as ctx:
            self.db.list_instruments(dataset_id="NSE_FUT_1M")
        message = str(ctx.exception)
        self.assertIn("NSE_FUT_1M", message)
        for dataset_id in ("NSE_INDEX_1M", "NSE_EQ_DAILY",
                           "NSE_SECTOR_INDEX_DAILY"):
            self.assertIn(dataset_id, message)

    def test_da_08(self):
        result = self.db.get_bars("NIFTY", "5m", "2026-01-26", "2026-01-26")
        self._check_bars("DA-8", result, 0, "EMPTY", ["NO_DATA_IN_RANGE"], [])

    def test_da_09(self):
        result = self.db.get_bars("NIFTY", "5m", "2024-06-03", "2024-06-07")
        self._check_bars("DA-9", result, 0, "EMPTY", ["NO_DATA_IN_RANGE"], [])

    def test_da_10(self):
        result = self.db.get_bars("BANKNIFTY", "1D", "2026-08-01",
                                  "2026-08-31")
        self._check_bars("DA-10", result, 11, "PARTIAL",
                         ["RANGE_TRUNCATED_START", "INCOMPLETE_BARS",
                          "FLAGGED_ROWS_INCLUDED"],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE"])

    def test_da_11(self):
        result = self.db.get_bars("NIFTY", "1D", "2025-01-09", "2025-01-31",
                                  fields=["close", "volume"])
        self._check_bars("DA-11", result, 17, "PARTIAL",
                         ["VOLUME_UNAVAILABLE"],
                         ["VOLUME_PARTIAL", "FLAGGED_ROWS_INCLUDED"])

    def test_da_12(self):
        with self.assertRaises(InvalidRequestError) as ctx:
            self.db.get_bars("CONCOR", "1D", fields=["oi"])
        self.assertIn("oi", str(ctx.exception))

    def test_da_13(self):
        report = self.db.check_availability(DataRequirement(
            "NIFTY", "5m", "2025-01-09", "2025-01-31",
            required_fields=("close", "volume")))
        self.assertEqual(report.status, "UNAVAILABLE")
        self.assertEqual(report.missing_fields, ("volume",))
        codes = {reason["code"] for reason in report.reasons}
        self.assertIn("VOLUME_UNAVAILABLE", codes)
        self.assertNotIn("VOLUME_PARTIAL", codes)
        self.assertNotIn("REQUIRED_FIELD_UNAVAILABLE", codes)
        self.assertEqual(report.estimated_bars, 1275)

    def test_da_14(self):
        with self.assertRaises(UnsupportedTimeframeError):
            self.db.get_bars("CONCOR", "15m")

    def test_da_15(self):
        with self.assertRaises(UnsupportedTimeframeError):
            self.db.get_bars("NIFTY", "7m")

    def test_da_16(self):
        with self.assertRaises(InvalidRequestError):
            self.db.get_bars("NIFTY", "5m", "2026-09-30", "2026-09-01")

    def test_da_17(self):
        result = self.db.get_bars("NIFTY", "5m", "2025-10-21", "2025-10-21")
        self._check_bars("DA-17", result, 13, "PARTIAL",
                         ["UNRECOGNISED_SESSION_IN_RANGE", "INCOMPLETE_BARS",
                          "FLAGGED_ROWS_INCLUDED", "VOLUME_UNAVAILABLE"],
                         ["VOLUME_PARTIAL"])

    def test_da_18(self):
        result = self.db.get_bars("BANKNIFTY", "5m", "2026-11-08",
                                  "2026-11-08")
        self._check_bars("DA-18", result, 13, "PARTIAL",
                         ["UNRECOGNISED_SESSION_IN_RANGE", "INCOMPLETE_BARS",
                          "FLAGGED_ROWS_INCLUDED"],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE"])
        # S-1: no record is an auction, every bar incomplete, and the
        # candidate-sessions note must be absent for this range.
        self.assertTrue((result.bars["record_type"] == "CANDLE").all())
        self.assertFalse(result.bars["is_complete"].any())
        self.assertNotIn("CANDIDATE_SESSIONS_IN_RANGE", result.meta["notes"])

    def test_da_19(self):
        result = self.db.get_bars("BANKNIFTY", "15m", "2026-11-08",
                                  "2026-11-08")
        self._check_bars("DA-19", result, 5, "PARTIAL",
                         ["UNRECOGNISED_SESSION_IN_RANGE", "INCOMPLETE_BARS",
                          "FLAGGED_ROWS_INCLUDED"],
                         ["VOLUME_PARTIAL", "VOLUME_UNAVAILABLE"])
        self.assertTrue((result.bars["record_type"] == "CANDLE").all())
        self.assertFalse(result.bars["is_complete"].any())
        self.assertNotIn("CANDIDATE_SESSIONS_IN_RANGE", result.meta["notes"])

    def test_da_20(self):
        result = self.db.get_bars("NIFTY", "5m", "2026-08-14", "2026-08-17")
        self._check_bars("DA-20", result, 146, "PARTIAL",
                         ["VOLUME_PARTIAL"],
                         ["VOLUME_UNAVAILABLE", "INCOMPLETE_BARS",
                          "FLAGGED_ROWS_INCLUDED"])

    def test_da_21(self):
        report = self.db.check_availability(DataRequirement(
            "NIFTY", "1D", "2026-08-10", "2026-08-21",
            required_fields=("close", "volume")))
        self.assertEqual(report.status, "PARTIAL")
        self.assertEqual(report.missing_fields, ("volume",))
        codes = {reason["code"] for reason in report.reasons}
        self.assertIn("VOLUME_PARTIAL", codes)
        self.assertNotIn("VOLUME_UNAVAILABLE", codes)
        message = [reason["message"] for reason in report.reasons
                   if reason["code"] == "VOLUME_PARTIAL"][0]
        self.assertIn("2026-08-10", message)
        self.assertIn("2026-08-14", message)
        self.assertEqual(report.estimated_bars, 10)

    def test_da_22(self):
        report = self.db.check_availability(DataRequirement(
            "NIFTY", "1D", "2026-08-17", "2026-08-21",
            required_fields=("close", "volume")))
        self.assertEqual(report.status, "AVAILABLE")
        self.assertEqual(report.missing_fields, ())
        codes = {reason["code"] for reason in report.reasons}
        self.assertNotIn("VOLUME_PARTIAL", codes)
        self.assertNotIn("VOLUME_UNAVAILABLE", codes)
        self.assertEqual(report.estimated_bars, 5)

    def test_da_23(self):
        report = self.db.check_availability(DataRequirement(
            "NIFTY", "1D", "2025-01-09", "2025-01-31"))
        self.assertEqual(report.status, "AVAILABLE")
        self.assertEqual(report.missing_fields, ())
        codes = {reason["code"] for reason in report.reasons}
        self.assertNotIn("REQUIRED_FIELD_UNAVAILABLE", codes)
        self.assertNotIn("VOLUME_UNAVAILABLE", codes)
        self.assertNotIn("VOLUME_PARTIAL", codes)

    def test_da_24(self):
        frame = self.db.list_instruments(dataset_id="NSE_INDEX_1M")
        self.assertEqual(frame["instrument_id"].tolist(),
                         ["BANKNIFTY", "NIFTY"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
