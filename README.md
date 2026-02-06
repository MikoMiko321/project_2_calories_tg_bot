users

tg_id (PK)

weight, height, age, daily_activity, city, target_calories

water_logs

id (PK), tg_id (FK), ts, volume_ml

food_logs

id (PK), tg_id (FK), ts, product, grams, calories

workout_logs

id (PK), tg_id (FK), ts, type, minutes, calories, water_ml
