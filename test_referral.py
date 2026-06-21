from dotenv import load_dotenv
load_dotenv()
import asyncio
from datetime import datetime
from database import get_user, update_user_field, save_user

# ── Налаштування тесту ──
REFERRER_ID = 8959011768  # твій реальний Telegram ID
NEW_USER_ID = 999999999  # вигаданий новий юзер


async def test():
    print("=== ТЕСТ РЕФЕРАЛЬНОЇ СИСТЕМИ ===\n")

    # 1. Перевіряємо реферера до тесту
    referrer = await get_user(REFERRER_ID)
    if not referrer:
        print(f"❌ Реферер {REFERRER_ID} не знайдений в базі!")
        return

    print(
        f"📋 Реферер ДО: subscription={referrer.get('subscription')}, trial_end={referrer.get('trial_end')}, subscription_end={referrer.get('subscription_end')}")

    # 2. Симулюємо нового юзера з реферальним кодом
    await save_user(NEW_USER_ID, {
        "id": NEW_USER_ID,
        "name": "Тестовий Юзер",
        "username": "test_user",
        "subscription": "premium",
        "trial_end": (datetime.now().strftime("%Y-%m-%d")),
        "referred_by": REFERRER_ID,
        "registered": True,
    })
    print(f"✅ Новий юзер {NEW_USER_ID} створений з referred_by={REFERRER_ID}")

    # 3. Запускаємо логіку +7 днів
    from datetime import timedelta
    referrer = await get_user(REFERRER_ID)
    ref_trial = referrer.get("trial_end")
    ref_sub_end = referrer.get("subscription_end")

    base_date = datetime.now()
    if ref_trial:
        try:
            d = datetime.strptime(ref_trial, "%Y-%m-%d")
            if d > base_date:
                base_date = d
        except ValueError:
            pass
    elif ref_sub_end:
        try:
            d = datetime.strptime(ref_sub_end, "%Y-%m-%d")
            if d > base_date:
                base_date = d
        except ValueError:
            pass

    new_end = (base_date + timedelta(days=7)).strftime("%Y-%m-%d")
    await update_user_field(REFERRER_ID, "subscription", "premium")
    if ref_trial:
        await update_user_field(REFERRER_ID, "trial_end", new_end)
    else:
        await update_user_field(REFERRER_ID, "subscription_end", new_end)

    # 4. Перевіряємо результат
    referrer_after = await get_user(REFERRER_ID)
    print(
        f"📋 Реферер ПІСЛЯ: subscription={referrer_after.get('subscription')}, trial_end={referrer_after.get('trial_end')}, subscription_end={referrer_after.get('subscription_end')}")
    print(f"\n✅ +7 днів нараховано до {new_end}")


asyncio.run(test())
