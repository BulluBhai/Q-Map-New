"""L5 tests: timeframe aggregation (T-AGG-01 to 13, T-DUP-03) and the
real-data acceptance checks ACC-01 (zero differences against the Owner's
derived files at 3m/5m/15m/1D, and 1MO over Feb-25 to Oct-26 per Q-1/X-7) and
ACC-07 (the auction sets the daily High or Low on 16 of 67 CAS days).
Documents 06 v1.5 sections 5.8 and 7, and 03 v1.2 Part B."""

# --- Imports -----------------------------------------------------------------
import os
import unittest
from datetime import date, datetime, time, timedelta

import pandas as pd

import support
from qmap_database import aggregation as agg
from qmap_database import session_rules as sr
from qmap_database import standardise as std
from qmap_database.access import QMapData
from qmap_database.errors import DataIntegrityError

# --- Constants ---------------------------------------------------------------
DERIVED_FILES = {"3m": support.NIFTY_3MIN, "5m": support.NIFTY_5MIN,
                 "15m": support.NIFTY_15MIN, "1D": support.NIFTY_DAILY,
                 "1MO": support.NIFTY_MONTHLY}
# Reference counts from the Verification Package v1.2 section 5.2.
ACC01_EXPECTED_MATCHED = {"3m": 55648, "5m": 33414, "15m": 11180, "1D": 448,
                          "1MO": 21}


# --- Helpers ------------------------------------------------------------------
def _bar(bars, ts_text):
    matching = bars[bars["ts"] == pd.Timestamp(ts_text)]
    assert len(matching) == 1, "no single bar at %s" % ts_text
    return matching.iloc[0]


def _window(day, minutes_expected=375, status=sr.STATUS_CANDIDATE,
            session_type=sr.TYPE_REGULAR, window_open=time(9, 15)):
    return agg.DayWindow(day, window_open, minutes_expected, status,
                         session_type,
                         is_cas=session_type in (sr.TYPE_CAS,
                                                 sr.TYPE_SPECIAL_CAS))


