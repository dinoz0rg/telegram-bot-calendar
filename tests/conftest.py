from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from telegram_bot_calendar import core

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2024, 6, 15)


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core, "today", lambda: TODAY)


def rows(markup: Any) -> list[list[dict[str, Any]]]:
    data: list[list[dict[str, Any]]] = json.loads(markup)["inline_keyboard"]
    return data


def golden(name: str) -> Any:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
