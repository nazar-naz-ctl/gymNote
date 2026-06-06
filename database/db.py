import json
import os
import aiofiles
from typing import Optional

DB_PATH = "data/users.json"


async def _load() -> dict:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DB_PATH):
        return {}
    async with aiofiles.open(DB_PATH, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content) if content.strip() else {}


async def _save(data: dict) -> None:
    os.makedirs("data", exist_ok=True)
    async with aiofiles.open(DB_PATH, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


async def get_user(user_id: int) -> Optional[dict]:
    db = await _load()
    return db.get(str(user_id))


async def save_user(user_id: int, data: dict) -> None:
    db = await _load()
    db[str(user_id)] = data
    await _save(db)


async def user_exists(user_id: int) -> bool:
    user = await get_user(user_id)
    return user is not None and user.get("registered", False)


async def update_user_field(user_id: int, field: str, value) -> None:
    db = await _load()
    if str(user_id) not in db:
        db[str(user_id)] = {}
    db[str(user_id)][field] = value
    await _save(db)


async def get_all_users() -> dict:
    return await _load()


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
    db = await _load()
    key = str(user_id)
    if key not in db:
        db[key] = {}
    if "results" not in db[key]:
        db[key]["results"] = {}
    if exercise not in db[key]["results"]:
        db[key]["results"][exercise] = []
    from datetime import datetime
    db[key]["results"][exercise].append({
        "weight": weight,
        "reps": reps,
        "date": datetime.now().strftime("%d.%m.%Y"),
    })
    await _save(db)


async def get_personal_record(user_id: int, exercise: str) -> dict:
    results = await get_exercise_results(user_id, exercise)
    if not results:
        return {}
    return max(results, key=lambda x: x["weight"])


async def get_giveaway_number() -> int:
    db = await _load()
    return db.get("giveaway_number", 1)


async def start_new_giveaway(current_user_count: int) -> int:
    db = await _load()
    number = db.get("giveaway_number", 1) + 1
    db["giveaway_number"] = number
    db["giveaway_start_count"] = current_user_count
    await _save(db)
    return number


async def get_channel_link() -> str:
    db = await _load()
    return db.get("channel_link", None)