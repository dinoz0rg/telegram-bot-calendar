"""Telethon example.

Run: API_ID=... API_HASH=... BOT_TOKEN=... python examples/telethon_bot.py
Get API_ID and API_HASH at https://my.telegram.org.
"""

import os

from telethon import TelegramClient, events

from telegram_bot_calendar import LSTEP, DetailedTelegramCalendar

bot = TelegramClient("bot", int(os.environ["API_ID"]), os.environ["API_HASH"])


@bot.on(events.NewMessage(pattern="/start"))
async def start(event: events.NewMessage.Event) -> None:
    markup, step = DetailedTelegramCalendar(telethon=True).build()
    await event.respond(f"Select {LSTEP[step or 'y']}", buttons=markup)


@bot.on(events.CallbackQuery(data=DetailedTelegramCalendar.func(telethon=True)))
async def on_date(event: events.CallbackQuery.Event) -> None:
    result, markup, step = DetailedTelegramCalendar(telethon=True).process(event.data)
    await event.answer()
    if result:
        await event.edit(f"You picked {result}")
    elif markup:
        await event.edit(f"Select {LSTEP[step or 'y']}", buttons=markup)


if __name__ == "__main__":
    bot.start(bot_token=os.environ["BOT_TOKEN"])
    bot.run_until_disconnected()
