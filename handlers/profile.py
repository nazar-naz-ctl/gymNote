from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user

router = Router()

GENDER_LABELS = {"male": "♂ Чоловік", "female": "♀ Жінка"}
LEVEL_LABELS = {
    "beginner": "🟢 Початківець",
    "intermediate": "🟡 Середній",
    "advanced": "🔴 Просунутий",
}
GOAL_LABELS = {
    "weight_loss": "⚡ Схуднення",
    "muscle_gain": "💪 Набір маси",
    "toning": "✨ Рельєф і тонус",
    "endurance": "🏃 Витривалість",
    "strength": "🏋️ Сила",
}
LOCATION_LABELS = {
    "gym": "🏋️ Тренажерний зал",
    "outdoor": "🌳 Вулична площадка",
    "home": "🏠 Вдома",
}
SUB_LABELS = {
    "free": "🆓 Безкоштовний",
    "standard": "⭐ Стандарт",
    "premium": "👑 Преміум",
}


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    from datetime import datetime
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Профіль не знайдено.", show_alert=True)
        return

    # Підписка і дні що залишились
    sub = user.get("subscription", "free")
    sub_line = SUB_LABELS.get(sub, "🆓")
    days_left_line = ""

    trial_end = user.get("trial_end")
    sub_end = user.get("subscription_end")

    if sub == "premium" and trial_end:
        try:
            days_left = (datetime.strptime(trial_end, "%Y-%m-%d") - datetime.now()).days
            if days_left > 0:
                days_left_line = f"\n⏳ Пробний період: ще <b>{days_left} дн.</b>"
            else:
                days_left_line = "\n⏳ Пробний період закінчився"
        except ValueError:
            pass
    elif sub in ("premium", "standard") and sub_end:
        try:
            days_left = (datetime.strptime(sub_end, "%Y-%m-%d") - datetime.now()).days
            if days_left > 0:
                days_left_line = f"\n⏳ Підписка діє ще: <b>{days_left} дн.</b>"
            else:
                days_left_line = "\n⏳ Підписка закінчилась"
        except ValueError:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Змінити дані", callback_data="profile_edit")],
        [InlineKeyboardButton(text="← Назад", callback_data="menu_profile")],
    ])
    await callback.message.edit_text(
        f"👤 <b>Мій профіль</b>\n\n"
        f"Ім'я:      {user.get('name', '—')}\n"
        f"Стать:     {GENDER_LABELS.get(user.get('gender', ''), '—')}\n"
        f"Вік:       {user.get('age', '—')}\n"
        f"Рівень:    {LEVEL_LABELS.get(user.get('level', ''), '—')}\n"
        f"Ціль:      {GOAL_LABELS.get(user.get('goal', ''), '—')}\n"
        f"Локація:   {LOCATION_LABELS.get(user.get('location', ''), '—')}\n"
        f"Днів/тиж: {user.get('days', '—')}\n"
        f"Травми:    {user.get('injuries_label', 'Немає')}\n\n"
        f"💳 <b>Підписка:</b> {sub_line}{days_left_line}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "profile_edit")
async def profile_edit(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Змінити рівень",  callback_data="reg_edit_level")],
        [InlineKeyboardButton(text="✏️ Змінити ціль",    callback_data="reg_edit_goal")],
        [InlineKeyboardButton(text="✏️ Змінити локацію", callback_data="reg_edit_location")],
        [InlineKeyboardButton(text="✏️ Змінити дні",     callback_data="reg_edit_days")],
        [InlineKeyboardButton(text="✏️ Змінити травми",  callback_data="reg_edit_injuries")],
        [InlineKeyboardButton(text="← Назад",            callback_data="profile")],
    ])
    await callback.message.edit_text(
        "✏️ <b>Редагування профілю</b>\n\nЩо хочеш змінити?",
        reply_markup=kb,
    )
