"""Session classification and calendar rules (document 02 v1.6, sections 5.5,
6.2 and 8).

Three separate concerns, kept apart deliberately (review item A3):
- the observed day shape (what the records look like);
- the session status and type (assigned from authoritative sources only);
- completeness expectations (derived from the status, never from the records).

A day becomes SPECIAL or SPECIAL_CAS only through a verified official calendar
entry or an explicit Owner confirmation. An observed shape never creates one.
"""

# --- Imports -----------------------------------------------------------------
import csv
from dataclasses import dataclass
from datetime import date, time, datetime, timedelta

from .errors import FileImportError

# --- Constants ---------------------------------------------------------------
SHAPE_REGULAR = "REGULAR_SHAPE"
SHAPE_CAS = "CAS_SHAPE"
SHAPE_OTHER = "OTHER"

STATUS_CONFIRMED_OFFICIAL = "CONFIRMED_OFFICIAL"
STATUS_CONFIRMED_BY_OWNER = "CONFIRMED_BY_OWNER"
STATUS_CANDIDATE = "CANDIDATE"
STATUS_UNRECOGNISED = "UNRECOGNISED_SESSION_SHAPE"

TYPE_REGULAR = "REGULAR"
TYPE_CAS = "CAS"
TYPE_SPECIAL = "SPECIAL"
TYPE_SPECIAL_CAS = "SPECIAL_CAS"

SESSION_OPEN = time(9, 15)
REGULAR_LAST_CANDLE = time(15, 29)
CAS_LAST_CANDLE = time(15, 14)
AUCTION_PHASE_TIME = time(15, 15)
REGULAR_CLOSE = time(15, 30)
# CAS applies from this date for CAS instruments (D-04).
CAS_START_DATE = date(2026, 8, 3)
# The quiet window of a CAS day: no record between 15:16 and 15:27 inclusive.
CAS_QUIET_FROM = time(15, 16)
CAS_QUIET_TO = time(15, 27)

EXPECTED_REGULAR_CANDLES = 375
EXPECTED_CAS_CANDLES = 360

BASIS_CONFIRMED = "CONFIRMED_SESSION"
BASIS_CANDIDATE = "CANDIDATE_SESSION"
BASIS_PROVISIONAL = "PROVISIONAL_REGULAR_ASSUMPTION"

CAL_SOURCE_DERIVED = "DERIVED_FROM_DATA"
CAL_SOURCE_REFERENCE_UNCONFIRMED = "REFERENCE_FILE_UNCONFIRMED"
CAL_SOURCE_OFFICIAL = "OFFICIAL_REFERENCE"
CAL_SOURCE_USER = "USER"

DAY_TRADING = "TRADING"
DAY_HOLIDAY = "HOLIDAY"
DAY_SPECIAL = "SPECIAL"


# --- Data structures ----------------------------------------------------------
@dataclass
class CalendarEntry:
    """One market_calendar row as classification needs it."""
    trade_date: date
    day_type: str
    session_open: time
    session_close: time
    description: str
    source: str
    verified: bool


@dataclass
class SessionConfirmation:
    """An Owner confirmation of one day for one instrument (calendar USER
    entry, or an instrument SESSION_PATTERN rule result for that date)."""
    session_type: str          # REGULAR / CAS / SPECIAL / SPECIAL_CAS
    session_open: time = None  # continuous-trading start (special sessions)
    session_close: time = None # official close where known


@dataclass
class DayClassification:
    trade_date: date
    observed_shape: str
    session_status: str
    session_type: str          # None while unrecognised
    session_open: time         # continuous window actually applied
    last_candle_time: time     # end of the continuous window applied
    official_close: time       # close used for the auction stamp, or None
    # True only when the close may be stamped without SESSION_CLOSE_UNVERIFIED:
    # a verified official calendar close, or the 15:30 standard of a regular
    # trading day under the candidate/confirmed CAS rule (D-04, D-09).
    close_verified: bool
    expected_basis: str
    is_weekend: bool


# --- Helpers ------------------------------------------------------------------
def _is_flat(row):
    """A flat print has one price on all four fields."""
    return row["open"] == row["high"] == row["low"] == row["close"]


