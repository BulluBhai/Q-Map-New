"""L3 tests: catalogue, calendar file and G-16 source handling (T-CAT-01 to
04, T-CAL-01, 02, 04, T-MNT-11, T-MNT-11b). Document 06 v1.5, section 5.6.

T-CAL-01 is tested to the M1a boundary: import leaves the rows unconfirmed and
recording provenance makes the confirmed years official. The re-validation
that then reclassifies stored days (and T-CAL-03) belongs to the M1b
REVALIDATE run.
"""

# --- Imports -----------------------------------------------------------------
import os
import shutil
import unittest
from datetime import date, time

import support
from qmap_database.catalogue import Catalogue
from qmap_database.errors import FileImportError
from qmap_database.maintenance import run_initial_load
from qmap_database.readers import sha256_of_file
from qmap_database.session_rules import read_official_calendar_file
from qmap_database.storage import DataRoot

# --- Constants ---------------------------------------------------------------
HOLIDAYS_2025 = ["2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
                 "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
                 "2025-08-27", "2025-10-02", "2025-10-22", "2025-11-05",
                 "2025-12-25"]


# --- Helpers ------------------------------------------------------------------
def _write_calendar_2025(path, break_mode=None):
    """The 2025 holidays from Deliverable 1 section 9.3 plus the two SPECIAL
    sessions named by T-CAL-01."""
    lines = ["trade_date,day_type,session_open,session_close,description"]
    for day in HOLIDAYS_2025:
        lines.append("%s,HOLIDAY,,,holiday" % day)
    lines.append("2025-02-01,SPECIAL,09:15,15:30,Budget-day session")
    lines.append("2025-10-21,SPECIAL,13:45,14:45,Muhurat trading")
    if break_mode == "bad_date":
        lines.append("01-02-25,HOLIDAY,,,two-digit year")
    elif break_mode == "special_without_times":
        lines.append("2025-12-31,SPECIAL,,,no times")
    elif break_mode == "duplicate_date":
        lines.append("2025-12-25,HOLIDAY,,,appears twice")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


class TestCatalogue(unittest.TestCase):

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_cat_01_coverage_correct(self):
        catalogue, _ = support.shared_catalogue()
        try:
            coverage = {row[1]: row for row in catalogue.coverage_table()}
        finally:
            catalogue.close()
        expectations = {
            "NIFTY": ("2025-01-09 09:15:00", "2026-11-06 15:30:00"),
            # The last BANKNIFTY record is the 11-Nov-26 closing print,
            # stamped 15:30 under D-09 (source_ts keeps 15:29).
            "BANKNIFTY": ("2026-08-17 09:15:00", "2026-11-11 15:30:00"),
            "CONCOR": ("1998-11-26 00:00:00", "2026-11-06 00:00:00"),
            "INFY": ("1998-01-02 00:00:00", "2026-11-06 00:00:00"),
            "NIFTYIT": ("2003-08-25 00:00:00", "2026-11-06 00:00:00"),
        }
        for instrument_id, (first, last) in expectations.items():
            row = coverage[instrument_id]
            self.assertEqual(str(row[3]), first, instrument_id)
            self.assertEqual(str(row[4]), last, instrument_id)

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_cat_02_volume_availability(self):
        catalogue, _ = support.shared_catalogue()
        try:
            row = catalogue.con.execute(
                "SELECT volume_first_date, volume_last_date FROM coverage "
                "WHERE instrument_id = 'NIFTY'").fetchone()
        finally:
            catalogue.close()
        self.assertEqual(row, (date(2026, 8, 17), date(2026, 11, 6)))

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_cat_03_provenance_chain(self):
        root, _ = support.shared_initial_load()
        concor = support.canonical_frame(root, "NSE_EQ_DAILY", "CONCOR")
        import_id = int(concor["import_id"].iloc[0])
        catalogue, _ = support.shared_catalogue()
        try:
            recorded_sha = catalogue.con.execute(
                "SELECT source_sha256 FROM import_log WHERE import_id = ?",
                [import_id]).fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(recorded_sha, sha256_of_file(support.CONCOR_TXT))
        self.assertEqual(recorded_sha,
                         support.ANNEX_B_SHA256["CONCOR.txt"])

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_cat_04_calendar_derivation(self):
        catalogue, _ = support.shared_catalogue()
        try:
            holidays = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE day_type = "
                "'HOLIDAY' AND trade_date BETWEEN DATE '2023-01-02' AND "
                "DATE '2026-11-06'").fetchone()[0]
            weekend_specials = [row[0] for row in catalogue.con.execute(
                "SELECT trade_date FROM market_calendar WHERE day_type = "
                "'SPECIAL' ORDER BY trade_date").fetchall()]
            verified = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE verified"
            ).fetchone()[0]
            non_derived = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE source != "
                "'DERIVED_FROM_DATA'").fetchone()[0]
            confirmed_days = catalogue.con.execute(
                "SELECT count(*) FROM day_profile WHERE session_status LIKE "
                "'CONFIRMED%'").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(holidays, 57)
        for weekend_session in (date(2025, 2, 1), date(2026, 2, 1),
                                date(2026, 11, 8)):
            self.assertIn(weekend_session, weekend_specials)
        self.assertEqual(verified, 0)
        self.assertEqual(non_derived, 0)
        # Derived rows never confirm any session (G-02).
        self.assertEqual(confirmed_days, 0)


