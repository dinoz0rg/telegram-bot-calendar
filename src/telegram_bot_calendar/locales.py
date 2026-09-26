"""Month and weekday names per locale, Monday first, plus checks for owner overrides."""

from __future__ import annotations

from collections.abc import Sequence

from telegram_bot_calendar._locale_data import MONTH_NAMES, WEEKDAY_NAMES

__all__ = ["MONTH_NAMES", "WEEKDAY_NAMES", "check_locale", "check_names"]


def check_locale(locale: str) -> None:
    """Raise ValueError for a locale we have no names for."""
    if locale not in MONTH_NAMES:
        known = ", ".join(sorted(MONTH_NAMES))
        raise ValueError(f"unknown locale {locale!r}; choose one of: {known}")


def check_names(kwarg: str, names: Sequence[str] | None, count: int, default: tuple[str, ...]) -> tuple[str, ...]:
    """``names`` as a tuple of ``count`` non-empty strings, or ``default`` when None."""
    if names is None:
        return default
    if isinstance(names, str) or len(names) != count or not all(isinstance(n, str) and n.strip() for n in names):
        raise ValueError(f"{kwarg} must be {count} non-empty strings")
    return tuple(names)
