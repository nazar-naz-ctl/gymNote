from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, save_user, update_user_field, get_channel_link
from keyboards import (
    gender_kb, age_kb, level_kb, goal_kb,
    location_kb, days_kb, injuries_kb, confirm_kb,
    main_reply_kb,
)

router = Router()

@router.callback_query(F.data == "role_client")
async def role_client(callback: CallbackQuery, state: FSMContext) -> None:
    await start_registration(callback, state)

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
INJURY_LABELS = {
    "none": "✅ Немає",
    "knees": "🦵 Коліна",
    "back": "🔙 Поперек",
    "shoulders": "🦴 Плечі",
}


class RegStates(StatesGroup):
    gender          = State()
    age             = State()
    level           = State()
    goal            = State()
    location        = State()
    days            = State()
    injuries        = State()
    injuries_custom = State()
    confirm         = State()


def progress_bar(step: int, total: int = 7) -> str:
    filled = round(step / total * 12)
    bar = "━" * filled + "░" * (12 - filled)
    return f"{bar} {round(step / total * 100)}%"


def summary_text(data: dict) -> str:
    return (
        "📋 <b>Перевір дані:</b>\n\n"
        f"Стать:     {GENDER_LABELS.get(data.get('gender', ''), '—')}\n"
        f"Вік:       {data.get('age', '—')}\n"
        f"Рівень:    {LEVEL_LABELS.get(data.get('level', ''), '—')}\n"
        f"Ціль:      {GOAL_LABELS.get(data.get('goal', ''), '—')}\n"
        f"Локація:   {LOCATION_LABELS.get(data.get('location', ''), '—')}\n"
        f"Днів/тиж: {data.get('days', '—')}\n"
        f"Травми:    {data.get('injuries_label', '—')}\n"
    )


async def show_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user_id = callback.from_user.id

    # Підмішуємо існуючі дані з бази
    existing = await get_user(user_id) or {}
    merged = {
        "gender": data.get("gender") or existing.get("gender"),
        "age": data.get("age") or existing.get("age"),
        "level": data.get("level") or existing.get("level"),
        "goal": data.get("goal") or existing.get("goal"),
        "location": data.get("location") or existing.get("location"),
        "days": data.get("days") or existing.get("days"),
        "injuries": data.get("injuries") or existing.get("injuries"),
        "injuries_label": data.get("injuries_label") or existing.get("injuries_label", "Немає"),
    }

    await state.set_state(RegStates.confirm)
    await callback.message.edit_text(
        summary_text(merged) + "\nВсе вірно?",
        reply_markup=confirm_kb(),
    )


