"""M3 tests: EMA Trend Alignment scanner T-EMA-01 to T-EMA-18 (document 10
v1.7, section B9.3; reference values verified against the source files in
document 13 v1.2), plus contract, registry, runner and output checks
(document 04 v1.3, sections 4 and 7).

G-03 is respected: CONCOR results whose window holds an unverified +/-15%
move are expected to be INVALID_DATA. The conditional reference values are
checked only on a separate temporary load in which the test itself records
the Owner-style VERIFIED_OK for that one occurrence; the shared load is never
changed.
"""

# --- Imports -----------------------------------------------------------------
import json
import os
import shutil
import unittest
from datetime import date, timedelta

import pandas as pd

import support
from qmap_database.access import BarResult, DataRequirement
from qmap_engine import contract, output, registry, runner
from qmap_scanners.ema_trend_alignment import scanner as ema

# --- Constants ---------------------------------------------------------------
SCANNER = [{"scanner_id": "ema_trend_alignment"}]
DP4 = 4


# --- Helpers ------------------------------------------------------------------
def run_one(root, instrument_id, analysis_end, parameters=None):
    entry = {"scanner_id": "ema_trend_alignment",
             "parameters": parameters or {}}
    result = runner.run_analysis(runner.RunConfig(
        root, [instrument_id], analysis_end, [entry]))
    return result.scanner_results[0]


class _FixtureData:
    """A stand-in for QMapData that serves a synthetic daily close series
    (T-EMA-10 to 12). It returns what get_bars returns: a BarResult."""

    def __init__(self, closes):
        start = date(2020, 1, 1)
        self.frame = pd.DataFrame({
            "ts": pd.to_datetime([start + timedelta(days=i)
                                  for i in range(len(closes))]),
            "record_type": "DAY", "close": closes, "is_complete": True,
            "is_forming": False, "quality_flags": None})

    def get_bars(self, instrument_id, timeframe, start=None, end=None, *,
                 fields=None, latest_n=None, include_auction_records=True,
                 exclude_flagged=False):
        bars = self.frame.tail(latest_n) if latest_n else self.frame
        meta = {"dataset_id": "NSE_EQ_DAILY", "warnings": [], "notes": [],
                "issues": [], "data_version": "fixture",
                "bar_count": len(bars), "returned_first_ts": bars["ts"].iloc[0],
                "returned_last_ts": bars["ts"].iloc[-1],
                "timezone": "Asia/Kolkata", "ts_meaning": "fixture"}
        return BarResult(bars=bars.reset_index(drop=True), meta=meta,
                         status="OK")


def run_fixture(closes):
    params = ema.default_parameters()
    requirement = ema.data_requirements("FIXTURE", params, None,
                                        "2030-01-01")[0]
    context = contract.ScannerContext(
        run_id="TEST", instrument_id="FIXTURE", parameters=params,
        analysis_start=None, analysis_end="2030-01-01",
        requirements=[(requirement, None)], _data=_FixtureData(closes))
    result = ema.run(context)
    return result, contract.validate_result(result, ema.INFO)


def _verified_root(label, verify_dates):
    """A separate temporary load of CONCOR and INFY in which the given
    CONCOR V-PX-05 occurrences are marked VERIFIED_OK."""
    from qmap_database.maintenance import (run_initial_load,
                                           verify_continuity_issue)
    from qmap_database.catalogue import Catalogue
    from qmap_database.storage import DataRoot
    root = support.new_temp_folder(label)
    source_folder = support.new_temp_folder(label + "_src")
    shutil.copy2(support.CONCOR_TXT, source_folder)     # a temporary copy
    run_initial_load(root, [os.path.join(source_folder, "CONCOR.txt"),
                            support.INFY_PARQUET])
    catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
    try:
        ids = [row[0] for row in catalogue.continuity_issues_awaiting_owner()
               if row[1] == "CONCOR" and row[2].date() in verify_dates]
    finally:
        catalogue.close()
    if len(ids) != len(verify_dates):
        raise AssertionError("expected %d issues to verify, found %d"
                             % (len(verify_dates), len(ids)))
    for issue_id in ids:
        verify_continuity_issue(root, issue_id, "test: verified for T-EMA")
    return root, source_folder


