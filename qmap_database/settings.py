"""Read and write the local user settings file (config/settings.json).

Settings are user-editable configuration inputs (the data root path and the
folders offered again at the next update), not database state (document 02
section 5.1). The data root itself must lie outside the repository.
"""

# --- Imports -----------------------------------------------------------------
import json
import os

# --- Constants ---------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CONFIG_FOLDER = os.path.join(_REPO_ROOT, "config")
SETTINGS_PATH = os.path.join(CONFIG_FOLDER, "settings.json")

DEFAULT_SETTINGS = {
    "data_root": "",
    "last_source_files": [],
    "last_source_folders": [],
}


# --- Main logic ---------------------------------------------------------------
def load_settings(path=SETTINGS_PATH):
    """Return the saved settings, falling back to defaults for missing keys.

    An unreadable or corrupt file is reported by returning defaults with the
    problem noted, never by crashing the application at start-up."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        if isinstance(stored, dict):
            settings.update(stored)
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        settings["_load_error"] = "settings.json could not be read: %s" % exc
    return settings


def save_settings(settings, path=SETTINGS_PATH):
    """Write settings to disk, creating the config folder when needed."""
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    to_store = {key: value for key, value in settings.items()
                if not key.startswith("_")}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(to_store, handle, indent=2)
