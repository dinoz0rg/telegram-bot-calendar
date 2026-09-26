"""aiogram 3 example. Run: BOT_TOKEN=... python examples/aiogram_bot.py"""

import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from telegram_bot_calendar import LSTEP, RangeTelegramCalendar, WMonthTelegramCalendar

dp = Dispatcher()


def keyboard(markup: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.model_validate_json(markup)


@dp.message(Command("start"))
async def start(message: Message) -> None:
    markup, step = WMonthTelegramCalendar().build()
    await message.answer(f"Select {LSTEP[step or 'd']}", reply_markup=keyboard(str(markup)))


@dp.message(Command("range"))
async def range_cmd(message: Message) -> None:
    markup, _ = RangeTelegramCalendar(calendar_id=1).build()
    await message.answer("Pick a range", reply_markup=keyboard(str(markup)))


@dp.callback_query(F.data.startswith("cbcal_0_"))
async def on_date(query: CallbackQuery) -> None:
    result, markup, step = WMonthTelegramCalendar().process(query.data)
    await query.answer()
    if not isinstance(query.message, Message):
        return
    if result:
        await query.message.edit_text(f"You picked {result}")
    elif markup:
        await query.message.edit_text(f"Select {LSTEP[step or 'd']}", reply_markup=keyboard(str(markup)))


@dp.callback_query(F.data.startswith("cbcal_1_"))
async def on_range(query: CallbackQuery) -> None:
    result, markup, _ = RangeTelegramCalendar(calendar_id=1).process(query.data)
    await query.answer()
    if not isinstance(query.message, Message):
        return
    if isinstance(result, tuple):
        await query.message.edit_text(f"Range: {result[0]} to {result[1]}")
    elif markup:
        await query.message.edit_reply_markup(reply_markup=keyboard(str(markup)))


async def main() -> None:
    await dp.start_polling(Bot(os.environ["BOT_TOKEN"]))


if __name__ == "__main__":
    asyncio.run(main())
