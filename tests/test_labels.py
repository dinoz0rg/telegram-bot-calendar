"""Locale-correct month/year labels, Buddhist era, RTL and the month_year_format override."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from telegram_bot_calendar import (
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    WMonthTelegramCalendar,
    WYearTelegramCalendar,
)
from telegram_bot_calendar.locales import MONTH_NAMES
from tests.conftest import TODAY, rows

D = date(2026, 5, 3)


def texts(markup: Any) -> list[list[str]]:
    return [[str(key["text"]) for key in row] for row in rows(markup) if row]


def title(markup: Any) -> str:
    return texts(markup)[-1][1]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("ja", "2026年5月"),
        ("zh_Hans", "2026年5月"),
        ("zh_Hant", "2026年5月"),
        ("ko", "2026년 5월"),
        ("hu", "2026. máj."),
        ("lt", f"{MONTH_NAMES['lt'][4]} 2026"),
        ("de", "Mai 2026"),
        ("ru", "май 2026"),
        ("en", "May 2026"),
    ],
)
def test_month_year_titles(code: str, expected: str) -> None:
    markup, _ = WMonthTelegramCalendar(current_date=D, locale=code).build()
    assert title(markup) == expected
    markup, _ = RangeTelegramCalendar(current_date=D, locale=code).build()
    assert texts(markup)[0][1] == expected


def test_year_labels() -> None:
    markup, _ = DetailedTelegramCalendar(current_date=D, locale="ja").build()
    assert texts(markup)[0] == ["2025年", "2026年"]
    markup, _ = WYearTelegramCalendar(current_date=D, locale="ko").build()
    assert title(markup) == "2026년"
    cal = RangeTelegramCalendar(current_date=D, locale="ja")
    _, screen, _ = cal.process("cbcal_0_g_m_2026_5_1")
    assert texts(screen)[0][1] == "2026年"


def test_range_summary_order() -> None:
    ja = RangeTelegramCalendar(locale="ja")
    assert ja.format_range(date(2026, 5, 3), date(2026, 5, 9)) == "5月3日 – 2026年5月9日"
    assert RangeTelegramCalendar(locale="de").format_range(date(2025, 5, 3), date(2026, 5, 9)) == (
        "3. Mai 2025 – 9. Mai 2026"
    )
    assert RangeTelegramCalendar(locale="ru").format_range(date(2026, 5, 3), date(2026, 5, 9)) == "3 май – 9 май 2026"


def test_default_output_unchanged() -> None:
    markup, _ = DetailedTelegramCalendar(current_date=TODAY).build()
    assert rows(markup)[0][0]["text"] == 2023  # still an int in the JSON


def test_buddhist_era() -> None:
    cal = WMonthTelegramCalendar(current_date=D, locale="th", buddhist_era=True)
    markup, _ = cal.build()
    assert title(markup).endswith("2569")
    assert "_2026_" in rows(markup)[-2][1]["callback_data"]
    result, _, _ = cal.process("cbcal_0_s_d_2026_5_3")
    assert result == date(2026, 5, 3)
    markup, _ = DetailedTelegramCalendar(current_date=D, locale="th", buddhist_era=True).build()
    assert texts(markup)[0] == ["2568", "2569"]
    rc = RangeTelegramCalendar(current_date=D, locale="th", buddhist_era=True)
    assert rc.format_range(date(2026, 5, 3), date(2026, 5, 9)).endswith("2569")
    assert texts(rc.build()[0])[0][1].endswith("2569")


def test_rtl() -> None:
    plain = texts(WMonthTelegramCalendar(current_date=D, locale="ar").build()[0])
    rtl = texts(WMonthTelegramCalendar(current_date=D, locale="ar", rtl=True).build()[0])
    assert rtl == [row[::-1] for row in plain]
    assert rtl[-1][-1] == "<<"
    months = texts(WYearTelegramCalendar(current_date=D, locale="ar", rtl=True).build()[0])
    assert months[0][0] == MONTH_NAMES["ar"][2]
    rng = texts(RangeTelegramCalendar(current_date=D, locale="ar", rtl=True).build()[0])
    assert rng[0][-1] == "‹"


def test_month_year_format_override() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=D, locale="ja", month_year_format="{year}/{month}").build()
    assert title(markup) == "2026/5月"
    months = [f"M{i}" for i in range(1, 13)]
    markup, _ = RangeTelegramCalendar(current_date=D, month_names=months, month_year_format="{month}-{year}").build()
    assert texts(markup)[0][1] == "M5-2026"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"buddhist_era": 1}, "buddhist_era"),
        ({"rtl": "yes"}, "rtl"),
        ({"month_year_format": "{month}"}, "month_year_format"),
        ({"month_year_format": 5}, "month_year_format"),
    ],
)
def test_new_options_validated(kwargs: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        WMonthTelegramCalendar(current_date=D, **kwargs)
