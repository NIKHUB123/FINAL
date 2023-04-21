#  Copyright (c) ChernV (@otter18), 2021.

import os
import sys
import time
from datetime import datetime

import colorama
from aiogram import Dispatcher, executor
from aiogram.types import Message
from tgbot.data.config import get_admins
from tgbot.data.loader import scheduler
from tgbot.handlers import dp
from tgbot.middlewares import setup_middlewares
from tgbot.services.api_session import AsyncSession
from tgbot.services.api_sqlite import create_dbx
from tgbot.utils.misc.bot_commands import set_commands
from tgbot.utils.misc.bot_filters import IsPrivate
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc_functions import (
    autobackup_admin,
    check_bot_data,
    check_mail,
    check_update,
    startup_notify,
    update_profit_day,
    update_profit_week,
)
from gunicorn.errors import HaltServer

from setup import bot, logger
from webhook import app


@app.on_message()
async def echo(message: Message):
    logger.info(
        f'</code>@{message.from_user.username}<code> ({message.chat.id}) used echo:\n\n%s',
        message.text,
    )
    await bot.send_message(message.chat.id, message.text)


async def scheduler_start(rSession):
    scheduler.add_job(update_profit_day, trigger="cron", hour=0)
    scheduler.add_job(
        update_profit_week, trigger="cron", day_of_week="mon", hour=0, minute=1
    )
    scheduler.add_job(autobackup_admin, trigger="cron", hour=0)
    scheduler.add_job(check_update, trigger="cron", hour=0, args=(rSession,))
    scheduler.add_job(check_mail, trigger="cron", hour=12, args=(rSession,))


async def on_startup(dp: Dispatcher):
    rSession = AsyncSession()
    dp.bot['rSession'] = rSession

    await dp.bot.delete_webhook()
    await dp.bot.get_updates(offset=-1)

    await set_commands(dp)
    await check_bot_data()
    await scheduler_start(rSession)
    await startup_notify(dp, rSession)

    bot_logger.warning("BOT WAS STARTED")
    print(
        colorama.Fore.LIGHTYELLOW_EX
        + f"~~~~~ Bot was started - @{(await dp.bot.get_me()).username} ~~~~~"
    )
    print(colorama.Fore.LIGHTBLUE_EX + "~~~~~ TG developer - @djimbox ~~~~~")
    print(colorama.Fore.RESET)

    if len(get_admins()) == 0:
        print("***** ENTER ADMIN ID IN settings.ini *****")


async def on_shutdown(dp: Dispatcher):
    rSession: AsyncSession = dp.bot['rSession']
    await rSession.close()

    await dp.storage.close()
   

