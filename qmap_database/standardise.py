"""Standardisation: timestamps, duplicates, record types, auction stamping
(document 02 v1.6, section 6.2; decisions D-08, D-09, D-10).

Standardisation converts a reader's raw frame into canonical records. It
classifies sessions and records, and stamps the closing auction, but it never
adjusts a price and never invents a record. Rows it cannot keep go to the
quarantine frame with a reason code; nothing is dropped silently.
"""

# --- Imports -----------------------------------------------------------------
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from . import session_rules as sr

# --- Constants ---------------------------------------------------------------
RECORD_CANDLE = "CANDLE"
RECORD_AUCTION_PHASE = "AUCTION_PHASE"
RECORD_CLOSING_AUCTION = "CLOSING_AUCTION"

FLAG_SUSPECT_FILL = "SUSPECT_FILL"
FLAG_OFF_TICK = "OFF_TICK_RULE_UNVERIFIED"
FLAG_SESSION_UNCONFIRMED = "SESSION_UNCONFIRMED"
FLAG_CAS_CANDIDATE = "CAS_CANDIDATE"
FLAG_SESSION_CLOSE_UNVERIFIED = "SESSION_CLOSE_UNVERIFIED"
FLAG_VOLUME_SEMANTICS = "VOLUME_SEMANTICS_UNVERIFIED"
FLAG_LARGE_GAP = "LARGE_GAP_UNVERIFIED"
FLAG_LEVEL_BREAK = "LEVEL_BREAK_UNVERIFIED"

REASON_BAD_TIMESTAMP = "BAD_TIMESTAMP"
REASON_DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"

_PRICE_COLUMNS = ["open", "high", "low", "close"]


# --- Result structures ----------------------------------------------------------
@dataclass
class StandardisedData:
    """Canonical records plus everything standardisation learned."""
    records: pd.DataFrame          # canonical rows with quality_flags as sets
    quarantine: pd.DataFrame       # original values + source_row + reason_code
    day_classes: dict = field(default_factory=dict)  # date -> DayClassification
    info_notes: list = field(default_factory=list)   # INFO messages
    duplicates_collapsed: int = 0


# --- Helpers ------------------------------------------------------------------
def _empty_quarantine(intraday):
    time_col = "ts" if intraday else "trade_date"
    return pd.DataFrame(columns=[time_col, "open", "high", "low", "close",
                                 "volume", "source_row", "reason_code"])


def _quarantine_rows(frame, mask, reason, store):
    """Move rows under `mask` into the quarantine store with a reason code."""
    taken = frame.loc[mask].copy()
    if len(taken) == 0:
        return frame, store
    taken["reason_code"] = reason
    keep_cols = [c for c in store.columns if c in taken.columns] + ["reason_code"]
    store = pd.concat([store, taken[list(dict.fromkeys(keep_cols))]],
                      ignore_index=True)
    return frame.loc[~mask].copy(), store


def _split_duplicates(frame, key_column, store, notes):
    """TC-07: exact duplicates collapse to one row with an INFO note;
    conflicting duplicates are all quarantined and the key reported missing."""
    collapsed = 0
    if not frame[key_column].duplicated().any():
        return frame, store, collapsed

    value_cols = _PRICE_COLUMNS + ["volume"]
    conflict_keys = []
    for key, group in frame[frame[key_column].duplicated(keep=False)].groupby(
            key_column):
        distinct = group[value_cols].drop_duplicates()
        if len(distinct) == 1:
            collapsed += len(group) - 1
        else:
            conflict_keys.append(key)

    if conflict_keys:
        mask = frame[key_column].isin(conflict_keys)
        frame, store = _quarantine_rows(frame, mask,
                                        REASON_DUPLICATE_CONFLICT, store)
    frame = frame.drop_duplicates(subset=[key_column], keep="first")
    if collapsed:
        notes.append("%d exact duplicate row(s) removed" % collapsed)
    return frame, store, collapsed


