"""Button texts. Pass ``style=Style(...)`` to change any of them."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    prev: str = "<<"
    next: str = ">>"
    no_page: str = "×"
    day_title: str = "{month} {year}"
    month_title: str = "{year}"
    year_title: str = " "
    blank: str = " "
    blocked: str = " "
    today: str = "•{day}"
    selected: str = "[{day}]"
    in_range: str = "·{day}·"
    confirm: str = "Confirm"
    change: str = "Change"
    today_button: str = "Today"
    range_text: str = "{start} – {end}"


DEFAULT_STYLE = Style()
RANGE_STYLE = Style(prev="‹", next="›", blocked="·")
