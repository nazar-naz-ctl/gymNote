from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database import get_user, update_user_field, save_last_workout

router = Router()


class WorkoutStates(StatesGroup):
    naming          = State()
    adding_exercise = State()
    adding_sets     = State()
    in_progress     = State()
    entering_weight = State()
    replacing_ex    = State()


# ── HELPERS ───────────────────────────────────────────────────────────────────

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


def make_dots(total: int, done: int) -> str:
    dots = ""
    for i in range(total):
        if i < done:
            dots += "🟢"
        elif i == done:
            dots += "🔵"
        else:
            dots += "⚪️"
    return dots


def reps_kb_workout() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 6", callback_data="reps_6"),
            InlineKeyboardButton(text="✅ 8", callback_data="reps_8"),
            InlineKeyboardButton(text="✅ 10", callback_data="reps_10"),
            InlineKeyboardButton(text="✅ 12", callback_data="reps_12"),
        ],
        [
            InlineKeyboardButton(text="✅ 15", callback_data="reps_15"),
            InlineKeyboardButton(text="✅ 20", callback_data="reps_20"),
        ],
        [
            InlineKeyboardButton(text="🔄 Замінити вправу", callback_data="replace_exercise"),
            InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_exercise"),
        ],
        [
            InlineKeyboardButton(text="🏁 Завершити тренування", callback_data="finish_early"),
        ],
    ])


def sets_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
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


def reps_kb_create() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="6", callback_data="reps_create_6"),
            InlineKeyboardButton(text="8", callback_data="reps_create_8"),
            InlineKeyboardButton(text="10", callback_data="reps_create_10"),
            InlineKeyboardButton(text="12", callback_data="reps_create_12"),
        ],
        [
            InlineKeyboardButton(text="15", callback_data="reps_create_15"),
            InlineKeyboardButton(text="20", callback_data="reps_create_20"),
        ],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
    ])


def exercises_list_kb(exercises: list) -> InlineKeyboardMarkup:
    buttons = []
    for i, ex in enumerate(exercises):
        row = []
        if i > 0:
            row.append(InlineKeyboardButton(text="▲", callback_data=f"ex_up_{i}"))
        else:
            row.append(InlineKeyboardButton(text="　", callback_data="ex_noop"))
        if i < len(exercises) - 1:
            row.append(InlineKeyboardButton(text="▼", callback_data=f"ex_down_{i}"))
        else:
            row.append(InlineKeyboardButton(text="　", callback_data="ex_noop"))
        row.append(InlineKeyboardButton(text=f"🗑 {ex['name']}", callback_data=f"ex_del_{i}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="➕ Ще вправу", callback_data="add_more_exercise")])
    buttons.append([InlineKeyboardButton(text="💾 Зберегти тренування", callback_data="save_workout")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def exercises_text(exercises: list) -> str:
    text = "<b>Вправи:</b>\n"
    for i, ex in enumerate(exercises, 1):
        text += f"{i}. {ex['name']} — {ex['sets']}×{ex['reps']}\n"
    return text


# ── CONSTRUCTOR MENU ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "constructor")
async def constructor_menu(callback: CallbackQuery):
    workouts = await get_custom_workouts(callback.from_user.id)
    buttons = []
    for i, w in enumerate(workouts):
        buttons.append([
            InlineKeyboardButton(text=f"▶️ {w['name']}", callback_data=f"start_workout_{i}"),
        ])
    if workouts:
        buttons.append([InlineKeyboardButton(text="🗑 Видалити тренування", callback_data="delete_workout_menu")])
    buttons.append([InlineKeyboardButton(text="➕ Створити тренування", callback_data="create_workout")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu_workout")])

    text = "🛠 <b>Конструктор</b>\n\n"
    if workouts:
        text += "<b>Твої тренування:</b>\n\n"
        for w in workouts:
            ex_names = " · ".join([e["name"] for e in w["exercises"]])
            text += f"📋 <b>{w['name']}</b>\n<i>{ex_names}</i>\n\n"
    else:
        text += "Ще немає тренувань.\nСтвори своє перше! 💪"

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "delete_workout_menu")
async def delete_workout_menu(callback: CallbackQuery):
    workouts = await get_custom_workouts(callback.from_user.id)
    buttons = []
    for i, w in enumerate(workouts):
        buttons.append([InlineKeyboardButton(text=f"🗑 {w['name']}", callback_data=f"delete_workout_{i}")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="constructor")])
    await callback.message.edit_text(
        "🗑 <b>Видалити тренування</b>\n\nВибери яке видалити:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


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


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "create_workout")
async def create_workout(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.naming)
    await state.update_data(exercises=[])
    await callback.message.edit_text(
        "➕ <b>Нове тренування</b>\n\n"
        "Введи назву тренування:\n"
        "<i>Наприклад: День A — Груди</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
        ]),
    )


@router.message(WorkoutStates.naming)
async def workout_set_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("✏️ Напиши назву текстом.")
        return
    await state.update_data(workout_name=message.text.strip())
    await state.set_state(WorkoutStates.adding_exercise)
    await message.answer(
        "💪 Введи назву першої вправи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
        ]),
    )


