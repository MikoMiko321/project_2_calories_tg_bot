from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    tg_id: int
    weight: float
    height: float
    age: int
    daily_activity: int
    city: str
    target_calories: int | None = None


class WaterLog(BaseModel):
    id: int | None = None
    tg_id: int
    ts: datetime
    volume_ml: int


class FoodLog(BaseModel):
    id: int | None = None
    tg_id: int
    ts: datetime
    product: str
    grams: int
    calories: float


class WorkoutLog(BaseModel):
    id: int | None = None
    tg_id: int
    ts: datetime
    type: str
    minutes: int
    calories: float
    water_ml: int
