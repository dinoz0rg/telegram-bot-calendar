"""first_weekday rotates the weekday header and the day grid together."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from telegram_bot_calendar import RangeTelegramCalendar, WMonthTelegramCalendar
from tests.conftest import rows

FEB = date(2026, 2, 10)  # 1 Feb 2026 is a Sunday


def texts(row: list[dict[str, Any]]) -> list[str]:
    return [str(key["text"]) for key in row]


def test_sunday_start_month_starting_on_sunday() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=FEB, first_weekday=6).build()
    grid = rows(markup)
    assert texts(grid[0]) == ["S", "M", "T", "W", "T", "F", "S"]
    assert texts(grid[1]) == ["1", "2", "3", "4", "5", "6", "7"]


def test_monday_default_same_month() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=FEB).build()
    grid = rows(markup)
    assert texts(grid[0]) == ["M", "T", "W", "T", "F", "S", "S"]
    assert texts(grid[1])[-1] == "1"


def test_saturday_start() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=FEB, first_weekday=5).build()
    grid = rows(markup)
    assert texts(grid[0]) == ["S", "S", "M", "T", "W", "T", "F"]
    assert texts(grid[1])[:2] == [" ", "1"]


def test_range_sunday_start() -> None:
    markup, _ = RangeTelegramCalendar(current_date=FEB, first_weekday=6, locale="ru").build()
    grid = rows(markup)
    header = next(r for r in grid if len(r) == 7)
    assert texts(header) == ["В", "П", "В", "С", "Ч", "П", "С"]
    first_week = grid[grid.index(header) + 1]
    assert texts(first_week) == ["1", "2", "3", "4", "5", "6", "7"]


@pytest.mark.parametrize("bad", [-1, 7, True, "0", 1.0])
def test_first_weekday_validated(bad: Any) -> None:
    with pytest.raises(ValueError, match="first_weekday"):
        WMonthTelegramCalendar(first_weekday=bad)
