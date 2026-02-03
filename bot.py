import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()

users = {}


@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("Привет. /set_profile, /log_water, /log_food, /log_workout, /check_progress")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
