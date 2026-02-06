import random
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, SQLModel, create_engine, select

from models import FoodLog, User, WaterLog, WorkoutLog

engine = create_engine("sqlite:///calories_tracker.db", echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def save_user(user: User):
    with get_session() as s:
        s.merge(user)
        s.commit()


def get_user(tg_id: int) -> User | None:
    with get_session() as s:
        return s.get(User, tg_id)


def save_water(log: WaterLog):
    with get_session() as s:
        s.add(log)
        s.commit()


def save_food(log: FoodLog):
    with get_session() as s:
        s.add(log)
        s.commit()


def save_workout(log: WorkoutLog):
    with get_session() as s:
        s.add(log)
        s.commit()


def get_water_logs(
    tg_id: int,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
):
    with get_session() as s:
        stmt = select(WaterLog).where(WaterLog.tg_id == tg_id)
        if from_ts:
            stmt = stmt.where(WaterLog.ts >= from_ts)
        if to_ts:
            stmt = stmt.where(WaterLog.ts <= to_ts)
        return s.exec(stmt).all()


def get_food_logs(
    tg_id: int,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
):
    with get_session() as s:
        stmt = select(FoodLog).where(FoodLog.tg_id == tg_id)
        if from_ts:
            stmt = stmt.where(FoodLog.ts >= from_ts)
        if to_ts:
            stmt = stmt.where(FoodLog.ts <= to_ts)
        return s.exec(stmt).all()


def get_workout_logs(
    tg_id: int,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
):
    with get_session() as s:
        stmt = select(WorkoutLog).where(WorkoutLog.tg_id == tg_id)
        if from_ts:
            stmt = stmt.where(WorkoutLog.ts >= from_ts)
        if to_ts:
            stmt = stmt.where(WorkoutLog.ts <= to_ts)
        return s.exec(stmt).all()


def clear_user_logs(tg_id: int) -> int:
    with get_session() as s:
        n = 0
        for model in (FoodLog, WaterLog, WorkoutLog):
            stmt = select(model).where(model.tg_id == tg_id)
            rows = s.exec(stmt).all()
            for r in rows:
                s.delete(r)
            n += len(rows)
        s.commit()
        return n


def seed_random_week(tg_id: int):
    """
    Здесь мы тупо генерим случайные данные на неделю назад для проверки работоспособности
    истории
    """
    today = date.today()

    with get_session() as s:
        for i in range(7):
            d = today - timedelta(days=i)
            ts = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

            s.add(
                WaterLog(
                    tg_id=tg_id,
                    ts=ts,
                    volume_ml=random.randint(1200, 3000),
                )
            )

            s.add(
                FoodLog(
                    tg_id=tg_id,
                    ts=ts,
                    product="test food",
                    grams=300,
                    calories=random.randint(1600, 2800),
                )
            )

            mins = random.choice([0, 20, 30, 45])
            if mins:
                s.add(
                    WorkoutLog(
                        tg_id=tg_id,
                        ts=ts,
                        type="test workout",
                        minutes=mins,
                        calories=mins * 10,
                        water_ml=0,
                    )
                )

        s.commit()
