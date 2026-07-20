import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
TRAINER_ID: int = int(os.getenv("TRAINER_ID", "0"))
BOT_NAME: str = "GymNote"
VERSION: str = "1.0.0"

# Premium-обмеження (ліміт 1 генерація/тиждень для безкоштовного тарифу)
# тимчасово вимкнено — усі користувачі мають повний доступ, поки проєкт
# не розросся до масштабу, де монетизація стане потрібною. Щоб знову
# увімкнути обмеження — просто зміни на True, решта коду не займати.
PREMIUM_ENABLED: bool = False