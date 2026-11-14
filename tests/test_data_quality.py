"""L2 tests: data quality, duplicates and missing data (T-DQ-01 to 08,
T-DUP-01 to 02, T-MISS-01 to 03). Document 06 v1.5, sections 5.2 to 5.4."""

# --- Imports -----------------------------------------------------------------
import os
import unittest
from datetime import date, datetime, timedelta

import pandas as pd

import support
from qmap_database import standardise as std
from qmap_database import validation
from qmap_database.catalogue import ISSUE_VERIFIED_OK


# --- Helpers ------------------------------------------------------------------
def _intraday_frame(rows):
    frame = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close",
                                        "volume"])
    frame["ts"] = frame["ts"].astype("datetime64[us]")
    frame["volume"] = frame["volume"].astype("Int64")
    frame["source_row"] = range(1, len(frame) + 1)
    return frame


def _daily_frame(rows):
    frame = pd.DataFrame(rows, columns=["trade_date", "open", "high", "low",
                                        "close", "volume"])
    frame["volume"] = frame["volume"].astype("Int64")
    frame["source_row"] = range(1, len(frame) + 1)
    return frame


def _validated_daily(rows, instrument_id="TEST"):
    standardised = std.standardise_daily(_daily_frame(rows))
    return validation.validate_daily(standardised, instrument_id)


