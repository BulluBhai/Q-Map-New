"""Shared test support for the Q-MAP test suite.

Provides the fixture paths, a cached read of the large sample files, and one
shared initial load that real-data tests reuse (building it once keeps the
suite fast). Fixtures are read in place and never modified; everything the
tests write goes to a temporary folder that is removed at exit.
"""

# --- Imports -----------------------------------------------------------------
import atexit
import os
import shutil
import sys
import tempfile

_TESTS_FOLDER = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TESTS_FOLDER, os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# --- Constants ---------------------------------------------------------------
FIXTURES = os.path.join(_TESTS_FOLDER, "fixtures", "source_samples")

NIFTY_1MIN = os.path.join(FIXTURES, "Nifty_1min_09Jan25-06Nov26.parquet")
BANKNIFTY_1MIN = os.path.join(FIXTURES,
                              "NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet")
BANKNIFTY_CSV = os.path.join(FIXTURES, "NSE_BANKNIFTY_1.csv")
CONCOR_TXT = os.path.join(FIXTURES, "CONCOR.txt")
CONCOR_PARQUET = os.path.join(FIXTURES, "CONCOR_daily 26Nov98-06Nov26.parquet")
INFY_PARQUET = os.path.join(FIXTURES, "INFY_daily 02Jan98-06Nov26.parquet")
NIFTYIT_TXT = os.path.join(FIXTURES, "Nifty IT.txt")
NIFTY_3MIN = os.path.join(FIXTURES, "Nifty_3min_02Jan23-30Oct26.parquet")
NIFTY_5MIN = os.path.join(FIXTURES, "Nifty_5min_02Jan23-30Oct26.parquet")
NIFTY_15MIN = os.path.join(FIXTURES, "Nifty_15min_02Jan23-30Oct26.parquet")
NIFTY_DAILY = os.path.join(FIXTURES, "Nifty_daily_02Jan23-30Oct26.parquet")
NIFTY_MONTHLY = os.path.join(FIXTURES, "Nifty_monthly_02Jan23-30Oct26.parquet")

# Annex B of the Consolidated Handover v1.0: the approved fingerprints.
ANNEX_B_SHA256 = {
    "Nifty_1min_09Jan25-06Nov26.parquet":
        "a4928e0d2f16bd6b6c8426297c2337e01e0291e859202c0abe3a372dd3472298",
    "NSE_BANKNIFTY, 1_1min 17Aug26-11Nov26.parquet":
        "117c901dfa123302be71633c878748ff145bd616174774341fca772701f32573",
    "NSE_BANKNIFTY_1.csv":
        "94d448669d38aa4387f4c227ade3a87ddb78fbef8fb9cc7cfaf13a50d85380e3",
    "CONCOR.txt":
        "add449571b6bce38d09fe0c339fee2a23c70cde34a88bd1bd6714d7fa5c9d67c",
    "CONCOR_daily 26Nov98-06Nov26.parquet":
        "e3398485035d9c1692561882feb3895bc9df95f826d4ac7a5d8a31bbe24609a8",
    "INFY_daily 02Jan98-06Nov26.parquet":
        "2bb57721041fad611ce3468517a1f70b9dd0c5e03aa262f6ab28b8cc971d2b01",
    "Nifty IT.txt":
        "7236641b5a04db8f815ecf303b9ac3a305e70e96010b6148d3f6305014eec6ef",
    "Nifty_3min_02Jan23-30Oct26.parquet":
        "31c9aba94c08a068a7bd650398010fb8f1154f2dcb88be3ed034a9b772afb2ab",
    "Nifty_5min_02Jan23-30Oct26.parquet":
        "d5acdcf83b15f43f4c3578c479a276f4574b71de98e8d625e4cab5b14113f040",
    "Nifty_15min_02Jan23-30Oct26.parquet":
        "91ed90d9fe028e94aaf596ea88f8648f44126bfcfc5bd7e20935a555dc231b84",
    "Nifty_daily_02Jan23-30Oct26.parquet":
        "192a5f03a9b85730b7449975c32be6ab968f178d7deea1cbacedc8a774e03018",
    "Nifty_monthly_02Jan23-30Oct26.parquet":
        "3322c27d5d3446502d9a07235ab198f415d655bfb796e34fa6a98331b02c4dbe",
}

INITIAL_LOAD_FILES = [NIFTY_1MIN, BANKNIFTY_1MIN, CONCOR_TXT, INFY_PARQUET,
                      NIFTYIT_TXT]

# --- Module state -------------------------------------------------------------
_shared = {"root": None, "result": None, "raw": {}}
_temp_folders = []


# --- Helpers -------------------------------------------------------------------
def fixtures_present():
    return all(os.path.exists(path) for path in INITIAL_LOAD_FILES)


def new_temp_folder(label):
    """A temporary folder that is removed when the test process exits."""
    folder = tempfile.mkdtemp(prefix="qmap_test_%s_" % label)
    _temp_folders.append(folder)
    return folder


@atexit.register
def _cleanup():
    for folder in _temp_folders:
        shutil.rmtree(folder, ignore_errors=True)
    if _shared["root"]:
        shutil.rmtree(_shared["root"], ignore_errors=True)


def shared_initial_load():
    """One initial load of the five inspected source files, built once and
    shared by every real-data test. Returns (data_root_path, result)."""
    if _shared["result"] is None:
        from qmap_database.maintenance import run_initial_load
        root = tempfile.mkdtemp(prefix="qmap_test_shared_root_")
        _shared["root"] = root
        _shared["result"] = run_initial_load(root, INITIAL_LOAD_FILES)
    return _shared["root"], _shared["result"]


def shared_catalogue():
    """A read-only catalogue connection onto the shared load."""
    from qmap_database.catalogue import Catalogue
    from qmap_database.storage import DataRoot
    root, _ = shared_initial_load()
    return Catalogue(DataRoot(root).catalogue_path, read_only=True), root


def read_raw(path):
    """Cache reader output for the big sample files across test modules."""
    if path not in _shared["raw"]:
        from qmap_database.readers import detect_and_read
        intraday = path in (NIFTY_1MIN, BANKNIFTY_1MIN, BANKNIFTY_CSV)
        _shared["raw"][path] = detect_and_read(path, intraday)
    return _shared["raw"][path]


def canonical_frame(root, dataset_id, file_safe_name):
    """All canonical rows of an instrument's active generation."""
    import glob
    import pandas as pd
    pattern = os.path.join(root, "market", dataset_id, file_safe_name,
                           "gen_*", "*.parquet")
    files = sorted(glob.glob(pattern))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