class TestEmaLogic(unittest.TestCase):
    """Calculation and classification tests that need no stored data."""

    def test_t_ema_01_ema_arithmetic(self):
        closes = [413.85, 417.85, 419.15, 425.10, 440.85, 439.80]
        values = ema.ema_series(closes, 3)
        self.assertEqual(values[:2], [None, None])
        for got, expected in zip(values[2:], [416.95, 421.025, 430.9375,
                                              435.36875]):
            self.assertAlmostEqual(got, expected, places=DP4)

    def test_t_ema_10_exact_tie_counts_zero(self):
        result, problems = run_fixture([100.0] * 800)
        self.assertEqual(problems, [])
        self.assertEqual(result["status"], "OK")
        self.assertEqual(set(result["calculations"]["answers"].values()), {0})
        self.assertEqual(result["calculations"]["net"], 0)
        self.assertEqual(result["score"]["value"], 50.0)
        self.assertEqual(result["calculations"]["state"], "NEUTRAL")

    def test_t_ema_11_monotonic_rise(self):
        result, _ = run_fixture([100.0 + i for i in range(800)])
        self.assertEqual(set(result["calculations"]["answers"].values()), {1})
        self.assertEqual(result["score"]["value"], 100.0)

    def test_t_ema_12_monotonic_fall(self):
        result, _ = run_fixture([1000.0 - 0.1 * i for i in range(800)])
        self.assertEqual(set(result["calculations"]["answers"].values()), {-1})
        self.assertEqual(result["score"]["value"], 0.0)

    def test_t_ema_16_every_net_count_classified(self):
        expected = {-6: (0.0, "BEARISH"), -5: (8.33, "BEARISH"),
                    -4: (16.67, "BEARISH"), -3: (25.0, "NEUTRAL_LEANING_BEARISH"),
                    -2: (33.33, "NEUTRAL"), -1: (41.67, "NEUTRAL"),
                    0: (50.0, "NEUTRAL"), 1: (58.33, "NEUTRAL"),
                    2: (66.67, "NEUTRAL"), 3: (75.0, "NEUTRAL_LEANING_BULLISH"),
                    4: (83.33, "BULLISH"), 5: (91.67, "BULLISH"),
                    6: (100.0, "BULLISH")}
        for net, (score, state) in expected.items():
            self.assertEqual(ema.score_for(net), score, net)
            self.assertEqual(ema.state_for(net), state, net)

    def test_fixture_short_history_is_insufficient(self):
        result, problems = run_fixture([100.0] * 799)
        self.assertEqual(problems, [])
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(result["score"])

    def test_parameter_validation(self):
        self.assertEqual(ema.validate_parameters(ema.default_parameters()), [])
        self.assertTrue(ema.validate_parameters({"window_bars": 799}))
        self.assertTrue(ema.validate_parameters({"short_period": 60}))
        self.assertTrue(ema.validate_parameters({"tie_band_pct": 2.0}))
        self.assertTrue(ema.validate_parameters({"unknown": 1}))


