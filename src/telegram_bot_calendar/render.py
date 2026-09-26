"""Turn rows of keys into Telegram markup: Bot API JSON or telethon buttons."""

from __future__ import annotations

import json
from typing import Any, Optional, Union

Label = Union[str, int]
Key = tuple[Label, str, Optional[str]]
"""A button: its label, its callback data and its Bot API ``style`` (or None)."""
STYLES = (None, "primary", "success", "danger")
TELETHON_MARK = "•"
"""Telethon buttons have no style, so a styled key gets this prefix instead."""
Rows = list[list[Key]]


def to_json(rows: Rows, extra: list[list[dict[str, Any]]]) -> str:
    """``InlineKeyboardMarkup`` JSON. ``extra`` rows are appended unchanged."""
    keyboard = [[_button(label, data, style) for label, data, style in row] for row in rows]
    return json.dumps({"inline_keyboard": keyboard + extra})


def _button(label: Label, data: str, style: str | None) -> dict[str, Any]:
    button: dict[str, Any] = {"text": label, "callback_data": data}
    if style is not None:
        button["style"] = style
    return button


def to_telethon(rows: Rows, extra: list[list[Any]]) -> list[list[Any]]:
    """Rows of ``telethon.Button.inline``; ``extra`` rows are appended unchanged."""
    button = telethon_button()
    return [
        [button.inline(text=f"{TELETHON_MARK if style else ''}{label}", data=data) for label, data, style in row]
        for row in rows
    ] + extra


def telethon_button() -> Any:
    try:
        from telethon import Button
    except ImportError as exc:
        raise ImportError("telethon=True needs Telethon: pip install 'telegram-bot-calendar[telethon]'") from exc
    return Button
