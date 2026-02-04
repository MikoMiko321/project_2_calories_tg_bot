class UserProfile:
    def __init__(
        self,
        tg_id: int,
        weight: float,
        height: float,
        age: int,
        daily_activity: int,
        city: str,
        target_calories: int | None = None,
    ):
        self.tg_id = tg_id
        self.weight = weight
        self.height = height
        self.age = age
        self.daily_activity = daily_activity
        self.city = city
        if target_calories:
            self.target_calories = target_calories
        else:
            self.target_calories = self._target_calories_calc()

    def _target_calories_calc(self) -> int:
        return int(10 * self.weight + 6.25 * self.height - 5 * self.age + 300)


def DailyActivity():
    pass
