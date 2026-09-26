"""Callback data: build and read ``cbcal_<id>_<action>_<step>_<Y>_<M>_<D>`` strings.

Optional tail tokens, in this order:

* ``r<YYYYMMDD>`` start of a date range,
* ``x<token>`` session token,
* ``<digits>`` random salt (ignored when read).
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import date

PREFIX = "cbcal"
LIMIT = 64
"""Telegram rejects callback data longer than 64 bytes."""

YEAR = "y"
MONTH = "m"
DAY = "d"
STEPS = (YEAR, MONTH, DAY)

SELECT = "s"
GOTO = "g"
NOTHING = "n"
CANCEL = "c"
CONFIRM = "k"
CHANGE = "r"
ACTIONS = (SELECT, GOTO, NOTHING, CANCEL, CONFIRM, CHANGE)

_TOKEN = re.compile(r"[A-Za-z0-9]{1,8}")
_ID = re.compile(r"[^_]+")


@dataclass(frozen=True)
class Payload:
    calendar_id: str
    action: str
    step: str | None = None
    day: date | None = None
    start: date | None = None
    session: str | None = None


def new_session() -> str:
    """A fresh random token for the ``session`` kwarg."""
    return secrets.token_hex(4)


def valid_session(token: str) -> bool:
    return _TOKEN.fullmatch(token) is not None


def valid_calendar_id(calendar_id: object) -> bool:
    return _ID.fullmatch(str(calendar_id)) is not None


def encode(p: Payload, salt: int | None = None) -> str:
    """Build callback data. Raises ValueError if it would exceed 64 bytes."""
    parts = [PREFIX, p.calendar_id, p.action]
    if p.action != NOTHING:
        if p.step is not None and p.day is not None:
            parts += [p.step, str(p.day.year), str(p.day.month), str(p.day.day)]
        if p.start is not None:
            parts.append(f"r{p.start.year:04d}{p.start.month:02d}{p.start.day:02d}")
        if p.session is not None:
            parts.append("x" + p.session)
    if salt is not None:
        parts.append(str(salt))
    data = "_".join(parts)
    if len(data.encode()) > LIMIT:
        raise ValueError(f"callback data is over {LIMIT} bytes: {data!r}")
    return data


def _text(data: object) -> str | None:
    if isinstance(data, bytes):
        try:
            return data.decode()
        except UnicodeDecodeError:
            return None
    return data if isinstance(data, str) else None


def is_calendar_callback(data: str | bytes | None, calendar_id: object = 0) -> bool:
    """True when ``data`` was made by the calendar with ``calendar_id``."""
    text = _text(data)
    if text is None:
        return False
    parts = text.split("_")
    return len(parts) >= 3 and parts[0] == PREFIX and parts[1] == str(calendar_id)


def _ymd(y: str, m: str, d: str) -> date | None:
    if not (y.isdigit() and m.isdigit() and d.isdigit()) or not y.isascii():
        return None
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def decode(data: object, calendar_id: object = 0) -> Payload | None:
    """Read callback data. Anything foreign or malformed gives None."""
    text = _text(data)
    if text is None or not is_calendar_callback(text, calendar_id):
        return None
    parts = text.split("_")
    action, rest = parts[2], parts[3:]
    if action not in ACTIONS:
        return None
    step: str | None = None
    day: date | None = None
    if len(rest) >= 4 and rest[0] in STEPS:
        day = _ymd(*rest[1:4])
        if day is None:
            return None
        step, rest = rest[0], rest[4:]
    start: date | None = None
    session: str | None = None
    for token in rest:
        if len(token) == 9 and token[0] == "r" and start is None:
            start = _ymd(token[1:5], token[5:7], token[7:9])
            if start is None:
                return None
        elif token[:1] == "x" and session is None and valid_session(token[1:]):
            session = token[1:]
        elif not (token.isascii() and token.isdigit()):
            return None
    return Payload(str(calendar_id), action, step, day, start, session)
