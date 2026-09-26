"""Range picker: tap a start day, tap an end day, then Confirm."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any, Callable, ClassVar

from telegram_bot_calendar import callback as cb
from telegram_bot_calendar import core, grid
from telegram_bot_calendar.core import NO_RESULT, CalendarBase, Outcome
from telegram_bot_calendar.render import Key, Rows
from telegram_bot_calendar.style import RANGE_STYLE, Style

SUMMARY = "summary"
"""``step`` for the summary screen and for the confirmed result."""

MONTHS_PER_ROW = 3
PRESETS_PER_ROW = 2

Preset = tuple[str, Callable[[date], tuple[date, date]]]


def this_month(t: date) -> tuple[date, date]:
    return grid.first_of_month(t), grid.last_of_month(t)


def last_month(t: date) -> tuple[date, date]:
    end = grid.first_of_month(t) - timedelta(days=1)
    return grid.first_of_month(end), end


def last_7_days(t: date) -> tuple[date, date]:
    return t - timedelta(days=6), t


def year_to_date(t: date) -> tuple[date, date]:
    return t.replace(month=1, day=1), t


DEFAULT_PRESETS: tuple[Preset, ...] = (
    ("This month", this_month),
    ("Last month", last_month),
    ("Last 7 days", last_7_days),
    ("Year to date", year_to_date),
)


class RangeTelegramCalendar(CalendarBase):
    """Confirm gives ``((start, end), None, SUMMARY)``."""

    default_style: ClassVar[Style] = RANGE_STYLE

    def __init__(
        self,
        calendar_id: Any = 0,
        current_date: date | None = None,
        *,
        presets: Sequence[Preset] | None = None,
        show_today: bool = True,
        mark_today: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(calendar_id, current_date, mark_today=mark_today, **kwargs)
        self.presets: tuple[Preset, ...] = DEFAULT_PRESETS if presets is None else tuple(presets)
        self.show_today = show_today

    def format_range(self, start: date, end: date) -> str:
        """For example ``1 Sep – 26 Sep 2026``; the year shows once if shared."""

        def fmt(d: date, year: bool) -> str:
            text = f"{d.day} {self._month_name(d.month)}"
            return f"{text} {d.year}" if year else text

        return self.style.range_text.format(start=fmt(start, start.year != end.year), end=fmt(end, True))

    # -- screens ----------------------------------------------------------------------------
    def _first_rows(self) -> Rows:
        self.step = cb.DAY
        return self._days()

    def _arrows(self, step: str, title: Key, prev_d: date | None, next_d: date | None, start: date | None) -> list[Key]:
        def arrow(text: str, d: date | None) -> Key:
            return self._key(text, cb.GOTO, step, d, start) if d else self._key(self.style.no_page)

        return [arrow(self.style.prev, prev_d), title, arrow(self.style.next, next_d)]

    def _days(self, start: date | None = None, end: date | None = None) -> Rows:
        first = grid.first_of_month(self.current_date)
        last = grid.last_of_month(first)
        title = f"{self._month_name(first.month)} {first.year}"
        rows: Rows = []
        if end is None:
            prev_d = grid.try_add_months(first, -1) if first > grid.first_of_month(self.min_date) else None
            next_d = grid.try_add_months(first, 1) if last < self.max_date else None
            title_key = self._key(title, cb.GOTO, cb.MONTH, self.current_date, start)
            rows.append(self._arrows(cb.DAY, title_key, prev_d, next_d, start))
        else:
            rows.append([self._key(title)])
        rows.append(self._weekday_row())
        for week in grid.day_weeks(first.year, first.month):
            rows.append([self._day_key(first, n, start, end) for n in week])
        if start is not None and end is not None:
            rows.append([self._key(self.format_range(start, end))])
            rows.append(
                [
                    self._key(self.style.confirm, cb.CONFIRM, cb.DAY, end, start),
                    self._key(self.style.change, cb.CHANGE, cb.DAY, start),
                ]
            )
        elif start is None:
            rows += self._quick_picks()
        return rows

    def _day_key(self, first: date, n: int, start: date | None, end: date | None) -> Key:
        if n == 0:
            return self._key(self.style.blank)
        d = first.replace(day=n)
        if not self._in_range(d):
            return self._key(self.style.blocked)
        text = str(self._day_label(d))
        if d in (start, end):
            text = self.style.selected.format(day=text)
        elif start is not None and end is not None and start < d < end:
            text = self.style.in_range.format(day=text)
        if end is not None:
            return self._key(text)
        return self._key(text, cb.SELECT, cb.DAY, d, start)

    def _quick_picks(self) -> Rows:
        now = core.today()
        keys: list[Key] = []
        for label, pick in self.presets:
            lo, hi = pick(now)
            lo, hi = max(lo, self.min_date), min(hi, self.max_date)
            if lo <= hi:
                keys.append(self._key(label, cb.SELECT, cb.DAY, hi, lo))
        rows = grid.chunk(keys, PRESETS_PER_ROW)
        if self.show_today and self._in_range(now):
            rows.append([self._key(self.style.today_button, cb.SELECT, cb.DAY, now, now)])
        return rows

    def _months(self, start: date | None) -> Rows:
        year = self.current_date.year
        keys: list[Key] = []
        for m in range(1, 13):
            first = date(year, m, 1)
            if grid.last_of_month(first) < self.min_date or first > self.max_date:
                keys.append(self._key(self.style.blank))
            else:
                keys.append(self._key(self._month_name(m), cb.GOTO, cb.DAY, first, start))
        prev_d = date(year - 1, 1, 1) if year > self.min_date.year else None
        next_d = date(year + 1, 1, 1) if year < self.max_date.year else None
        title = self._key(str(year), cb.NOTHING)
        return [self._arrows(cb.MONTH, title, prev_d, next_d, start), *grid.chunk(keys, MONTHS_PER_ROW)]

    # -- taps -------------------------------------------------------------------------------
    def _handle(self, p: cb.Payload) -> Outcome:
        if p.day is None:
            return NO_RESULT
        self.current_date = p.day
        if p.action == cb.GOTO:
            if p.step == cb.MONTH:
                return self._screen(self._months(p.start), cb.MONTH)
            return self._screen(self._days(p.start), cb.DAY)
        if p.action == cb.CHANGE:
            return self._screen(self._days(), cb.DAY)
        if not self._in_range(p.day) or (p.start is not None and not self._in_range(p.start)):
            return NO_RESULT
        if p.action == cb.SELECT:
            if p.start is None:
                return self._screen(self._days(start=p.day), cb.DAY)
            lo, hi = sorted((p.start, p.day))
            self.current_date = hi
            return self._screen(self._days(lo, hi), SUMMARY)
        if p.action == cb.CONFIRM and p.start is not None:
            lo, hi = sorted((p.start, p.day))
            return (lo, hi), None, SUMMARY
        return NO_RESULT
