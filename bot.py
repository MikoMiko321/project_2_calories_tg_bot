from dotenv import load_dotenv

load_dotenv()

import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from db import (
    clear_user_logs,
    get_food_logs,
    get_user,
    get_water_logs,
    get_workout_logs,
    init_db,
    save_food,
    save_user,
    save_water,
    save_workout,
    seed_random_week,
)
from models import FoodLog, User, WaterLog, WorkoutLog
from services import get_calorie_value, get_current_weather

logging.basicConfig(level=logging.INFO)

bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()


class LogMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text:
            logging.info("cmd from %s: %s", event.from_user.id, event.text)
        return await handler(event, data)


dp.message.middleware(LogMiddleware())


class Profile(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()


class WaterFSM(StatesGroup):
    volume = State()


class FoodFSM(StatesGroup):
    product = State()
    grams = State()


class WorkoutFSM(StatesGroup):
    kind = State()
    minutes = State()


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="🍎 Прием пищи")],
        [KeyboardButton(text="🏃 Тренировки")],
        [KeyboardButton(text="📊 Прогресс за сегодня")],
        [KeyboardButton(text="🧪 Сгенерировать тестовую неделю")],
        [KeyboardButton(text="📈 Прогресс за неделю")],
        [KeyboardButton(text="⚙️ Редактировать профиль")],
        [KeyboardButton(text="🧹 Сбросить историю")],
    ],
    resize_keyboard=True,
)


