from dotenv import load_dotenv

load_dotenv()

import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from db import (
    get_food_logs,
    get_user,
    get_water_logs,
    get_workout_logs,
    init_db,
    save_food,
    save_user,
    save_water,
    save_workout,
)
from models import FoodLog, User, WaterLog, WorkoutLog
from services import get_calorie_value, get_current_weather

logging.basicConfig(level=logging.INFO)

bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


class Profile(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()


class FoodFSM(StatesGroup):
    grams = State()


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


def calc_water_goal_ml(user: User, temp_c: float | None) -> tuple[int, str]:
    goal = int(user.weight * 30)
    goal += (user.daily_activity // 30) * 500
    if temp_c is not None and temp_c > 25:
        goal += 700
        mode = "повышенный расход воды"
    else:
        mode = "стандартный расход воды"
    return goal, mode


def calc_calorie_goal(user: User) -> int:
    if user.target_calories is not None:
        return int(user.target_calories)
    base = 10 * user.weight + 6.25 * user.height - 5 * user.age
    kcal_per_min = 5  # линейно: 45 мин -> 225 ккал (в вилке 200–400)
    return int(base + user.daily_activity * kcal_per_min)


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
    save_water(WaterLog(tg_id=m.from_user.id, ts=datetime.now(timezone.utc), volume_ml=ml))
    await m.answer(f"💧 Записал {ml} мл")


@dp.message(lambda m: m.text == "🍎 Прием пищи")
async def menu_food(m: Message):
    await m.answer("Введи: /log_food <продукт>")


@dp.message(Command("log_food"))
async def log_food(m: Message, state: FSMContext):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Пример: /log_food банан")
        return
    product = parts[1].strip()
    kcal_per_g = get_calorie_value(product)
    if kcal_per_g is None:
        await m.answer("Не смог оценить калории, попробуй другое название")
        return
    await state.update_data(product=product, kcal_per_g=float(kcal_per_g))
    await m.answer(f"🍎 {product}: примерно {kcal_per_g} ккал/г. Сколько грамм съел?")
    await state.set_state(FoodFSM.grams)


@dp.message(FoodFSM.grams)
async def food_grams(m: Message, state: FSMContext):
    data = await state.get_data()
    try:
        grams = int(m.text)
    except Exception:
        await m.answer("Нужно число грамм, например 150")
        return
    calories = float(data["kcal_per_g"]) * grams
    save_food(
        FoodLog(
            tg_id=m.from_user.id,
            ts=datetime.now(timezone.utc),
            product=data["product"],
            grams=grams,
            calories=calories,
        )
    )
    await state.clear()
    await m.answer(f"🍎 Записано: {calories:.0f} ккал")


@dp.message(lambda m: m.text == "🏃 Тренировки")
async def menu_workout(m: Message):
    await m.answer("Введи: /log_workout <тип> <мин>")


@dp.message(Command("log_workout"))
async def log_workout(m: Message):
    parts = m.text.split()
    if len(parts) < 3:
        await m.answer("Пример: /log_workout бег 30")
        return
    _, kind, minutes_s = parts[:3]
    try:
        minutes = int(minutes_s)
    except Exception:
        await m.answer("Минуты должны быть числом, пример: /log_workout бег 30")
        return
    kcal_per_min = 10  # грубо, потом улучшим по типу
    calories = float(minutes * kcal_per_min)
    save_workout(
        WorkoutLog(
            tg_id=m.from_user.id,
            ts=datetime.now(timezone.utc),
            type=kind,
            minutes=minutes,
            calories=calories,
            water_ml=0,
        )
    )
    await m.answer(f"🏃 Записал: {kind} {minutes} мин — {calories:.0f} ккал")


@dp.message(lambda m: m.text == "📊 Прогресс за сегодня")
@dp.message(Command("check_progress"))
async def check_progress(m: Message):
    user = get_user(m.from_user.id)
    if user is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return

    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    temp = get_current_weather(user.city)
    water_goal, water_mode = calc_water_goal_ml(user, temp)
    calorie_goal = calc_calorie_goal(user)

    water_drunk = sum(w.volume_ml for w in get_water_logs(user.tg_id, start, now))
    calories_eaten = sum(f.calories for f in get_food_logs(user.tg_id, start, now))
    calories_burned = sum(w.calories for w in get_workout_logs(user.tg_id, start, now))

    water_left = max(0, water_goal - water_drunk)
    calories_left = max(0, calorie_goal - calories_eaten)
    balance = calories_eaten - calories_burned

    t_str = f"{temp:.1f}°C" if temp is not None else "неизвестна"
    await m.answer(
        "📊 Прогресс:\n\n"
        f"Сегодня в городе {user.city} температура {t_str} ({water_mode})\n\n"
        "Вода:\n"
        f"- Выпито: {water_drunk} мл из {water_goal} мл.\n"
        f"- Осталось: {water_left} мл.\n\n"
        "Калории:\n"
        f"- Потреблено: {calories_eaten:.0f} ккал из {calorie_goal} ккал.\n"
        f"- Осталось: {calories_left:.0f} ккал.\n"
        f"- Сожжено: {calories_burned:.0f} ккал.\n"
        f"- Баланс: {balance:.0f} ккал."
    )


@dp.message(lambda m: m.text == "📈 Прогресс за неделю")
@dp.message(Command("last_week_progress"))
async def last_week_progress(m: Message):
    user = get_user(m.from_user.id)
    if user is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)

    water = sum(w.volume_ml for w in get_water_logs(user.tg_id, start, now))
    food = sum(f.calories for f in get_food_logs(user.tg_id, start, now))
    workout = sum(w.calories for w in get_workout_logs(user.tg_id, start, now))

    await m.answer(f"📈 За 7 дней:\n💧 Вода: {water} мл\n🍎 Калории: {food:.0f} ккал\n🏃 Сожжено: {workout:.0f} ккал")


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