@router.message(WorkoutStates.adding_exercise)
async def workout_add_exercise(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("✏️ Напиши назву вправи текстом.")
        return
    await state.update_data(current_exercise=message.text.strip())
    await state.set_state(WorkoutStates.adding_sets)
    data = await state.get_data()
    await message.answer(
        f"💪 <b>{data['current_exercise']}</b>\n\nКількість підходів:",
        reply_markup=sets_kb(),
    )


@router.callback_query(WorkoutStates.adding_sets, F.data.startswith("sets_"))
async def workout_set_sets(callback: CallbackQuery, state: FSMContext):
    sets = int(callback.data.replace("sets_", ""))
    await state.update_data(current_sets=sets)
    data = await state.get_data()
    await callback.message.edit_text(
        f"💪 <b>{data['current_exercise']}</b>\n"
        f"Підходів: {sets}\n\n"
        f"Кількість повторів:",
        reply_markup=reps_kb_create(),
    )


@router.callback_query(F.data.startswith("reps_create_"))
async def workout_set_reps(callback: CallbackQuery, state: FSMContext):
    reps = int(callback.data.replace("reps_create_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    exercises.append({
        "name": data["current_exercise"],
        "sets": data["current_sets"],
        "reps": reps,
    })
    await state.update_data(exercises=exercises)
    await state.set_state(WorkoutStates.adding_exercise)

    text = f"✅ Додано: <b>{data['current_exercise']}</b> — {data['current_sets']}×{reps}\n\n"
    text += exercises_text(exercises)
    text += "\n⬆️⬇️ — змінити порядок\n🗑 — видалити вправу"

    await callback.message.edit_text(text, reply_markup=exercises_list_kb(exercises))


@router.callback_query(F.data == "ex_noop")
async def ex_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("ex_up_"))
async def ex_move_up(callback: CallbackQuery, state: FSMContext):
    i = int(callback.data.replace("ex_up_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    if i > 0:
        exercises[i], exercises[i-1] = exercises[i-1], exercises[i]
        await state.update_data(exercises=exercises)
    text = exercises_text(exercises)
    text += "\n⬆️⬇️ — змінити порядок\n🗑 — видалити вправу"
    await callback.message.edit_text(text, reply_markup=exercises_list_kb(exercises))
    await callback.answer()


@router.callback_query(F.data.startswith("ex_down_"))
async def ex_move_down(callback: CallbackQuery, state: FSMContext):
    i = int(callback.data.replace("ex_down_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    if i < len(exercises) - 1:
        exercises[i], exercises[i+1] = exercises[i+1], exercises[i]
        await state.update_data(exercises=exercises)
    text = exercises_text(exercises)
    text += "\n⬆️⬇️ — змінити порядок\n🗑 — видалити вправу"
    await callback.message.edit_text(text, reply_markup=exercises_list_kb(exercises))
    await callback.answer()


@router.callback_query(F.data.startswith("ex_del_"))
async def ex_delete(callback: CallbackQuery, state: FSMContext):
    i = int(callback.data.replace("ex_del_", ""))
    data = await state.get_data()
    exercises = data.get("exercises", [])
    if i < len(exercises):
        deleted = exercises[i]["name"]
        exercises.pop(i)
        await state.update_data(exercises=exercises)
        await callback.answer(f"🗑 '{deleted}' видалено!")
    if not exercises:
        await callback.message.edit_text(
            "💪 Введи назву першої вправи:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
            ]),
        )
        await state.set_state(WorkoutStates.adding_exercise)
        return
    text = exercises_text(exercises)
    text += "\n⬆️⬇️ — змінити порядок\n🗑 — видалити вправу"
    await callback.message.edit_text(text, reply_markup=exercises_list_kb(exercises))


@router.callback_query(F.data == "add_more_exercise")
async def add_more_exercise(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.adding_exercise)
    await callback.message.edit_text(
        "💪 Введи назву наступної вправи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_workout")],
        ]),
    )