class TestCalendarFile(unittest.TestCase):

    @unittest.skipUnless(os.path.exists(support.CONCOR_TXT), "sample absent")
    def test_t_cal_01_official_only_after_provenance(self):
        folder = support.new_temp_folder("tcal01")
        calendar_path = os.path.join(folder, "nse_market_calendar.csv")
        _write_calendar_2025(calendar_path)
        root = support.new_temp_folder("tcal01_root")
        run_initial_load(root, [support.CONCOR_TXT],
                         calendar_file=calendar_path)
        catalogue = Catalogue(DataRoot(root).catalogue_path)
        try:
            # Step 1: imported rows are unconfirmed and change nothing.
            unconfirmed = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE source = "
                "'REFERENCE_FILE_UNCONFIRMED' AND NOT verified").fetchone()[0]
            self.assertEqual(unconfirmed, 15)   # 13 holidays + 2 specials
            basis = catalogue.con.execute(
                "SELECT completeness_basis FROM coverage WHERE instrument_id "
                "= 'CONCOR'").fetchone()[0]
            self.assertEqual(basis, "PROVISIONAL_DERIVED_CALENDAR")
            # Step 2: the Owner records provenance for 2025.
            catalogue.record_calendar_provenance(
                [2025], "NSE trading holiday circular 2025 (file sha256 %s)"
                % sha256_of_file(calendar_path), "Owner, 14-Nov-26")
            official = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE source = "
                "'OFFICIAL_REFERENCE' AND verified AND evidence IS NOT NULL "
                "AND confirmed_at IS NOT NULL").fetchone()[0]
            self.assertEqual(official, 15)
            special = catalogue.con.execute(
                "SELECT session_open, session_close FROM market_calendar "
                "WHERE trade_date = DATE '2025-10-21'").fetchone()
            self.assertEqual(special, (time(13, 45), time(14, 45)))
        finally:
            catalogue.close()

    def test_t_cal_02_malformed_calendar_refused(self):
        folder = support.new_temp_folder("tcal02")
        for break_mode, expected_text in [
                ("bad_date", "not a YYYY-MM-DD date"),
                ("special_without_times", "needs session_open"),
                ("duplicate_date", "appears twice")]:
            path = os.path.join(folder, "cal_%s.csv" % break_mode)
            _write_calendar_2025(path, break_mode)
            with self.assertRaises(FileImportError,
                                   msg=break_mode) as ctx:
                read_official_calendar_file(path)
            self.assertIn(expected_text, str(ctx.exception))

    @unittest.skipUnless(os.path.exists(support.CONCOR_TXT), "sample absent")
    def test_t_cal_04_changed_file_loses_official_status(self):
        folder = support.new_temp_folder("tcal04")
        calendar_path = os.path.join(folder, "nse_market_calendar.csv")
        _write_calendar_2025(calendar_path)
        root = support.new_temp_folder("tcal04_root")
        run_initial_load(root, [support.CONCOR_TXT],
                         calendar_file=calendar_path)
        catalogue = Catalogue(DataRoot(root).catalogue_path)
        try:
            catalogue.record_calendar_provenance([2025], "NSE circular",
                                                 "Owner, 14-Nov-26")
        finally:
            catalogue.close()
        # Edit one row (description change alters the SHA-256) and re-import.
        with open(calendar_path, "a", encoding="utf-8") as handle:
            handle.write("2025-12-31,HOLIDAY,,,added row\n")
        run_initial_load(root, [support.CONCOR_TXT],
                         calendar_file=calendar_path)
        catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
        try:
            still_official = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE source = "
                "'OFFICIAL_REFERENCE'").fetchone()[0]
            unconfirmed = catalogue.con.execute(
                "SELECT count(*) FROM market_calendar WHERE source = "
                "'REFERENCE_FILE_UNCONFIRMED' AND NOT verified").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(still_official, 0)
        self.assertEqual(unconfirmed, 16)