class TestContract(unittest.TestCase):

    def test_registry_is_explicit_and_consistent(self):
        infos = registry.check_registry()
        self.assertEqual([i.scanner_id for i in infos], ["ema_trend_alignment"])
        with self.assertRaises(RuntimeError):
            registry.check_registry({"wrong_key": ema})

    def test_validate_result_rejects_bad_results(self):
        result, _ = run_fixture([100.0 + i for i in range(800)])
        self.assertEqual(contract.validate_result(result, ema.INFO), [])
        bad = json.loads(json.dumps(result))
        bad["score"]["value"] = 101
        self.assertTrue(contract.validate_result(bad, ema.INFO))
        bad = json.loads(json.dumps(result))
        bad["interpretation"] = "text"
        self.assertTrue(contract.validate_result(bad, ema.INFO))
        bad = json.loads(json.dumps(result))
        bad["status"] = "INSUFFICIENT_DATA"
        self.assertTrue(contract.validate_result(bad, ema.INFO))
        bad = json.loads(json.dumps(result))
        bad["scanner"]["version"] = "9.9.9"
        self.assertTrue(contract.validate_result(bad, ema.INFO))

    def test_undeclared_requirement_refused(self):
        params = ema.default_parameters()
        declared = ema.data_requirements("FIXTURE", params, None, "2030-01-01")
        context = contract.ScannerContext(
            "TEST", "FIXTURE", params, None, "2030-01-01",
            [(declared[0], None)], _data=_FixtureData([1.0] * 900))
        with self.assertRaises(contract.UndeclaredRequirementError):
            context.fetch(DataRequirement("FIXTURE", "1D", latest_n=5))

    def test_scanner_reads_data_only_through_the_interface(self):
        # SC-02 and the architecture boundary: no file, Parquet, DuckDB or
        # catalogue access inside the scanner module.
        with open(ema.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        for forbidden in ("read_parquet", "duckdb", "pyarrow", "open(",
                          "qmap_database.storage", "qmap_database.catalogue",
                          "os.path"):
            self.assertNotIn(forbidden, source, forbidden)

    def test_runner_rejects_bad_configuration(self):
        root, _ = support.shared_initial_load()
        with self.assertRaises(runner.RunConfigError):
            runner.run_analysis(runner.RunConfig(root, ["NOPE"], "2026-11-06",
                                                 SCANNER))
        with self.assertRaises(runner.RunConfigError):
            runner.run_analysis(runner.RunConfig(
                root, ["INFY"], "2026-11-06",
                [{"scanner_id": "ema_trend_alignment",
                  "parameters": {"window_bars": 10}}]))


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestEmaOnSharedLoad(unittest.TestCase):
    """Default behaviour on the shared, unverified load (G-03 applies)."""

    @classmethod
    def setUpClass(cls):
        cls.root, _ = support.shared_initial_load()

    def assert_values(self, result, close, s, m, l, lookback):
        facts = result["facts"]
        self.assertAlmostEqual(facts["close"], close, places=DP4)
        self.assertAlmostEqual(facts["ema_short"], s, places=DP4)
        self.assertAlmostEqual(facts["ema_medium"], m, places=DP4)
        self.assertAlmostEqual(facts["ema_long"], l, places=DP4)
        self.assertAlmostEqual(facts["ema_medium_lookback"], lookback,
                               places=DP4)

    def test_t_ema_02_concor_default_is_invalid(self):
        result = run_one(self.root, "CONCOR", "2026-11-06")
        self.assertEqual(result["status"], "INVALID_DATA")
        self.assertIsNone(result["score"])
        self.assertTrue(any("04-Jun-24" in m
                            for m in result["status_messages"]))

    def test_t_ema_03_infy_neutral_reference(self):
        result = run_one(self.root, "INFY", "2026-11-06")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["facts"]["window_start_date"], "2023-08-17")
        self.assert_values(result, 1181.40, 1132.2614, 1108.5365, 1203.8765,
                           1084.5193)
        self.assertEqual(list(result["calculations"]["answers"].values()),
                         [1, 1, -1, 1, -1, 1])
        self.assertEqual(result["calculations"]["net"], 2)
        self.assertEqual(result["score"]["value"], 66.67)
        self.assertEqual(result["calculations"]["state"], "NEUTRAL")

    def test_t_ema_04_infy_fully_bullish_reference(self):
        result = run_one(self.root, "INFY", "2026-02-03")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["facts"]["window_start_date"], "2022-11-16")
        self.assert_values(result, 1656.00, 1646.1038, 1617.6051, 1589.1800,
                           1598.2591)
        self.assertEqual(result["score"]["value"], 100.0)
        self.assertEqual(result["calculations"]["state"], "BULLISH")

    def test_t_ema_06_insufficient_history(self):
        result = run_one(self.root, "CONCOR", "2001-12-31")
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(result["score"])
        self.assertIn("needs 800 complete daily bars; 690 available",
                      result["status_messages"])

    def test_t_ema_07_first_date_with_enough_history(self):
        self.assertEqual(run_one(self.root, "CONCOR", "2002-06-05")["status"],
                         "INSUFFICIENT_DATA")
        result = run_one(self.root, "CONCOR", "2002-06-06")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["facts"]["analysis_date"], "2002-06-06")

    def test_t_ema_08_continuity_break_blocks(self):
        result = run_one(self.root, "CONCOR", "2014-06-30")
        self.assertEqual(result["status"], "INVALID_DATA")
        self.assertEqual(result["facts"]["window_start_date"], "2011-04-11")
        self.assertTrue(any("06-Sep-13" in m for m in result["status_messages"]))

    def test_t_ema_09_recovery_after_the_break(self):
        before = run_one(self.root, "CONCOR", "2016-12-07")
        after = run_one(self.root, "CONCOR", "2016-12-08")
        self.assertEqual(before["status"], "INVALID_DATA")
        self.assertEqual(after["status"], "OK")
        self.assertEqual(after["facts"]["window_start_date"], "2013-09-10")

    def test_t_ema_13_determinism(self):
        first = run_one(self.root, "INFY", "2026-11-06")
        second = run_one(self.root, "INFY", "2026-11-06")
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_t_ema_15_insufficient_result_passes_contract(self):
        result = run_one(self.root, "CONCOR", "2001-12-31")
        self.assertIsNone(result["score"])
        self.assertEqual(contract.validate_result(result, ema.INFO), [])

    def test_t_ema_17_stale_data_proposed_rule(self):
        # D-EMA-11 is a proposal; the provisional behaviour is applied and
        # labelled as such in every result.
        result = run_one(self.root, "CONCOR", "2026-11-10")
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(result["score"])
        self.assertIn("data ends 06-Nov-26; analysis date 10-Nov-26 "
                      "(D-EMA-11, proposed)", result["status_messages"])
        self.assertTrue(any("PROPOSED" in rule for rule in
                            result["calculations"]["provisional_rules"]))

    def test_t_ema_18_open_only_anomaly_blocks(self):
        result = run_one(self.root, "CONCOR", "2007-12-31")
        self.assertEqual(result["status"], "INVALID_DATA")
        self.assertEqual(result["facts"]["window_start_date"], "2004-10-14")
        self.assertTrue(any("15-May-06" in m for m in result["status_messages"]))

    def test_not_applicable_for_an_index(self):
        result = run_one(self.root, "NIFTY", "2026-11-06")
        self.assertEqual(result["status"], "NOT_APPLICABLE")

    def test_output_files_round_trip(self):
        run = runner.run_analysis(runner.RunConfig(
            self.root, ["INFY", "CONCOR"], "2026-11-06", SCANNER))
        folder = support.new_temp_folder("ema_out")
        json_path, xlsx_path = output.write_outputs([run], folder)
        self.assertTrue(os.path.basename(json_path).startswith("Q-MAP_Run_"))
        with open(json_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["3_scanner_results"], run.scanner_results)
        self.assertIsNone(payload["5_interpretation"])
        sections = {k: payload[k] for k in ("1_run_context",
                                            "2_data_references",
                                            "3_scanner_results",
                                            "4_combined_scores")}
        self.assertEqual(payload["integrity"]["content_sha256"],
                         output._canonical_sha256(sections))
        import openpyxl
        sheet = openpyxl.load_workbook(xlsx_path)["Scanner_Results"]
        rows = list(sheet.iter_rows(min_row=2, values_only=True))
        infy = [r for r in rows if r[0] == "INFY"][0]
        self.assertEqual(infy[4], 66.67)
        # Excel holds 15 significant digits; the JSON is the full-precision
        # authoritative record (document 05 section 7.3).
        self.assertAlmostEqual(infy[15],
                               run.scanner_results[0]["facts"]["ema_medium"],
                               places=9)
        self.assertEqual([f for f in os.listdir(folder)
                          if f.endswith(".partial")], [])


