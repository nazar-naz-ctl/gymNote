import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["gymnote"]

# Колекції
users_col = db["users"]
workouts_col = db["workouts"]
programs_col = db["programs"]
saved_tracks_col = db["saved_tracks"]


async def get_user(user_id: int) -> dict | None:
    return await users_col.find_one({"_id": user_id})


async def save_user(user_id: int, data: dict):
    await users_col.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True
    )


async def get_all_users() -> list:
    return await users_col.find().to_list(length=None)


async def delete_user(user_id: int):
    await users_col.delete_one({"_id": user_id})