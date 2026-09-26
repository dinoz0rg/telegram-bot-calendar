"""Render README screenshots from real keyboards.

Run: python docs/render_screenshots.py   (needs: pip install playwright && playwright install chromium)
Writes docs/img/<name>-<theme>.png at 2x.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))

from telegram_bot_calendar import (  # noqa: E402
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    WMonthTelegramCalendar,
    WYearTelegramCalendar,
    core,
)
from telegram_bot_calendar.locales import WEEKDAY_NAMES  # noqa: E402

TODAY = date(2026, 5, 14)
THEMES: dict[str, dict[str, str]] = {
    "light": {
        "page": "#dfe8d6",
        "bubble": "#ffffff",
        "text": "#000000",
        "meta": "#8a9aa9",
        "button": "rgba(0, 0, 0, 0.34)",
        "button_text": "#ffffff",
        "header": "#ffffff",
        "header_text": "#000000",
        "subtitle": "#8a9aa9",
        "avatar": "#3a8bd6",
    },
    "dark": {
        "page": "#0e1621",
        "bubble": "#182533",
        "text": "#f5f5f5",
        "meta": "#6d7f8f",
        "button": "rgba(255, 255, 255, 0.10)",
        "button_text": "#ffffff",
        "header": "#17212b",
        "header_text": "#ffffff",
        "subtitle": "#6d7f8f",
        "avatar": "#5288c1",
    },
}


def shots() -> list[tuple[str, str, str]]:
    """(file name, message text, markup JSON) for each screen."""
    out: list[tuple[str, str, str]] = []

    def add(name: str, text: str, markup: Any) -> None:
        out.append((name, text, str(markup)))

    add("day-picker", "Select day", WMonthTelegramCalendar(current_date=TODAY).build()[0])
    add("month-picker", "Select month", WYearTelegramCalendar(current_date=TODAY).build()[0])
    add("year-picker", "Select year", DetailedTelegramCalendar(current_date=TODAY).build()[0])
    blocked = WMonthTelegramCalendar(
        current_date=TODAY,
        min_date=date(2026, 5, 8),
        max_date=date(2026, 5, 27),
        blocked_day_button="·",
        mark_today=True,
    )
    add("blocked-today", "Pick a delivery day", blocked.build()[0])
    summary = RangeTelegramCalendar(current_date=TODAY, presets=()).process("cbcal_0_s_d_2026_5_22_r20260511")[1]
    add("range-confirm", "Pick a range", summary)
    add("quick-picks", "Pick a range", RangeTelegramCalendar(current_date=TODAY, cancel_button="Cancel").build()[0])
    return out


def key(button: dict[str, Any]) -> str:
    label = html.escape(str(button["text"]))
    if not label.strip():
        return '<div class="key empty">&nbsp;</div>'
    return f'<div class="key">{label}</div>'


def page(text: str, markup: str, theme: dict[str, str]) -> str:
    rows = [row for row in json.loads(markup)["inline_keyboard"] if row]
    weekdays = WEEKDAY_NAMES["en"]

    def row_html(row: list[dict[str, Any]]) -> str:
        cls = "row weekdays" if [b["text"] for b in row] == list(weekdays) else "row"
        return f'<div class="{cls}">' + "".join(key(b) for b in row) + "</div>"

    keyboard = "".join(row_html(row) for row in rows)
    t = theme
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><style>
body {{ margin: 0; background: {t["page"]}; font: 15px/1.35 -apple-system, "Segoe UI", Roboto, sans-serif; }}
#shot {{ width: 392px; background: {t["page"]}; }}
.header {{ display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 14px;
  background: {t["header"]}; border-bottom: 1px solid rgba(0, 0, 0, 0.08); }}
.avatar {{ width: 36px; height: 36px; border-radius: 50%; background: {t["avatar"]}; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 600; }}
.title {{ color: {t["header_text"]}; font-weight: 600; font-size: 15px; line-height: 1.2; }}
.subtitle {{ color: {t["subtitle"]}; font-size: 13px; line-height: 1.2; }}
.chat {{ padding: 16px; }}
.msg {{ display: flex; flex-direction: column; }}
.bubble {{ background: {t["bubble"]}; color: {t["text"]}; border-radius: 14px 14px 14px 4px; padding: 7px 10px 6px; }}
.meta {{ color: {t["meta"]}; font-size: 12px; text-align: right; }}
.kb {{ display: flex; flex-direction: column; gap: 2px; margin-top: 2px; }}
.row {{ display: flex; gap: 2px; }}
.key {{ flex: 1 1 0; min-width: 0; height: 22px; display: flex; align-items: center; justify-content: center;
  background: {t["button"]}; color: {t["button_text"]}; border-radius: 4px; padding: 0 2px; font-size: 12px;
  font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.key.empty {{ opacity: 0.35; }}
.row.weekdays .key {{ background: transparent; color: {t["meta"]}; font-weight: 400; }}
</style><body><div id="shot"><div class="header"><div class="avatar" aria-hidden="true">C</div>
<div><div class="title">Calendar Bot</div><div class="subtitle">bot</div></div></div>
<div class="chat"><div class="msg"><div class="bubble"><div>{html.escape(text)}</div>
<div class="meta">12:00</div></div><div class="kb">{keyboard}</div></div></div></div></body></html>"""


def main() -> None:
    from playwright.sync_api import sync_playwright

    core.today = lambda: TODAY
    out_dir = ROOT / "img"
    out_dir.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(device_scale_factor=2, viewport={"width": 392, "height": 200})
        for name, text, markup in shots():
            for theme_name, theme in THEMES.items():
                tab.set_content(page(text, markup, theme))
                tab.locator("#shot").screenshot(path=str(out_dir / f"{name}-{theme_name}.png"))
        browser.close()


if __name__ == "__main__":
    main()
