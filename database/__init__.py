from datetime import datetime
from database.mongo import users_col
from typing import Optional
from .db import (
    get_user,
    save_user,
    user_exists,
    update_user_field,
    get_all_users,
    get_all_exercises,
    get_exercise_results,
    save_exercise_result,
    get_personal_record,
    get_giveaway_number,
    start_new_giveaway,
    get_channel_link,
save_last_workout,
    get_last_workout,
)

all = [
    "get_user",
    "save_user",
    "user_exists",
    "update_user_field",
    "get_all_users",
    "get_all_exercises",
    "get_exercise_results",
    "save_exercise_result",
    "get_personal_record",
    "get_giveaway_number",
    "start_new_giveaway",
    "get_channel_link",
]


async def save_last_workout(user_id: int, workout_name: str, completed_sets: dict) -> None:
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"last_workout": {
            "name": workout_name,
            "completed_sets": completed_sets,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }}},
        upsert=True
    )


async def get_last_workout(user_id: int) -> Optional[dict]:
    user = await get_user(user_id)
    if not user:
        return None
    return user.get("last_workout")


async def update_streak(user_id: int) -> dict:
    from datetime import datetime, timedelta
    user = await get_user(user_id)
    if not user:
        return {"current": 0, "best": 0}

    today = datetime.now().strftime("%d.%m.%Y")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

    current_streak = user.get("streak_current", 0)
    best_streak = user.get("streak_best", 0)
    last_workout_date = user.get("streak_last_date", "")

    if last_workout_date == today:
        pass
    elif last_workout_date == yesterday:
        current_streak += 1
    else:
        current_streak = 1

    if current_streak > best_streak:
        best_streak = current_streak

    await users_col.update_one(
        {"_id": user_id},
        {"$set": {
            "streak_current": current_streak,
            "streak_best": best_streak,
            "streak_last_date": today,
        }},
        upsert=True
    )
    return {"current": current_streak, "best": best_streak}


async def get_streak(user_id: int) -> dict:
    user = await get_user(user_id)
    if not user:
        return {"current": 0, "best": 0}
    return {
        "current": user.get("streak_current", 0),
        "best": user.get("streak_best", 0),
    }