# telegram-bot-calendar

Date and date-range pickers for Telegram bots, built as inline keyboards.

| | |
|---|---|
| ![Day picker light](docs/img/day-picker-light.png)<br>Day picker (light) | ![Day picker dark](docs/img/day-picker-dark.png)<br>Day picker (dark) |
| ![Month picker light](docs/img/month-picker-light.png)<br>Month picker (light) | ![Month picker dark](docs/img/month-picker-dark.png)<br>Month picker (dark) |
| ![Year picker light](docs/img/year-picker-light.png)<br>Year picker (light) | ![Year picker dark](docs/img/year-picker-dark.png)<br>Year picker (dark) |
| ![Blocked days + today light](docs/img/blocked-today-light.png)<br>Blocked days + today (light) | ![Blocked days + today dark](docs/img/blocked-today-dark.png)<br>Blocked days + today (dark) |
| ![Range + Confirm light](docs/img/range-confirm-light.png)<br>Range + Confirm (light) | ![Range + Confirm dark](docs/img/range-confirm-dark.png)<br>Range + Confirm (dark) |
| ![Quick picks + Cancel light](docs/img/quick-picks-light.png)<br>Quick picks + Cancel (light) | ![Quick picks + Cancel dark](docs/img/quick-picks-dark.png)<br>Quick picks + Cancel (dark) |

## Install

```bash
pip install telegram-bot-calendar
pip install "telegram-bot-calendar[telethon]"   # for Telethon markup
```

Python 3.9+. No runtime dependencies. Fully typed (`py.typed`).

## Quick start (python-telegram-bot v21)

```python
import os
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram_bot_calendar import LSTEP, DetailedTelegramCalendar

async def start(update, context):
    markup, step = DetailedTelegramCalendar().build()
    await update.message.reply_text(f"Select {LSTEP[step]}", reply_markup=markup)

async def on_tap(update, context):
    result, markup, step = DetailedTelegramCalendar().process(update.callback_query.data)
    if result or markup:  # None, None, None means a no-op tap
        text = f"You picked {result}" if result else f"Select {LSTEP[step]}"
        await update.callback_query.edit_message_text(text, reply_markup=markup)

app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
app.add_handlers([CommandHandler("start", start), CallbackQueryHandler(on_tap, pattern="^cbcal_0_")])
app.run_polling()
```

For full bots, see `examples/ptb_bot.py`, `examples/aiogram_bot.py` and `examples/telethon_bot.py`. Each one reads `BOT_TOKEN` from the environment.

## Features

- `DetailedTelegramCalendar` (year → month → day), `WYearTelegramCalendar` (month → day), `WMonthTelegramCalendar` (day only).
- `RangeTelegramCalendar`: tap a start day and an end day, then Confirm. It also has quick picks (This month, Last month, Last 7 days, Year to date) and a Today button.
- `min_date` / `max_date`. Days outside the limits are blocked, and forged taps on them are ignored.
- Today marker (`mark_today=True`) and a blocked-day marker (`blocked_day_button`).
- Cancel button. `result` is `CANCELLED`.
- Expiry. Taps from an old calendar with another `session` return `EXPIRED`.
- Taps from other calendars or with malformed data return `(None, None, None)`. It never raises.
- Locales: `en`, `eo`, `ru`.
- Bot API JSON markup, or Telethon buttons with `telethon=True`.

## Return values

- `.build()` → `(markup, step)`
- `.process(data)` → `(result, markup, step)`

`step` is `"y"`, `"m"` or `"d"`. `LSTEP` maps these to `"year"`, `"month"` and `"day"`. The range picker uses `"summary"` for the summary screen and for the final `(start, end)` result.

## Keyword arguments

| kwarg | default | meaning |
|---|---|---|
| `calendar_id` | `0` | Tells calendars in one chat apart. Must not contain `_`. |
| `current_date` | today | The date the calendar opens at. |
| `min_date` | `date(1, 1, 1)` | Earliest date that can be picked. |
| `max_date` | `date(2999, 12, 31)` | Latest date that can be picked. |
| `locale` | `"en"` | Month and weekday names: `en`, `eo`, `ru`. |
| `telethon` | `False` | Return Telethon `Button` rows instead of JSON. |
| `additional_buttons` | `None` | Extra Bot API button dicts, two per row, added at the bottom. |
| `style` | `None` | A `Style(...)` that sets button texts (arrows, markers, Confirm, and so on). |
| `cancel_button` | `None` | Text of a Cancel button. The button is shown only when you set this text. |
| `session` | `None` | 1–8 letters or digits. Taps with another token return `EXPIRED`. See `new_session()`. |
| `blocked_day_button` | `" "` (range: `"·"`) | Text shown for days outside the limits. |
| `mark_today` | `False` (range: `True`) | Mark today's date. |
| `is_random` | `False` | Add a random salt to callbacks. |
| `presets`, `show_today` | defaults | Range only: quick picks and the Today button. |

## Callback format

```
cbcal_<id>_<action>_<step>_<Y>_<M>_<D>[_r<YYYYMMDD>][_x<session>][_<salt>]
```

The actions are `s` (select), `g` (go to), `n` (nothing), `c` (cancel), `k` (confirm) and `r` (change). A calendar checks at construction time that every callback fits Telegram's 64-byte limit. Use `is_calendar_callback(data, calendar_id)` to route taps.

## License

MIT. See `LICENSE`.
