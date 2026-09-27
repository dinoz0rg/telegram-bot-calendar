"""Step-by-step picker: year, then month, then day."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from telegram_bot_calendar import callback as cb
from telegram_bot_calendar import grid
from telegram_bot_calendar.core import CalendarBase, Outcome
from telegram_bot_calendar.render import Key, Rows
from telegram_bot_calendar.style import Style

YEARS_PER_ROW = 2
YEAR_ROWS = 2
MONTHS_PER_ROW = 3

_NEXT_STEP = {cb.YEAR: cb.MONTH, cb.MONTH: cb.DAY}


class DetailedTelegramCalendar(CalendarBase):
    """Starts at the year screen. ``process`` returns the picked ``date``."""

    first_step: ClassVar[str] = cb.YEAR

    def _first_rows(self) -> Rows:
        self.step = self.first_step
        return self._rows_for(self.first_step)

    def _handle(self, p: cb.Payload) -> Outcome:
        if p.step is None or p.day is None:
            return None, None, None
        self.current_date = p.day
        if p.action == cb.GOTO:
            return self._screen(self._rows_for(p.step), p.step)
        if p.action != cb.SELECT:
            return None, None, None
        if p.step in _NEXT_STEP:
            nxt = _NEXT_STEP[p.step]
            return self._screen(self._rows_for(nxt), nxt)
        if not self._in_range(p.day):
            return None, None, None
        return p.day, None, p.step

    def _rows_for(self, step: str) -> Rows:
        if step == cb.YEAR:
            return self._year_rows()
        if step == cb.MONTH:
            return self._month_rows()
        return self._day_rows()

    def _pick(self, label: object, step: str, d: date | None) -> Key:
        if d is None:
            return self._key(self.style.blank)
        return self._key(label if isinstance(label, (str, int)) else str(label), cb.SELECT, step, d)

    def _title_values(self) -> dict[str, object]:
        d = self.current_date
        return {"year": self._year(d.year), "month": self._month_name(d.month), "day": d.day}

    def _title(self, title: str, default: str, locale_text: object) -> str:
        """``title`` from the style; the locale's label when the style keeps the default."""
        if title != default:
            return title
        return str(locale_text).replace("{", "{{").replace("}", "}}")  # _nav formats it again

    def _nav(
        self, step: str, prev_d: date | None, next_d: date | None, title: str, title_key: tuple[str, str | None]
    ) -> list[Key]:
        values = self._title_values()
        action, title_step = title_key
        prev_key = self._key(self.style.prev.format(**values), cb.GOTO, step, prev_d) if prev_d else None
        next_key = self._key(self.style.next.format(**values), cb.GOTO, step, next_d) if next_d else None
        return [
            prev_key or self._key(self.style.no_page),
            self._key(title.format(**values), action, title_step, self.current_date),
            next_key or self._key(self.style.no_page),
        ]

    def _year_rows(self) -> Rows:
        count = YEARS_PER_ROW * YEAR_ROWS
        lo, hi = self.min_date.year, self.max_date.year
        centred = self.current_date.year - (count - 1) // 2
        # Keep the window inside [lo, hi] so no slot is blank unless the span is shorter than count.
        first_year = max(min(max(centred, lo), hi - count + 1), lo)
        offset = first_year - self.current_date.year
        slots = grid.year_slots(self.current_date, offset, count, self.min_date, self.max_date)
        keys = [self._pick(self._year_label(d.year) if d else "", cb.YEAR, d) for d in slots]
        has_prev = first_year > self.min_date.year
        has_next = first_year + count <= self.max_date.year
        # Aim at the centre of the adjacent page so re-centring lands exactly on it (no overlap).
        prev_first = max(first_year - count, lo)
        next_first = max(min(first_year + count, hi - count + 1), lo)
        shift = (count - 1) // 2 - self.current_date.year
        prev_d = grid.try_add_months(self.current_date, 12 * (prev_first + shift)) if has_prev else None
        next_d = grid.try_add_months(self.current_date, 12 * (next_first + shift)) if has_next else None
        nav = self._nav(cb.YEAR, prev_d, next_d, self.style.year_title, (cb.NOTHING, None))
        return [*grid.chunk(keys, YEARS_PER_ROW), nav]

    def _month_rows(self) -> Rows:
        slots = grid.month_slots(self.current_date, self.min_date, self.max_date)
        keys = [self._pick(self._month_name(d.month) if d else "", cb.MONTH, d) for d in slots]
        year = self.current_date.year
        prev_d = grid.try_add_months(self.current_date, -12) if year > self.min_date.year else None
        next_d = grid.try_add_months(self.current_date, 12) if year < self.max_date.year else None
        title = self._title(self.style.month_title, Style.month_title, self._year_label(year))
        nav = self._nav(cb.MONTH, prev_d, next_d, title, (cb.GOTO, cb.YEAR))
        return [*grid.chunk(keys, MONTHS_PER_ROW), nav]

    def _day_rows(self) -> Rows:
        d = self.current_date
        rows: Rows = [self._weekday_row()]
        for week, slots in zip(
            grid.day_weeks(d.year, d.month, self.first_weekday),
            grid.day_slots(d.year, d.month, self.min_date, self.max_date, self.first_weekday),
        ):
            row: list[Key] = []
            for n, slot in zip(week, slots):
                if slot is not None:
                    row.append(self._key(self._day_label(slot), cb.SELECT, cb.DAY, slot, style=self._day_style(slot)))
                else:
                    row.append(self._key(self.style.blocked if n else self.style.blank))
            rows.append(row)
        first, last = grid.first_of_month(d), grid.last_of_month(d)
        prev_d = grid.try_add_months(d, -1) if first > self.min_date else None
        next_d = grid.try_add_months(d, 1) if last < self.max_date else None
        title = self._title(self.style.day_title, Style.day_title, self._month_year(d))
        rows.append(self._nav(cb.DAY, prev_d, next_d, title, (cb.GOTO, cb.MONTH)))
        return rows


class WMonthTelegramCalendar(DetailedTelegramCalendar):
    """Starts at the day screen of ``current_date``'s month."""

    first_step: ClassVar[str] = cb.DAY


class WYearTelegramCalendar(DetailedTelegramCalendar):
    """Starts at the month screen of ``current_date``'s year."""

    first_step: ClassVar[str] = cb.MONTH
