from __future__ import annotations

import json
import sys
import types
from datetime import date
from typing import Any

import pytest

from telegram_bot_calendar import (
    CANCELLED,
    EXPIRED,
    LSTEP,
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    Style,
    WMonthTelegramCalendar,
    WYearTelegramCalendar,
    new_session,
)
from telegram_bot_calendar.core import CalendarBase
from tests.conftest import TODAY, rows


def labels(markup: Any) -> list[Any]:
    return [b["text"] for row in rows(markup) for b in row]


def data_for(markup: Any, text: Any) -> str:
    return str(next(b["callback_data"] for row in rows(markup) for b in row if b["text"] == text))


def test_full_walk_year_month_day() -> None:
    cal = DetailedTelegramCalendar(current_date=TODAY)
    markup: Any
    markup, step = cal.build()
    assert step is not None and LSTEP[step] == "year"
    _, markup, step = DetailedTelegramCalendar().process(data_for(markup, 2025))
    assert step == "m"
    _, markup, step = DetailedTelegramCalendar().process(data_for(markup, "Mar"))
    assert step == "d"
    result, markup, step = DetailedTelegramCalendar().process(data_for(markup, 9))
    assert result == date(2025, 3, 9) and markup is None and step == "d"


def test_navigation_and_back_buttons() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=TODAY).build()
    nav = rows(markup)[-2]
    _, prev, step = WMonthTelegramCalendar().process(nav[0]["callback_data"])
    assert step == "d" and "May 2024" in labels(prev)
    _, months, step = WMonthTelegramCalendar().process(nav[1]["callback_data"])
    assert step == "m" and "Jan" in labels(months)
    _, years, step = WMonthTelegramCalendar().process(rows(months)[-2][1]["callback_data"])
    assert step == "y" and 2024 in labels(years)
    assert WMonthTelegramCalendar().process(rows(years)[-2][1]["callback_data"]) == (None, None, None)
    _, nxt, _ = WYearTelegramCalendar().process(rows(years)[-2][2]["callback_data"])
    assert 2028 in labels(nxt)


def test_locale_and_additional_buttons() -> None:
    extra = [{"text": "a", "callback_data": "x"}] * 3
    markup, _ = WYearTelegramCalendar(current_date=TODAY, locale="ru", additional_buttons=extra).build()
    assert "июн" in labels(markup)
    assert rows(markup)[-2:] == [extra[:2], extra[2:]]
    with pytest.raises(ValueError, match="locale"):
        WMonthTelegramCalendar(locale="xx")


def test_limits_hide_arrows_and_block_forged_taps() -> None:
    cal = WMonthTelegramCalendar(current_date=TODAY, min_date=date(2024, 6, 10), max_date=date(2024, 6, 20))
    assert labels(cal.build()[0]).count("×") == 2
    assert cal.process("cbcal_0_s_d_2024_6_5") == (None, None, None)
    assert cal.process("cbcal_0_s_d_2024_6_12")[0] == date(2024, 6, 12)
    assert cal.process("cbcal_0_x_d_2024_6_12") == (None, None, None)
    assert cal.process("cbcal_0_s") == (None, None, None)
    assert cal.process("cbcal_0_k_d_2024_6_12") == (None, None, None)


def test_year_edges_do_not_overflow() -> None:
    markup, _ = DetailedTelegramCalendar(current_date=date(1, 1, 1)).build()
    assert labels(markup)[:4] == [1, 2, 3, 4]
    top = DetailedTelegramCalendar(current_date=date(2999, 12, 31))
    assert labels(top.build()[0])[-1] == "×"
    assert top.process("cbcal_0_g_y_9999_12_31")[2] == "y"


def test_cancel_and_session_expiry() -> None:
    s = new_session()
    cal = WMonthTelegramCalendar(current_date=TODAY, session=s, cancel_button="Cancel")
    markup, _ = cal.build()
    cancel = data_for(markup, "Cancel")
    assert cancel == f"cbcal_0_c_x{s}"
    assert cal.process(cancel) == (CANCELLED, None, None)
    assert cal.process(data_for(markup, 3))[0] == date(2024, 6, 3)
    assert WMonthTelegramCalendar(session="other").process(cancel) == (EXPIRED, None, None)
    assert repr(CANCELLED) == "CANCELLED"


