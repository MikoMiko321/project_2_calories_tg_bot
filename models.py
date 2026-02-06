from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    tg_id: int = Field(primary_key=True)
    weight: float
    height: float
    age: int
    daily_activity: int
    city: str
    target_calories: int | None = None


class WaterLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(foreign_key="user.tg_id")
    ts: datetime
    volume_ml: int


class FoodLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(foreign_key="user.tg_id")
    ts: datetime
    product: str
    grams: int
    calories: float


class WorkoutLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(foreign_key="user.tg_id")
    ts: datetime
    type: str
    minutes: int
    calories: float
    water_ml: int
