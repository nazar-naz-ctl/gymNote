from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_all_exercises,
    get_exercise_results,
    get_personal_record,
    save_exercise_result,
    get_user,
)


router = Router()


class ProgressStates(StatesGroup):
    waiting_exercise = State()
    waiting_weight   = State()
    waiting_reps     = State()


@router.callback_query(F.data == "progress")
async def progress_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Мій прогрес",       callback_data="progress_my")],
        [InlineKeyboardButton(text="➕ Записати результат", callback_data="progress_add")],
        [InlineKeyboardButton(text="🏆 Особисті рекорди",  callback_data="progress_records")],
        [InlineKeyboardButton(text="⭐ Аналіз програми",    callback_data="progress_analysis")],
        [InlineKeyboardButton(text="← Назад",              callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "📊 <b>Статистика і прогрес</b>\n\nОбирай:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "progress_my")
async def progress_my(callback: CallbackQuery):
    user_id = callback.from_user.id
    exercises = await get_all_exercises(user_id)
    if not exercises:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Записати перший результат", callback_data="progress_add")],
            [InlineKeyboardButton(text="← Назад", callback_data="progress")],
        ])
        await callback.message.edit_text(
            "📊 <b>Мій прогрес</b>\n\nЩе немає записів.\n"
            "Почни записувати результати після тренувань!",
            reply_markup=kb,
        )
        return
    buttons = []
    for ex in exercises:
        buttons.append([InlineKeyboardButton(
            text=f"📈 {ex}",
            callback_data=f"pv_{exercises.index(ex)}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="progress")])
    await callback.message.edit_text(
        "📊 <b>Мій прогрес</b>\n\nОбери вправу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("pv_"))
async def view_exercise_progress(callback: CallbackQuery):
    idx = int(callback.data.replace("pv_", ""))
    user_id = callback.from_user.id
    exercises = await get_all_exercises(user_id)
    if idx >= len(exercises):
        await callback.answer("Помилка", show_alert=True)
        return
    exercise = exercises[idx]
    results = await get_exercise_results(user_id, exercise)
    record = await get_personal_record(user_id, exercise)
    if not results:
        await callback.answer("Немає результатів.", show_alert=True)
        return
    text = f"📈 <b>{exercise}</b>\n\n"
    text += f"🏆 Рекорд: {record.get('weight')}кг × {record.get('reps')} повт ({record.get('date')})\n\n"
    text += "<b>Останні результати:</b>\n"
    for r in results[-10:]:
        text += f"  {r['date']} — {r['weight']}кг × {r['reps']} повт\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="progress_my")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "progress_add")
async def progress_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProgressStates.waiting_exercise)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="progress")],
    ])
    await callback.message.edit_text(
        "➕ <b>Записати результат</b>\n\n"
        "Введи назву вправи:\n"
        "Наприклад: <i>Жим лежачи</i>",
        reply_markup=kb,
    )


@router.message(ProgressStates.waiting_exercise)
async def get_exercise_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("✏️ Напиши назву вправи текстом.")
        return
    await state.update_data(exercise=message.text.strip())
    await state.set_state(ProgressStates.waiting_weight)
    await message.answer(
        f"💪 <b>{message.text}</b>\n\n"
        f"Введи вагу в кг:\nНаприклад: <i>80</i>",
    )


@router.message(ProgressStates.waiting_weight)
async def get_weight(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введи число текстом. Наприклад: <i>80</i>")
        return
    try:
        weight = float(message.text.strip().replace(",", "."))
        await state.update_data(weight=weight)
        await state.set_state(ProgressStates.waiting_reps)
        await message.answer(
            f"⚡️ Вага: <b>{weight} кг</b>\n\n"
            f"Введи кількість повторів:\nНаприклад: <i>8</i>",
        )
    except ValueError:
        await message.answer("❌ Введи число. Наприклад: <i>80</i>")


@router.message(ProgressStates.waiting_reps)
async def get_reps(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введи число текстом. Наприклад: <i>8</i>")
        return
    try:
        reps = int(message.text.strip())
        data = await state.get_data()
        exercise = data["exercise"]
        weight = data["weight"]
        user_id = message.from_user.id
        await save_exercise_result(user_id, exercise, weight, reps)
        record = await get_personal_record(user_id, exercise)
        is_record = (
            record.get("weight") == weight and
            record.get("reps") == reps
        )
        await state.clear()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ще записати", callback_data="progress_add")],
            [InlineKeyboardButton(text="📊 Прогрес", callback_data="progress_my")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ])
        text = f"✅ <b>Записано!</b>\n\n{exercise}\n{weight}кг × {reps} повт"
        if is_record:
            text += "\n\n🏆 <b>НОВИЙ РЕКОРД!</b> 🎉"
        await message.answer(text, reply_markup=kb)
    except ValueError:
        await message.answer("❌ Введи ціле число. Наприклад: <i>8</i>")


@router.callback_query(F.data == "progress_records")
async def progress_records(callback: CallbackQuery):
    user_id = callback.from_user.id
    exercises = await get_all_exercises(user_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="progress")],
    ])
    if not exercises:
        await callback.message.edit_text(
            "🏆 <b>Особисті рекорди</b>\n\nЩе немає записів.",
            reply_markup=kb,
        )
        return
    text = "🏆 <b>Особисті рекорди</b>\n\n"
    for ex in exercises:
        record = await get_personal_record(user_id, ex)
        if record:
            text += f"💪 {ex}\n"
            text += f"   {record['weight']}кг × {record['reps']} повт — {record['date']}\n\n"
    await callback.message.edit_text(text, reply_markup=kb)