@router.callback_query(F.data == "save_workout")
async def save_workout_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await save_custom_workout(
        callback.from_user.id,
        data["workout_name"],
        data["exercises"],
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Збережено!</b>\n\n📋 {data['workout_name']}\nВправ: {len(data['exercises'])}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Мої тренування", callback_data="constructor")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]),
    )


@router.callback_query(F.data == "cancel_workout")
async def cancel_workout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Скасовано.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛠 Конструктор", callback_data="constructor")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]),
    )


# ── START WORKOUT ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.replace("start_workout_", ""))
    workouts = await get_custom_workouts(callback.from_user.id)
    if index >= len(workouts):
        await callback.answer("Тренування не знайдено.", show_alert=True)
        return
    await state.update_data(
        workout=workouts[index],
        workout_index=index,
        exercise_index=0,
        set_index=0,
        completed_sets={},
        current_weight=0.0,
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
    weight = data.get("current_weight", 0.0)

    last = await get_last_result(callback.from_user.id, ex_name)
    last_text = ""
    if last:
        last_text = "\n⏮ <i>Минулого разу: "
        last_text += " · ".join([f"{r['weight']}кг×{r['reps']}" for r in last])
        last_text += "</i>"

    dots = make_dots(total_sets, set_idx)
    weight_display = f"{weight} кг" if weight > 0 else "не вказана"

    await callback.message.edit_text(
        f"🏋️ <b>{ex_name}</b>\n"
        f"<i>{workout['name']} · Вправа {ex_idx+1}/{len(exercises)}</i>\n\n"
        f"Підхід <b>{set_idx+1}</b>/{total_sets} · Ціль: {target_reps} повт\n"
        f"{dots}\n\n"
        f"⚖️ Вага: <b>{weight_display}</b>\n"
        f"<i>Напиши вагу в чат щоб змінити</i>"
        f"{last_text}",
        reply_markup=reps_kb_workout(),
    )


# ── WEIGHT INPUT ──────────────────────────────────────────────────────────────

@router.message(WorkoutStates.in_progress)
async def weight_input(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введи вагу текстом. Наприклад: <i>60</i> або <i>57.5</i>")
        return
    try:
        weight = float(message.text.strip().replace(",", "."))
        if weight < 0:
            raise ValueError
        await state.update_data(current_weight=weight)
        data = await state.get_data()
        workout = data["workout"]
        ex_idx = data["exercise_index"]
        set_idx = data["set_index"]
        exercise = workout["exercises"][ex_idx]
        ex_name = exercise["name"]
        total_sets = exercise["sets"]
        target_reps = exercise["reps"]

        last = await get_last_result(message.from_user.id, ex_name)
        last_text = ""
        if last:
            last_text = "\n⏮ <i>Минулого разу: "
            last_text += " · ".join([f"{r['weight']}кг×{r['reps']}" for r in last])
            last_text += "</i>"

        dots = make_dots(total_sets, set_idx)

        await message.answer(
            f"🏋️ <b>{ex_name}</b>\n"
            f"<i>{workout['name']} · Вправа {ex_idx+1}/{len(workout['exercises'])}</i>\n\n"
            f"Підхід <b>{set_idx+1}</b>/{total_sets} · Ціль: {target_reps} повт\n"
            f"{dots}\n\n"
            f"⚖️ Вага: <b>{weight} кг</b> ✅\n"
            f"<i>Напиши вагу в чат щоб змінити</i>"
            f"{last_text}",
            reply_markup=reps_kb_workout(),
        )
    except ValueError:
        await message.answer("❌ Введи число. Наприклад: <i>60</i> або <i>57.5</i>")


# ── REPS DONE ─────────────────────────────────────────────────────────────────

@router.callback_query(WorkoutStates.in_progress, F.data.startswith("reps_"))
async def reps_done(callback: CallbackQuery, state: FSMContext):
    reps = int(callback.data.replace("reps_", ""))
    data = await state.get_data()
    workout = data["workout"]
    ex_idx = data["exercise_index"]
    set_idx = data["set_index"]
    exercise = workout["exercises"][ex_idx]
    ex_name = exercise["name"]
    total_sets = exercise["sets"]
    weight = data.get("current_weight", 0.0)

    completed = data.get("completed_sets", {})
    if ex_name not in completed:
        completed[ex_name] = []
    completed[ex_name].append({"weight": weight, "reps": reps})

    # Перевірка рекорду
    user = await get_user(callback.from_user.id)
    results = user.get("results", {}).get(ex_name, []) if user else []
    is_record = weight > 0 and (not results or weight > max((r["weight"] for r in results), default=0))
    record_text = "\n🏆 <b>Новий рекорд!</b> 🔥" if is_record else ""

    if set_idx + 1 >= total_sets:
        await save_workout_result(callback.from_user.id, ex_name, completed[ex_name])
        await state.update_data(
            completed_sets=completed,
            exercise_index=ex_idx + 1,
            set_index=0,
            current_weight=weight,
        )
        dots = "🟢" * total_sets
        await callback.message.edit_text(
            f"✅ <b>{ex_name}</b> — виконано!\n"
            f"{dots}\n"
            f"{weight}кг × {reps}{record_text}\n\n"
            f"😮 Відпочинь 90 сек...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Наступна вправа", callback_data="next_exercise")],
                [InlineKeyboardButton(text="🏁 Завершити тренування", callback_data="finish_early")],
            ]),
        )
    else:
        await state.update_data(
            completed_sets=completed,
            set_index=set_idx + 1,
            current_weight=weight,
        )
        dots = make_dots(total_sets, set_idx + 1)
        await callback.message.edit_text(
            f"✅ Підхід {set_idx+1}/{total_sets}\n"
            f"{dots}\n"
            f"{weight}кг × {reps}{record_text}\n\n"
            f"😮 Відпочинь 90 сек...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Наступний підхід", callback_data="next_after_rest")],
                [InlineKeyboardButton(text="🏁 Завершити", callback_data="finish_early")],
            ]),
        )
    await callback.answer()