def test_foreign_calendar_is_ignored() -> None:
    assert WMonthTelegramCalendar(calendar_id=2).process("cbcal_1_s_d_2024_6_1") == (None, None, None)
    check = WMonthTelegramCalendar.func(calendar_id=1)
    assert check(types.SimpleNamespace(data="cbcal_1_n"))
    assert not check(types.SimpleNamespace(data="cbcal_12_n"))
    assert WMonthTelegramCalendar.func(calendar_id=1, telethon=True)(b"cbcal_1_n")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"calendar_id": "a_b"},
        {"calendar_id": ""},
        {"calendar_id": "x" * 60},
        {"session": "bad token"},
        {"min_date": date(2024, 2, 1), "max_date": date(2024, 1, 1)},
    ],
)
def test_constructor_validation(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        WMonthTelegramCalendar(**kwargs)


def test_random_salt_and_style() -> None:
    cal = WMonthTelegramCalendar(current_date=TODAY, is_random=True, style=Style(prev="<", next=">"))
    markup, _ = cal.build()
    one = data_for(markup, 1)
    assert one.startswith("cbcal_0_s_d_2024_6_1_") and cal.process(one)[0] == date(2024, 6, 1)
    assert "<" in labels(markup) and ">" in labels(markup)


def test_base_is_abstract() -> None:
    with pytest.raises(NotImplementedError):
        CalendarBase().build()
    with pytest.raises(NotImplementedError):
        CalendarBase().process("cbcal_0_s_d_2024_1_1")


def test_range_flow() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY)
    markup: Any
    markup, _ = cal.build()
    _, markup, step = RangeTelegramCalendar().process(data_for(markup, "20"))
    assert step == "d" and ("20", "primary") in [(b["text"], b.get("style")) for r in rows(markup) for b in r]
    _, markup, step = RangeTelegramCalendar().process(data_for(markup, "12"))
    assert step == "summary" and "12 Jun – 20 Jun 2024" in labels(markup)
    result, _, step = RangeTelegramCalendar().process(data_for(markup, "✓ Confirm"))
    assert result == (date(2024, 6, 12), date(2024, 6, 20)) and step == "summary"
    _, markup, step = RangeTelegramCalendar().process(data_for(markup, "Change"))
    assert step == "d" and all(b.get("style") != "primary" or b["text"] == "15" for r in rows(markup) for b in r)


def test_range_month_screen_and_presets() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY, min_date=date(2024, 3, 5), max_date=date(2025, 2, 1))
    markup, _ = cal.build()
    _, months, step = cal.process(data_for(markup, "Jun 2024"))
    assert step == "m" and labels(months)[3:6] == [" ", " ", "Mar"]
    _, days, step = cal.process(data_for(months, "Apr"))
    assert step == "d" and "Apr 2024" in labels(days)
    _, nxt, _ = cal.process(data_for(months, "›"))
    assert "2025" in labels(nxt) and labels(nxt).count(" ") == 10
    picks = labels(markup)
    assert "Year to date" in picks and "Today" in picks
    assert data_for(markup, "Year to date") == "cbcal_0_s_d_2024_6_15_r20240305"
    assert cal.process("cbcal_0_s_d_2024_6_15_r20240101") == (None, None, None)
    assert cal.process("cbcal_0_n") == (None, None, None)
    assert cal.process("cbcal_0_c") == (CANCELLED, None, None)
    assert cal.process("cbcal_0_g") == (None, None, None)
    assert cal.process("cbcal_0_k_d_2024_6_15") == (None, None, None)


def test_range_presets_out_of_limits_are_dropped() -> None:
    cal = RangeTelegramCalendar(current_date=date(2020, 1, 1), max_date=date(2020, 1, 31), show_today=False)
    picks = labels(cal.build()[0])
    assert "This month" not in picks and "Today" not in picks
    assert cal.format_range(date(2019, 12, 30), date(2020, 1, 2)) == "30 Dec 2019 – 2 Jan 2020"