class TestDataQuality(unittest.TestCase):

    def test_t_dq_01_invalid_ohlc_quarantined(self):
        # Nifty IT 01-Jul-05: open 60.65 below the low (invalid record).
        records, quarantine, _ = _validated_daily([
            (date(2005, 6, 30), 3070.0, 3080.0, 3060.0, 3072.10, 100),
            (date(2005, 7, 1), 60.65, 3062.75, 3041.80, 3051.35, 100),
        ], "NIFTYIT")
        self.assertEqual(len(records), 1)
        self.assertEqual(len(quarantine), 1)
        self.assertEqual(quarantine["reason_code"].iloc[0], "INVALID_OHLC")

    def _off_tick_day(self):
        base = datetime(2024, 3, 2, 10, 0)
        rows = [(base + timedelta(minutes=i), 22394.40, 22410.35, 22389.95,
                 22394.40, None) for i in range(5)]
        rows.append((base + timedelta(minutes=5), 22394.80549, 22410.35,
                     22389.95, 22394.80549, None))
        return _intraday_frame(rows)

    def test_t_dq_02a_off_tick_quarantined_under_verified_rule(self):
        standardised = std.standardise_intraday(self._off_tick_day())
        rule = [{"value": "0.05", "effective_from": None, "effective_to": None,
                 "verified": True}]
        records, quarantine, _ = validation.validate_intraday(
            standardised, "NIFTY", tick_rules=rule)
        self.assertEqual(len(quarantine), 1)
        self.assertEqual(quarantine["reason_code"].iloc[0],
                         "OFF_TICK_SYNTHETIC")
        self.assertNotIn(22394.80549, records["close"].tolist())

    def test_t_dq_02b_off_tick_flagged_under_unverified_rule(self):
        standardised = std.standardise_intraday(self._off_tick_day())
        rule = [{"value": "0.05", "effective_from": None, "effective_to": None,
                 "verified": False}]
        records, quarantine, issues = validation.validate_intraday(
            standardised, "NIFTY", tick_rules=rule)
        self.assertEqual(len(quarantine), 0)
        flagged = records[records["quality_flags"].map(
            lambda flags: std.FLAG_OFF_TICK in flags)]
        self.assertEqual(len(flagged), 1)
        self.assertTrue(any(i.check_code == "V-PX-03" for i in issues))

    def test_t_dq_02c_rule_verification_needs_g04_record(self):
        from qmap_database.catalogue import Catalogue
        folder = support.new_temp_folder("tdq02c")
        catalogue = Catalogue(os.path.join(folder, "cat.duckdb"))
        try:
            catalogue.ensure_schema()
            catalogue.add_instrument_rule("NIFTY", "TICK_SIZE", "0.05", None,
                                          None, False, "OWNER_CONFIRMED",
                                          None, None)
            with self.assertRaises(ValueError) as ctx:
                catalogue.set_rule_verified("NIFTY", "TICK_SIZE", "0.05",
                                            evidence="",
                                            effective_from=date(2025, 1, 1),
                                            confirmed_at="Owner 13-Nov-26")
            self.assertIn("evidence", str(ctx.exception))
            with self.assertRaises(ValueError) as ctx:
                catalogue.set_rule_verified("NIFTY", "TICK_SIZE", "0.05",
                                            evidence="NSE circular",
                                            effective_from=None,
                                            confirmed_at="Owner 13-Nov-26")
            self.assertIn("effective_from", str(ctx.exception))
            rules = catalogue.get_tick_rules("NIFTY")
            self.assertFalse(rules[0]["verified"])
        finally:
            catalogue.close()

    def test_t_dq_03_constant_step_run_flagged(self):
        base = datetime(2024, 3, 2, 10, 0)
        rows = [(base + timedelta(minutes=i), 100.0 + 0.40 * i, 110.0, 95.0,
                 100.0 + 0.40 * i, None) for i in range(5)]
        standardised = std.standardise_intraday(_intraday_frame(rows))
        records, _, issues = validation.validate_intraday(standardised, "TEST")
        flagged = records["quality_flags"].map(
            lambda flags: std.FLAG_SUSPECT_FILL in flags)
        self.assertEqual(int(flagged.sum()), 5)
        fill_issues = [i for i in issues if i.check_code == "V-PX-04"]
        self.assertEqual(len(fill_issues), 1)

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_dq_04_large_gap_flagged_not_changed(self):
        root, _ = support.shared_initial_load()
        concor = support.canonical_frame(root, "NSE_EQ_DAILY", "CONCOR")
        row = concor[concor["trade_date"].astype(str) == "2013-09-06"]
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row["open"].iloc[0], 171.78)
        self.assertIn(std.FLAG_LARGE_GAP, row["quality_flags"].iloc[0] or "")
        catalogue, _ = support.shared_catalogue()
        try:
            issues = catalogue.con.execute(
                "SELECT affects_continuity, status FROM data_issue WHERE "
                "instrument_id = 'CONCOR' AND check_code = 'V-PX-05' AND "
                "ts_from = TIMESTAMP '2013-09-06 00:00:00'").fetchall()
            self.assertEqual(issues, [(True, "OPEN")])
        finally:
            catalogue.close()

    def test_t_dq_05_negative_volume_quarantined(self):
        records, quarantine, _ = _validated_daily([
            (date(2020, 1, 1), 100.0, 101.0, 99.0, 100.5, 500),
            (date(2020, 1, 2), 100.0, 101.0, 99.0, 100.5, -100),
        ])
        self.assertEqual(len(records), 1)
        self.assertEqual(quarantine["reason_code"].iloc[0], "BAD_VOLUME")

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_dq_06_no_automatic_price_adjustment(self):
        root, _ = support.shared_initial_load()
        stored = support.canonical_frame(root, "NSE_EQ_DAILY", "CONCOR")
        source = support.read_raw(support.CONCOR_TXT).frame
        self.assertEqual(len(stored), 6860)
        merged = stored.sort_values("trade_date").reset_index(drop=True)
        source = source.sort_values("trade_date").reset_index(drop=True)
        for column in ("open", "high", "low", "close"):
            differences = (merged[column] - source[column]).abs().max()
            self.assertEqual(differences, 0.0, column)
        self.assertTrue((merged["volume"] == source["volume"]).all())

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_dq_07_every_15pct_move_blocks(self):
        catalogue, _ = support.shared_catalogue()
        try:
            rows = catalogue.con.execute(
                "SELECT strftime(ts_from, '%Y-%m-%d'), affects_continuity, "
                "status, evidence FROM data_issue WHERE instrument_id = "
                "'CONCOR' AND check_code = 'V-PX-05' AND ts_from IN "
                "(TIMESTAMP '2006-05-15 00:00:00', "
                "TIMESTAMP '2024-06-04 00:00:00') ORDER BY ts_from"
            ).fetchall()
        finally:
            catalogue.close()
        self.assertEqual(len(rows), 2)
        for day, affects, status, evidence in rows:
            self.assertTrue(affects)
            self.assertEqual(status, "OPEN")
            self.assertIn("open_change=", evidence)
            self.assertIn("close_change=", evidence)
        # 15-May-06 is an open-only move (+16.0% open, -3.6% close): it blocks
        # like any other (G-03; the P-01 proposal is not adopted).
        self.assertIn("16.0", rows[0][3])

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_dq_08_verified_ok_unblocks_only_that_occurrence(self):
        # A separate load so the shared catalogue stays unchanged.
        from qmap_database.catalogue import Catalogue
        from qmap_database.maintenance import run_initial_load
        from qmap_database.storage import DataRoot
        root = support.new_temp_folder("tdq08_root")
        run_initial_load(root, [support.CONCOR_TXT])
        catalogue = Catalogue(DataRoot(root).catalogue_path)
        try:
            issue_id = catalogue.con.execute(
                "SELECT issue_id FROM data_issue WHERE instrument_id = "
                "'CONCOR' AND check_code = 'V-PX-05' AND ts_from = "
                "TIMESTAMP '2024-06-04 00:00:00'").fetchone()[0]
            catalogue.mark_issue_verified_ok(issue_id,
                                             "Owner verified 13-Nov-26")
            row = catalogue.con.execute(
                "SELECT status, affects_continuity FROM data_issue WHERE "
                "issue_id = ?", [issue_id]).fetchone()
            self.assertEqual(row, (ISSUE_VERIFIED_OK, False))
            others = catalogue.con.execute(
                "SELECT count(*) FROM data_issue WHERE instrument_id = "
                "'CONCOR' AND check_code = 'V-PX-05' AND status = 'OPEN' AND "
                "affects_continuity").fetchone()[0]
            self.assertEqual(others, 7)   # the other CONCOR occurrences
        finally:
            catalogue.close()


