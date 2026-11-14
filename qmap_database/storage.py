"""Physical storage: data-root layout, canonical Parquet files, the
generation commit protocol, start-up recovery and the integrity check
(document 02 v1.6, sections 2, 4 and 9.4).

Every change to an instrument's stored data follows one protocol:
stage -> validate the whole generation -> rename into market\\ -> activate in
one catalogue transaction -> prune. Files of an active generation are never
modified in place; readers resolve files only through the catalogue pointer.
"""

# --- Imports -----------------------------------------------------------------
import os
import shutil

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .errors import DataIntegrityError
from .readers import sha256_of_file

# --- Constants ---------------------------------------------------------------
GENERATION_FOLDER = "gen_%06d"

_INTRADAY_SCHEMA = pa.schema([
    ("instrument_id", pa.string()),
    ("ts", pa.timestamp("us")),
    ("record_type", pa.string()),
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.int64()),
    ("source_ts", pa.timestamp("us")),
    ("quality_flags", pa.string()),
    ("import_id", pa.int64()),
])

_DAILY_SCHEMA = pa.schema([
    ("instrument_id", pa.string()),
    ("trade_date", pa.date32()),
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.int64()),
    ("quality_flags", pa.string()),
    ("import_id", pa.int64()),
])


# --- Data root layout -----------------------------------------------------------
class DataRoot:
    """The one folder the Owner chooses; everything Q-MAP stores lives here."""

    def __init__(self, path):
        self.path = os.path.abspath(path)

    @property
    def catalogue_path(self):
        return os.path.join(self.path, "catalogue", "qmap_catalogue.duckdb")

    def folder(self, *parts):
        return os.path.join(self.path, *parts)

    def ensure_layout(self):
        for parts in (("catalogue",), ("market",), ("staging",),
                      ("quarantine",), ("held",), ("reference",),
                      ("backups", "catalogue"), ("reports",), ("logs",)):
            os.makedirs(self.folder(*parts), exist_ok=True)

    def market_generation(self, dataset_id, file_safe_name, generation):
        return self.folder("market", dataset_id, file_safe_name,
                           GENERATION_FOLDER % generation)

    def staging_generation(self, dataset_id, file_safe_name, generation):
        return self.folder("staging", dataset_id, file_safe_name,
                           GENERATION_FOLDER % generation)


# --- Helpers ---------------------------------------------------------------------
def flags_to_text(flag_sets):
    """Serialise per-row flag sets to the semicolon convention; empty -> null."""
    return [";".join(sorted(flags)) if flags else None for flags in flag_sets]


def _records_to_table(records, instrument_id, import_id, intraday):
    frame = records.copy()
    frame["instrument_id"] = instrument_id
    frame["import_id"] = import_id
    frame["quality_flags"] = flags_to_text(frame["quality_flags"])
    if intraday:
        columns = ["instrument_id", "ts", "record_type", "open", "high", "low",
                   "close", "volume", "source_ts", "quality_flags", "import_id"]
        schema = _INTRADAY_SCHEMA
    else:
        columns = ["instrument_id", "trade_date", "open", "high", "low",
                   "close", "volume", "quality_flags", "import_id"]
        schema = _DAILY_SCHEMA
    return pa.Table.from_pandas(frame[columns], schema=schema,
                                preserve_index=False)


def split_into_periods(records, intraday, file_safe_name):
    """Intraday data is stored one file per year; daily data one file per
    instrument (02 section 2.2)."""
    if not intraday:
        return {"ALL": ("%s.parquet" % file_safe_name, records)}
    periods = {}
    for year, year_rows in records.groupby(records["ts"].dt.year):
        periods[str(year)] = ("%s_%d.parquet" % (file_safe_name, year),
                              year_rows.reset_index(drop=True))
    return periods


# --- Main logic: generation commit protocol ----------------------------------------
def stage_and_validate_generation(data_root, dataset_id, instrument_id,
                                  file_safe_name, generation, records,
                                  import_id, intraday):
    """Steps 1 and 2 of the commit protocol: write every file of the new
    generation into staging, then read each one back and check it.

    Returns the data_file rows for the later activation step. Any check
    failure raises DataIntegrityError and leaves staging for the caller to
    discard; nothing has touched market\\ or the catalogue yet."""
    staging_folder = data_root.staging_generation(dataset_id, file_safe_name,
                                                  generation)
    if os.path.exists(staging_folder):
        shutil.rmtree(staging_folder)
    os.makedirs(staging_folder)

    time_column = "ts" if intraday else "trade_date"
    periods = split_into_periods(records, intraday, file_safe_name)
    file_rows = []
    for period in sorted(periods):
        file_name, period_records = periods[period]
        table = _records_to_table(period_records, instrument_id, import_id,
                                  intraday)
        file_path = os.path.join(staging_folder, file_name)
        pq.write_table(table, file_path)

        # Step 2: validate by reading back what was actually written.
        written = pd.read_parquet(file_path)
        if len(written) != len(period_records):
            raise DataIntegrityError(
                "%s: staged file holds %d rows, expected %d"
                % (file_name, len(written), len(period_records)))
        if written[time_column].duplicated().any():
            raise DataIntegrityError(
                "%s: staged file contains a duplicate key" % file_name)
        relative_path = os.path.relpath(
            os.path.join(data_root.market_generation(dataset_id,
                                                     file_safe_name,
                                                     generation), file_name),
            data_root.path).replace(os.sep, "/")
        min_val = period_records[time_column].min()
        max_val = period_records[time_column].max()
        file_rows.append({
            "relative_path": relative_path,
            "dataset_id": dataset_id,
            "period": period,
            "row_count": len(period_records),
            "min_ts": pd.Timestamp(min_val).to_pydatetime(),
            "max_ts": pd.Timestamp(max_val).to_pydatetime(),
            "sha256": sha256_of_file(file_path),
        })

    # The year files together must form the expected continuous set of years.
    if intraday and len(file_rows) > 1:
        years = sorted(int(f["period"]) for f in file_rows)
        if years != list(range(years[0], years[-1] + 1)):
            raise DataIntegrityError(
                "%s generation %d: year files are not continuous (%s)"
                % (instrument_id, generation, years))
    return file_rows