def test_telethon_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    made: list[tuple[str, str]] = []

    class Button:
        @staticmethod
        def inline(text: str, data: str) -> tuple[str, str]:
            made.append((text, data))
            return text, data

    monkeypatch.setitem(sys.modules, "telethon", types.SimpleNamespace(Button=Button))
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, telethon=True).build()
    assert isinstance(markup, list) and markup[1][5] == ("1", "cbcal_0_s_d_2024_6_1")
    extra = [["kept"]]
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, telethon=True, additional_buttons=extra).build()
    assert isinstance(markup, list) and markup[-1] == [["kept"]]


def test_telethon_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "telethon", None)
    with pytest.raises(ImportError, match="Telethon"):
        WMonthTelegramCalendar(telethon=True)


def test_markup_is_json_string() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=TODAY).build()
    assert isinstance(markup, str) and "inline_keyboard" in json.loads(markup)


def test_default_current_date_uses_frozen_today(monkeypatch: pytest.MonkeyPatch) -> None:
    from telegram_bot_calendar import core

    monkeypatch.setattr(core, "today", lambda: date(2020, 2, 10))
    assert "Feb 2020" in labels(RangeTelegramCalendar().build()[0])
    assert "cbcal_0_s_d_2020_2_10" in str(WMonthTelegramCalendar().build()[0])


def test_markers_are_typed_singletons() -> None:
    from telegram_bot_calendar.core import _Marker

    assert isinstance(CANCELLED, _Marker) and isinstance(EXPIRED, _Marker)
    assert (repr(CANCELLED), repr(EXPIRED)) == ("CANCELLED", "EXPIRED")
    with pytest.raises(TypeError):
        type("Sub", (_Marker,), {})


def test_markers_compare_by_identity() -> None:
    cal = WMonthTelegramCalendar(current_date=TODAY, cancel_button="Cancel", session="abc")
    markup, _ = cal.build()
    assert cal.process(data_for(markup, "Cancel"))[0] is CANCELLED
    other = WMonthTelegramCalendar(current_date=TODAY, session="xyz")
    assert other.process(data_for(markup, 1))[0] is EXPIRED


def _year_view(markup: Any) -> tuple[list[Any], dict[str, Any], dict[str, Any]]:
    r = [row for row in rows(markup) if row]
    return [b["text"] for row in r[:-1] for b in row], r[-1][0], r[-1][2]


def test_year_grid_clamps_to_max_date() -> None:
    cal = DetailedTelegramCalendar(current_date=date(2026, 6, 1), max_date=date(2026, 12, 31))
    years, prev, nxt = _year_view(cal.build()[0])
    assert years == [2023, 2024, 2025, 2026]
    assert prev == {"text": "<<", "callback_data": "cbcal_0_g_y_2022_6_1"}
    assert nxt["callback_data"] == "cbcal_0_n"


def test_year_grid_clamps_to_min_date() -> None:
    cal = DetailedTelegramCalendar(current_date=date(2020, 6, 1), min_date=date(2020, 1, 1))
    years, prev, nxt = _year_view(cal.build()[0])
    assert years == [2020, 2021, 2022, 2023]
    assert prev["callback_data"] == "cbcal_0_n"
    assert nxt["text"] == ">>"


def test_year_paging_never_blank() -> None:
    kw: dict[str, Any] = {"min_date": date(2015, 1, 1), "max_date": date(2026, 12, 31)}
    markup, _ = DetailedTelegramCalendar(current_date=date(2026, 6, 1), **kw).build()
    firsts = []
    for _ in range(5):
        years, prev, _ = _year_view(markup)
        assert " " not in years
        firsts.append(years[0])
        if prev["callback_data"] == "cbcal_0_n":
            break
        _, page, _ = DetailedTelegramCalendar(**kw).process(prev["callback_data"])
        assert page is not None
        markup = page
    assert firsts == [2023, 2021, 2017, 2015]
    _, nxt_markup, _ = DetailedTelegramCalendar(**kw).process(_year_view(markup)[2]["callback_data"])
    assert " " not in _year_view(nxt_markup)[0]


def test_year_grid_short_span_keeps_blanks() -> None:
    kw: dict[str, Any] = {"min_date": date(2025, 1, 1), "max_date": date(2026, 12, 31)}
    years, prev, nxt = _year_view(DetailedTelegramCalendar(current_date=date(2026, 6, 1), **kw).build()[0])
    assert years == [2025, 2026, " ", " "]
    assert prev["callback_data"] == nxt["callback_data"] == "cbcal_0_n"
