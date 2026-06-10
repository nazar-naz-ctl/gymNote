from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database import get_user, update_user_field

router = Router()


class WorkoutStates(StatesGroup):
    naming          = State()
    adding_exercise = State()
    adding_sets     = State()
    adding_reps     = State()
    in_progress     = State()
    entering_weight = State()
    entering_reps   = State()


async def save_custom_workout(user_id: int, name: str, exercises: list) -> None:
    user = await get_user(user_id)
    workouts = user.get("custom_workouts", []) if user else []
    workouts.append({"name": name, "exercises": exercises})
    await update_user_field(user_id, "custom_workouts", workouts)


async def get_custom_workouts(user_id: int) -> list:
    user = await get_user(user_id)
    if not user:
        return []
    return user.get("custom_workouts", [])


async def get_last_result(user_id: int, exercise: str) -> list:
    user = await get_user(user_id)
    if not user:
        return []
    results = user.get("results", {}).get(exercise, [])
    if not results:
        return []
    by_date = {}
    for r in results:
        d = r.get("date", "")
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(r)
    last_date = sorted(by_date.keys())[-1]
    return by_date[last_date]


async def save_workout_result(user_id: int, exercise: str, sets: list) -> None:
    user = await get_user(user_id)
    results = user.get("results", {}) if user else {}
    if exercise not in results:
        results[exercise] = []
    today = datetime.now().strftime("%d.%m.%Y")
    for s in sets:
        results[exercise].append({
            "weight": s["weight"],
            "reps":   s["reps"],
            "date":   today,
        })
    await update_user_field(user_id, "results", results)


@router.callback_query(F.data == "constructor")
async def constructor_menu(callback: CallbackQuery):
    workouts = await get_custom_workouts(callback.from_user.id)
    buttons = []
    for i, w in enumerate(workouts):
        buttons.append([
            InlineKeyboardButton(text=f"▶️ {w['name']}", callback_data=f"start_workout_{i}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_workout_{i}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Створити тренування", callback_data="create_workout")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu_workout")])
    text = "🛠 <b>Конструктор</b>\n\nТвої тренування:" if workouts else "🛠 <b>Конструктор</b>\n\nЩе немає тренувань."
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "create_workout")
async def create_workout(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.naming)
    await state.update_data(exercises=[])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    await callback.message.edit_text(
        "➕ <b>Нове тренування</b>\n\nВведи назву:\nНаприклад: <i>День A — Груди</i>",
        reply_markup=kb,
    )


@router.message(WorkoutStates.naming)
async def workout_set_name(message: Message, state: FSMContext):
    await state.update_data(workout_name=message.text.strip())
    await state.set_state(WorkoutStates.adding_exercise)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    await message.answer(
        "💪 Введи назву першої вправи:",
        reply_markup=kb,
    )


@router.message(WorkoutStates.adding_exercise)
async def workout_add_exercise(message: Message, state: FSMContext):
    await state.update_data(current_exercise=message.text.strip())
    await state.set_state(WorkoutStates.adding_sets)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="3", callback_data="sets_3"),
            InlineKeyboardButton(text="4", callback_data="sets_4"),
            InlineKeyboardButton(text="5", callback_data="sets_5"),
        ],
        [
            InlineKeyboardButton(text="6", callback_data="sets_6"),
            InlineKeyboardButton(text="7", callback_data="sets_7"),
            InlineKeyboardButton(text="8", callback_data="sets_8"),
        ],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    await message.answer(
        f"💪 <b>{message.text}</b>\n\nКількість підходів:",
        reply_markup=kb,
    )


@router.callback_query(WorkoutStates.adding_sets, F.data.startswith("sets_"))
async def workout_set_sets(callback: CallbackQuery, state: FSMContext):
    sets = int(callback.data.replace("sets_", ""))
    await state.update_data(current_sets=sets)
    await state.set_state(WorkoutStates.adding_reps)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="6", callback_data="reps_6"),
            InlineKeyboardButton(text="8", callback_data="reps_8"),
            InlineKeyboardButton(text="10", callback_data="reps_10"),
        ],
        [
            InlineKeyboardButton(text="12", callback_data="reps_12"),
            InlineKeyboardButton(text="15", callback_data="reps_15"),
            InlineKeyboardButton(text="20", callback_data="reps_20"),
        ],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    data = await state.get_data()
    await callback.message.edit_text(
        f"💪 <b>{data['current_exercise']}</b>\nПідходів: {sets}\n\nКількість повторів:",
        reply_markup=kb,
    )


