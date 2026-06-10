from typing import Optional
from database.mongo import users_col
from datetime import datetime


async def get_user(user_id: int) -> Optional[dict]:
    user = await users_col.find_one({"_id": user_id})
    return user


async def save_user(user_id: int, data: dict) -> None:
    data["_id"] = user_id
    await users_col.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True
    )


async def user_exists(user_id: int) -> bool:
    user = await get_user(user_id)
    return user is not None and user.get("registered", False)


async def update_user_field(user_id: int, field: str, value) -> None:
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {field: value}},
        upsert=True
    )


async def get_all_users() -> dict:
    users = await users_col.find().to_list(length=None)
    return {str(u["_id"]): u for u in users if isinstance(u["_id"], int)}


async def get_all_exercises(user_id: int) -> list:
    user = await get_user(user_id)
    if not user:
        return []
    return list(user.get("results", {}).keys())


async def get_exercise_results(user_id: int, exercise: str) -> list:
    user = await get_user(user_id)
    if not user:
        return []
    return user.get("results", {}).get(exercise, [])


async def save_exercise_result(user_id: int, exercise: str, weight: float, reps: int) -> None:
    user = await get_user(user_id)
    results = {}
    if user:
        results = user.get("results", {})
    if exercise not in results:
        results[exercise] = []
    results[exercise].append({
        "weight": weight,
        "reps": reps,
        "date": datetime.now().strftime("%d.%m.%Y"),
    })
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"results": results}},
        upsert=True
    )


async def get_personal_record(user_id: int, exercise: str) -> dict:
    results = await get_exercise_results(user_id, exercise)
    if not results:
        return {}
    return max(results, key=lambda x: x["weight"])


async def get_giveaway_number() -> int:
    from database.mongo import db
    doc = await db["settings"].find_one({"_id": "giveaway"})
    return doc.get("number", 1) if doc else 1


async def start_new_giveaway(current_user_count: int) -> int:
    from database.mongo import db
    number = await get_giveaway_number() + 1
    await db["settings"].update_one(
        {"_id": "giveaway"},
        {"$set": {"number": number, "start_count": current_user_count}},
        upsert=True
    )
    return number


async def get_channel_link() -> str:
    from database.mongo import db
    doc = await db["settings"].find_one({"_id": "settings"})
    return doc.get("channel_link", None) if doc else None