def move_generation_into_market(data_root, dataset_id, file_safe_name,
                                generation):
    """Step 3: one folder rename on the same drive. The generation is still
    inactive, because the catalogue does not point to it yet."""
    staging_folder = data_root.staging_generation(dataset_id, file_safe_name,
                                                  generation)
    market_folder = data_root.market_generation(dataset_id, file_safe_name,
                                                generation)
    os.makedirs(os.path.dirname(market_folder), exist_ok=True)
    if os.path.exists(market_folder):
        raise DataIntegrityError(
            "cannot move generation into place: %s already exists"
            % market_folder)
    os.replace(staging_folder, market_folder)


def discard_staging(data_root, dataset_id, file_safe_name, generation):
    """Remove a staged generation after a validation failure; the previous
    generation stays active and untouched."""
    staging_folder = data_root.staging_generation(dataset_id, file_safe_name,
                                                  generation)
    if os.path.exists(staging_folder):
        shutil.rmtree(staging_folder)


# --- Main logic: recovery and integrity ---------------------------------------------
def startup_recovery(data_root, catalogue):
    """Handle interruptions of earlier runs (02 section 9.4 recovery table).

    - Any staging content is an incomplete build: deleted and logged.
    - A market generation folder with no catalogue registration and no active
      pointer is unactivated: removed and logged.
    Returns the log messages."""
    messages = []
    staging_root = data_root.folder("staging")
    if os.path.isdir(staging_root):
        for name in os.listdir(staging_root):
            path = os.path.join(staging_root, name)
            shutil.rmtree(path, ignore_errors=True)
            messages.append("recovery: discarded incomplete staging '%s'" % name)

    known = {}
    for instrument in catalogue.instruments():
        known[(instrument["dataset_id"], instrument["file_safe_name"])] = \
            instrument
    registered = set()
    for row in catalogue.con.execute(
            "SELECT DISTINCT instrument_id, generation FROM data_file"
    ).fetchall():
        registered.add((row[0], row[1]))

    market_root = data_root.folder("market")
    if os.path.isdir(market_root):
        for dataset_id in os.listdir(market_root):
            dataset_folder = os.path.join(market_root, dataset_id)
            if not os.path.isdir(dataset_folder):
                continue
            for safe_name in os.listdir(dataset_folder):
                instrument = known.get((dataset_id, safe_name))
                instrument_folder = os.path.join(dataset_folder, safe_name)
                for gen_name in os.listdir(instrument_folder):
                    if not gen_name.startswith("gen_"):
                        continue
                    generation = int(gen_name.split("_")[1])
                    instrument_id = (instrument["instrument_id"] if instrument
                                     else None)
                    if instrument_id and (instrument_id, generation) in registered:
                        continue
                    # Unactivated: renamed into place but never committed.
                    shutil.rmtree(os.path.join(instrument_folder, gen_name),
                                  ignore_errors=True)
                    messages.append(
                        "recovery: removed unactivated generation %s/%s/%s"
                        % (dataset_id, safe_name, gen_name))
    return messages


def integrity_check(data_root, catalogue):
    """V-INT-01: every file of each active generation exists and matches its
    catalogue fingerprint and row count. Returns mismatch messages (empty
    means the check passed)."""
    problems = []
    for relative_path, row_count, sha256, instrument_id in \
            catalogue.active_data_files():
        full_path = os.path.join(data_root.path,
                                 relative_path.replace("/", os.sep))
        if not os.path.exists(full_path):
            problems.append("INTEGRITY_MISMATCH: %s is missing (%s)"
                            % (relative_path, instrument_id))
            continue
        actual_sha = sha256_of_file(full_path)
        if actual_sha != sha256:
            problems.append("INTEGRITY_MISMATCH: %s fingerprint differs (%s)"
                            % (relative_path, instrument_id))
            continue
        actual_rows = pq.read_metadata(full_path).num_rows
        if actual_rows != row_count:
            problems.append("INTEGRITY_MISMATCH: %s has %d rows, catalogue "
                            "says %d (%s)" % (relative_path, actual_rows,
                                              row_count, instrument_id))
    return problems


# --- Main logic: quarantine --------------------------------------------------------
def write_quarantine(data_root, dataset_id, file_safe_name, import_id,
                     quarantine_frame, intraday):
    """Rows that fail validation stay visible and reviewable (02 section 4.4).
    Returns the file path, or None when there is nothing to write."""
    if quarantine_frame is None or len(quarantine_frame) == 0:
        return None
    folder = data_root.folder("quarantine", dataset_id)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s_imp%06d.parquet"
                        % (file_safe_name, import_id))
    frame = quarantine_frame.copy()
    frame["import_id"] = import_id
    if "volume" in frame.columns:
        frame["volume"] = frame["volume"].astype("Int64")
    frame.to_parquet(path)
    return path