class TestDuplicates(unittest.TestCase):

    def _nifty_0916_rows(self, second_close):
        return [
            (datetime(2025, 1, 9, 9, 15), 23679.70, 23689.50, 23661.65,
             23662.45, None),
            (datetime(2025, 1, 9, 9, 16), 23642.75, 23642.75, 23631.20,
             23638.70, None),
            (datetime(2025, 1, 9, 9, 16), 23642.75, 23642.75, 23631.20,
             second_close, None),
            (datetime(2025, 1, 9, 9, 17), 23640.00, 23661.15, 23640.00,
             23652.80, None),
        ]

    def test_t_dup_01_exact_duplicate_collapsed(self):
        frame = _intraday_frame(self._nifty_0916_rows(23638.70))
        standardised = std.standardise_intraday(frame)
        at_0916 = standardised.records[
            standardised.records["ts"] == datetime(2025, 1, 9, 9, 16)]
        self.assertEqual(len(at_0916), 1)
        self.assertEqual(standardised.duplicates_collapsed, 1)
        self.assertTrue(any("duplicate" in note for note in
                            standardised.info_notes))

    def test_t_dup_02_conflicting_duplicate_quarantined(self):
        frame = _intraday_frame(self._nifty_0916_rows(23640.00))
        standardised = std.standardise_intraday(frame)
        at_0916 = standardised.records[
            standardised.records["ts"] == datetime(2025, 1, 9, 9, 16)]
        self.assertEqual(len(at_0916), 0)       # the minute is missing
        self.assertEqual(len(standardised.quarantine), 2)  # both copies
        self.assertTrue((standardised.quarantine["reason_code"]
                         == "DUPLICATE_CONFLICT").all())


class TestMissingData(unittest.TestCase):

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_miss_01_missing_candles_detected(self):
        catalogue, _ = support.shared_catalogue()
        try:
            profile = catalogue.con.execute(
                "SELECT expected_candles, present_candles, missing_ranges "
                "FROM day_profile WHERE instrument_id = 'BANKNIFTY' AND "
                "trade_date = DATE '2026-08-19'").fetchone()
            self.assertEqual(profile, (360, 358, "13:28-13:29"))
            # The only missing minutes on *recognised* days are these two.
            others = catalogue.con.execute(
                "SELECT count(*) FROM day_profile WHERE missing_candles > 0 "
                "AND session_status != 'UNRECOGNISED_SESSION_SHAPE' AND NOT "
                "(instrument_id = 'BANKNIFTY' AND trade_date = "
                "DATE '2026-08-19')").fetchone()[0]
            self.assertEqual(others, 0)
        finally:
            catalogue.close()

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_miss_02_holidays_not_missing(self):
        catalogue, _ = support.shared_catalogue()
        try:
            missing = catalogue.con.execute(
                "SELECT count(*) FROM data_issue WHERE check_code = "
                "'V-CAL-02' AND description LIKE '%2026-01-26%'").fetchone()[0]
            self.assertEqual(missing, 0)
            calendar_row = catalogue.con.execute(
                "SELECT day_type, source, verified FROM market_calendar "
                "WHERE trade_date = DATE '2026-01-26'").fetchone()
            self.assertEqual(calendar_row,
                             ("HOLIDAY", "DERIVED_FROM_DATA", False))
        finally:
            catalogue.close()

    def test_t_miss_03_missing_day_for_one_instrument(self):
        # Two daily instruments; INFY lacks one date CONCOR has.
        from qmap_database.catalogue import Catalogue
        from qmap_database.maintenance import run_initial_load
        from qmap_database.storage import DataRoot
        folder = support.new_temp_folder("tmiss03_src")
        concor_path = os.path.join(folder, "CONCOR.txt")
        infy_path = os.path.join(folder, "INFY.txt")
        days = ["2026-11-02", "2026-11-03", "2026-11-04"]
        with open(concor_path, "w") as handle:
            for day in days:
                handle.write("%s,100,101,99,100.5,10\n" % day)
        with open(infy_path, "w") as handle:
            for day in (days[0], days[2]):
                handle.write("%s,200,201,199,200.5,10\n" % day)
        root = support.new_temp_folder("tmiss03_root")
        run_initial_load(root, [concor_path, infy_path])
        catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
        try:
            issues = catalogue.con.execute(
                "SELECT instrument_id, description FROM data_issue WHERE "
                "check_code = 'V-CAL-02'").fetchall()
        finally:
            catalogue.close()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0][0], "INFY")
        self.assertIn("2026-11-03", issues[0][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