class TestSourceConflicts(unittest.TestCase):

    @unittest.skipUnless(support.fixtures_present(), "sample files absent")
    def test_t_mnt_11_different_files_conflict(self):
        root = support.new_temp_folder("tmnt11_root")
        result = run_initial_load(root,
                                  [support.CONCOR_TXT, support.CONCOR_PARQUET])
        actions = {outcome.path: outcome.action
                   for outcome in result.file_outcomes}
        self.assertEqual(actions[support.CONCOR_TXT], "SOURCE_CONFLICT")
        self.assertEqual(actions[support.CONCOR_PARQUET], "SOURCE_CONFLICT")
        # Nothing imported for CONCOR before the Owner chooses.
        catalogue = Catalogue(DataRoot(root).catalogue_path)
        try:
            active = catalogue.con.execute(
                "SELECT active_generation FROM instrument WHERE "
                "instrument_id = 'CONCOR'").fetchone()[0]
            self.assertIsNone(active)
            issue = catalogue.con.execute(
                "SELECT description, evidence FROM data_issue WHERE "
                "check_code = 'G-16'").fetchone()
            self.assertIn("CONCOR", issue[0])
            self.assertIn("CONCOR.txt", issue[1])
            self.assertIn(support.ANNEX_B_SHA256["CONCOR.txt"], issue[1])
            self.assertIn(support.ANNEX_B_SHA256[
                "CONCOR_daily 26Nov98-06Nov26.parquet"], issue[1])
        finally:
            catalogue.close()
        # After the Owner chooses CONCOR.txt, only it is imported.
        second = run_initial_load(root, [support.CONCOR_TXT])
        self.assertEqual(second.file_outcomes[0].action, "NEW")
        self.assertEqual(second.file_outcomes[0].rows_stored, 6860)
        catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
        try:
            sources = catalogue.con.execute(
                "SELECT count(DISTINCT source_sha256) FROM import_log WHERE "
                "instrument_id = 'CONCOR' AND action = 'NEW'").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual(sources, 1)

    @unittest.skipUnless(os.path.exists(support.CONCOR_TXT), "sample absent")
    def test_t_mnt_11b_byte_identical_copy_is_duplicate(self):
        folder = support.new_temp_folder("tmnt11b")
        copy_path = os.path.join(folder, "CONCOR_daily_copy.txt")
        shutil.copyfile(support.CONCOR_TXT, copy_path)
        root = support.new_temp_folder("tmnt11b_root")
        result = run_initial_load(root, [support.CONCOR_TXT, copy_path])
        actions = sorted(outcome.action for outcome in result.file_outcomes)
        self.assertEqual(actions, ["DUPLICATE_SOURCE", "NEW"])
        catalogue = Catalogue(DataRoot(root).catalogue_path, read_only=True)
        try:
            generation, rows = catalogue.con.execute(
                "SELECT generation, row_count FROM data_file WHERE "
                "instrument_id = 'CONCOR'").fetchone()
            generations = catalogue.con.execute(
                "SELECT count(DISTINCT generation) FROM data_file WHERE "
                "instrument_id = 'CONCOR'").fetchone()[0]
        finally:
            catalogue.close()
        self.assertEqual((generation, rows, generations), (1, 6860, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