@router.callback_query(WorkoutStates.adding_reps, F.data.startswith("reps_"))
async def workout_set_reps(callback: CallbackQuery, state: FSMContext):
    reps = int(callback.data.replace("reps_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    exercises.append({
        "name": data["current_exercise"],
        "sets": data["current_sets"],
        "reps": reps,
    })
    await state.update_data(exercises=exercises)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ще вправу", callback_data="add_more_exercise")],
        [InlineKeyboardButton(text="💾 Зберегти", callback_data="save_workout")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    text = f"✅ Додано: <b>{data['current_exercise']}</b> — {data['current_sets']}×{reps}\n\n<b>Вправи:</b>\n"
    for i, ex in enumerate(exercises, 1):
        text += f"{i}. {ex['name']} — {ex['sets']}×{ex['reps']}\n"

    delete_buttons = []
    for i, ex in enumerate(exercises):
        delete_buttons.append([InlineKeyboardButton(text=f"🗑 {ex['name']}", callback_data=f"del_ex_{i}")])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ще вправу", callback_data="add_more_exercise")],
        [InlineKeyboardButton(text="💾 Зберегти", callback_data="save_workout")],
        *delete_buttons,
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "add_more_exercise")
async def add_more_exercise(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.adding_exercise)
    await callback.message.edit_text("💪 Введи назву наступної вправи:")


@router.callback_query(F.data == "save_workout")
async def save_workout_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await save_custom_workout(
        callback.from_user.id,
        data["workout_name"],
        data["exercises"],
    )
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Мої тренування", callback_data="constructor")],
        [InlineKeyboardButton(text="🏠 Меню",            callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        f"✅ <b>Збережено!</b>\n\n📋 {data['workout_name']}\nВправ: {len(data['exercises'])}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.replace("start_workout_", ""))
    workouts = await get_custom_workouts(callback.from_user.id)
    if index >= len(workouts):
        await callback.answer("Тренування не знайдено.", show_alert=True)
        return
    await state.update_data(
        workout=workouts[index],
        exercise_index=0,
        set_index=0,
        completed_sets={},
        start_time=datetime.now().strftime("%H:%M"),
    )
    await state.set_state(WorkoutStates.in_progress)
    await show_current_exercise(callback, state)


async def show_current_exercise(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout = data["workout"]
    ex_idx = data["exercise_index"]
    set_idx = data["set_index"]
    exercises = workout["exercises"]
    if ex_idx >= len(exercises):
        await finish_workout(callback, state)
        return
    exercise = exercises[ex_idx]
    ex_name = exercise["name"]
    total_sets = exercise["sets"]
    target_reps = exercise["reps"]
    last = await get_last_result(callback.from_user.id, ex_name)
    last_text = ""
    if last:
        last_text = "\n\n<b>Минулого разу:</b>\n"
        for i, r in enumerate(last, 1):
            last_text += f"  Підхід {i}: {r['weight']}кг × {r['reps']}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Зробив", callback_data="set_done"),
            InlineKeyboardButton(text="✏️ Ввести вагу", callback_data="enter_weight"),
        ],
        [InlineKeyboardButton(text="⏭️ Наступна вправа", callback_data="skip_exercise")],
        [InlineKeyboardButton(text="🏁 Завершити тренування", callback_data="finish_early")],
    ])
    await callback.message.edit_text(
        f"🏋️ <b>{ex_name}</b>\n"
        f"Підхід {set_idx + 1}/{total_sets} · Ціль: {target_reps} повт"
        f"{last_text}",
        reply_markup=kb,
    )


@router.callback_query(WorkoutStates.in_progress, F.data == "set_done")
async def set_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout = data["workout"]
    ex_idx = data["exercise_index"]
    set_idx = data["set_index"]
    exercise = workout["exercises"][ex_idx]
    ex_name = exercise["name"]
    total_sets = exercise["sets"]
    target_reps = exercise["reps"]
    completed = data.get("completed_sets", {})
    if ex_name not in completed:
        completed[ex_name] = []
    completed[ex_name].append({"weight": 0, "reps": target_reps})
    await state.update_data(completed_sets=completed)
    if set_idx + 1 >= total_sets:
        await save_workout_result(callback.from_user.id, ex_name, completed[ex_name])
        await state.update_data(exercise_index=ex_idx + 1, set_index=0)
    else:
        await state.update_data(set_index=set_idx + 1)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Наступний підхід", callback_data="next_after_rest")],
    ])
    await callback.message.edit_text(
        "✅ Підхід зараховано!\n\n😮 Відпочинь 90 сек...",
        reply_markup=kb,
    )


@router.callback_query(WorkoutStates.in_progress, F.data == "enter_weight")
async def enter_weight_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.entering_weight)
    await callback.message.edit_text("✏️ Введи вагу в кг:\nНаприклад: <i>80</i>")


@router.message(WorkoutStates.entering_weight)
async def enter_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.strip().replace(",", "."))
        await state.update_data(current_weight=weight)
        await state.set_state(WorkoutStates.entering_reps)
        await message.answer(f"⚡ Вага: <b>{weight} кг</b>\n\nВведи кількість повторів:")
    except ValueError:
        await message.answer("❌ Введи число. Наприклад: <i>80</i>")