def observe_day_shape(day_times, last_row):
    """Classify the observed shape of one day from its record times.

    `day_times` is the sorted list of datetime.time values; `last_row` is the
    final record (for the flat-print test). Missing minutes inside the window
    do not change the shape: TC-26 forbids rejecting 1-minute data for gaps,
    and completeness reports them separately.
    """
    first, last = day_times[0], day_times[-1]

    # The CAS signature is tested first: a raw vendor CAS day whose final
    # print lands at 15:29 would otherwise look like a regular day, although
    # its 15:15-15:28 region is empty rather than continuously traded.
    has_1514 = CAS_LAST_CANDLE in day_times
    quiet = not any(CAS_QUIET_FROM <= t <= CAS_QUIET_TO for t in day_times)
    if (first == SESSION_OPEN and has_1514 and quiet
            and last >= AUCTION_PHASE_TIME and _is_flat(last_row)):
        return SHAPE_CAS

    if (first == SESSION_OPEN and last == REGULAR_LAST_CANDLE
            and all(SESSION_OPEN <= t <= REGULAR_LAST_CANDLE for t in day_times)):
        return SHAPE_REGULAR

    return SHAPE_OTHER


# --- Main logic: session status assignment --------------------------------------
def classify_day(trade_date, day_times, last_row, calendar_entry=None,
                 owner_confirmation=None, instrument_has_cas_rule_confirmed=False):
    """Assign observed shape, session status and type for one instrument-day.

    Authority order: verified official calendar entry, then Owner confirmation,
    then candidate rules, then UNRECOGNISED_SESSION_SHAPE. Weekends and OTHER
    shapes are never candidates (document 02 section 6.2).
    """
    shape = observe_day_shape(day_times, last_row)
    weekend = trade_date.weekday() >= 5

    # 1. Verified official calendar entry.
    if calendar_entry is not None and calendar_entry.verified \
            and calendar_entry.source == CAL_SOURCE_OFFICIAL:
        return _classify_confirmed(trade_date, shape, weekend,
                                   STATUS_CONFIRMED_OFFICIAL, calendar_entry,
                                   instrument_has_cas_rule_confirmed)

    # 2. Owner confirmation for this instrument and day.
    if owner_confirmation is not None:
        session_open = owner_confirmation.session_open or SESSION_OPEN
        close = owner_confirmation.session_close
        session_type = owner_confirmation.session_type
        if session_type in (TYPE_CAS, TYPE_SPECIAL_CAS):
            last_candle = (_minus_minutes(close, 16) if close
                           else CAS_LAST_CANDLE)
        else:
            last_candle = (_minus_minutes(close, 1) if close
                           else REGULAR_LAST_CANDLE)
        if session_type in (TYPE_SPECIAL, TYPE_SPECIAL_CAS):
            # An Owner-confirmed special session has no *official* close, so
            # the closing print keeps its source time and the flag
            # SESSION_CLOSE_UNVERIFIED (D-09 step 5; T-SES-04b, T-SES-05b).
            close_for_stamp, close_verified = None, False
        else:
            close_for_stamp, close_verified = (close or REGULAR_CLOSE), True
        return DayClassification(
            trade_date, shape, STATUS_CONFIRMED_BY_OWNER, session_type,
            session_open, last_candle, close_for_stamp, close_verified,
            BASIS_CONFIRMED, weekend)

    # 3. Candidates: weekdays only. A weekend shape never confirms anything.
    if not weekend:
        if shape == SHAPE_REGULAR:
            return DayClassification(trade_date, shape, STATUS_CANDIDATE,
                                     TYPE_REGULAR, SESSION_OPEN,
                                     REGULAR_LAST_CANDLE, REGULAR_CLOSE, True,
                                     BASIS_CANDIDATE, weekend)
        if shape == SHAPE_CAS and trade_date >= CAS_START_DATE:
            if instrument_has_cas_rule_confirmed:
                # The Owner has confirmed the instrument's CAS rule (D-06):
                # CAS-shaped weekdays stop being candidates.
                return DayClassification(
                    trade_date, shape, STATUS_CONFIRMED_BY_OWNER, TYPE_CAS,
                    SESSION_OPEN, CAS_LAST_CANDLE, REGULAR_CLOSE, True,
                    BASIS_CONFIRMED, weekend)
            return DayClassification(trade_date, shape, STATUS_CANDIDATE,
                                     TYPE_CAS, SESSION_OPEN, CAS_LAST_CANDLE,
                                     REGULAR_CLOSE, True,
                                     BASIS_CANDIDATE, weekend)

    # 4. Everything else is unrecognised. The provisional window is the
    # regular session 09:15-15:29 (S-1): used for expected units only, and for
    # a CAS-candidate instrument it stays 09:15-15:29 until a CAS rule is
    # confirmed (E-08).
    return DayClassification(trade_date, shape, STATUS_UNRECOGNISED, None,
                             SESSION_OPEN, REGULAR_LAST_CANDLE, None, False,
                             BASIS_PROVISIONAL, weekend)


