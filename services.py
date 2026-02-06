import logging
import os

import requests

# load_dotenv()
from openai import OpenAI

OPEN_WEATHER_MAP_API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY")
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")

client = OpenAI(api_key=OPEN_AI_KEY)
logger = logging.getLogger(__name__)


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


# OpenFoodFact - мне не понравился их апи, для моих целей слишком проблемно это все
def get_calorie_value(food: str) -> int | None:
    if not OPEN_AI_KEY:
        raise RuntimeError("OPEN_AI_KEY not set")

    resp = client.responses.create(
        model="gpt-4o-mini", input=f'Сколько килокалорий в 1 грамме продукта "{food}"? Ответь ТОЛЬКО ОДНИМ ЧИСЛОМ.'
    )

    try:
        return int(float(resp.output_text.strip()))
    except Exception:
        return None