@router.message(WorkoutStates.entering_reps)
async def enter_reps(message: Message, state: FSMContext):
    try:
        reps = int(message.text.strip())
        data = await state.get_data()
        workout = data["workout"]
        ex_idx = data["exercise_index"]
        set_idx = data["set_index"]
        exercise = workout["exercises"][ex_idx]
        ex_name = exercise["name"]
        total_sets = exercise["sets"]
        weight = data["current_weight"]
        completed = data.get("completed_sets", {})
        if ex_name not in completed:
            completed[ex_name] = []
        completed[ex_name].append({"weight": weight, "reps": reps})
        await state.update_data(completed_sets=completed)
        await state.set_state(WorkoutStates.in_progress)
        user = await get_user(message.from_user.id)
        results = user.get("results", {}).get(ex_name, []) if user else []
        is_record = not results or weight > max(r["weight"] for r in results)
        record_text = "\n🏆 <b>НОВИЙ РЕКОРД!</b> 🔥" if is_record else ""
        if set_idx + 1 >= total_sets:
            await save_workout_result(message.from_user.id, ex_name, completed[ex_name])
            await state.update_data(exercise_index=ex_idx + 1, set_index=0)
        else:
            await state.update_data(set_index=set_idx + 1)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Наступний підхід", callback_data="next_after_rest")],
        ])
        await message.answer(
            f"✅ {weight}кг × {reps}{record_text}\n\n😮 Відпочинь 90 сек...",
            reply_markup=kb,
        )
    except ValueError:
        await message.answer("❌ Введи ціле число. Наприклад: <i>8</i>")


@router.callback_query(F.data == "next_after_rest")
async def next_after_rest(callback: CallbackQuery, state: FSMContext):
    await show_current_exercise(callback, state)


@router.callback_query(F.data == "skip_rest")
async def skip_rest(callback: CallbackQuery, state: FSMContext):
    await show_current_exercise(callback, state)


@router.callback_query(WorkoutStates.in_progress, F.data == "skip_exercise")
async def skip_exercise(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(exercise_index=data["exercise_index"] + 1, set_index=0)
    await show_current_exercise(callback, state)


async def finish_workout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout = data["workout"]
    completed = data.get("completed_sets", {})
    start_time = data.get("start_time", "—")
    await state.clear()
    text = f"🏁 <b>Тренування завершено!</b>\n\n📋 {workout['name']}\n⏱ {start_time}\n\n<b>Результати:</b>\n"
    for ex_name, sets in completed.items():
        text += f"\n💪 {ex_name}\n"
        for i, s in enumerate(sets, 1):
            if s["weight"] > 0:
                text += f"  Підхід {i}: {s['weight']}кг × {s['reps']}\n"
            else:
                text += f"  Підхід {i}: ✅ {s['reps']} повт\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Прогрес", callback_data="progress")],
        [InlineKeyboardButton(text="🏠 Меню",    callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "cancel_workout")
async def cancel_workout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Створення тренування скасовано.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛠 Конструктор", callback_data="constructor")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ])
    )

@router.callback_query(F.data == "finish_early")
async def finish_early(callback: CallbackQuery, state: FSMContext):
    await finish_workout(callback, state)


@router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    index = int(callback.data.replace("delete_workout_", ""))
    user_id = callback.from_user.id
    user = await get_user(user_id)
    workouts = user.get("custom_workouts", []) if user else []
    if index < len(workouts):
        deleted_name = workouts[index]["name"]
        workouts.pop(index)
        await update_user_field(user_id, "custom_workouts", workouts)
        await callback.answer(f"🗑 '{deleted_name}' видалено!")
    await constructor_menu(callback)


@router.callback_query(F.data.startswith("del_ex_"))
async def delete_exercise(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.replace("del_ex_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    if index < len(exercises):
        deleted = exercises[index]["name"]
        exercises.pop(index)
        await state.update_data(exercises=exercises)
        await callback.answer(f"🗑 '{deleted}' видалено!")

    if not exercises:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
        ])
        await callback.message.edit_text(
            "💪 Введи назву першої вправи:",
            reply_markup=kb,
        )
        await state.set_state(WorkoutStates.adding_exercise)
        return

    text = "<b>Вправи:</b>\n"
    for i, ex in enumerate(exercises, 1):
        text += f"{i}. {ex['name']} — {ex['sets']}×{ex['reps']}\n"

    delete_buttons = []
    for i, ex in enumerate(exercises):
        delete_buttons.append([InlineKeyboardButton(text=f"🗑 {ex['name']}", callback_data=f"del_ex_{i}")])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ще вправу", callback_data="add_more_exercise")],
        [InlineKeyboardButton(text="💾 Зберегти", callback_data="save_workout")],
        *delete_buttons,
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)