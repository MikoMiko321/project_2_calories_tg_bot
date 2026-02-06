import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv

from db import get_user, save_user
from models import User

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


# ---------- FSM профиля ----------


class Profile(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()


# Главное меню

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="🍎 Прием пищи")],
        [KeyboardButton(text="🏃 Тренировки")],
        [KeyboardButton(text="📊 Прогресс за сегодня")],
        [KeyboardButton(text="📈 Прогресс за неделю")],
        [KeyboardButton(text="⚙️ Редактировать профиль")],
    ],
    resize_keyboard=True,
)


# хендлеры


@dp.message(Command("start"))
async def start(m: Message):
    user = get_user(m.from_user.id)
    if user is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return
    await m.answer("Меню:", reply_markup=main_menu)


@dp.message(Command("set_profile"))
async def set_profile(m: Message, state: FSMContext):
    await m.answer("Введите ваш вес (в кг):")
    await state.set_state(Profile.weight)


@dp.message(Profile.weight)
async def profile_weight(m: Message, state: FSMContext):
    await state.update_data(weight=float(m.text))
    await m.answer("Введите ваш рост (в см):")
    await state.set_state(Profile.height)


@dp.message(Profile.height)
async def profile_height(m: Message, state: FSMContext):
    await state.update_data(height=float(m.text))
    await m.answer("Введите ваш возраст:")
    await state.set_state(Profile.age)


@dp.message(Profile.age)
async def profile_age(m: Message, state: FSMContext):
    await state.update_data(age=int(m.text))
    await m.answer("Сколько минут активности у вас в день?")
    await state.set_state(Profile.activity)


@dp.message(Profile.activity)
async def profile_activity(m: Message, state: FSMContext):
    await state.update_data(activity=int(m.text))
    await m.answer("В каком городе вы находитесь?")
    await state.set_state(Profile.city)


@dp.message(Profile.city)
async def profile_city(m: Message, state: FSMContext):
    data = await state.get_data()

    user = User(
        tg_id=m.from_user.id,
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        daily_activity=data["activity"],
        city=m.text,
    )
    save_user(user)

    await state.clear()
    await m.answer("Профиль создан ✅", reply_markup=main_menu)


# обработка команд


@dp.message(Command("log_water"))
async def log_water(m: Message):
    await m.answer("Логирование воды — скоро")


@dp.message(Command("log_food"))
async def log_food(m: Message):
    await m.answer("Логирование еды — скоро")


@dp.message(Command("log_workout"))
async def log_workout(m: Message):
    await m.answer("Логирование тренировок — скоро")


@dp.message(Command("check_progress"))
async def check_progress(m: Message):
    await m.answer("Прогресс за сегодня — скоро")


@dp.message(Command("last_week_progress"))
async def last_week_progress(m: Message):
    await m.answer("Прогресс за неделю — скоро")


@dp.message(lambda m: m.text == "✏️ Редактировать профиль")
async def edit_profile(m: Message, state: FSMContext):
    await m.answer("Редактирование профиля: /set_profile")


# ---------- Run ----------


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
