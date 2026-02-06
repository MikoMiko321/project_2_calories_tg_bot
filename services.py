import logging
import os

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

OPEN_WEATHER_MAP_API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY")

# OpenAI сам читает OPENAI_API_KEY из env
client = OpenAI()


def get_current_weather(city: str) -> float | None:
    if not OPEN_WEATHER_MAP_API_KEY:
        raise RuntimeError("OPEN_WEATHER_MAP_API_KEY not set")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPEN_WEATHER_MAP_API_KEY,
        "units": "metric",
    }

    resp = requests.get(url, params=params, timeout=10)
    logger.info(f"{params} {resp.status_code}")
    resp.raise_for_status()

    try:
        return float(resp.json()["main"]["temp"])
    except Exception:
        return None


def get_calorie_value(food: str) -> float | None:
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=(f'Сколько килокалорий в 1 грамме продукта "{food}"? Ответь одним числом, например: 0.89'),
    )

    try:
        return float(resp.output_text.strip())
    except Exception:
        return None
