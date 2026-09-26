"""Pure date layout. Turns dates into slots; knows nothing about Telegram."""

from __future__ import annotations

import calendar
from datetime import date
from typing import Optional, TypeVar

_WEEK = calendar.Calendar(firstweekday=calendar.MONDAY)

Slot = Optional[date]
"""A date the user may pick, or None for a cell with nothing to pick."""


def month_length(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def add_months(d: date, months: int) -> date:
    """Shift ``d`` by whole months; the day is clamped to the target month's end.

    Raises OverflowError when the result leaves the ``date`` range.
    """
    index = d.year * 12 + (d.month - 1) + months
    year, month0 = divmod(index, 12)
    if not 1 <= year <= 9999:
        raise OverflowError("date out of range")
    return date(year, month0 + 1, min(d.day, month_length(year, month0 + 1)))


def try_add_months(d: date, months: int) -> date | None:
    try:
        return add_months(d, months)
    except OverflowError:
        return None


def first_of_month(d: date) -> date:
    return d.replace(day=1)


def last_of_month(d: date) -> date:
    return d.replace(day=month_length(d.year, d.month))


def day_weeks(year: int, month: int) -> list[list[int]]:
    """Weeks of the month, Monday first; 0 marks padding outside the month."""
    return _WEEK.monthdayscalendar(year, month)


def day_slots(year: int, month: int, lo: date, hi: date) -> list[list[Slot]]:
    """Rows of 7 slots; days outside ``[lo, hi]`` and padding are None."""
    return [
        [date(year, month, n) if n and lo <= date(year, month, n) <= hi else None for n in week]
        for week in day_weeks(year, month)
    ]


def month_slots(anchor: date, lo: date, hi: date) -> list[Slot]:
    """The 12 months of ``anchor.year``; each keeps ``anchor.day`` (clamped)."""
    out: list[Slot] = []
    for month in range(1, 13):
        d = date(anchor.year, month, min(anchor.day, month_length(anchor.year, month)))
        out.append(d if lo <= last_of_month(d) and first_of_month(d) <= hi else None)
    return out


def year_slots(anchor: date, offset: int, count: int, lo: date, hi: date) -> list[Slot]:
    """``count`` years from ``anchor.year + offset``; each keeps ``anchor``'s month and day.

    Years outside ``[lo, hi]`` or outside the ``date`` range are None.
    """
    out: list[Slot] = []
    for i in range(count):
        d = try_add_months(anchor, 12 * (offset + i))
        ok = d is not None and lo <= d.replace(month=12, day=31) and d.replace(month=1, day=1) <= hi
        out.append(d if ok else None)
    return out


T = TypeVar("T")


def chunk(items: list[T], size: int) -> list[list[T]]:
    """Split ``items`` into rows of ``size``; the last row may be shorter."""
    return [items[i : i + size] for i in range(0, len(items), size)]
