from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import hmac
import json
import os
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


def verify_telegram(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="No init data")
    parsed = {}
    for part in init_data.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            parsed[k] = v
    hash_val = parsed.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, hash_val):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return json.loads(parsed.get("user", "{}"))


def get_user_id(request: Request) -> int:
    init_data = request.headers.get("X-Init-Data", "")
    tg_user = verify_telegram(init_data)
    return tg_user.get("id")


# ── Профіль користувача ──
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


# ── Особисті рекорди ──
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


# ── Журнал тренувань ──
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


# ── Кастомні тренування ──
@app.get("/api/workouts")
async def get_workouts(request: Request):
    user_id = get_user_id(request)
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"workouts": user.get("custom_workouts", [])}


# ── Програми тренувань ──
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


# ── Статистика ──
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