@router.callback_query(F.data == "next_after_rest")
async def next_after_rest(callback: CallbackQuery, state: FSMContext):
    await show_current_exercise(callback, state)


@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    await show_current_exercise(callback, state)


@router.callback_query(WorkoutStates.in_progress, F.data == "skip_exercise")
async def skip_exercise(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(exercise_index=data["exercise_index"] + 1, set_index=0, current_weight=0.0)
    await show_current_exercise(callback, state)


# ── REPLACE EXERCISE ──────────────────────────────────────────────────────────

@router.callback_query(WorkoutStates.in_progress, F.data == "replace_exercise")
async def replace_exercise(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout = data["workout"]
    ex_idx = data["exercise_index"]
    current_ex = workout["exercises"][ex_idx]["name"]
    await state.set_state(WorkoutStates.replacing_ex)
    await callback.message.edit_text(
        f"🔄 <b>Замінити вправу</b>\n\n"
        f"Зараз: <b>{current_ex}</b>\n\n"
        f"Введи назву нової вправи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_replace")],
        ]),
    )


@router.callback_query(F.data == "cancel_replace")
async def cancel_replace(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.in_progress)
    await show_current_exercise(callback, state)


@router.message(WorkoutStates.replacing_ex)
async def do_replace_exercise(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("✏️ Напиши назву вправи текстом.")
        return
    new_name = message.text.strip()
    data = await state.get_data()
    workout = data["workout"]
    ex_idx = data["exercise_index"]
    old_name = workout["exercises"][ex_idx]["name"]
    workout["exercises"][ex_idx]["name"] = new_name
    await state.update_data(workout=workout, current_weight=0.0)
    await state.set_state(WorkoutStates.in_progress)
    await message.answer(f"✅ <b>{old_name}</b> замінено на <b>{new_name}</b>")

    class FakeCallback:
        def __init__(self, msg): self.message = msg; self.from_user = msg.from_user
        async def answer(self): pass

    await show_current_exercise(FakeCallback(message), state)


# ── FINISH ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "finish_early")
async def finish_early(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WorkoutStates.in_progress)
    await finish_workout(callback, state)


async def finish_workout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout = data["workout"]
    completed = data.get("completed_sets", {})
    start_time = data.get("start_time", "—")

    await save_last_workout(callback.from_user.id, workout["name"], completed)
    # Оновлюємо серію
    from database import update_streak
    streak = await update_streak(callback.from_user.id)
    streak_text = f"\n\n🔥 <b>Серія: {streak['current']} день!</b>"
    if streak['current'] >= 7:
        streak_text += "\nТиждень без пропусків! 💪"
    elif streak['current'] >= 30:
        streak_text += "\nМісяць без пропусків! 🏆"
    if streak['best'] > 1:
        streak_text += f"\n🏆 Рекорд: {streak['best']} днів"
    await state.clear()

    total_sets = sum(len(s) for s in completed.values())
    total_volume = sum(
        s["weight"] * s["reps"]
        for sets in completed.values()
        for s in sets
    )

    text = "🏁 <b>Тренування завершено!</b>\n\n"
    text += f"📋 {workout['name']}\n"
    text += f"⏱ Початок: {start_time}\n\n"
    text += f"💪 Підходів: <b>{total_sets}</b>\n"
    if total_volume > 0:
        text += f"⚖️ Об'єм: <b>{int(total_volume)} кг</b>\n\n"

    if completed:
        text += "<b>Результати:</b>\n"
        for ex_name, sets in completed.items():
            text += f"\n🏋️ {ex_name}\n"
            for i, s in enumerate(sets, 1):
                if s["weight"] > 0:
                    text += f"  {i}. {s['weight']}кг × {s['reps']}\n"
                else:
                    text += f"  {i}. ✅ {s['reps']} повт\n"
    else:
        text += "Підходів не записано."

    text += streak_text

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторити", callback_data="repeat_last_workout")],
            [InlineKeyboardButton(text="🛠 До конструктора", callback_data="constructor")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]),
    )


