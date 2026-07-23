from typing import Optional
from database.mongo import users_col, saved_tracks_col
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


async def save_last_workout(user_id: int, workout_name: str, completed_sets: dict) -> None:
    now = datetime.now()
    record = {
        "name": workout_name,
        "completed_sets": completed_sets,
        "date": now.strftime("%d.%m.%Y %H:%M"),
    }

    user = await users_col.find_one({"_id": user_id})
    update_fields = {"last_workout": record}
    if not user or not user.get("first_workout_at"):
        update_fields["first_workout_at"] = now.isoformat()

    await users_col.update_one(
        {"_id": user_id},
        {
            "$set": update_fields,
            "$push": {
                "workout_history": {
                    "$each": [record],
                    "$slice": -200,  # тримаємо лише останні 200 — без цього документ МОГ БИ рости безмежно
                }
            },
        },
        upsert=True
    )


async def get_workout_history(user_id: int, limit: int = 50) -> list:
    """Повертає останні limit завершених тренувань, найновіші спершу."""
    user = await users_col.find_one({"_id": user_id})
    if not user:
        return []
    history = user.get("workout_history", [])
    return list(reversed(history))[:limit]


async def count_completed_workouts(user_id: int) -> int:
    user = await users_col.find_one({"_id": user_id})
    if not user:
        return 0
    return len(user.get("workout_history", []))


async def get_last_workout(user_id: int) -> Optional[dict]:
    user = await get_user(user_id)
    if not user:
        return None
    return user.get("last_workout")


from bson import ObjectId
from datetime import datetime

async def add_saved_track(user_id: int, title: str, performer: str, file_id: str) -> str:
    """Зберігає трек користувача. Повертає id збереженого запису."""
    doc = {
        "user_id": user_id,
        "title": title or "Невідомий трек",
        "performer": performer or "Невідомий виконавець",
        "file_id": file_id,
        "saved_at": datetime.utcnow(),
    }
    result = await saved_tracks_col.insert_one(doc)
    return str(result.inserted_id)


async def get_saved_tracks(user_id: int) -> list[dict]:
    """Список збережених треків, найновіші перші."""
    cursor = saved_tracks_col.find({"user_id": user_id}).sort("saved_at", -1)
    tracks = await cursor.to_list(length=100)
    for t in tracks:
        t["_id"] = str(t["_id"])
    return tracks


async def get_saved_track(user_id: int, track_id: str) -> dict | None:
    track = await saved_tracks_col.find_one({"_id": ObjectId(track_id), "user_id": user_id})
    if track:
        track["_id"] = str(track["_id"])
    return track


async def delete_saved_track(user_id: int, track_id: str) -> bool:
    result = await saved_tracks_col.delete_one({"_id": ObjectId(track_id), "user_id": user_id})
    return result.deleted_count > 0


async def is_track_saved(user_id: int, file_id: str) -> bool:
    track = await saved_tracks_col.find_one({"user_id": user_id, "file_id": file_id})
    return track is not None