class TestAggregation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not support.fixtures_present():
            raise unittest.SkipTest("sample files absent")
        root, _ = support.shared_initial_load()
        cls.db = QMapData(root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def test_t_agg_01_one_minute_to_five(self):
        bars = self.db.get_bars("NIFTY", "5m", "2025-01-09",
                                "2025-01-09").bars
        bar = _bar(bars, "2025-01-09 09:15:00")
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [23674.75, 23689.50, 23607.75, 23618.20])
        self.assertTrue(pd.isna(bar["volume"]))
        self.assertEqual((bar["expected_units"], bar["present_units"]),
                         (5, 5))
        self.assertTrue(bar["is_complete"])

    def test_t_agg_01b_five_minute_with_volume(self):
        bars = self.db.get_bars("NIFTY", "5m", "2026-08-17",
                                "2026-08-17").bars
        bar = _bar(bars, "2026-08-17 09:15:00")
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [24354.65, 24357.60, 24282.80, 24306.65])
        self.assertEqual(bar["volume"], 9824234)

    def test_t_agg_02_missing_minutes(self):
        bars = self.db.get_bars("BANKNIFTY", "5m", "2026-08-19",
                                "2026-08-19").bars
        bar = _bar(bars, "2026-08-19 13:25:00")
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [57061.60, 57076.10, 57052.95, 57068.40])
        self.assertEqual(bar["volume"], 291326)
        self.assertEqual((bar["expected_units"], bar["present_units"]),
                         (5, 3))
        self.assertFalse(bar["is_complete"])
        self.assertFalse(bar["is_forming"])
        # No filled candle: the bar count for the day stays 72 + 2 auctions.
        self.assertEqual(len(bars), 74)

    def test_t_agg_03_closing_auction_fifteen_minute(self):
        result = self.db.get_bars("NIFTY", "15m", "2026-08-17", "2026-08-17")
        bars = result.bars
        bar = _bar(bars, "2026-08-17 15:00:00")
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [24337.70, 24360.10, 24330.70, 24341.90])
        self.assertEqual(bar["volume"], 23634943)
        self.assertTrue(bar["is_complete"])
        self.assertEqual(len(bars[bars["ts"] == pd.Timestamp(
            "2026-08-17 15:15:00")]), 0)   # no 15:15 interval on a CAS day
        closing = bars[bars["record_type"] == "CLOSING_AUCTION"]
        self.assertEqual(len(closing), 1)
        self.assertEqual(closing["close"].iloc[0], 24287.65)

    def test_t_agg_04_auction_excluded_on_request(self):
        bars = self.db.get_bars("NIFTY", "15m", "2026-08-17", "2026-08-17",
                                include_auction_records=False).bars
        self.assertEqual(str(bars["ts"].iloc[-1]), "2026-08-17 15:00:00")
        self.assertTrue((bars["record_type"] == "CANDLE").all())

    def test_t_agg_05_forming_bar(self):
        # Fixture: a NIFTY-like latest stored day ending at 11:02.
        from qmap_database.access import QMapData as Access
        from qmap_database.maintenance import run_initial_load
        folder = support.new_temp_folder("tagg05_src")
        rows = []
        for day_offset in range(3):
            day = datetime(2026, 11, 2 + day_offset, 9, 15)
            minutes = 375 if day_offset < 2 else 108   # last day ends 11:02
            for minute in range(minutes):
                ts = day + timedelta(minutes=minute)
                rows.append((ts, 100.0 + minute * 0.05, 101.0 + minute * 0.05,
                             99.0, 100.5 + minute * 0.05, 10))
        frame = pd.DataFrame(rows, columns=["datetime", "open", "high", "low",
                                            "close", "Volume"])
        path = os.path.join(folder, "Nifty_1min_fixture.parquet")
        frame.to_parquet(path)
        root = support.new_temp_folder("tagg05_root")
        run_initial_load(root, [path])
        db = Access(root)
        try:
            result = db.get_bars("NIFTY", "15m", "2026-11-04", "2026-11-04")
            bar = _bar(result.bars, "2026-11-04 11:00:00")
            self.assertTrue(bar["is_forming"])
            self.assertFalse(bar["is_complete"])
            self.assertEqual(bar["present_units"], 3)
            self.assertIn("FORMING_BAR",
                          {w["code"] for w in result.meta["warnings"]})
        finally:
            db.close()

    def test_t_agg_06_truncated_hourly_bar(self):
        bars = self.db.get_bars("NIFTY", "60m", "2025-07-31",
                                "2025-07-31").bars
        bar = _bar(bars, "2025-07-31 15:15:00")
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [24762.30, 24766.60, 24747.55, 24765.60])
        self.assertEqual((bar["expected_units"], bar["present_units"]),
                         (15, 15))
        self.assertTrue(bar["is_complete"])
        self.assertTrue(bar["session_truncated"])

    def test_t_agg_07_daily_from_one_minute_cas_day(self):
        bars = self.db.get_bars("NIFTY", "1D", "2026-08-17",
                                "2026-08-17").bars
        bar = bars.iloc[0]
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [24354.65, 24360.10, 24226.95, 24287.65])
        self.assertEqual(bar["volume"], 218297189)
        # The auction volume is null, so the daily volume is complete.
        self.assertTrue(bar["volume_complete"])
        self.assertTrue(bar["is_complete"])

    def test_t_agg_08_auction_sets_daily_high(self):
        bars = self.db.get_bars("NIFTY", "1D", "2026-08-03",
                                "2026-08-03").bars
        self.assertEqual(bars.iloc[0]["high"], 24774.30)

    def test_t_agg_09_daily_with_auction_phase_record(self):
        bars = self.db.get_bars("BANKNIFTY", "1D", "2026-08-18",
                                "2026-08-18").bars
        bar = bars.iloc[0]
        self.assertEqual([bar["open"], bar["high"], bar["low"], bar["close"]],
                         [57331.10, 57584.70, 57217.60, 57262.40])

    def test_t_agg_10_special_session_anchoring(self):
        # Before confirmation: anchored at 09:15 (the provisional open).
        bars = self.db.get_bars("NIFTY", "60m", "2025-10-21",
                                "2025-10-21").bars
        first = _bar(bars, "2025-10-21 13:15:00")
        second = _bar(bars, "2025-10-21 14:15:00")
        self.assertEqual(first["present_units"], 30)    # 13:45-14:14
        self.assertEqual(second["present_units"], 31)   # 14:15-14:45
        self.assertFalse(first["is_complete"] or second["is_complete"])
        for bar in (first, second):
            self.assertIn("SESSION_UNCONFIRMED", bar["quality_flags"])
        # After confirmation (13:45-14:45): one 60-minute bar anchored at
        # 13:45 covering 60 of 60, then the closing print at 14:45.
        raw = support.read_raw(support.NIFTY_1MIN).frame
        day_rows = raw[raw["ts"].dt.date == date(2025, 10, 21)].reset_index(
            drop=True)
        confirmation = sr.SessionConfirmation(sr.TYPE_SPECIAL, time(13, 45),
                                              time(14, 45))
        standardised = std.standardise_intraday(
            day_rows, owner_confirmations={date(2025, 10, 21): confirmation})
        window = _window(date(2025, 10, 21), 60, sr.STATUS_CONFIRMED_BY_OWNER,
                         sr.TYPE_SPECIAL, window_open=time(13, 45))
        confirmed_bars = agg.aggregate_intraday(
            standardised.records, {date(2025, 10, 21): window}, 60)
        candle_bars = confirmed_bars[confirmed_bars["record_type"]
                                     == "CANDLE"]
        self.assertEqual(len(candle_bars), 1)
        self.assertEqual(str(candle_bars["ts"].iloc[0]),
                         "2025-10-21 13:45:00")
        self.assertEqual((candle_bars["expected_units"].iloc[0],
                          candle_bars["present_units"].iloc[0]), (60, 60))
        self.assertTrue(candle_bars["is_complete"].iloc[0])
        closing = confirmed_bars[confirmed_bars["record_type"]
                                 == "CLOSING_AUCTION"]
        self.assertEqual(str(closing["ts"].iloc[0]), "2025-10-21 14:45:00")

    def test_t_agg_11_exclude_flagged(self):
        # T-DQ-03 style fixture: a constant-step run flagged SUSPECT_FILL.
        day = date(2026, 11, 2)
        rows = []
        for minute in range(10):
            ts = datetime(2026, 11, 2, 9, 15) + timedelta(minutes=minute)
            if minute < 5:
                rows.append((ts, "CANDLE", 100.0 + 0.4 * minute, 110.0, 95.0,
                             100.0 + 0.4 * minute, 10, ts, "SUSPECT_FILL"))
            else:
                rows.append((ts, "CANDLE", 100.0, 110.0 + minute, 95.0,
                             100.5, 10, ts, None))
        records = pd.DataFrame(rows, columns=["ts", "record_type", "open",
                                              "high", "low", "close",
                                              "volume", "source_ts",
                                              "quality_flags"])
        records["ts"] = records["ts"].astype("datetime64[us]")
        records["volume"] = records["volume"].astype("Int64")
        windows = {day: _window(day, 375)}
        included = agg.aggregate_intraday(records, windows, 5)
        self.assertEqual(included.iloc[0]["present_units"], 5)
        self.assertIn("SUSPECT_FILL", included.iloc[0]["quality_flags"])
        excluded = agg.aggregate_intraday(records, windows, 5,
                                          exclude_flagged=True)
        first_interval = excluded[excluded["ts"]
                                  == pd.Timestamp("2026-11-02 09:15:00")]
        self.assertEqual(len(first_interval), 0)   # all 5 minutes missing
        second = _bar(excluded, "2026-11-02 09:20:00")
        self.assertEqual(second["present_units"], 5)

    def test_t_agg_12_monthly_from_daily(self):
        derived = pd.read_parquet(support.NIFTY_MONTHLY)
        derived = derived[(derived["datetime"] >= "2025-02-01")
                          & (derived["datetime"] <= "2026-10-31")]
        mine = self.db.get_bars("NIFTY", "1MO", "2025-02-01",
                                "2026-10-31").bars
        self.assertEqual(len(mine), 21)
        merged = derived.merge(mine, left_on="datetime", right_on="ts",
                               how="outer", indicator=True)
        self.assertTrue((merged["_merge"] == "both").all())  # labels match
        for column in ("open", "high", "low", "close"):
            delta = (merged[column + "_x"] - merged[column + "_y"]).abs()
            self.assertLessEqual(float(delta.max()), 0.000001, column)

    def test_t_agg_13_daily_volume_excludes_auction(self):
        result = self.db.get_bars("BANKNIFTY", "1D", "2026-08-18",
                                  "2026-08-18")
        bar = result.bars.iloc[0]
        self.assertEqual(bar["volume"], 123512346)
        self.assertNotIn(bar["volume"], (123532339, 123552332))
        self.assertFalse(bar["volume_complete"])
        self.assertIn("VOLUME_EXCLUDES_AUCTION", bar["quality_flags"])
        self.assertIn("DAILY_VOLUME_EXCLUDES_AUCTION", result.meta["notes"])

    def test_t_dup_03_defensive_duplicate_check(self):
        day = date(2026, 11, 2)
        ts = datetime(2026, 11, 2, 9, 15)
        records = pd.DataFrame(
            [(ts, "CANDLE", 100.0, 101.0, 99.0, 100.5, 10, ts, None)] * 2,
            columns=["ts", "record_type", "open", "high", "low", "close",
                     "volume", "source_ts", "quality_flags"])
        records["ts"] = records["ts"].astype("datetime64[us]")
        records["volume"] = records["volume"].astype("Int64")
        with self.assertRaises(DataIntegrityError):
            agg.aggregate_intraday(records, {day: _window(day)}, 5)