# ── REPEAT LAST ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "repeat_last_workout")
async def repeat_last_workout(callback: CallbackQuery, state: FSMContext):
    from database import get_last_workout
    last = await get_last_workout(callback.from_user.id)
    if not last:
        await callback.answer("❌ Ще немає завершених тренувань!", show_alert=True)
        return

    text = f"🔄 <b>Останнє тренування</b>\n📅 {last['date']}\n📋 {last['name']}\n\n<b>Результати:</b>\n"
    for ex_name, sets in last["completed_sets"].items():
        text += f"\n💪 {ex_name}\n"
        for i, s in enumerate(sets, 1):
            if s["weight"] > 0:
                text += f"  {i}. {s['weight']}кг × {s['reps']}\n"
            else:
                text += f"  {i}. ✅ {s['reps']} повт\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="menu_workout")],
        ]),
    )


# ── IMPORT PROGRAM ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "import_program")
async def import_program(callback: CallbackQuery, state: FSMContext):
    text = callback.message.text or ""
    lines = text.split("\n")

    # Знаходимо дні
    days = []
    for line in lines:
        if "День" in line and ("📌" in line or "—" in line):
            # Чистимо від html тегів і зайвих символів
            clean = line.replace("<b>", "").replace("</b>", "")
            clean = clean.replace("📌", "").replace("━", "").strip()
            if clean:
                days.append(clean)

    if not days:
        await callback.answer("❌ Не вдалося знайти дні в програмі", show_alert=True)
        return

    await state.update_data(program_text=text, program_days=days)

    buttons = []
    for i, day in enumerate(days):
        buttons.append([InlineKeyboardButton(text=f"📋 {day}", callback_data=f"import_day_{i}")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_import")])

    await callback.message.edit_text(
        "📥 <b>Зберегти в конструктор</b>\n\nВибери який день імпортувати:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "cancel_import")
async def cancel_import(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Скасовано")
    await callback.message.edit_text(
        "❌ Імпорт скасовано.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Програми", callback_data="programs")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]),
    )


@router.callback_query(F.data.startswith("import_day_"))
async def import_day(callback: CallbackQuery, state: FSMContext):
    day_idx = int(callback.data.replace("import_day_", ""))
    data = await state.get_data()
    program_text = data.get("program_text", "")
    days = data.get("program_days", [])

    if day_idx >= len(days):
        await callback.answer("❌ Помилка", show_alert=True)
        return

    day_name = days[day_idx]
    lines = program_text.split("\n")

    # Знаходимо вправи цього дня
    exercises = []
    in_day = False
    for line in lines:
        clean_line = line.replace("<b>", "").replace("</b>", "").strip()

        # Перевіряємо чи це наш день
        if "День" in clean_line and day_name.replace("📌", "").strip() in clean_line:
            in_day = True
            continue

        # Якщо зустріли наступний день — зупиняємось
        if in_day and "День" in clean_line and "📌" in line:
            break

        # Парсимо вправи
        if in_day and clean_line.startswith("•"):
            ex_line = clean_line.replace("•", "").strip()
            # Парсимо підходи×повтори
            sets, reps = 3, 10  # дефолт
            if "×" in ex_line or "x" in ex_line.lower():
                ex_line = ex_line.replace("x", "×").replace("X", "×")
                parts = ex_line.split("—")
                if len(parts) >= 2:
                    ex_name = parts[0].strip()
                    sr = parts[-1].strip()
                    if "×" in sr:
                        sr_parts = sr.split("×")
                        try:
                            sets = int(sr_parts[0].strip())
                            reps = int(sr_parts[1].strip().split()[0])
                        except (ValueError, IndexError):
                            pass
                else:
                    ex_name = ex_line.split("—")[0].strip() if "—" in ex_line else ex_line
            else:
                ex_name = ex_line.split("—")[0].strip() if "—" in ex_line else ex_line

            # Чистимо суперсет
            if "Суперсет:" in ex_name:
                ex_name = ex_name.replace("Суперсет:", "").strip()

            if ex_name:
                exercises.append({"name": ex_name, "sets": sets, "reps": reps})

    if not exercises:
        await callback.answer("❌ Не вдалося знайти вправи", show_alert=True)
        return

    # Зберігаємо як тренування в конструкторі
    await save_custom_workout(callback.from_user.id, day_name.strip(), exercises)
    await state.clear()

    text = f"✅ <b>Збережено в конструктор!</b>\n\n📋 {day_name.strip()}\n\n<b>Вправи:</b>\n"
    for i, ex in enumerate(exercises, 1):
        text += f"{i}. {ex['name']} — {ex['sets']}×{ex['reps']}\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Запустити тренування", callback_data="constructor")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]),
    )