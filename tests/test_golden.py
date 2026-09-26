"""Each screen must match a keyboard written out in tests/fixtures/."""

from __future__ import annotations

from datetime import date

from telegram_bot_calendar import (
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    WMonthTelegramCalendar,
    WYearTelegramCalendar,
)
from tests.conftest import TODAY, golden, rows


def test_year_picker() -> None:
    markup, step = DetailedTelegramCalendar(current_date=TODAY).build()
    assert step == "y"
    assert rows(markup) == golden("year_picker")


def test_month_picker() -> None:
    markup, step = WYearTelegramCalendar(current_date=TODAY).build()
    assert step == "m"
    assert rows(markup) == golden("month_picker")


def test_day_picker() -> None:
    markup, step = WMonthTelegramCalendar(current_date=TODAY).build()
    assert step == "d"
    assert rows(markup) == golden("day_picker")


def test_blocked_days_and_today() -> None:
    cal = WMonthTelegramCalendar(
        current_date=TODAY,
        min_date=date(2024, 6, 10),
        max_date=date(2024, 6, 25),
        blocked_day_button="·",
        mark_today=True,
    )
    assert rows(cal.build()[0]) == golden("blocked_today")


def test_range_summary_with_confirm() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY, presets=())
    result, markup, step = cal.process("cbcal_0_s_d_2024_6_20_r20240612")
    assert result is None and step == "summary"
    assert rows(markup) == golden("range_summary")


def test_quick_picks_and_cancel() -> None:
    markup, step = RangeTelegramCalendar(current_date=TODAY, cancel_button="Cancel").build()
    assert step == "d"
    assert rows(markup) == golden("quick_picks_cancel")