def _classify_confirmed(trade_date, shape, weekend, status, entry,
                        cas_rule_confirmed):
    """Session type and windows from a verified calendar entry (section 5.5)."""
    session_open = entry.session_open or SESSION_OPEN
    session_close = entry.session_close or REGULAR_CLOSE
    special = entry.day_type == DAY_SPECIAL
    # Under a confirmed CAS rule, continuous trading ends 15 minutes before
    # the official close; the last candle starts one minute before that.
    if cas_rule_confirmed and trade_date >= CAS_START_DATE:
        session_type = TYPE_SPECIAL_CAS if special else TYPE_CAS
        last_candle = _minus_minutes(session_close, 16)
    else:
        session_type = TYPE_SPECIAL if special else TYPE_REGULAR
        last_candle = _minus_minutes(session_close, 1)
    return DayClassification(trade_date, shape, status, session_type,
                             session_open, last_candle, session_close, True,
                             BASIS_CONFIRMED, weekend)


def _minus_minutes(t, minutes):
    """Subtract minutes from a time-of-day value."""
    anchor = datetime(2000, 1, 1, t.hour, t.minute)
    moved = anchor - timedelta(minutes=minutes)
    return time(moved.hour, moved.minute)


def expected_minutes(classification):
    """Expected continuous-session candle count for a classified day."""
    start = classification.session_open
    end = classification.last_candle_time
    start_dt = datetime(2000, 1, 1, start.hour, start.minute)
    end_dt = datetime(2000, 1, 1, end.hour, end.minute)
    return int((end_dt - start_dt).total_seconds() // 60) + 1


# --- Main logic: derived calendar (section 8) -----------------------------------
def derive_calendar(dates_by_instrument):
    """Derive unverified calendar rows from the loaded data.

    A weekday with no data in any instrument whose coverage spans it is a
    candidate holiday; a weekend day with data anywhere is a derived SPECIAL
    row. Both carry source DERIVED_FROM_DATA and verified = false, and they
    never confirm a session (G-02).
    """
    ranges = {}
    all_dates = set()
    for instrument_id, dates in dates_by_instrument.items():
        if not dates:
            continue
        ranges[instrument_id] = (min(dates), max(dates))
        all_dates.update(dates)
    if not ranges:
        return []

    overall_first = min(first for first, _ in ranges.values())
    overall_last = max(last for _, last in ranges.values())

    rows = []
    current = overall_first
    one_day = timedelta(days=1)
    while current <= overall_last:
        covering = [iid for iid, (first, last) in ranges.items()
                    if first <= current <= last]
        has_data = current in all_dates
        if current.weekday() < 5:
            if covering and not has_data:
                rows.append(CalendarEntry(current, DAY_HOLIDAY, None, None,
                                          "derived: no data in any instrument",
                                          CAL_SOURCE_DERIVED, False))
        else:
            if has_data:
                rows.append(CalendarEntry(current, DAY_SPECIAL, None, None,
                                          "derived: weekend day with data",
                                          CAL_SOURCE_DERIVED, False))
        current += one_day
    return rows


# --- Main logic: official calendar file (G-02, section 5.5) ---------------------
def read_official_calendar_file(path):
    """Parse reference\\nse_market_calendar.csv. Importing never, by itself,
    makes the rows official: the caller stores them as
    REFERENCE_FILE_UNCONFIRMED until the Owner records provenance.

    A malformed date or time, an unknown day_type, a SPECIAL row without
    times, or a duplicated date is a file-level ERROR (T-CAL-02)."""
    rows = []
    seen_dates = set()
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"trade_date", "day_type"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise FileImportError(
                "calendar file must have the columns trade_date and day_type",
                check_code="V-FILE-01")
        for line_no, record in enumerate(reader, start=2):
            trade_date = _parse_calendar_date(record.get("trade_date", ""), line_no)
            if trade_date in seen_dates:
                raise FileImportError(
                    "calendar file line %d: date %s appears twice"
                    % (line_no, trade_date), check_code="V-FILE-01")
            seen_dates.add(trade_date)
            day_type = (record.get("day_type") or "").strip().upper()
            if day_type not in (DAY_TRADING, DAY_HOLIDAY, DAY_SPECIAL):
                raise FileImportError(
                    "calendar file line %d: unknown day_type '%s'"
                    % (line_no, record.get("day_type")), check_code="V-FILE-01")
            session_open = _parse_calendar_time(record.get("session_open"), line_no)
            session_close = _parse_calendar_time(record.get("session_close"), line_no)
            if day_type == DAY_SPECIAL and (session_open is None
                                            or session_close is None):
                raise FileImportError(
                    "calendar file line %d: a SPECIAL row needs session_open "
                    "and session_close" % line_no, check_code="V-FILE-01")
            if day_type == DAY_HOLIDAY and (session_open or session_close):
                raise FileImportError(
                    "calendar file line %d: a HOLIDAY row must not carry "
                    "session times" % line_no, check_code="V-FILE-01")
            rows.append(CalendarEntry(trade_date, day_type, session_open,
                                      session_close,
                                      (record.get("description") or "").strip(),
                                      CAL_SOURCE_REFERENCE_UNCONFIRMED, False))
    return rows


def _parse_calendar_date(text, line_no):
    """YYYY-MM-DD only; two-digit years are ambiguous back to 1998."""
    text = (text or "").strip()
    parts = text.split("-")
    if len(parts) != 3 or len(parts[0]) != 4:
        raise FileImportError(
            "calendar file line %d: '%s' is not a YYYY-MM-DD date"
            % (line_no, text), check_code="V-FILE-01")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        raise FileImportError(
            "calendar file line %d: invalid date '%s'" % (line_no, text),
            check_code="V-FILE-01")


# --- Main logic: Owner session confirmations stored as instrument rules ---------
# The Owner's answers to the confirmation lists are stored as instrument_rule
# rows (SESSION_PATTERN, OWNER_CONFIRMED) per 02 section 6.2. The rule value
# encodes the confirmed pattern:
#   "CAS"                      - the blanket CAS rule for the instrument
#   "SPECIAL|13:45|14:45"      - one special session with its times
#   "SPECIAL_CAS|14:20|"       - one CAS-style special session (close unknown)
def encode_session_confirmation(session_type, session_open=None,
                                session_close=None):
    if session_type == TYPE_CAS:
        return TYPE_CAS
    open_text = session_open.strftime("%H:%M") if session_open else ""
    close_text = session_close.strftime("%H:%M") if session_close else ""
    return "%s|%s|%s" % (session_type, open_text, close_text)


def decode_session_confirmation(value):
    """Return a SessionConfirmation for a per-day rule value, or None for the
    blanket CAS rule (which is handled through cas_rule_confirmed)."""
    if value == TYPE_CAS:
        return None
    parts = value.split("|")
    session_type = parts[0]
    def _time(text):
        if not text:
            return None
        hour, minute = text.split(":")
        return time(int(hour), int(minute))
    return SessionConfirmation(session_type,
                               _time(parts[1] if len(parts) > 1 else ""),
                               _time(parts[2] if len(parts) > 2 else ""))


def _parse_calendar_time(text, line_no):
    """HH:MM IST, or None when blank."""
    text = (text or "").strip()
    if not text:
        return None
    parts = text.split(":")
    try:
        if len(parts) != 2:
            raise ValueError("expected HH:MM")
        return time(int(parts[0]), int(parts[1]))
    except ValueError:
        raise FileImportError(
            "calendar file line %d: invalid time '%s' (expected HH:MM)"
            % (line_no, text), check_code="V-FILE-01")
