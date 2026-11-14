"""L2 tests: session and timestamp validation (T-SES-01 to 11). Document 06
v1.5, section 5.5.

T-SES-04b and T-SES-05b verify the confirmed classification itself; the
REVALIDATE run that applies a confirmation to stored data arrives with M1b.
"""

# --- Imports -----------------------------------------------------------------
import unittest
from datetime import date, datetime, time, timedelta

import pandas as pd

import support
from qmap_database import session_rules as sr
from qmap_database import standardise as std
from qmap_database import validation


# --- Helpers ------------------------------------------------------------------
def _day_slice(path, day):
    raw = support.read_raw(path).frame
    frame = raw[raw["ts"].dt.date == day].reset_index(drop=True)
    return frame.copy()


def _standardise_day(path, day, **kwargs):
    return std.standardise_intraday(_day_slice(path, day), **kwargs)


def _profiles_for(standardised, instrument_id):
    records, quarantine, _ = validation.validate_intraday(standardised,
                                                          instrument_id)
    profiles, issues = validation.build_day_profiles(
        records, quarantine, standardised.day_classes, instrument_id)
    return records, profiles, issues


class TestSessionClassification(unittest.TestCase):

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_01_regular_day(self):
        standardised = _standardise_day(support.NIFTY_1MIN, date(2025, 7, 31))
        classification = standardised.day_classes[date(2025, 7, 31)]
        self.assertEqual(classification.observed_shape, sr.SHAPE_REGULAR)
        self.assertEqual(classification.session_status, sr.STATUS_CANDIDATE)
        self.assertEqual(classification.session_type, sr.TYPE_REGULAR)
        records = standardised.records
        self.assertEqual(len(records), 375)
        self.assertTrue((records["record_type"] == std.RECORD_CANDLE).all())
        self.assertEqual(records["ts"].min().time(), time(9, 15))
        self.assertEqual(records["ts"].max().time(), time(15, 29))

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_02_cas_day_master_style(self):
        standardised = _standardise_day(support.NIFTY_1MIN, date(2026, 8, 17))
        classification = standardised.day_classes[date(2026, 8, 17)]
        self.assertEqual(classification.observed_shape, sr.SHAPE_CAS)
        self.assertEqual(classification.session_status, sr.STATUS_CANDIDATE)
        self.assertEqual(classification.session_type, sr.TYPE_CAS)
        records = standardised.records
        candles = records[records["record_type"] == std.RECORD_CANDLE]
        self.assertEqual(len(candles), 360)
        self.assertEqual(candles["ts"].max().time(), time(15, 14))
        closing = records[records["record_type"] == std.RECORD_CLOSING_AUCTION]
        self.assertEqual(len(closing), 1)
        self.assertEqual(closing["ts"].iloc[0], datetime(2026, 8, 17, 15, 30))
        self.assertEqual(closing["source_ts"].iloc[0],
                         datetime(2026, 8, 17, 15, 30))
        self.assertAlmostEqual(closing["close"].iloc[0], 24287.65)
        self.assertTrue(records["quality_flags"].map(
            lambda flags: std.FLAG_CAS_CANDIDATE in flags).all())

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_03_cas_day_raw_vendor_style(self):
        standardised = _standardise_day(support.BANKNIFTY_1MIN,
                                        date(2026, 8, 18))
        records = standardised.records
        phase = records[records["record_type"] == std.RECORD_AUCTION_PHASE]
        self.assertEqual(len(phase), 1)
        self.assertEqual(phase["ts"].iloc[0], datetime(2026, 8, 18, 15, 15))
        self.assertAlmostEqual(phase["open"].iloc[0], 57314.55)
        self.assertAlmostEqual(phase["low"].iloc[0], 57308.15)
        closing = records[records["record_type"] == std.RECORD_CLOSING_AUCTION]
        self.assertEqual(len(closing), 1)
        self.assertEqual(closing["ts"].iloc[0], datetime(2026, 8, 18, 15, 30))
        self.assertEqual(closing["source_ts"].iloc[0],
                         datetime(2026, 8, 18, 15, 29))
        self.assertAlmostEqual(closing["close"].iloc[0], 57262.40)

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_04_short_session_before_confirmation(self):
        standardised = _standardise_day(support.NIFTY_1MIN, date(2025, 10, 21))
        classification = standardised.day_classes[date(2025, 10, 21)]
        self.assertEqual(classification.observed_shape, sr.SHAPE_OTHER)
        self.assertEqual(classification.session_status, sr.STATUS_UNRECOGNISED)
        self.assertIsNone(classification.session_type)
        records, profiles, issues = _profiles_for(standardised, "NIFTY")
        self.assertEqual(len(records), 61)
        self.assertTrue((records["record_type"] == std.RECORD_CANDLE).all())
        self.assertTrue(records["quality_flags"].map(
            lambda flags: std.FLAG_SESSION_UNCONFIRMED in flags).all())
        profile = profiles[0]
        self.assertEqual(profile["expected_basis"], sr.BASIS_PROVISIONAL)
        self.assertEqual(profile["expected_candles"], 375)
        self.assertEqual(profile["missing_ranges"],
                         "09:15-13:44;14:46-15:29")
        self.assertTrue(any(i.check_code == "V-SES-01"
                            and i.severity == "WARNING" for i in issues))

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_04b_short_session_after_owner_confirmation(self):
        confirmation = sr.SessionConfirmation(sr.TYPE_SPECIAL, time(13, 45),
                                              time(14, 45))
        standardised = _standardise_day(
            support.NIFTY_1MIN, date(2025, 10, 21),
            owner_confirmations={date(2025, 10, 21): confirmation})
        classification = standardised.day_classes[date(2025, 10, 21)]
        self.assertEqual(classification.session_status,
                         sr.STATUS_CONFIRMED_BY_OWNER)
        self.assertEqual(classification.session_type, sr.TYPE_SPECIAL)
        records, profiles, _ = _profiles_for(standardised, "NIFTY")
        candles = records[records["record_type"] == std.RECORD_CANDLE]
        self.assertEqual(len(candles), 60)
        self.assertEqual(candles["ts"].min().time(), time(13, 45))
        self.assertEqual(candles["ts"].max().time(), time(14, 44))
        closing = records[records["record_type"] == std.RECORD_CLOSING_AUCTION]
        self.assertEqual(closing["ts"].iloc[0], datetime(2025, 10, 21, 14, 45))
        self.assertEqual(closing["source_ts"].iloc[0],
                         datetime(2025, 10, 21, 14, 45))
        self.assertIn(std.FLAG_SESSION_CLOSE_UNVERIFIED,
                      closing["quality_flags"].iloc[0])
        profile = profiles[0]
        self.assertEqual(profile["expected_candles"], 60)
        self.assertEqual(profile["missing_candles"], 0)

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_05_cas_like_short_session_before_confirmation(self):
        standardised = _standardise_day(support.BANKNIFTY_1MIN,
                                        date(2026, 11, 8))
        classification = standardised.day_classes[date(2026, 11, 8)]
        self.assertEqual(classification.session_status, sr.STATUS_UNRECOGNISED)
        records = standardised.records
        self.assertEqual(len(records), 57)
        self.assertTrue((records["record_type"] == std.RECORD_CANDLE).all())
        self.assertTrue(records["quality_flags"].map(
            lambda flags: std.FLAG_SESSION_UNCONFIRMED in flags).all())

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_05b_cas_like_short_session_after_confirmation(self):
        confirmation = sr.SessionConfirmation(sr.TYPE_SPECIAL_CAS,
                                              time(14, 20), None)
        standardised = _standardise_day(
            support.BANKNIFTY_1MIN, date(2026, 11, 8),
            owner_confirmations={date(2026, 11, 8): confirmation})
        classification = standardised.day_classes[date(2026, 11, 8)]
        self.assertEqual(classification.session_status,
                         sr.STATUS_CONFIRMED_BY_OWNER)
        self.assertEqual(classification.session_type, sr.TYPE_SPECIAL_CAS)
        records = standardised.records
        candles = records[records["record_type"] == std.RECORD_CANDLE]
        self.assertEqual(len(candles), 55)
        self.assertEqual(candles["ts"].min().time(), time(14, 20))
        self.assertEqual(candles["ts"].max().time(), time(15, 14))
        phase = records[records["record_type"] == std.RECORD_AUCTION_PHASE]
        self.assertEqual(phase["ts"].iloc[0].time(), time(15, 15))
        closing = records[records["record_type"] == std.RECORD_CLOSING_AUCTION]
        self.assertEqual(closing["ts"].iloc[0].time(), time(15, 29))
        self.assertEqual(closing["source_ts"].iloc[0].time(), time(15, 29))
        self.assertIn(std.FLAG_SESSION_CLOSE_UNVERIFIED,
                      closing["quality_flags"].iloc[0])

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_06_classification_counts_after_first_import(self):
        catalogue, _ = support.shared_catalogue()
        try:
            counts = dict(
                ((row[0], row[1], row[2]), row[3]) for row in
                catalogue.con.execute(
                    "SELECT instrument_id, session_status, session_type, "
                    "count(*) FROM day_profile GROUP BY ALL").fetchall())
            unrecognised = [row[0:2] for row in catalogue.con.execute(
                "SELECT instrument_id, trade_date FROM day_profile WHERE "
                "session_status = 'UNRECOGNISED_SESSION_SHAPE' "
                "ORDER BY instrument_id, trade_date").fetchall()]
            special = catalogue.con.execute(
                "SELECT count(*) FROM day_profile WHERE session_type IN "
                "('SPECIAL', 'SPECIAL_CAS')").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(counts[("NIFTY", "CANDIDATE", "REGULAR")], 383)
        self.assertEqual(counts[("NIFTY", "CANDIDATE", "CAS")], 67)
        self.assertEqual(counts[("BANKNIFTY", "CANDIDATE", "CAS")], 59)
        self.assertEqual(unrecognised, [
            ("BANKNIFTY", date(2026, 11, 8)),
            ("NIFTY", date(2025, 2, 1)),
            ("NIFTY", date(2025, 10, 21)),
            ("NIFTY", date(2026, 2, 1)),
        ])
        self.assertEqual(special, 0)   # never SPECIAL without confirmation

    def test_t_ses_07_record_outside_confirmed_session(self):
        rows = []
        day = date(2026, 1, 5)   # Monday
        for minute in range(375):
            ts = datetime(2026, 1, 5, 9, 15) + timedelta(minutes=minute)
            rows.append((ts, 100.0, 101.0, 99.0, 100.5, None))
        rows.append((datetime(2026, 1, 5, 15, 31), 100.0, 101.0, 99.0, 100.5,
                     None))
        frame = pd.DataFrame(rows, columns=["ts", "open", "high", "low",
                                            "close", "volume"])
        frame["ts"] = frame["ts"].astype("datetime64[us]")
        frame["volume"] = frame["volume"].astype("Int64")
        frame["source_row"] = range(1, len(frame) + 1)
        entry = sr.CalendarEntry(day, sr.DAY_TRADING, None, None, "",
                                 sr.CAL_SOURCE_OFFICIAL, True)
        standardised = std.standardise_intraday(frame,
                                                calendar_entries={day: entry})
        classification = standardised.day_classes[day]
        self.assertEqual(classification.session_status,
                         sr.STATUS_CONFIRMED_OFFICIAL)
        records, quarantine, _ = validation.validate_intraday(standardised,
                                                              "TEST")
        self.assertEqual(len(records), 375)
        self.assertEqual(len(quarantine), 1)
        self.assertEqual(quarantine["reason_code"].iloc[0], "OUTSIDE_SESSION")

    def test_t_ses_08_non_whole_minute_timestamp(self):
        rows = [(datetime(2026, 1, 5, 9, 15, 0), 100.0, 101.0, 99.0, 100.5,
                 None),
                (datetime(2026, 1, 5, 9, 15, 30), 100.0, 101.0, 99.0, 100.5,
                 None)]
        frame = pd.DataFrame(rows, columns=["ts", "open", "high", "low",
                                            "close", "volume"])
        frame["ts"] = frame["ts"].astype("datetime64[us]")
        frame["volume"] = frame["volume"].astype("Int64")
        frame["source_row"] = [1, 2]
        standardised = std.standardise_intraday(frame)
        self.assertEqual(len(standardised.records), 1)
        self.assertEqual(standardised.quarantine["reason_code"].iloc[0],
                         "BAD_TIMESTAMP")

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_09_record_totals_after_import(self):
        root, _ = support.shared_initial_load()
        nifty = support.canonical_frame(root, "NSE_INDEX_1M", "NIFTY")
        banknifty = support.canonical_frame(root, "NSE_INDEX_1M", "BANKNIFTY")
        self.assertEqual(nifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 168556, "CLOSING_AUCTION": 67})
        self.assertEqual(banknifty.groupby("record_type").size().to_dict(),
                         {"CANDLE": 21295, "AUCTION_PHASE": 42,
                          "CLOSING_AUCTION": 59})
        nifty_flagged = nifty["quality_flags"].fillna("").str.contains(
            std.FLAG_SESSION_UNCONFIRMED).sum()
        banknifty_flagged = banknifty["quality_flags"].fillna("").str.contains(
            std.FLAG_SESSION_UNCONFIRMED).sum()
        self.assertEqual(int(nifty_flagged), 811)      # 61 + 375 + 375
        self.assertEqual(int(banknifty_flagged), 57)
        # 0 quarantined for both intraday instruments.
        catalogue, _ = support.shared_catalogue()
        try:
            quarantined = catalogue.con.execute(
                "SELECT coalesce(sum(rows_quarantined), 0) FROM import_log "
                "WHERE instrument_id IN ('NIFTY', 'BANKNIFTY')").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(int(quarantined), 0)

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_10_truncated_day_is_not_special(self):
        day_frame = _day_slice(support.NIFTY_1MIN, date(2025, 7, 31))
        truncated = day_frame[day_frame["ts"].dt.time
                              <= time(11, 59)].reset_index(drop=True)
        standardised = std.standardise_intraday(truncated)
        classification = standardised.day_classes[date(2025, 7, 31)]
        self.assertEqual(classification.observed_shape, sr.SHAPE_OTHER)
        self.assertEqual(classification.session_status, sr.STATUS_UNRECOGNISED)
        self.assertIsNone(classification.session_type)
        records, profiles, issues = _profiles_for(standardised, "NIFTY")
        self.assertEqual(len(records), 165)
        self.assertTrue((records["record_type"] == std.RECORD_CANDLE).all())
        self.assertTrue(records["quality_flags"].map(
            lambda flags: std.FLAG_SESSION_UNCONFIRMED in flags).all())
        profile = profiles[0]
        self.assertEqual(profile["expected_candles"], 375)
        self.assertEqual(profile["expected_basis"], sr.BASIS_PROVISIONAL)
        self.assertEqual(profile["missing_ranges"], "12:00-15:29")
        self.assertTrue(any(i.check_code == "V-SES-01"
                            and i.severity == "WARNING" for i in issues))

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_ses_11_weekend_full_session_not_assumed_regular(self):
        day = date(2026, 2, 1)   # Sunday Budget-day session
        standardised = _standardise_day(support.NIFTY_1MIN, day)
        classification = standardised.day_classes[day]
        self.assertEqual(classification.observed_shape, sr.SHAPE_REGULAR)
        self.assertEqual(classification.session_status, sr.STATUS_UNRECOGNISED)
        records = standardised.records
        self.assertEqual(len(records), 375)
        self.assertTrue(records["quality_flags"].map(
            lambda flags: std.FLAG_SESSION_UNCONFIRMED in flags).all())
        # After the Owner confirms a special session 09:15-15:30: flags gone,
        # prices unchanged.
        confirmation = sr.SessionConfirmation(sr.TYPE_SPECIAL, time(9, 15),
                                              time(15, 30))
        confirmed = _standardise_day(
            support.NIFTY_1MIN, day,
            owner_confirmations={day: confirmation})
        self.assertEqual(confirmed.day_classes[day].session_status,
                         sr.STATUS_CONFIRMED_BY_OWNER)
        self.assertEqual(confirmed.day_classes[day].session_type,
                         sr.TYPE_SPECIAL)
        self.assertFalse(confirmed.records["quality_flags"].map(
            lambda flags: std.FLAG_SESSION_UNCONFIRMED in flags).any())
        self.assertTrue((confirmed.records[["open", "high", "low", "close"]]
                         .values == records[["open", "high", "low", "close"]]
                         .values).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