def calc_water_goal_ml(
    user: User,
    temp: float | None,
    workout_minutes: int = 0,
) -> tuple[int, str]:
    goal = int(user.weight * 30 + (user.daily_activity // 30) * 500)
    goal += workout_minutes * 10
    reason = "стандартный расход воды"

    if temp is not None and temp > 25:
        goal += 700
        reason = "повышенный расход воды"

    return goal, reason


def calc_calorie_goal(user: User) -> int:
    base = 10 * user.weight + 6.25 * user.height - 5 * user.age
    return int(base + user.daily_activity * 5)


@dp.message(Command("start"))
async def start(m: Message):
    if get_user(m.from_user.id) is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return
    await m.answer("Меню:", reply_markup=main_menu)


@dp.message(Command("set_profile"))
@dp.message(lambda m: m.text == "⚙️ Редактировать профиль")
async def set_profile(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Введите вес (кг):")
    await state.set_state(Profile.weight)


@dp.message(Profile.weight)
async def p_weight(m: Message, state: FSMContext):
    await state.update_data(weight=float(m.text))
    await m.answer("Введите рост (см):")
    await state.set_state(Profile.height)


@dp.message(Profile.height)
async def p_height(m: Message, state: FSMContext):
    await state.update_data(height=float(m.text))
    await m.answer("Введите возраст:")
    await state.set_state(Profile.age)


@dp.message(Profile.age)
async def p_age(m: Message, state: FSMContext):
    await state.update_data(age=int(m.text))
    await m.answer("Минут активности в день:")
    await state.set_state(Profile.activity)


@dp.message(Profile.activity)
async def p_activity(m: Message, state: FSMContext):
    await state.update_data(activity=int(m.text))
    await m.answer("Город:")
    await state.set_state(Profile.city)


@dp.message(Profile.city)
async def p_city(m: Message, state: FSMContext):
    data = await state.get_data()
    save_user(User(tg_id=m.from_user.id, **data))
    await state.clear()
    await m.answer("Профиль сохранён ✅", reply_markup=main_menu)


@dp.message(Command("log_water"))
@dp.message(lambda m: m.text == "💧 Вода")
async def water_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Сколько мл воды выпил (мл)?")
    await state.set_state(WaterFSM.volume)


@dp.message(WaterFSM.volume)
async def water_save(m: Message, state: FSMContext):
    ml = int(m.text)
    save_water(WaterLog(tg_id=m.from_user.id, ts=datetime.now(timezone.utc), volume_ml=ml))
    await state.clear()
    await m.answer(f"💧 Записал {ml} мл", reply_markup=main_menu)


@dp.message(Command("log_food"))
@dp.message(lambda m: m.text == "🍎 Прием пищи")
async def food_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Что ты съел?")
    await state.set_state(FoodFSM.product)


@dp.message(FoodFSM.product)
async def food_product(m: Message, state: FSMContext):
    kcal = get_calorie_value(m.text)
    if kcal is None:
        await m.answer("Не понял продукт, попробуй иначе")
        return
    await state.update_data(product=m.text, kcal=kcal)
    await m.answer("Сколько грамм?")
    await state.set_state(FoodFSM.grams)


@dp.message(FoodFSM.grams)
async def food_grams(m: Message, state: FSMContext):
    data = await state.get_data()
    grams = int(m.text)
    calories = grams * data["kcal"]
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
    await m.answer(f"🍎 Записано {calories:.0f} ккал", reply_markup=main_menu)


@dp.message(Command("log_workout"))
@dp.message(lambda m: m.text == "🏃 Тренировки")
async def workout_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Тип тренировки?")
    await state.set_state(WorkoutFSM.kind)


@dp.message(WorkoutFSM.kind)
async def workout_kind(m: Message, state: FSMContext):
    await state.update_data(kind=m.text)
    await m.answer("Сколько минут?")
    await state.set_state(WorkoutFSM.minutes)


@dp.message(WorkoutFSM.minutes)
async def workout_minutes(m: Message, state: FSMContext):
    data = await state.get_data()
    minutes = int(m.text)
    calories = minutes * 10
    save_workout(
        WorkoutLog(
            tg_id=m.from_user.id,
            ts=datetime.now(timezone.utc),
            type=data["kind"],
            minutes=minutes,
            calories=calories,
            water_ml=0,
        )
    )
    await state.clear()
    await m.answer("🏃 Тренировка записана", reply_markup=main_menu)


@dp.message(Command("check_progress"))
@dp.message(lambda m: m.text == "📊 Прогресс за сегодня")
async def progress_today(m: Message):
    user = get_user(m.from_user.id)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    temp = get_current_weather(user.city)

    workout_minutes = sum(w.minutes for w in get_workout_logs(user.tg_id, start, now))
    water_goal, mode = calc_water_goal_ml(user, temp, workout_minutes)
    calorie_goal = calc_calorie_goal(user)

    water = sum(w.volume_ml for w in get_water_logs(user.tg_id, start, now))
    food = sum(f.calories for f in get_food_logs(user.tg_id, start, now))
    workout = sum(w.calories for w in get_workout_logs(user.tg_id, start, now))

    await m.answer(
        f"📊 Прогресс\n\n"
        f"🌡 {user.city}: {temp}°C ({mode})\n\n"
        f"💧 {water}/{water_goal} мл\n"
        f"🍎 {food}/{calorie_goal} ккал\n"
        f"🏃 Сожжено: {workout} ккал\n"
        f"⚖ Баланс: {food - calorie_goal - workout} ккал"
    )


@dp.message(Command("week_progress"))
@dp.message(lambda m: m.text == "📈 Прогресс за неделю")
async def progress_week(m: Message):
    user = get_user(m.from_user.id)
    if user is None:
        await m.answer("Сначала создай профиль: /set_profile")
        return

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)

    food_logs = get_food_logs(user.tg_id, start, now)
    water_logs = get_water_logs(user.tg_id, start, now)
    workout_logs = get_workout_logs(user.tg_id, start, now)

    by_day = defaultdict(lambda: {"food": 0, "water": 0, "burned": 0})

    for f in food_logs:
        day = f.ts.date()
        by_day[day]["food"] += f.calories

    for w in water_logs:
        day = w.ts.date()
        by_day[day]["water"] += w.volume_ml

    for w in workout_logs:
        day = w.ts.date()
        by_day[day]["burned"] += w.calories

    lines = ["📈 Прогресс за 7 дней:\n"]
    for day in sorted(by_day.keys(), reverse=True):
        d = by_day[day]
        lines.append(
            f"{day}:\n"
            f"  💧 Вода: {d['water']} мл\n"
            f"  🍎 Калории: {int(d['food'])} ккал\n"
            f"  🏃 Сожжено: {int(d['burned'])} ккал\n"
        )

    await m.answer("\n".join(lines))


@dp.message(lambda m: m.text == "🧪 Сгенерировать тестовую неделю")
async def seed_week_menu(m: Message):
    seed_random_week(m.from_user.id)
    await m.answer("🧪 Тестовая неделя сгенерирована", reply_markup=main_menu)


@dp.message(Command("reset_history"))
@dp.message(lambda m: m.text == "🧹 Сбросить историю")
async def reset_history(m: Message):
    deleted = clear_user_logs(m.from_user.id)
    await m.answer(
        f"🧹 История очищена.\nУдалено записей: {deleted}",
        reply_markup=main_menu,
    )


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
