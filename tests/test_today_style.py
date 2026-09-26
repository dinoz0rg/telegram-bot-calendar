"""Today's button uses the Bot API ``style`` field; everything else is unchanged."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

import pytest

from telegram_bot_calendar import (
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    Style,
    WMonthTelegramCalendar,
)
from telegram_bot_calendar.style import RANGE_STYLE
from tests.conftest import TODAY, rows


def styled(markup: Any) -> list[dict[str, Any]]:
    return [b for row in rows(markup) for b in row if "style" in b]


def test_wmonth_today_is_primary() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, mark_today=True).build()
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("15", "primary")]
    assert "•" not in markup


def test_detailed_day_view_today_is_primary() -> None:
    cal = DetailedTelegramCalendar(current_date=TODAY, mark_today=True)
    markup = cal.process("cbcal_0_s_m_2024_6_1")[1]
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("15", "primary")]


def test_no_style_when_mark_today_off() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=TODAY).build()
    assert '"style"' not in markup
    markup, _ = RangeTelegramCalendar(current_date=TODAY, mark_today=False).build()
    assert '"style"' not in markup


def test_range_selected_today_keeps_marker() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY, presets=())
    markup = cal.process("cbcal_0_s_d_2024_6_15")[1]
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("15", "primary")]


@pytest.mark.parametrize("value", ["success", "danger"])
def test_other_styles(value: str) -> None:
    cal = WMonthTelegramCalendar(current_date=TODAY, mark_today=True, style=Style(today_style=value))
    assert [b["style"] for b in styled(cal.build()[0])] == [value]


def test_old_dot_look() -> None:
    cal = WMonthTelegramCalendar(current_date=TODAY, mark_today=True, style=Style(today="•{day}", today_style=None))
    markup, _ = cal.build()
    assert '"style"' not in markup
    assert any(b["text"] == "•15" for row in rows(markup) for b in row)


@pytest.mark.parametrize("value", ["blue", "", 5, "Primary"])
def test_bad_today_style(value: Any) -> None:
    with pytest.raises(ValueError, match="today_style"):
        WMonthTelegramCalendar(style=Style(today_style=value))


def test_range_style_defaults() -> None:
    assert RANGE_STYLE.today == "{day}"
    assert RANGE_STYLE.today_style == "primary"


def test_telethon_keeps_a_visible_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    from telegram_bot_calendar import render

    class Button:
        @staticmethod
        def inline(text: str, data: str) -> tuple[str, str]:
            return text, data

    monkeypatch.setattr(render, "telethon_button", lambda: Button)
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, mark_today=True, telethon=True).build()
    texts = [button[0] for row in markup for button in row]
    assert "•15" in texts and "15" not in texts


def test_callback_data_unchanged() -> None:
    on = rows(WMonthTelegramCalendar(current_date=TODAY, mark_today=True).build()[0])
    off = rows(WMonthTelegramCalendar(current_date=TODAY).build()[0])
    assert [[b["callback_data"] for b in r] for r in on] == [[b["callback_data"] for b in r] for r in off]
    assert date(2024, 6, 15) == TODAY


def test_style_positional_fields_unchanged() -> None:
    fields = list(Style.__dataclass_fields__)
    assert fields[-1] == "confirm_style"
    assert fields.index("today") == 8


def test_rtl_keeps_style_on_today() -> None:
    markup, _ = WMonthTelegramCalendar(current_date=TODAY, mark_today=True, rtl=True).build()
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("15", "primary")]


def test_range_span_is_one_solid_bar() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY, presets=(), style=replace(RANGE_STYLE, today_style="danger"))
    markup = cal.process("cbcal_0_s_d_2024_6_20_r20240612")[1]
    days = [(b["text"], b.get("style")) for b in styled(markup) if b["text"].isdigit()]
    assert days == [(str(n), "primary") for n in range(12, 21)]
    texts = [str(b["text"]) for row in rows(markup) for b in row]
    assert not any("[" in t or "·" in t for t in texts)


def test_range_confirm_green_change_plain() -> None:
    markup = RangeTelegramCalendar(current_date=TODAY, presets=()).process("cbcal_0_s_d_2024_6_20_r20240612")[1]
    confirm, change = rows(markup)[-2]
    assert (confirm["text"], confirm["style"]) == ("✓ Confirm", "success")
    assert change["text"] == "Change" and "style" not in change


def test_range_today_outside_selection_keeps_today_style() -> None:
    cal = RangeTelegramCalendar(current_date=TODAY, presets=(), style=replace(RANGE_STYLE, today_style="danger"))
    markup = cal.process("cbcal_0_s_d_2024_6_5")[1]
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("5", "primary"), ("15", "danger")]


def test_range_old_look_reachable() -> None:
    old = replace(
        RANGE_STYLE,
        selected="[{day}]",
        in_range="·{day}·",
        confirm="Confirm",
        selected_style=None,
        in_range_style=None,
        confirm_style=None,
    )
    markup = RangeTelegramCalendar(current_date=TODAY, presets=(), style=old).process(
        "cbcal_0_s_d_2024_6_20_r20240612"
    )[1]
    texts = [b["text"] for row in rows(markup) for b in row]
    assert "[12]" in texts and "·13·" in texts and "Confirm" in texts
    assert [(b["text"], b["style"]) for b in styled(markup)] == [("·15·", "primary")]


def test_range_callback_data_unchanged_by_styles() -> None:
    old = replace(RANGE_STYLE, selected_style=None, in_range_style=None, confirm_style=None)
    data = "cbcal_0_s_d_2024_6_20_r20240612"
    new_rows = rows(RangeTelegramCalendar(current_date=TODAY, presets=()).process(data)[1])
    old_rows = rows(RangeTelegramCalendar(current_date=TODAY, presets=(), style=old).process(data)[1])
    assert [[b["callback_data"] for b in r] for r in new_rows] == [[b["callback_data"] for b in r] for r in old_rows]


@pytest.mark.parametrize("field", ["selected_style", "in_range_style", "confirm_style"])
def test_bad_range_styles(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        RangeTelegramCalendar(style=replace(RANGE_STYLE, **{field: "blue"}))


def test_telethon_range_span_is_marked(monkeypatch: pytest.MonkeyPatch) -> None:
    from telegram_bot_calendar import render

    class Button:
        @staticmethod
        def inline(text: str, data: str) -> tuple[str, str]:
            return text, data

    monkeypatch.setattr(render, "telethon_button", lambda: Button)
    cal = RangeTelegramCalendar(current_date=TODAY, presets=(), telethon=True)
    markup: Any = cal.process("cbcal_0_s_d_2024_6_20_r20240612")[1]
    texts = [button[0] for row in markup for button in row]
    assert [f"•{n}" for n in range(12, 21)] == [t for t in texts if t.startswith("•") and t[1:].isdigit()]
    assert "•✓ Confirm" in texts and "Change" in texts
