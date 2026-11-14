"""Exception classes for the Q-MAP Database subsystem.

The public interface exceptions follow document 03 section A6. The import-side
exceptions (FileImportError) are internal to the Data Manager: a reader or
validation raises one when a whole file must be refused, and maintenance
records the refusal as import_log.action = FAILED with the message.
"""


# --- Public interface exception hierarchy (document 03 A6) --------------------
class QMapDataError(Exception):
    """Base class for every Q-MAP data error."""


class UnknownInstrumentError(QMapDataError):
    """The requested instrument is not in the catalogue."""


class UnsupportedTimeframeError(QMapDataError):
    """The requested timeframe is not supported for the instrument."""


class InvalidRequestError(QMapDataError):
    """The request parameters are invalid (bad range, unknown field, ...)."""


class DatabaseUnavailableError(QMapDataError):
    """The catalogue cannot be opened, e.g. another program is writing."""


class DataIntegrityError(QMapDataError):
    """Stored data does not match the catalogue (fingerprints, keys, counts)."""


# --- Import-side exceptions (internal to the Data Manager) --------------------
class FileImportError(Exception):
    """A file-level import failure: the whole file is refused (V-FILE-01,
    V-SCH-01, V-TS-01, resolution test). The message is shown to the Owner
    verbatim, so it must name the file, the line or column, and the reason."""

    def __init__(self, message, check_code="V-FILE-01"):
        super().__init__(message)
        self.check_code = check_code
