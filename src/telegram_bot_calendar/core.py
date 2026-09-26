"""Shared calendar plumbing: options, callbacks, markup and the tap entry point."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from typing import Any, Callable, ClassVar, Final, Optional, Union, final

from telegram_bot_calendar import callback as cb
from telegram_bot_calendar import grid, render
from telegram_bot_calendar.locales import (
    DAY_MONTH,
    DAY_MONTH_YEAR,
    MONTH_NAMES,
    MONTH_YEAR,
    WEEKDAY_NAMES,
    YEAR,
    check_locale,
    check_month_year_format,
    check_names,
)
from telegram_bot_calendar.style import DEFAULT_STYLE, Style


@final
class _Marker:
    """Type of the ``CANCELLED`` / ``EXPIRED`` sentinels. Compare with ``is``."""

    __slots__ = ("_name",)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError("_Marker is final")

    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name


CANCELLED: Final[_Marker] = _Marker("CANCELLED")
"""``result`` when the user taps Cancel."""
EXPIRED: Final[_Marker] = _Marker("EXPIRED")
"""``result`` when a tap carries a different ``session`` token."""


def today() -> date:
    """The current date. Tests replace this to freeze time."""
    return date.today()


NO_RESULT: tuple[None, None, None] = (None, None, None)
LSTEP: dict[str, str] = {cb.YEAR: "year", cb.MONTH: "month", cb.DAY: "day"}

Markup = Union[str, list[list[Any]]]
Result = Union[date, tuple[date, date], _Marker, None]
Outcome = tuple[Result, Optional[Markup], Optional[str]]


class CalendarBase:
    """Common options. Subclasses implement ``_first_rows`` and ``_handle``."""

    default_style: ClassVar[Style] = DEFAULT_STYLE
    random_salt: ClassVar[bool] = False

    def __init__(
        self,
        calendar_id: Any = 0,
        current_date: date | None = None,
        additional_buttons: list[Any] | None = None,
        locale: str = "en",
        min_date: date | None = None,
        max_date: date | None = None,
        telethon: bool = False,
        *,
        style: Style | None = None,
        is_random: bool | None = None,
        cancel_button: str | None = None,
        session: str | None = None,
        blocked_day_button: str | None = None,
        mark_today: bool = False,
        first_weekday: int = 0,
        month_names: Sequence[str] | None = None,
        weekday_names: Sequence[str] | None = None,
        month_year_format: str | None = None,
        buddhist_era: bool = False,
        rtl: bool = False,
    ) -> None:
        if not cb.valid_calendar_id(calendar_id):
            raise ValueError("calendar_id must be non-empty and must not contain '_'")
        if session is not None and not cb.valid_session(session):
            raise ValueError("session must be 1-8 ASCII letters or digits")
        check_locale(locale)
        if type(first_weekday) is not int or not 0 <= first_weekday <= 6:
            raise ValueError("first_weekday must be an int from 0 (Monday) to 6 (Sunday)")
        self.first_weekday = first_weekday
        self.month_names = check_names("month_names", month_names, 12, MONTH_NAMES[locale])
        self.weekday_names = check_names("weekday_names", weekday_names, 7, WEEKDAY_NAMES[locale])
        self.month_year_format = check_month_year_format(month_year_format, MONTH_YEAR[locale])
        self.year_format = YEAR[locale]
        self.day_month_format = DAY_MONTH[locale]
        self.day_month_year_format = DAY_MONTH_YEAR[locale]
        for name, flag in (("buddhist_era", buddhist_era), ("rtl", rtl)):
            if type(flag) is not bool:
                raise ValueError(f"{name} must be True or False")
        self.buddhist_era = buddhist_era
        self.rtl = rtl
        self.calendar_id = calendar_id
        self.current_date = current_date or today()
        self.locale = locale
        self.min_date = min_date or date(1, 1, 1)
        self.max_date = max_date or date(2999, 12, 31)
        if self.min_date > self.max_date:
            raise ValueError("min_date is after max_date")
        self.telethon = telethon
        if telethon:
            render.telethon_button()
        self.style = style or self.default_style
        if blocked_day_button is not None:
            self.style = replace(self.style, blocked=blocked_day_button)
        for name in ("today_style", "selected_style", "in_range_style", "confirm_style"):
            if getattr(self.style, name) not in render.STYLES:
                raise ValueError(f"{name} must be None, 'primary', 'success' or 'danger'")
        self.salted = self.random_salt if is_random is None else is_random
        self.cancel_button = cancel_button
        self.session = session
        self.mark_today = mark_today
        self.additional_buttons = list(additional_buttons or [])
        self.step: str | None = None
        self._markup: Markup | None = None
        self._check_size()

    # -- public API -------------------------------------------------------------------------
    @staticmethod
    def func(calendar_id: Any = 0, telethon: bool = False) -> Callable[[Any], bool]:
        """A filter for handler registration: True for this calendar's taps."""

        def check(update: Any) -> bool:
            data = update if telethon else getattr(update, "data", None)
            return cb.is_calendar_callback(data, calendar_id)

        return check

    def build(self) -> tuple[Markup, str | None]:
        """The first screen: ``(markup, step)``."""
        if self._markup is None:
            self._markup = self._finish(self._first_rows())
        return self._markup, self.step

    def process(self, call_data: Any) -> Outcome:
        """Handle a tap: ``(result, markup, step)``. Never raises on bad data."""
        p = cb.decode(call_data, self.calendar_id)
        if p is None or p.action == cb.NOTHING:
            return NO_RESULT
        if self.session is not None and p.session != self.session:
            return EXPIRED, None, None
        if p.action == cb.CANCEL:
            return CANCELLED, None, None
        try:
            return self._handle(p)
        except (ValueError, OverflowError):
            return NO_RESULT

    # -- for subclasses ---------------------------------------------------------------------
    def _first_rows(self) -> render.Rows:
        raise NotImplementedError

    def _handle(self, p: cb.Payload) -> Outcome:
        raise NotImplementedError

    def _screen(self, rows: render.Rows, step: str) -> Outcome:
        self.step = step
        return None, self._finish(rows), step

    def _key(
        self,
        label: render.Label,
        action: str = cb.NOTHING,
        step: str | None = None,
        day: date | None = None,
        start: date | None = None,
        *,
        style: str | None = None,
    ) -> render.Key:
        payload = cb.Payload(str(self.calendar_id), action, step, day, start, self.session)
        salt = random.randint(1, 10**18) if self.salted and action != cb.NOTHING else None
        return label, cb.encode(payload, salt), style

    def _in_range(self, d: date) -> bool:
        return self.min_date <= d <= self.max_date

    def _month_name(self, month: int) -> str:
        return self.month_names[month - 1]

    def _year(self, year: int) -> int:
        """The displayed year: +543 in the Buddhist era. Labels only."""
        return year + 543 if self.buddhist_era else year

    def _year_label(self, year: int) -> render.Label:
        text = self.year_format.format(year=self._year(year))
        return int(text) if text.isdigit() else text  # plain years stay ints, as before

    def _month_year(self, d: date) -> str:
        return self.month_year_format.format(month=self._month_name(d.month), year=self._year(d.year))

    def _day_month(self, d: date, year: bool) -> str:
        template = self.day_month_year_format if year else self.day_month_format
        return template.format(day=d.day, month=self._month_name(d.month), year=self._year(d.year))

    def _weekday_row(self) -> list[render.Key]:
        names = self.weekday_names[self.first_weekday :] + self.weekday_names[: self.first_weekday]
        return [self._key(name) for name in names]

    def _day_label(self, d: date) -> render.Label:
        if self.mark_today and d == today():
            return self.style.today.format(day=d.day)
        return d.day

    def _day_style(self, d: date) -> str | None:
        """The Bot API button style for day ``d``: ``style.today_style`` on today, else None."""
        return self.style.today_style if self.mark_today and d == today() else None

    def _finish(self, rows: render.Rows) -> Markup:
        rows = [row[::-1] for row in rows] if self.rtl else list(rows)
        if self.cancel_button:
            rows.append([self._key(self.cancel_button, cb.CANCEL)])
        extra = grid.chunk(self.additional_buttons, 2) or [[]]
        if self.telethon:
            return render.to_telethon(rows, extra if self.additional_buttons else [])
        return render.to_json(rows, extra)

    def _check_size(self) -> None:
        worst = cb.Payload(
            str(self.calendar_id), cb.CONFIRM, cb.DAY, date(9999, 12, 31), date(9999, 12, 31), self.session
        )
        try:
            cb.encode(worst, 10**18 if self.salted else None)
        except ValueError:
            raise ValueError("calendar_id is too long: callback data would exceed 64 bytes") from None
