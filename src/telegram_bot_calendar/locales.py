"""Month and weekday names per locale. Weeks start on Monday."""

from __future__ import annotations

MONTH_NAMES: dict[str, tuple[str, ...]] = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "eo": ("jan", "feb", "mar", "apr", "maj", "jun", "jul", "aŭg", "sep", "okt", "nov", "dec"),
    "ru": ("янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"),
}

WEEKDAY_NAMES: dict[str, tuple[str, ...]] = {
    "en": ("M", "T", "W", "T", "F", "S", "S"),
    "eo": ("L", "M", "M", "Ĵ", "V", "S", "D"),
    "ru": ("П", "В", "С", "Ч", "П", "С", "В"),
}


def check_locale(locale: str) -> None:
    """Raise ValueError for a locale we have no names for."""
    if locale not in MONTH_NAMES:
        known = ", ".join(sorted(MONTH_NAMES))
        raise ValueError(f"unknown locale {locale!r}; choose one of: {known}")
