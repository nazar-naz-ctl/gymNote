import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
TRAINER_ID: int = int(os.getenv("TRAINER_ID", "0"))
BOT_NAME: str = "GymNote"
VERSION: str = "1.0.0"