"""Locale tables: coverage, sizes, overrides and the generator."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from telegram_bot_calendar import (
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    WMonthTelegramCalendar,
    WYearTelegramCalendar,
)
from telegram_bot_calendar.locales import MONTH_NAMES, WEEKDAY_NAMES
from tests.conftest import TODAY, rows

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    "ar",
    "az",
    "bg",
    "bn",
    "ca",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "et",
    "fa",
    "fi",
    "fil",
    "fr",
    "he",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ka",
    "kk",
    "ko",
    "lt",
    "lv",
    "ms",
    "nb",
    "nl",
    "pl",
    "pt",
    "pt_BR",
    "ro",
    "sk",
    "sl",
    "sr",
    "sv",
    "sw",
    "ta",
    "th",
    "tr",
    "uk",
    "ur",
    "uz",
    "vi",
    "zh_Hans",
    "zh_Hant",
    "en",
    "eo",
    "ru",
)
PICKERS = (DetailedTelegramCalendar, WYearTelegramCalendar, WMonthTelegramCalendar, RangeTelegramCalendar)


def test_all_required_locales() -> None:
    assert set(REQUIRED) <= set(MONTH_NAMES)
    assert set(MONTH_NAMES) == set(WEEKDAY_NAMES)


def test_existing_locales_unchanged() -> None:
    assert MONTH_NAMES["en"] == ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    assert WEEKDAY_NAMES["en"] == ("M", "T", "W", "T", "F", "S", "S")
    assert MONTH_NAMES["eo"] == ("jan", "feb", "mar", "apr", "maj", "jun", "jul", "aŭg", "sep", "okt", "nov", "dec")
    assert WEEKDAY_NAMES["eo"] == ("L", "M", "M", "Ĵ", "V", "S", "D")
    assert MONTH_NAMES["ru"] == ("янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек")
    assert WEEKDAY_NAMES["ru"] == ("П", "В", "С", "Ч", "П", "С", "В")


@pytest.mark.parametrize("code", sorted(MONTH_NAMES))
def test_names_fit_buttons(code: str) -> None:
    months, days = MONTH_NAMES[code], WEEKDAY_NAMES[code]
    assert len(months) == 12 and len(days) == 7
    assert all(name.strip() and len(name) <= 12 for name in months)
    assert all(name.strip() and len(name) <= 4 for name in days)


def longest_id() -> str:
    n = 1
    while True:
        try:
            WMonthTelegramCalendar(calendar_id="x" * (n + 1), current_date=TODAY)
        except ValueError:
            return "x" * n
        n += 1


def callbacks(markup: Any) -> list[str]:
    return [key["callback_data"] for row in rows(markup) for key in row if "callback_data" in key]


@pytest.mark.parametrize("code", sorted(MONTH_NAMES))
def test_callbacks_fit_for_every_locale(code: str) -> None:
    cid = longest_id()
    for picker in PICKERS:
        markup, _ = picker(calendar_id=cid, current_date=TODAY, locale=code).build()
        data = callbacks(markup)
        assert data and all(len(d.encode()) <= 64 for d in data)
        assert json.dumps(markup, ensure_ascii=False)


def test_overrides() -> None:
    months = [f"M{i}" for i in range(1, 13)]
    days = list("1234567")
    markup, _ = WYearTelegramCalendar(current_date=TODAY, month_names=months).build()
    assert "M6" in [key["text"] for row in rows(markup) for key in row]
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, weekday_names=days, first_weekday=6).build()
    assert [key["text"] for key in rows(markup)[0]] == list("7123456")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"month_names": ["a"] * 11},
        {"month_names": ["a"] * 11 + [""]},
        {"month_names": "abcdefghijkl"},
        {"weekday_names": ["a"] * 8},
        {"weekday_names": ["a"] * 6 + [1]},
    ],
)
def test_overrides_validated(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="_names"):
        WMonthTelegramCalendar(current_date=date(2024, 1, 1), **kwargs)


def test_committed_table_matches_generator() -> None:
    pytest.importorskip("babel")
    spec = importlib.util.spec_from_file_location("gen_locales", ROOT / "scripts" / "gen_locales.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    committed = (ROOT / "src" / "telegram_bot_calendar" / "_locale_data.py").read_text(encoding="utf-8")
    assert module.render() == committed
