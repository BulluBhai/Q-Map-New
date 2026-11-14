"""M1a real-data acceptance checks on the inspected sample files: ACC-02,
ACC-04, ACC-06, ACC-08 (document 06 v1.5, section 7) plus the Annex B
fingerprint verification of the committed fixtures.

ACC-03's confirmed state, ACC-05 and the maintenance acceptance checks belong
to M1b; ACC-01 and ACC-07 belong to M2 (aggregation).
"""

# --- Imports -----------------------------------------------------------------
import os
import unittest
from datetime import date

import support
from qmap_database.readers import sha256_of_file

# --- Constants ---------------------------------------------------------------
# ACC-06 / document 13: every inspected +/-15% occurrence, per instrument.
EXPECTED_G03_DATES = {
    "CONCOR": ["2004-05-26", "2004-05-27", "2006-05-15", "2008-01-31",
               "2013-09-06", "2020-03-20", "2020-08-10", "2024-06-04"],
    "INFY": ["2000-08-08", "2001-04-11", "2001-04-18", "2003-04-10",
             "2003-10-24", "2013-01-11", "2013-04-12", "2019-10-22"],
    "NIFTYIT": ["2004-05-28"],
}

# Deliverable 1 section 9.3: the 2025 weekdays with no data in any instrument.
HOLIDAYS_2025 = ["2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
                 "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
                 "2025-08-27", "2025-10-02", "2025-10-22", "2025-11-05",
                 "2025-12-25"]


class TestFixtureFingerprints(unittest.TestCase):

    def test_annex_b_sha256(self):
        """The committed sample files are byte-identical to Annex B."""
        for name, expected in support.ANNEX_B_SHA256.items():
            path = os.path.join(support.FIXTURES, name)
            if not os.path.exists(path):
                self.skipTest("%s absent" % name)
            self.assertEqual(sha256_of_file(path), expected, name)


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestAcceptanceM1a(unittest.TestCase):

    def test_acc_02_import_totals(self):
        """Stored and quarantined totals, before any confirmation."""
        catalogue, root = support.shared_catalogue()
        try:
            stored = dict(catalogue.con.execute(
                "SELECT instrument_id, rows_stored FROM import_log WHERE "
                "action = 'NEW'").fetchall())
            quarantined = dict(catalogue.con.execute(
                "SELECT instrument_id, rows_quarantined FROM import_log "
                "WHERE action = 'NEW'").fetchall())
        finally:
            catalogue.close()
        self.assertEqual(stored, {"NIFTY": 168623, "BANKNIFTY": 21396,
                                  "CONCOR": 6860, "INFY": 7169,
                                  "NIFTYIT": 5760})
        self.assertEqual(quarantined, {"NIFTY": 0, "BANKNIFTY": 0,
                                       "CONCOR": 0, "INFY": 0, "NIFTYIT": 1})
        nifty = support.canonical_frame(root, "NSE_INDEX_1M", "NIFTY")
        banknifty = support.canonical_frame(root, "NSE_INDEX_1M", "BANKNIFTY")
        self.assertEqual(nifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 168556, "CLOSING_AUCTION": 67})
        self.assertEqual(banknifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 21295, "AUCTION_PHASE": 42,
                          "CLOSING_AUCTION": 59})

    def test_acc_04_completeness(self):
        """BANKNIFTY: only 19-Aug-26 13:28-13:29 missing on recognised days;
        NIFTY sample: no missing candles on recognised days."""
        catalogue, _ = support.shared_catalogue()
        try:
            rows = catalogue.con.execute(
                "SELECT instrument_id, trade_date, missing_ranges FROM "
                "day_profile WHERE missing_candles > 0 AND session_status != "
                "'UNRECOGNISED_SESSION_SHAPE' ORDER BY instrument_id, "
                "trade_date").fetchall()
        finally:
            catalogue.close()
        self.assertEqual(rows, [("BANKNIFTY", date(2026, 8, 19),
                                 "13:28-13:29")])

    def test_acc_06_known_issues_represented(self):
        """Every inspected +/-15% occurrence has an OPEN issue blocking
        continuity (G-03), and the NIFTYIT invalid record is quarantined."""
        catalogue, root = support.shared_catalogue()
        try:
            for instrument_id, expected_dates in EXPECTED_G03_DATES.items():
                rows = catalogue.con.execute(
                    "SELECT strftime(ts_from, '%Y-%m-%d'), "
                    "affects_continuity, status FROM data_issue WHERE "
                    "instrument_id = ? AND check_code = 'V-PX-05' "
                    "ORDER BY ts_from", [instrument_id]).fetchall()
                self.assertEqual([r[0] for r in rows], expected_dates,
                                 instrument_id)
                for day, affects_continuity, status in rows:
                    self.assertTrue(affects_continuity, day)
                    self.assertEqual(status, "OPEN", day)
        finally:
            catalogue.close()
        quarantine_folder = os.path.join(root, "quarantine",
                                         "NSE_SECTOR_INDEX_DAILY")
        files = os.listdir(quarantine_folder)
        self.assertEqual(len(files), 1)
        import pandas as pd
        quarantined = pd.read_parquet(os.path.join(quarantine_folder,
                                                   files[0]))
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(str(quarantined["trade_date"].iloc[0]), "2005-07-01")
        self.assertEqual(quarantined["reason_code"].iloc[0], "INVALID_OHLC")
        self.assertAlmostEqual(quarantined["open"].iloc[0], 60.65)

    def test_acc_08_calendar(self):
        """Absent weekdays and weekend sessions match Deliverable 1 sections
        9.3 and 9.4 for the loaded range; every derived entry unverified."""
        catalogue, _ = support.shared_catalogue()
        try:
            count_2023_2026 = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE day_type = "
                "'HOLIDAY' AND trade_date BETWEEN DATE '2023-01-02' AND "
                "DATE '2026-11-06'").fetchone()[0]
            holidays_2025 = [str(row[0]) for row in catalogue.con.execute(
                "SELECT trade_date FROM market_calendar WHERE day_type = "
                "'HOLIDAY' AND year(trade_date) = 2025 ORDER BY trade_date"
            ).fetchall()]
            weekend_specials = [row[0] for row in catalogue.con.execute(
                "SELECT trade_date FROM market_calendar WHERE day_type = "
                "'SPECIAL' AND trade_date >= DATE '2025-01-09'"
                " ORDER BY trade_date").fetchall()]
            unverified = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE verified OR "
                "source != 'DERIVED_FROM_DATA'").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(count_2023_2026, 57)
        self.assertEqual(holidays_2025, HOLIDAYS_2025)
        for expected in (date(2025, 2, 1), date(2026, 2, 1),
                         date(2026, 11, 8)):
            self.assertIn(expected, weekend_specials)
        self.assertEqual(unverified, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
