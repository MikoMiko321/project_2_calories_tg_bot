project_2_calories_tg_bot/
├─ bot.py
├─ config.py
├─ users.py
├─ calculations.py
├─ food_api.py
├─ weather_api.py
├─ requirements.txt
└─ README.md

users

tg_id (PK)

weight, height, age, daily_activity, city, target_calories

water_logs

id (PK), tg_id (FK), ts, volume_ml

food_logs

id (PK), tg_id (FK), ts, product, grams, calories

workout_logs

id (PK), tg_id (FK), ts, type, minutes, calories, water_ml
