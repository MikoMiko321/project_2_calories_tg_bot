from datetime import datetime

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
