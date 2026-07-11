from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from bson import ObjectId
from dotenv import load_dotenv
from database.mongo import db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Авторизація
# ============================================================

def verify_telegram(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="No init data")

    # ВАЖЛИВО: parse_qsl сам декодує URL-encoded значення.
    # Ручний split("&")/split("=") ламав hash, бо Telegram підписує
    # ДЕКОДОВАНІ значення, а не сирий url-encoded рядок.
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_val = parsed.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, hash_val):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return json.loads(parsed.get("user", "{}"))


def get_user_id(request: Request) -> int:
    # Більше НЕМАЄ бекдору через X-Telegram-User-Id — тільки initData.
    init_data = request.headers.get("X-Init-Data", "")
    tg_user = verify_telegram(init_data)
    user_id = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


# ============================================================
# Профіль користувача
# ============================================================

@app.get("/api/user")
async def get_user(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user_id,
        "name": user.get("name", ""),
        "username": user.get("username", ""),
        "subscription": user.get("subscription", "free"),
        "subscription_end": user.get("subscription_end"),
        "level": user.get("level", "beginner"),
        "goal": user.get("goal", ""),
        "location": user.get("location", ""),
        "days": user.get("days", 3),
        "xp": user.get("xp", 0),
        "gymcoin": user.get("gymcoin", 0),
        "streak": user.get("streak", 0),
        "workouts_count": user.get("workouts_count", 0),
    }


# ============================================================
# Особисті рекорди
# ============================================================

