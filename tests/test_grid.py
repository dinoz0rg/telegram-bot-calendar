from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from telegram_bot_calendar import grid

months = st.tuples(st.integers(1, 9999), st.integers(1, 12))
dates = st.dates(date(1, 1, 1), date(9999, 12, 31))


@given(months, dates, dates)
def test_day_grid_invariants(ym: tuple[int, int], a: date, b: date) -> None:
    lo, hi = min(a, b), max(a, b)
    year, month = ym
    slots = grid.day_slots(year, month, lo, hi)
    assert all(len(row) == 7 for row in slots)
    flat = [d for row in slots for d in row if d is not None]
    expected = [
        date(year, month, n) for n in range(1, grid.month_length(year, month) + 1) if lo <= date(year, month, n) <= hi
    ]
    assert flat == expected
    assert len(set(flat)) == len(flat)
    for row in grid.day_weeks(year, month):
        assert len(row) == 7


@given(dates, st.integers(-2000, 2000))
def test_add_months(d: date, n: int) -> None:
    try:
        out = grid.add_months(d, n)
    except OverflowError:
        return
    assert (out.year * 12 + out.month) - (d.year * 12 + d.month) == n
    assert out.day == min(d.day, grid.month_length(out.year, out.month))


def test_add_months_clamps_and_overflows() -> None:
    assert grid.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    with pytest.raises(OverflowError):
        grid.add_months(date(9999, 12, 1), 1)
    assert grid.try_add_months(date(1, 1, 1), -1) is None


def test_month_and_year_slots_respect_limits() -> None:
    lo, hi = date(2024, 3, 15), date(2025, 2, 1)
    months = grid.month_slots(date(2024, 1, 31), lo, hi)
    assert months[:2] == [None, None] and months[2] == date(2024, 3, 31) and months[1] is None
    years = grid.year_slots(date(2024, 6, 1), -1, 4, lo, hi)
    assert years == [None, date(2024, 6, 1), date(2025, 6, 1), None]
    assert grid.year_slots(date(1, 3, 1), -1, 2, date(1, 1, 1), hi) == [None, date(1, 3, 1)]
    assert grid.chunk([1, 2, 3], 2) == [[1, 2], [3]]