# ══════════════════════════════════════════════════════
# ⭐ Аналіз програми (Premium-аналітика)
# ══════════════════════════════════════════════════════

BREAKDOWN_LABELS = {
    "push_pull": "Push/Pull баланс",
    "quad_ham": "Квадрицепс/Задня поверхня стегна",
    "horizontal_vertical": "Горизонтальні/Вертикальні рухи",
    "compound_isolation": "Базові/Ізоляційні вправи",
    "diversity": "Різноманітність рухів",
    "joint_balance": "Баланс навантаження на суглоби",
    "coverage": "Покриття м'язових груп",
}


def _score_label(score: float) -> str:
    if score >= 85:
        return "🟢 Відмінно"
    if score >= 70:
        return "🟡 Добре"
    return "🔴 Потребує уваги"


def _render_analysis(program: dict, level: int, equipment: list, goal: str, title: str) -> str:
    from backend.generator import validate_program
    from backend.generator.program_state import build_program_state
    from backend.generator.optimization_problems import collect_problems

    report = validate_program(program, level=level, equipment=equipment, goal=goal)
    intelligence = report["intelligence_score"]
    breakdown = report.get("intelligence_breakdown", {})
    weekly_balance = report["weekly_balance_score"]

    state = build_program_state(program, level=level, equipment=equipment, goal=goal)
    problems = collect_problems(state)

    lines = [f"⭐ <b>{title}</b>\n"]
    lines.append(f"Загальна якість: <b>{round(intelligence)}/100</b> {_score_label(intelligence)}")
    lines.append(f"Тижневий баланс навантаження: <b>{round(weekly_balance)}/100</b> {_score_label(weekly_balance)}\n")

    lines.append("<b>Деталі за критеріями:</b>")
    for key, label in BREAKDOWN_LABELS.items():
        val = breakdown.get(key)
        if val is not None:
            lines.append(f"  {label}: {round(val)}/100")

    if problems:
        lines.append("\n<b>💡 Рекомендації:</b>")
        for prob in problems[:3]:
            lines.append(f"  • {prob.reason}")
    else:
        lines.append("\n✅ Суттєвих проблем не знайдено — програма добре збалансована.")

    return "\n".join(lines)


@router.callback_query(F.data == "progress_analysis")
async def progress_analysis(callback: CallbackQuery, state: FSMContext):
    from backend.generator import program_from_storable

    data = await state.get_data()
    stored = data.get("current_program")
    own_goal = data.get("current_goal")
    own_level = data.get("current_level")
    own_equipment = data.get("current_equipment")

    user = await get_user(callback.from_user.id)
    assigned = user.get("assigned_program") if user else None
    assigned_goal = user.get("assigned_program_goal") if user else None
    assigned_level = user.get("assigned_program_level") if user else None
    assigned_equipment = user.get("assigned_program_equipment") if user else None

    if not stored and not assigned:
        await callback.message.edit_text(
            "⭐ <b>Аналіз програми</b>\n\n"
            "У тебе ще немає багатоденної програми для аналізу.\n"
            "Створи її через головне меню 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="progress")],
            ]),
        )
        return

    sections = []

    if assigned and assigned_goal and assigned_level and assigned_equipment:
        assigned_program = program_from_storable(assigned)
        sections.append(_render_analysis(
            assigned_program, assigned_level, assigned_equipment, assigned_goal,
            "Програма від тренера",
        ))

    if stored and own_goal and own_level and own_equipment:
        program = program_from_storable(stored)
        sections.append(_render_analysis(
            program, own_level, own_equipment, own_goal,
            "Твоя власна програма",
        ))

    if not sections:
        await callback.message.edit_text(
            "⭐ <b>Аналіз програми</b>\n\n"
            "Не вдалося проаналізувати — бракує даних про обладнання/рівень/ціль "
            "(могло статись, якщо програма з'явилась до цього оновлення).\n"
            "Згенеруй нову програму, щоб аналіз запрацював.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="progress")],
            ]),
        )
        return

    await callback.message.edit_text(
        "\n\n━━━━━━━━━━━━━━━━\n\n".join(sections),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="progress")],
        ]),
    )