@unittest.skipUnless(support.fixtures_present(), "sample files absent")
class TestEmaAfterOwnerVerification(unittest.TestCase):
    """Conditional reference values (T-EMA-02, 05, 14, 18): valid only after
    the specific occurrence is verified. A separate temporary load is used."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.source_folder = _verified_root(
            "ema_verified", {date(2024, 6, 4), date(2006, 5, 15)})

    def test_t_ema_02_concor_bearish_reference(self):
        result = run_one(self.root, "CONCOR", "2026-11-06")
        self.assertEqual(result["status"], "OK")
        facts = result["facts"]
        self.assertEqual(facts["window_start_date"], "2023-08-17")
        for name, value in (("close", 439.80), ("ema_short", 432.7297),
                            ("ema_medium", 452.6585), ("ema_long", 486.4492),
                            ("ema_medium_lookback", 466.7276)):
            self.assertAlmostEqual(facts[name], value, places=DP4, msg=name)
        self.assertEqual(list(result["calculations"]["answers"].values()),
                         [1, -1, -1, -1, -1, -1])
        self.assertEqual(result["score"]["value"], 16.67)
        self.assertEqual(result["calculations"]["state"], "BEARISH")

    def test_t_ema_05_bullish_with_bearish_long_term(self):
        result = run_one(self.root, "CONCOR", "2026-09-09")
        self.assertEqual(result["status"], "OK")
        facts = result["facts"]
        self.assertEqual(facts["window_start_date"], "2023-06-21")
        for name, value in (("close", 510.00), ("ema_short", 509.8872),
                            ("ema_medium", 504.0989), ("ema_long", 506.0167),
                            ("ema_medium_lookback", 502.3052)):
            self.assertAlmostEqual(facts[name], value, places=DP4, msg=name)
        self.assertEqual(list(result["calculations"]["answers"].values()),
                         [1, 1, 1, 1, -1, 1])
        self.assertEqual(result["score"]["value"], 83.33)

    def test_t_ema_18_conditional_values(self):
        result = run_one(self.root, "CONCOR", "2007-12-31")
        self.assertEqual(result["status"], "OK")
        facts = result["facts"]
        for name, value in (("close", 246.61), ("ema_short", 236.3180),
                            ("ema_medium", 241.2234), ("ema_long", 252.5792),
                            ("ema_medium_lookback", 244.1076)):
            self.assertAlmostEqual(facts[name], value, places=DP4, msg=name)
        self.assertEqual(result["calculations"]["net"], -2)
        self.assertEqual(result["score"]["value"], 33.33)
        self.assertEqual(result["calculations"]["state"], "NEUTRAL")

    def test_t_ema_14_held_revision_does_not_change_the_result(self):
        from qmap_database.maintenance import run_update
        before = run_one(self.root, "CONCOR", "2026-11-06")
        path = os.path.join(self.source_folder, "CONCOR.txt")
        with open(path, "rb") as handle:
            content = handle.read()
        # Revise one historical close (2010), as a source back-adjustment
        # would; the revision must be HELD, never applied automatically.
        line_start = content.index(b"2010-06-01,")
        line_end = content.index(b"\n", line_start)
        fields = content[line_start:line_end].rstrip(b"\r").split(b",")
        fields[4] = b"%.2f" % (float(fields[4]) + 1.0)
        content = (content[:line_start] + b",".join(fields) + b"\r"
                   + content[line_end:])
        with open(path, "wb") as handle:
            handle.write(content)
        result = run_update(self.root, [self.source_folder])
        self.assertTrue(any(o.action == "HELD_REVISION"
                            for o in result.file_outcomes),
                        [o.action for o in result.file_outcomes])
        after = run_one(self.root, "CONCOR", "2026-11-06")
        self.assertEqual(after["status"], "OK")
        self.assertEqual(after["facts"], before["facts"])
        self.assertEqual(after["score"], before["score"])
        self.assertTrue(any(m.startswith("HELD_REVISION_EXISTS")
                            for m in after["status_messages"]))

    def test_other_occurrences_still_block(self):
        # Verifying 04-Jun-24 does not unblock 20-Mar-20 / 10-Aug-20.
        result = run_one(self.root, "CONCOR", "2022-12-30")
        self.assertEqual(result["status"], "INVALID_DATA")


if __name__ == "__main__":
    unittest.main()