# --- Main logic: intraday -------------------------------------------------------
def standardise_intraday(raw_frame, calendar_entries=None,
                         owner_confirmations=None,
                         cas_rule_confirmed=False):
    """Standardise a 1-minute frame into canonical intraday records.

    calendar_entries: dict date -> session_rules.CalendarEntry (verified rows
    matter; unverified rows never confirm anything).
    owner_confirmations: dict date -> session_rules.SessionConfirmation.
    cas_rule_confirmed: True once the Owner has confirmed the instrument's CAS
    SESSION_PATTERN rule (D-06); until then CAS days stay candidates.
    """
    calendar_entries = calendar_entries or {}
    owner_confirmations = owner_confirmations or {}
    notes = []
    quarantine = _empty_quarantine(intraday=True)

    frame = raw_frame.copy().sort_values(["ts", "source_row"]).reset_index(drop=True)

    # Step 1 (V-TS-02): intraday timestamps must be whole minutes.
    off_minute = (frame["ts"].dt.second != 0) | (frame["ts"].dt.microsecond != 0)
    frame, quarantine = _quarantine_rows(frame, off_minute,
                                         REASON_BAD_TIMESTAMP, quarantine)

    # Step 2 (TC-07): duplicates.
    frame, quarantine, collapsed = _split_duplicates(frame, "ts", quarantine,
                                                     notes)
    frame = frame.reset_index(drop=True)

    # Steps 3-5: per-day session classification, record classification and the
    # closing-auction stamp. The observed first/last records are never taken
    # as proof of official session times (review item A3).
    frame["source_ts"] = frame["ts"]
    frame["record_type"] = RECORD_CANDLE
    frame["quality_flags"] = [set() for _ in range(len(frame))]

    day_classes = {}
    new_ts = frame["ts"].copy()
    dates = frame["ts"].dt.date

    for day, day_index in frame.groupby(dates).groups.items():
        day_index = list(day_index)
        day_rows = frame.loc[day_index]
        day_times = sorted(day_rows["ts"].dt.time.tolist())
        last_pos = day_rows["ts"].idxmax()
        classification = sr.classify_day(
            day, day_times, frame.loc[last_pos],
            calendar_entry=calendar_entries.get(day),
            owner_confirmation=owner_confirmations.get(day),
            instrument_has_cas_rule_confirmed=cas_rule_confirmed)
        day_classes[day] = classification

        status, stype = classification.session_status, classification.session_type

        if status == sr.STATUS_UNRECOGNISED:
            # Everything retained as CANDLE, flagged; nothing re-stamped or
            # labelled as an auction (02 section 6.2 step 4).
            for idx in day_index:
                frame.at[idx, "quality_flags"].add(FLAG_SESSION_UNCONFIRMED)
            continue

        is_cas_like = stype in (sr.TYPE_CAS, sr.TYPE_SPECIAL_CAS)
        is_special = stype in (sr.TYPE_SPECIAL, sr.TYPE_SPECIAL_CAS)

        if is_cas_like or is_special:
            window_end = classification.last_candle_time
            after_window = day_rows[day_rows["ts"].dt.time > window_end]
            if len(after_window) > 0:
                last_idx = after_window["ts"].idxmax()
                last_row = frame.loc[last_idx]
                is_flat = (last_row["open"] == last_row["high"]
                           == last_row["low"] == last_row["close"])
                if is_flat:
                    frame.at[last_idx, "record_type"] = RECORD_CLOSING_AUCTION
                    if classification.close_verified and classification.official_close:
                        new_ts.at[last_idx] = pd.Timestamp(datetime.combine(
                            day, classification.official_close))
                    else:
                        # No verified official close: the print keeps its
                        # source time, explicitly marked (D-09 step 5).
                        frame.at[last_idx, "quality_flags"].add(
                            FLAG_SESSION_CLOSE_UNVERIFIED)
                if is_cas_like:
                    phase_mask = ((after_window["ts"].dt.time
                                   == sr.AUCTION_PHASE_TIME)
                                  & (after_window.index != last_idx))
                    for idx in after_window.index[phase_mask]:
                        frame.at[idx, "record_type"] = RECORD_AUCTION_PHASE

        if status == sr.STATUS_CANDIDATE and stype == sr.TYPE_CAS:
            for idx in day_index:
                frame.at[idx, "quality_flags"].add(FLAG_CAS_CANDIDATE)

    frame["ts"] = new_ts.astype("datetime64[us]")
    frame["source_ts"] = frame["source_ts"].astype("datetime64[us]")
    frame = frame.sort_values("ts").reset_index(drop=True)

    return StandardisedData(records=frame, quarantine=quarantine,
                            day_classes=day_classes, info_notes=notes,
                            duplicates_collapsed=collapsed)


# --- Main logic: daily ----------------------------------------------------------
def standardise_daily(raw_frame):
    """Standardise a daily frame: duplicates only; there is no session
    classification for daily data (02 section 6.2, last paragraph)."""
    notes = []
    quarantine = _empty_quarantine(intraday=False)
    frame = (raw_frame.copy()
             .sort_values(["trade_date", "source_row"]).reset_index(drop=True))
    frame, quarantine, collapsed = _split_duplicates(frame, "trade_date",
                                                     quarantine, notes)
    frame = frame.reset_index(drop=True)
    frame["quality_flags"] = [set() for _ in range(len(frame))]
    return StandardisedData(records=frame, quarantine=quarantine,
                            info_notes=notes, duplicates_collapsed=collapsed)
