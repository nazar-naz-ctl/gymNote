import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, BOT_NAME
from handlers import main_router
from database import get_all_users, update_user_field, get_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(BOT_NAME)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


async def check_subscriptions_daily():
    while True:
        await asyncio.sleep(86400)
        logger.info("🔄 Перевірка підписок...")
        try:
            all_users = await get_all_users()
            today = datetime.now()
            for uid, data in all_users.items():
                try:
                    user_id = int(uid)
                except ValueError:
                    continue
                if not isinstance(data, dict):
                    continue
                sub = data.get("subscription", "free")
                if sub == "free":
                    continue
                trial_end = data.get("trial_end")
                sub_end = data.get("subscription_end")
                end_date_str = None
                is_trial = False
                if trial_end and sub == "premium":
                    end_date_str = trial_end
                    is_trial = True
                elif sub_end and sub in ("premium", "standard"):
                    end_date_str = sub_end
                if not end_date_str:
                    continue
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                    days_left = (end_date - today).days
                    if days_left == 2:
                        if is_trial:
                            msg = "⚠️ Через 2 дні закінчується твій пробний період Преміум.\n\nОформи підписку в розділі 💳 Підписка."
                        else:
                            msg = "⚠️ Через 2 дні закінчується твоя підписка.\n\nОформи підписку в розділі 💳 Підписка."
                        try:
                            await bot.send_message(user_id, msg)
                            # Сповіщення тренеру
                            try:
                                from config import TRAINER_ID
                                user = await get_user(user_id)
                                name = user.get("name", "—") if user else "—"
                                await bot.send_message(
                                    TRAINER_ID,
                                    f"⚠ <b>Підписка закінчується!</b>\n\n"
                                    f"Клієнт: {name}\n"
                                    f"ID: <code>{user_id}</code>\n"
                                    f"Залишилось: 2 дні",
                                )
                            except Exception:
                                pass
                        except Exception:
                            pass
                    elif days_left < 0:
                        await update_user_field(user_id, "subscription", "free")
                        if is_trial:
                            await update_user_field(user_id, "trial_end", None)
                        else:
                            await update_user_field(user_id, "subscription_end", None)
                        try:
                            await bot.send_message(
                                user_id,
                                "😔 Твоя підписка закінчилась і ти перейшов на безкоштовний тариф.\n\n"
                                "Щоб продовжити — оформи підписку в розділі 💳 Підписка."
                            )
                        except Exception:
                            pass
                except ValueError:
                    continue
        except Exception as e:
            logger.error(f"Помилка перевірки підписок: {e}")


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)
    logger.info(f"🚀 {BOT_NAME} запущено")
    asyncio.create_task(check_subscriptions_daily())
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info(f"⛔️ {BOT_NAME} зупинено")


if __name__ == "__main__":
    asyncio.run(main())