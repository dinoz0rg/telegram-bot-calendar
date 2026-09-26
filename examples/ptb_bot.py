"""python-telegram-bot v21 example. Run: BOT_TOKEN=... python examples/ptb_bot.py"""

import os

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from telegram_bot_calendar import (
    CANCELLED,
    EXPIRED,
    LSTEP,
    DetailedTelegramCalendar,
    RangeTelegramCalendar,
    new_session,
)


def day_picker(context: ContextTypes.DEFAULT_TYPE) -> DetailedTelegramCalendar:
    session = context.user_data.get("session") if context.user_data is not None else None
    return DetailedTelegramCalendar(session=session, cancel_button="Cancel")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data is not None:
        context.user_data["session"] = new_session()
    markup, step = day_picker(context).build()
    if update.message:
        await update.message.reply_text(f"Select {LSTEP[step or 'y']}", reply_markup=markup)


async def range_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup, _ = RangeTelegramCalendar(calendar_id=1, cancel_button="Cancel").build()
    if update.message:
        await update.message.reply_text("Pick a range", reply_markup=markup)


async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    result, markup, step = day_picker(context).process(query.data)
    await query.answer()
    if result is EXPIRED:
        await query.edit_message_text("This calendar has expired. Send /start again.")
    elif result is CANCELLED:
        await query.edit_message_text("Cancelled.")
    elif result:
        await query.edit_message_text(f"You picked {result}")
    elif markup:
        await query.edit_message_text(f"Select {LSTEP[step or 'y']}", reply_markup=markup)


async def on_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    result, markup, _ = RangeTelegramCalendar(calendar_id=1, cancel_button="Cancel").process(query.data)
    await query.answer()
    if result is CANCELLED:
        await query.edit_message_text("Cancelled.")
    elif isinstance(result, tuple):
        await query.edit_message_text(f"Range: {result[0]} to {result[1]}")
    elif markup:
        await query.edit_message_reply_markup(markup)


def main() -> None:
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("range", range_cmd))
    app.add_handler(CallbackQueryHandler(on_date, pattern=r"^cbcal_0_"))
    app.add_handler(CallbackQueryHandler(on_range, pattern=r"^cbcal_1_"))
    app.run_polling()


if __name__ == "__main__":
    main()