async def show_confirm_from_msg(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(RegStates.confirm)
    await message.answer(
        summary_text(data) + "\nВсе вірно?",
        reply_markup=confirm_kb(),
    )


async def start_registration(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegStates.gender)
    await callback.message.edit_text(
        f"<b>Крок 1/7 — Стать</b>\n{progress_bar(1)}\n\nОбери свою стать:",
        reply_markup=gender_kb(),
    )


@router.callback_query(F.data.startswith("reg_gender_"))
async def step_gender(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_gender_", "")
    data = await state.get_data()
    await state.update_data(gender=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.age)
    await callback.message.edit_text(
        f"<b>Крок 2/7 — Вік</b>\n{progress_bar(2)}\n\nОбери вікову групу:",
        reply_markup=age_kb(),
    )


@router.callback_query(F.data.startswith("reg_age_"))
async def step_age(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_age_", "")
    data = await state.get_data()
    await state.update_data(age=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.level)
    await callback.message.edit_text(
        f"<b>Крок 3/7 — Рівень</b>\n{progress_bar(3)}\n\nОбери свій рівень:",
        reply_markup=level_kb(),
    )


@router.callback_query(F.data.startswith("reg_level_"))
async def step_level(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_level_", "")
    data = await state.get_data()
    await state.update_data(level=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.goal)
    await callback.message.edit_text(
        f"<b>Крок 4/7 — Ціль</b>\n{progress_bar(4)}\n\nЯка твоя ціль?",
        reply_markup=goal_kb(),
    )


@router.callback_query(F.data.startswith("reg_goal_"))
async def step_goal(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_goal_", "")
    data = await state.get_data()
    await state.update_data(goal=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.location)
    await callback.message.edit_text(
        f"<b>Крок 5/7 — Локація</b>\n{progress_bar(5)}\n\nДе тренуєшся?",
        reply_markup=location_kb(),
    )


@router.callback_query(F.data.startswith("reg_location_"))
async def step_location(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_location_", "")
    data = await state.get_data()
    await state.update_data(location=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.days)
    await callback.message.edit_text(
        f"<b>Крок 6/7 — Дні</b>\n{progress_bar(6)}\n\nСкільки разів на тиждень?",
        reply_markup=days_kb(),
    )


@router.callback_query(F.data.startswith("reg_days_"))
async def step_days(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_days_", "")
    data = await state.get_data()
    await state.update_data(days=value)
    if data.get("editing"):
        await state.update_data(editing=False)
        await show_confirm(callback, state)
        return
    await state.set_state(RegStates.injuries)
    await callback.message.edit_text(
        f"<b>Крок 7/7 — Травми</b>\n{progress_bar(7)}\n\nЄ травми або обмеження?",
        reply_markup=injuries_kb(),
    )


@router.callback_query(F.data.startswith("reg_injuries_") & ~F.data.endswith("_custom"))
async def step_injuries(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("reg_injuries_", "")
    label = INJURY_LABELS.get(value, value)
    await state.update_data(injuries=value, injuries_label=label)
    await show_confirm(callback, state)


@router.callback_query(F.data == "reg_injuries_custom")
async def step_injuries_custom_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegStates.injuries_custom)
    await callback.message.edit_text(
        "✏️ Напиши свої травми або обмеження:",
    )


@router.message(RegStates.injuries_custom)
async def step_injuries_custom_input(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("✏️ Будь ласка, напиши текстом, а не фото/стікером/голосовим.")
        return
    await state.update_data(injuries="custom", injuries_label=message.text)
    await show_confirm_from_msg(message, state)


EDIT_STEPS = {
    "reg_edit_gender":   (RegStates.gender,   "Крок 1/7 — Стать",    1, gender_kb),
    "reg_edit_age":      (RegStates.age,       "Крок 2/7 — Вік",      2, age_kb),
    "reg_edit_level":    (RegStates.level,     "Крок 3/7 — Рівень",   3, level_kb),
    "reg_edit_goal":     (RegStates.goal,      "Крок 4/7 — Ціль",     4, goal_kb),
    "reg_edit_location": (RegStates.location,  "Крок 5/7 — Локація",  5, location_kb),
    "reg_edit_days":     (RegStates.days,      "Крок 6/7 — Дні",      6, days_kb),
    "reg_edit_injuries": (RegStates.injuries,  "Крок 7/7 — Травми",   7, injuries_kb),
}


@router.callback_query(F.data.startswith("reg_edit_"))
async def edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data
    if key not in EDIT_STEPS:
        return
    new_state, title, step, kb_func = EDIT_STEPS[key]
    await state.update_data(editing=True)
    await state.set_state(new_state)
    await callback.message.edit_text(
        f"<b>{title}</b>\n{progress_bar(step)}\n\nОбери новий варіант:",
        reply_markup=kb_func(),
    )


@router.callback_query(F.data == "reg_confirm")
async def confirm_registration(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from datetime import datetime, timedelta
    data = await state.get_data()
    user_id = callback.from_user.id
    referrer_id = data.get("referrer_id")

    trial_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # Завантажуємо існуючі дані з бази
    existing = await get_user(user_id) or {}

    user_data = {
        "id": user_id,
        "name": callback.from_user.full_name,
        "username": callback.from_user.username,
        "registered_at": existing.get("registered_at") or datetime.now().isoformat(),
        "gender": data.get("gender") or existing.get("gender"),
        "age": data.get("age") or existing.get("age"),
        "level": data.get("level") or existing.get("level"),
        "goal": data.get("goal") or existing.get("goal"),
        "location": data.get("location") or existing.get("location"),
        "days": data.get("days") or existing.get("days"),
        "injuries": data.get("injuries") or existing.get("injuries"),
        "injuries_label": data.get("injuries_label") or existing.get("injuries_label", "Немає"),
        "subscription": existing.get("subscription", "free"),
        "trial_end": existing.get("trial_end"),
        "subscription_end": existing.get("subscription_end"),
        "registered": existing.get("registered", True),
        "referred_by": existing.get("referred_by") or data.get("referrer_id"),
        "joined_giveaway": existing.get("joined_giveaway", 1),
    }

    # Пробний період тільки для нових користувачів
    if not existing.get("registered"):
        user_data["subscription"] = "premium"
        user_data["trial_end"] = trial_end
    await save_user(user_id, user_data)

    # Сповіщення тренеру про нову реєстрацію
    try:
        from bot import bot
        from config import TRAINER_ID
        await bot.send_message(
            TRAINER_ID,
            f"🆕 <b>Новий клієнт!</b>\n\n"
            f"Ім'я: {callback.from_user.full_name}\n"
            f"Username: @{callback.from_user.username or '—'}\n"
            f"ID: <code>{user_id}</code>\n"
            f"Рівень: {user_data.get('level', '—')}\n"
            f"Локація: {user_data.get('location', '—')}",
        )
    except Exception:
        pass

    # +7 днів запрошувачу за реферала
    if referrer_id:
        referrer = await get_user(referrer_id)
        if referrer:
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
            await update_user_field(referrer_id, "subscription", "premium")
            if ref_trial:
                await update_user_field(referrer_id, "trial_end", new_end)
            else:
                await update_user_field(referrer_id, "subscription_end", new_end)
            try:
                from bot import bot
                await bot.send_message(
                    referrer_id,
                    f"🎁 <b>+7 днів Преміум!</b>\n\n"
                    f"Твій друг {callback.from_user.first_name} зареєструвався по твоєму посиланню.\n"
                    f"Преміум продовжено до <b>{new_end}</b> 🔥"
                )
            except Exception:
                pass

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"✅ <b>Реєстрацію завершено!</b>\n\n"
        f"Вітаємо в GymNote, {callback.from_user.first_name}! 💪\n\n"
        f"🎁 Тобі активовано <b>пробний період 7 днів Преміум!</b>\n"
        f"Після закінчення перейдеш на безкоштовний тариф.\n\n"
        f"Обирай з меню що хочеш зробити:",
        reply_markup=main_reply_kb(),
    )