@app.get("/api/records")
async def get_records(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    results = user.get("results", {})
    records = []
    for exercise, sets in results.items():
        if sets:
            best = max(sets, key=lambda s: s.get("weight", 0))
            records.append({
                "exercise": exercise,
                "weight": best.get("weight", 0),
                "reps": best.get("reps", 0),
                "date": best.get("date", ""),
            })
    return {"records": records}


# ============================================================
# Журнал тренувань (історія)
# ============================================================

@app.get("/api/journal")
async def get_journal(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    results = user.get("results", {})
    entries = []
    dates = {}
    for exercise, sets in results.items():
        for s in sets:
            date = s.get("date", "")
            if date not in dates:
                dates[date] = []
            dates[date].append({
                "exercise": exercise,
                "weight": s.get("weight", 0),
                "reps": s.get("reps", 0),
            })
    for date, sets in sorted(dates.items(), reverse=True):
        entries.append({"date": date, "sets": sets})
    return {"journal": entries}


# ============================================================
# Кастомні тренування
# ============================================================

@app.get("/api/workouts")
async def get_workouts(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"workouts": user.get("custom_workouts", [])}


# ============================================================
# Програми тренувань
# ============================================================

@app.get("/api/programs")
async def get_programs(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    level = user.get("level", "beginner")
    location = user.get("location", "gym")
    programs = [
        {"id": "gym_beginner_1", "name": "Фулбоді для початківців", "location": "gym", "level": "beginner", "days": 3, "description": "Базова програма для початку"},
        {"id": "gym_beginner_2", "name": "Спліт верх/низ", "location": "gym", "level": "beginner", "days": 4, "description": "Розподіл на верх і низ тіла"},
        {"id": "gym_intermediate_1", "name": "Спліт 4 дні", "location": "gym", "level": "intermediate", "days": 4, "description": "Класичний спліт для середнього рівня"},
        {"id": "gym_advanced_1", "name": "PPL програма", "location": "gym", "level": "advanced", "days": 6, "description": "Push Pull Legs"},
        {"id": "home_beginner_1", "name": "Вдома без інвентарю", "location": "home", "level": "beginner", "days": 3, "description": "Тренування вдома"},
        {"id": "home_intermediate_1", "name": "Схуднення вдома", "location": "home", "level": "intermediate", "days": 4, "description": "Кардіо та силові"},
        {"id": "outdoor_beginner_1", "name": "Каліcтеніка початок", "location": "outdoor", "level": "beginner", "days": 3, "description": "На турніку та брусах"},
        {"id": "outdoor_advanced_1", "name": "Воркаут атлет", "location": "outdoor", "level": "advanced", "days": 5, "description": "Просунута каліcтеніка"},
    ]
    recommended = [p for p in programs if p["level"] == level and p["location"] == location]
    return {
        "programs": programs,
        "recommended": recommended,
        "user_level": level,
        "user_location": location,
    }


# ============================================================
# Статистика
# ============================================================

@app.get("/api/stats")
async def get_stats(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    results = user.get("results", {})
    total_sets = sum(len(sets) for sets in results.values())
    return {
        "workouts_count": user.get("workouts_count", 0),
        "streak": user.get("streak", 0),
        "records_count": len(results),
        "total_sets": total_sets,
        "xp": user.get("xp", 0),
        "gymcoin": user.get("gymcoin", 0),
    }


# ============================================================
# Session Engine — журнал тренувань у реальному часі
# ============================================================

# ⚠️ ЗАГЛУШКА: поки що беремо фіксований шаблон дня, бо ще не звʼязано
# з генератором програм. Коли будемо інтегрувати реальні програми,
# треба буде замінити get_today_template() на вибір дня з активної
# програми користувача (user["active_program"]).
DEFAULT_DAY_TEMPLATE = {
    "day_label": "День 1",
    "exercises": [
        {"name": "Жим лежачи", "type": "Базова · Груди", "rest": 90,
         "planned": [{"weight": 80, "reps": 10}, {"weight": 80, "reps": 10}, {"weight": 80, "reps": 8}, {"weight": 75, "reps": 10}]},
        {"name": "Тяга штанги в нахилі", "type": "Базова · Спина", "rest": 90,
         "planned": [{"weight": 60, "reps": 10}, {"weight": 60, "reps": 10}, {"weight": 60, "reps": 8}]},
        {"name": "Жим гантелей сидячи", "type": "Допоміжна · Плечі", "rest": 60,
         "planned": [{"weight": 22, "reps": 12}, {"weight": 22, "reps": 12}]},
    ],
}


def get_previous_result(user: dict, exercise_name: str) -> str:
    """Повертає текстове представлення останнього результату по вправі, або '—'."""
    sets = user.get("results", {}).get(exercise_name, [])
    if not sets:
        return "—"
    last = sets[-1]
    return f"{last.get('weight', 0)} × {last.get('reps', 0)}"


def get_best_weight(user: dict, exercise_name: str) -> float:
    """Максимальна вага, коли-небудь записана по цій вправі (для визначення PR)."""
    sets = user.get("results", {}).get(exercise_name, [])
    if not sets:
        return 0
    return max(s.get("weight", 0) for s in sets)


def build_session_response(doc: dict) -> dict:
    """Формує відповідь у форматі, який очікує journal.js."""
    return {
        "session_id": str(doc["_id"]),
        "day_label": doc["day_label"],
        "current_exercise_idx": doc.get("current_exercise_idx", 0),
        "current_set_idx": doc.get("current_set_idx", 0),
        "volume_so_far": doc.get("volume_so_far", 0),
        "exercises": [
            {
                "name": ex["name"],
                "type": ex["type"],
                "rest": ex["rest"],
                "prev": ex["prev"],
                "sets": ex["planned"],
            }
            for ex in doc["exercises"]
        ],
    }


@app.get("/api/session/current")
async def get_current_session(request: Request):
    user_id = get_user_id(request)
    doc = await db["sessions"].find_one({"user_id": user_id, "status": "in_progress"})
    if not doc:
        return {"session": None}
    return {"session": build_session_response(doc)}


@app.post("/api/session/start")
async def start_session(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Якщо вже є незавершена сесія — повертаємо саме її, не створюємо нову
    existing = await db["sessions"].find_one({"user_id": user_id, "status": "in_progress"})
    if existing:
        return build_session_response(existing)

    template = DEFAULT_DAY_TEMPLATE  # TODO: замінити на реальний день з активної програми
    exercises = []
    for ex in template["exercises"]:
        exercises.append({
            "name": ex["name"],
            "type": ex["type"],
            "rest": ex["rest"],
            "planned": ex["planned"],
            "actual": [],
            "prev": get_previous_result(user, ex["name"]),
        })

    doc = {
        "user_id": user_id,
        "status": "in_progress",
        "day_label": template["day_label"],
        "exercises": exercises,
        "current_exercise_idx": 0,
        "current_set_idx": 0,
        "volume_so_far": 0,
        "started_at": datetime.now(timezone.utc),
        "finished_at": None,
    }
    result = await db["sessions"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return build_session_response(doc)


@app.post("/api/session/log_set")
async def log_set(request: Request):
    user_id = get_user_id(request)
    body = await request.json()

    session_id = body.get("session_id")
    exercise_idx = body.get("exercise_idx")
    set_idx = body.get("set_idx")
    weight = float(body.get("weight", 0))
    reps = int(body.get("reps", 0))

    doc = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if doc["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Session already finished")

    user = await db["users"].find_one({"_id": user_id})
    exercise = doc["exercises"][exercise_idx]
    best_before = get_best_weight(user, exercise["name"])
    is_pr = weight > best_before
    delta = round(weight - best_before, 1) if is_pr and best_before > 0 else None

    new_entry = {"weight": weight, "reps": reps, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}

    # Рахуємо наступну позицію (та сама логіка, що й на фронті)
    total_sets_in_ex = len(exercise["planned"])
    is_last_set_of_ex = set_idx == total_sets_in_ex - 1
    is_last_ex = exercise_idx == len(doc["exercises"]) - 1

    if is_last_set_of_ex and not is_last_ex:
        next_ex_idx, next_set_idx = exercise_idx + 1, 0
    elif not is_last_set_of_ex:
        next_ex_idx, next_set_idx = exercise_idx, set_idx + 1
    else:
        next_ex_idx, next_set_idx = exercise_idx, set_idx  # останній підхід — фініш обробить finish()

    await db["sessions"].update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {f"exercises.{exercise_idx}.actual": new_entry},
            "$inc": {"volume_so_far": weight * reps},
            "$set": {"current_exercise_idx": next_ex_idx, "current_set_idx": next_set_idx},
        },
    )

    return {"is_pr": is_pr, "exercise": exercise["name"], "delta": delta}


@app.post("/api/session/finish")
async def finish_session(request: Request):
    user_id = get_user_id(request)
    body = await request.json()
    session_id = body.get("session_id")

    doc = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if doc["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Session already finished")

    user = await db["users"].find_one({"_id": user_id})
    finished_at = datetime.now(timezone.utc)
    duration_sec = int((finished_at - doc["started_at"]).total_seconds())

    total_volume = 0
    prs = []
    results_update = {}

    for ex in doc["exercises"]:
        name = ex["name"]
        best_before = get_best_weight(user, name)
        best_in_session = 0
        for entry in ex["actual"]:
            total_volume += entry["weight"] * entry["reps"]
            best_in_session = max(best_in_session, entry["weight"])
        if best_in_session > best_before and ex["actual"]:
            prs.append({"exercise": name, "delta": round(best_in_session - best_before, 1)})
        if ex["actual"]:
            results_update[f"results.{name}"] = ex["actual"]

    # Дописуємо результати в профіль користувача (додаємо до існуючого списку по кожній вправі)
    for field, new_sets in results_update.items():
        exercise_name = field.split(".", 1)[1]
        await db["users"].update_one(
            {"_id": user_id},
            {"$push": {f"results.{exercise_name}": {"$each": new_sets}}},
        )

    await db["users"].update_one(
        {"_id": user_id},
        {"$inc": {"workouts_count": 1}},
    )

    await db["sessions"].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"status": "finished", "finished_at": finished_at}},
    )

    # Стрік/XP/рівень — нараховує сам бот окремим повідомленням (не тут),
    # щоб не дублювати логіку гейміфікації в двох місцях.

    return {"duration_sec": duration_sec, "total_volume": total_volume, "prs": prs}
