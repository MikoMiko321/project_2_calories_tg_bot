import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv

from db import (
    get_food_logs,
    get_user,
    get_water_logs,
    get_workout_logs,
    save_food,
    save_user,
    save_water,
    save_workout,
)
from models import FoodLog, User, WaterLog, WorkoutLog

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


# ---------- Меню ----------

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


# ---------- Общие функции ----------


async def start_profile_flow(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Введите ваш вес (в кг):")
    await state.set_state(Profile.weight)


def format_profile(user: User) -> str:
    return (
        "📋 Текущий профиль:\n\n"
        f"Вес: {user.weight} кг\n"
        f"Рост: {user.height} см\n"
        f"Возраст: {user.age}\n"
        f"Активность: {user.daily_activity} мин/день\n"
        f"Город: {user.city}\n"
    )


# ---------- Start / Profile ----------


@dp.message(Command("start"))
async def start(m: Message):
    user = get_user(m.from_user.id)
    if user is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return
    await m.answer("Меню:", reply_markup=main_menu)


@dp.message(Command("set_profile"))
async def cmd_set_profile(m: Message, state: FSMContext):
    await start_profile_flow(m, state)


@dp.message(lambda m: m.text == "⚙️ Редактировать профиль")
async def menu_set_profile(m: Message, state: FSMContext):
    user = get_user(m.from_user.id)
    if user:
        await m.answer(format_profile(user))
    await start_profile_flow(m, state)


# ---------- FSM шаги ----------


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
    await m.answer("Профиль сохранён ✅", reply_markup=main_menu)


# ---------- 💧 Вода ----------


async def water_entry(m: Message):
    await m.answer("Введи: /log_water <мл>")


@dp.message(lambda m: m.text == "💧 Вода")
async def menu_water(m: Message):
    await water_entry(m)


@dp.message(Command("log_water"))
async def log_water(m: Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await water_entry(m)
        return

    try:
        ml = int(parts[1])
    except Exception:
        await m.answer("Пример: /log_water 250")
        return

    save_water(
        WaterLog(
            tg_id=m.from_user.id,
            ts=datetime.utcnow(),
            volume_ml=ml,
        )
    )
    await m.answer(f"💧 Записал {ml} мл")


# ---------- 🍎 Еда (упрощённо) ----------


@dp.message(lambda m: m.text == "🍎 Прием пищи")
async def menu_food(m: Message):
    await m.answer("Введи: /log_food <продукт> <граммы> <ккал>")


@dp.message(Command("log_food"))
async def log_food(m: Message):
    parts = m.text.split()
    if len(parts) < 4:
        await m.answer("Пример: /log_food банан 150 135")
        return

    _, product, grams, calories = parts
    save_food(
        FoodLog(
            tg_id=m.from_user.id,
            ts=datetime.utcnow(),
            product=product,
            grams=int(grams),
            calories=float(calories),
        )
    )
    await m.answer("🍎 Записал приём пищи")


# ---------- 🏃 Тренировки ----------


@dp.message(lambda m: m.text == "🏃 Тренировки")
async def menu_workout(m: Message):
    await m.answer("Введи: /log_workout <тип> <мин> <ккал>")


@dp.message(Command("log_workout"))
async def log_workout(m: Message):
    parts = m.text.split()
    if len(parts) < 4:
        await m.answer("Пример: /log_workout бег 30 300")
        return

    _, kind, minutes, calories = parts
    save_workout(
        WorkoutLog(
            tg_id=m.from_user.id,
            ts=datetime.utcnow(),
            type=kind,
            minutes=int(minutes),
            calories=float(calories),
            water_ml=0,
        )
    )
    await m.answer("🏃 Тренировка записана")


# ---------- 📊 Прогресс ----------


@dp.message(lambda m: m.text == "📊 Прогресс за сегодня")
@dp.message(Command("check_progress"))
async def today_progress(m: Message):
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0)

    water = sum(w.volume_ml for w in get_water_logs(m.from_user.id, start, now))
    food = sum(f.calories for f in get_food_logs(m.from_user.id, start, now))
    workout = sum(w.calories for w in get_workout_logs(m.from_user.id, start, now))

    await m.answer(f"📊 Сегодня:\n💧 Вода: {water} мл\n🍎 Калории: {food} ккал\n🏃 Сожжено: {workout} ккал")


@dp.message(lambda m: m.text == "📈 Прогресс за неделю")
@dp.message(Command("last_week_progress"))
async def week_progress(m: Message):
    now = datetime.utcnow()
    start = now - timedelta(days=7)

    water = sum(w.volume_ml for w in get_water_logs(m.from_user.id, start, now))
    food = sum(f.calories for f in get_food_logs(m.from_user.id, start, now))
    workout = sum(w.calories for w in get_workout_logs(m.from_user.id, start, now))

    await m.answer(f"📈 За 7 дней:\n💧 Вода: {water} мл\n🍎 Калории: {food} ккал\n🏃 Сожжено: {workout} ккал")


# ---------- Run ----------


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
