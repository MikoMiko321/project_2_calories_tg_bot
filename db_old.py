import sqlite3
from pathlib import Path

from models import FoodLog, User, WaterLog, WorkoutLog

DB_PATH = Path("app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        weight REAL,
        height REAL,
        age INTEGER,
        daily_activity INTEGER,
        city TEXT,
        target_calories INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS water_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        ts TEXT,
        volume_ml INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        ts TEXT,
        product TEXT,
        grams INTEGER,
        calories REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        ts TEXT,
        type TEXT,
        minutes INTEGER,
        calories REAL,
        water_ml INTEGER
    )
    """)

    conn.commit()
    conn.close()


def create_or_update_user(user: User):
    conn = get_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO users
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.tg_id,
            user.weight,
            user.height,
            user.age,
            user.daily_activity,
            user.city,
            user.target_calories,
        ),
    )
    conn.commit()
    conn.close()


def insert_water(log: WaterLog):
    conn = get_conn()
    conn.execute(
        "INSERT INTO water_logs (tg_id, ts, volume_ml) VALUES (?, ?, ?)",
        (log.tg_id, log.ts.isoformat(), log.volume_ml),
    )
    conn.commit()
    conn.close()


def insert_food(log: FoodLog):
    conn = get_conn()
    conn.execute(
        "INSERT INTO food_logs (tg_id, ts, product, grams, calories) VALUES (?, ?, ?, ?, ?)",
        (log.tg_id, log.ts.isoformat(), log.product, log.grams, log.calories),
    )
    conn.commit()
    conn.close()


def insert_workout(log: WorkoutLog):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO workout_logs (tg_id, ts, type, minutes, calories, water_ml)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (log.tg_id, log.ts.isoformat(), log.type, log.minutes, log.calories, log.water_ml),
    )
    conn.commit()
    conn.close()


if not DB_PATH.exists():
    init_db()