class TestAcceptanceM2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not support.fixtures_present() or not all(
                os.path.exists(p) for p in DERIVED_FILES.values()):
            raise unittest.SkipTest("sample files absent")
        root, _ = support.shared_initial_load()
        cls.db = QMapData(root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def test_acc_01_zero_differences_against_derived_files(self):
        """0 O/H/L/C differences at 3m/5m/15m/1D over 09-Jan-25 to 30-Oct-26
        and at 1MO over Feb-25 to Oct-26 (Q-1/X-7). The derived files' 15:30
        rows are compared with Q-MAP's CLOSING_AUCTION rows; volumes must be
        exactly equal, and a null on one side only counts as a mismatch."""
        for timeframe, path in DERIVED_FILES.items():
            derived = pd.read_parquet(path)[["datetime", "open", "high",
                                             "low", "close", "Volume"]]
            if timeframe == "1MO":
                start, end = "2025-02-01", "2026-10-31"
            else:
                start, end = "2025-01-09", "2026-10-30"
            derived = derived[(derived["datetime"] >= start)
                              & (derived["datetime"]
                                 <= end + " 23:59:59")]
            mine = self.db.get_bars("NIFTY", timeframe, start, end).bars
            merged = derived.merge(mine[["ts", "open", "high", "low",
                                         "close", "volume"]],
                                   left_on="datetime", right_on="ts",
                                   how="outer", suffixes=("_d", "_q"),
                                   indicator=True)
            only_derived = int((merged["_merge"] == "left_only").sum())
            only_mine = int((merged["_merge"] == "right_only").sum())
            both = merged[merged["_merge"] == "both"]
            self.assertEqual((only_derived, only_mine), (0, 0), timeframe)
            self.assertEqual(len(both), ACC01_EXPECTED_MATCHED[timeframe],
                             timeframe)
            for column in ("open", "high", "low", "close"):
                delta = (both[column + "_d"].astype(float)
                         - both[column + "_q"].astype(float)).abs()
                self.assertLessEqual(float(delta.max()), 0.000001,
                                     "%s %s" % (timeframe, column))
            one_side_null = int((both["Volume"].isna()
                                 != both["volume"].isna()).sum())
            self.assertEqual(one_side_null, 0, timeframe)
            with_values = both[both["Volume"].notna()]
            if len(with_values):
                self.assertTrue((with_values["Volume"].astype("int64")
                                 == with_values["volume"].astype("int64"))
                                .all(), timeframe)

    def test_acc_07_auction_sets_daily_high_or_low_on_16_of_67_days(self):
        root, _ = support.shared_initial_load()
        records = support.canonical_frame(root, "NSE_INDEX_1M", "NIFTY")
        dates = records["ts"].dt.date
        affected, cas_days = 0, 0
        for day, day_rows in records.groupby(dates):
            closing = day_rows[day_rows["record_type"] == "CLOSING_AUCTION"]
            if len(closing) == 0:
                continue
            cas_days += 1
            candles = day_rows[day_rows["record_type"] == "CANDLE"]
            auction_price = float(closing["close"].iloc[0])
            if auction_price > float(candles["high"].max()) \
                    or auction_price < float(candles["low"].min()):
                affected += 1
        self.assertEqual(cas_days, 67)
        self.assertEqual(affected, 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
