"""Turn rows of keys into Telegram markup: Bot API JSON or telethon buttons."""

from __future__ import annotations

import json
from typing import Any, Union

Label = Union[str, int]
Key = tuple[Label, str]
"""A button: its label and its callback data."""
Rows = list[list[Key]]


def to_json(rows: Rows, extra: list[list[dict[str, Any]]]) -> str:
    """``InlineKeyboardMarkup`` JSON. ``extra`` rows are appended unchanged."""
    keyboard: list[list[dict[str, Any]]] = [
        [{"text": label, "callback_data": data} for label, data in row] for row in rows
    ]
    return json.dumps({"inline_keyboard": keyboard + extra})


def to_telethon(rows: Rows, extra: list[list[Any]]) -> list[list[Any]]:
    """Rows of ``telethon.Button.inline``; ``extra`` rows are appended unchanged."""
    button = telethon_button()
    return [[button.inline(text=str(label), data=data) for label, data in row] for row in rows] + extra


def telethon_button() -> Any:
    try:
        from telethon import Button
    except ImportError as exc:
        raise ImportError("telethon=True needs Telethon: pip install 'telegram-bot-calendar[telethon]'") from exc
    return Button
