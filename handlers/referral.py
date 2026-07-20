from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user, get_all_users, get_giveaway_number, get_channel_link

router = Router()


async def get_referral_stats(user_id: int) -> dict:
    all_users = await get_all_users()
    count = 0
    referred = []
    for uid, data in all_users.items():
        try:
            int(uid)  # пропускаємо нечислові ключі (questions, prices тощо)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("referred_by") == user_id:
            count += 1
            referred.append({
                "name": data.get("name", "Невідомий"),
                "giveaway": data.get("joined_giveaway", 1),
            })
    return {"count": count, "referred": referred}


async def get_new_referrals(user_id: int) -> list:
    current = await get_giveaway_number()
    all_users = await get_all_users()
    result = []
    for uid, data in all_users.items():
        try:
            int(uid)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("referred_by") == user_id and data.get("joined_giveaway", 1) == current:
            result.append(data.get("name", "Невідомий"))
    return result


def get_pool(count: int) -> str:
    if count >= 30:
        return "🥇 Пул 1 місця"
    elif count >= 20:
        return "🥈 Пул 2 місця"
    elif count >= 10:
        return "🥉 Пул 3 місця"
    return "👥 Загальний пул"


def next_pool_info(count: int) -> str:
    if count < 10:
        return f"До 🥉 пулу ще {10 - count} людей"
    elif count < 20:
        return f"До 🥈 пулу ще {20 - count} людей"
    elif count < 30:
        return f"До 🥇 пулу ще {30 - count} людей"
    return "🔥 Ти в найвищому пулі!"


@router.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = await get_referral_stats(user_id)
    total = stats["count"]
    new_refs = await get_new_referrals(user_id)
    new_count = len(new_refs)
    pool = get_pool(new_count)
    next_info = next_pool_info(new_count)
    giveaway_num = await get_giveaway_number()
    bot_username = "gymnote1bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    share_url = (
        f"https://t.me/share/url?url={ref_link}"
        f"&text=Приєднуйся до GymNote 💪"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поділитись з другом",    url=share_url)],
        [InlineKeyboardButton(text="👥 Всі мої реферали",       callback_data="referral_all")],
        [InlineKeyboardButton(text="🆕 Нові у цьому розіграші", callback_data="referral_new")],
        [InlineKeyboardButton(text="🏆 Лідерборд",              callback_data="referral_top")],
        [InlineKeyboardButton(text="← Назад",                   callback_data="menu_profile")],
    ])
    await callback.message.edit_text(
        f"🏆 <b>Реферальна система</b>\n\n"
        f"Твоє посилання:\n<code>{ref_link}</code>\n\n"
        f"👥 Всього запрошено: <b>{total}</b>\n"
        f"🆕 У розіграші #{giveaway_num}: <b>{new_count}</b>\n"
        f"🎯 Твій пул: <b>{pool}</b>\n"
        f"📊 {next_info}\n\n"
        f"<b>Пули розіграшу #{giveaway_num}:</b>\n"
        f"🥇 30+ — 1 місце\n"
        f"🥈 20+ — 2 місце\n"
        f"🥉 10+ — 3 місце",
        reply_markup=kb,
    )


@router.callback_query(F.data == "referral_all")
async def referral_all(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = await get_referral_stats(user_id)
    referred = stats["referred"]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="referral_menu")],
    ])
    if not referred:
        await callback.message.edit_text(
            "👥 <b>Всі мої реферали</b>\n\nЩе ніхто не прийшов.",
            reply_markup=kb,
        )
        return
    text = f"👥 <b>Всі мої реферали — {len(referred)}</b>\n\n"
    for i, ref in enumerate(referred, 1):
        text += f"{i}. {ref['name']} (розіграш #{ref['giveaway']})\n"
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "referral_new")
async def referral_new(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_refs = await get_new_referrals(user_id)
    giveaway_num = await get_giveaway_number()
    pool = get_pool(len(new_refs))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="referral_menu")],
    ])
    if not new_refs:
        await callback.message.edit_text(
            f"🆕 <b>Розіграш #{giveaway_num}</b>\n\nЩе ніхто не прийшов.",
            reply_markup=kb,
        )
        return
    text = f"🆕 <b>Розіграш #{giveaway_num}</b>\n\n"
    for i, name in enumerate(new_refs, 1):
        text += f"{i}. {name}\n"
    text += f"\n🎯 Твій пул: {pool}"
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "referral_top")
async def referral_top(callback: CallbackQuery):
    all_users = await get_all_users()
    giveaway_num = await get_giveaway_number()
    scores = {}
    for uid, data in all_users.items():
        try:
            int(uid)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        ref_by = data.get("referred_by")
        if ref_by and data.get("joined_giveaway", 1) == giveaway_num:
            scores[ref_by] = scores.get(ref_by, 0) + 1
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="referral_menu")],
    ])
    if not top:
        await callback.message.edit_text(
            f"🏆 <b>Лідерборд — Розіграш #{giveaway_num}</b>\n\nЩе немає учасників.",
            reply_markup=kb,
        )
        return
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = f"🏆 <b>Лідерборд — Розіграш #{giveaway_num}</b>\n\n"
    for i, (uid, count) in enumerate(top):
        user = await get_user(int(uid))
        name = user.get("name", "Невідомий") if user else "Невідомий"
        text += f"{medals[i]} {name} — {count} {get_pool(count)}\n"
    await callback.message.edit_text(text, reply_markup=kb)