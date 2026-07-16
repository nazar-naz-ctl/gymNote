from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import random

from database import get_user, update_user_field
from exercises_db import get_exercises

from backend.generator import (
    generate_program,
    generate_optimized_program,
    format_program,
    program_to_storable,
    program_from_storable,
    find_exercises,
    filter_by_difficulty,
)

router = Router()


class GeneratorStates(StatesGroup):
    location  = State()
    equipment = State()
    goal      = State()
    level     = State()
    days      = State()


LOCATION_MAP = {
    "loc_gym":     ("зал", "🏋️ Зал"),
    "loc_home":    ("дома", "🏠 Дома"),
    "loc_outdoor": ("вулиця", "🌳 Вулиця"),
}

EQUIPMENT_MAP = {
    "eq_barbell":       "штанга",
    "eq_dumbbells":     "гантелі",
    "eq_machines":      "тренажер",
    "eq_bodyweight":    "власна вага",
    "eq_bands":         "резинки",
    "eq_mini_band":     "міні-петля",
    "eq_long_band":     "довга петля",
    "eq_therapy_band":  "терапевтична стрічка",
    "eq_kettlebell":    "гиря",
    "eq_pullup":        "турнік",
    "eq_bars":          "бруси",
    "eq_trx":           "TRX",
    "eq_rings":         "кільця",
}

GOAL_MAP = {
    "goal_mass":      "маса",
    "goal_relief":    "рельєф",
    "goal_strength":  "сила",
    "goal_loss":      "схуднення",
    "goal_endurance": "витривалість",
}

LEVEL_MAP = {
    "lvl_1": (1, "🟢 Початківець"),
    "lvl_2": (2, "🟡 Середній"),
    "lvl_3": (3, "🔴 Просунутий"),
    "lvl_4": (4, "🔥 Атлет"),
}


async def check_generation_limit(callback: CallbackQuery) -> bool:
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        last_gen = user.get("last_generation_date", "") if user else ""
        if last_gen:
            try:
                last_date = datetime.strptime(last_gen, "%d.%m.%Y")
                if datetime.now() - last_date < timedelta(days=7):
                    next_date = (last_date + timedelta(days=7)).strftime("%d.%m.%Y")
                    await callback.answer(
                        f"❌ Безкоштовно — 1 генерація на тиждень.\nНаступна: {next_date}",
                        show_alert=True
                    )
                    return False
            except ValueError:
                pass
    return True


async def generate_and_send(callback: CallbackQuery, state: FSMContext, location, equipment, goal, level, days):
    await callback.message.edit_text("⏳ Генерую програму...")

    program, quality_report = generate_optimized_program(location, equipment, goal, level, days)

    if not program:
        await callback.message.edit_text(
            "❌ Не вдалося знайти вправи для твоїх параметрів.\n"
            "Спробуй додати більше обладнання або змінити локацію.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Спробувати ще раз", callback_data="open_generator")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
        return

    await state.update_data(
        current_program=program_to_storable(program),
        current_goal=goal,
        current_level=level,
        current_days=days,
        current_equipment=equipment,
    )

    parts = format_program(program, goal, level, days, equipment, score=quality_report["score"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="regen_program")],
        [InlineKeyboardButton(text="🔁 Замінити вправу", callback_data="replace_start")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    for i, part in enumerate(parts):
        if i == 0:
            await callback.message.edit_text(part, reply_markup=kb if len(parts) == 1 else None)
        elif i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        await update_user_field(
            callback.from_user.id,
            "last_generation_date",
            datetime.now().strftime("%d.%m.%Y")
        )


@router.callback_query(F.data == "open_generator")
async def generator_start(callback: CallbackQuery, state: FSMContext):
    if not await check_generation_limit(callback):
        return

    await state.set_state(GeneratorStates.location)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал", callback_data="loc_gym")],
        [InlineKeyboardButton(text="🏠 Вдома", callback_data="loc_home")],
        [InlineKeyboardButton(text="🌳 Вулиця / Майданчик", callback_data="loc_outdoor")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "🤖 <b>Генератор програм</b>\n\n"
        "Крок 1/5 — Де будеш тренуватись?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.location, F.data.startswith("loc_"))
async def generator_location(callback: CallbackQuery, state: FSMContext):
    location, loc_name = LOCATION_MAP[callback.data]
    await state.update_data(location=location, selected_equipment=[])

    if location == "зал":
        buttons = [
            [InlineKeyboardButton(text="🏋️ Штанга", callback_data="eq_barbell"),
             InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells")],
            [InlineKeyboardButton(text="⚙️ Тренажери", callback_data="eq_machines"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx"),
             InlineKeyboardButton(text="🔴 Резинки (загальні)", callback_data="eq_bands")],
            [InlineKeyboardButton(text="🟢 Міні-петля", callback_data="eq_mini_band"),
             InlineKeyboardButton(text="🟣 Довга петля", callback_data="eq_long_band")],
            [InlineKeyboardButton(text="🟡 Терапевтична стрічка", callback_data="eq_therapy_band")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]
    elif location == "дома":
        buttons = [
            [InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔴 Резинки (загальні)", callback_data="eq_bands"),
             InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx")],
            [InlineKeyboardButton(text="🟢 Міні-петля", callback_data="eq_mini_band"),
             InlineKeyboardButton(text="🟣 Довга петля", callback_data="eq_long_band")],
            [InlineKeyboardButton(text="🟡 Терапевтична стрічка", callback_data="eq_therapy_band")],
            [InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔝 Турнік", callback_data="eq_pullup"),
             InlineKeyboardButton(text="🤸 Бруси", callback_data="eq_bars")],
            [InlineKeyboardButton(text="🔴 Резинки (загальні)", callback_data="eq_bands"),
             InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="⭕ Кільця", callback_data="eq_rings"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🟢 Міні-петля", callback_data="eq_mini_band"),
             InlineKeyboardButton(text="🟣 Довга петля", callback_data="eq_long_band")],
            [InlineKeyboardButton(text="🟡 Терапевтична стрічка", callback_data="eq_therapy_band")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]

    await state.set_state(GeneratorStates.equipment)
    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(GeneratorStates.equipment, F.data.startswith("eq_"))
async def generator_equipment(callback: CallbackQuery, state: FSMContext):
    if callback.data == "eq_done":
        data = await state.get_data()
        selected = data.get("selected_equipment", [])

        if not selected:
            selected = ["власна вага"]
            await state.update_data(selected_equipment=selected)

        await ask_goal(callback, state)
        return

    data = await state.get_data()
    selected = data.get("selected_equipment", [])
    eq_name = EQUIPMENT_MAP.get(callback.data, "")

    if eq_name in selected:
        selected.remove(eq_name)
        if eq_name == "тренажер" and "блок" in selected:
            selected.remove("блок")
        await callback.answer(f"❌ {eq_name} прибрано")
    else:
        selected.append(eq_name)
        if eq_name == "тренажер" and "блок" not in selected:
            selected.append("блок")
        await callback.answer(f"✅ {eq_name} додано")

    await state.update_data(selected_equipment=selected)
    selected_text = ", ".join(selected) if selected else "нічого"
    data = await state.get_data()
    loc_name = {"зал": "🏋️ Зал", "дома": "🏠 Дома", "вулиця": "🌳 Вулиця"}.get(data["location"], "")

    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n"
        f"🏋️ Обрано: <b>{selected_text}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=callback.message.reply_markup,
    )


async def ask_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GeneratorStates.goal)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Набір маси", callback_data="goal_mass")],
        [InlineKeyboardButton(text="✂️ Рельєф / Сушка", callback_data="goal_relief")],
        [InlineKeyboardButton(text="🏋️ Сила", callback_data="goal_strength")],
        [InlineKeyboardButton(text="🔥 Схуднення", callback_data="goal_loss")],
        [InlineKeyboardButton(text="🏃 Витривалість", callback_data="goal_endurance")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 3/5 — Яка твоя ціль?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.goal, F.data.startswith("goal_"))
async def generator_goal(callback: CallbackQuery, state: FSMContext):
    goal = GOAL_MAP[callback.data]
    await state.update_data(goal=goal)
    await state.set_state(GeneratorStates.level)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець — до 6 місяців", callback_data="lvl_1")],
        [InlineKeyboardButton(text="🟡 Середній — 6-18 місяців", callback_data="lvl_2")],
        [InlineKeyboardButton(text="🔴 Просунутий — 1.5-3 роки", callback_data="lvl_3")],
        [InlineKeyboardButton(text="🔥 Атлет — 3+ роки", callback_data="lvl_4")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 4/5 — Твій рівень підготовки?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.level, F.data.startswith("lvl_"))
async def generator_level(callback: CallbackQuery, state: FSMContext):
    level_num, _ = LEVEL_MAP[callback.data]
    await state.update_data(level=level_num)
    await state.set_state(GeneratorStates.days)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 день", callback_data="days_1"),
            InlineKeyboardButton(text="2 дні", callback_data="days_2"),
            InlineKeyboardButton(text="3 дні", callback_data="days_3"),
        ],
        [
            InlineKeyboardButton(text="4 дні", callback_data="days_4"),
            InlineKeyboardButton(text="5 днів", callback_data="days_5"),
            InlineKeyboardButton(text="6 днів", callback_data="days_6"),
        ],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 5/5 — Скільки днів на тиждень тренуєшся?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.days, F.data.startswith("days_"))
async def generator_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.replace("days_", ""))
    data = await state.get_data()

    location = data["location"]
    equipment = data["selected_equipment"]
    goal = data["goal"]
    level = data["level"]

    await state.update_data(
        last_location=location,
        last_equipment=equipment,
        last_goal=goal,
        last_level=level,
        last_days=days,
    )
    await state.set_state(None)

    await generate_and_send(callback, state, location, equipment, goal, level, days)


@router.callback_query(F.data == "regen_program")
async def regen_program(callback: CallbackQuery, state: FSMContext):
    if not await check_generation_limit(callback):
        return

    data = await state.get_data()
    location = data.get("last_location")
    equipment = data.get("last_equipment")
    goal = data.get("last_goal")
    level = data.get("last_level")
    days = data.get("last_days")

    if not all([location, equipment, goal, level, days]):
        await callback.answer("⚠️ Параметри втрачені, почни спочатку", show_alert=True)
        await generator_start(callback, state)
        return

    await generate_and_send(callback, state, location, equipment, goal, level, days)


@router.callback_query(F.data == "replace_start")
async def replace_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stored = data.get("current_program")
    if not stored:
        await callback.answer("⚠️ Спочатку згенеруй програму", show_alert=True)
        return
    program = program_from_storable(stored)

    buttons = []
    for day_num, day_data in program.items():
        if not day_data.get("exercises"):
            continue
        buttons.append([InlineKeyboardButton(
            text=f"День {day_num} — {day_data['name']}",
            callback_data=f"replace_day:{day_num}",
        )])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="replace_cancel")])

    await callback.message.answer(
        "🔁 <b>Заміна вправи</b>\n\nОбери день:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("replace_day:"))
async def replace_day(callback: CallbackQuery, state: FSMContext):
    day_num = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    stored = data.get("current_program")
    if not stored:
        await callback.answer("⚠️ Програма застаріла", show_alert=True)
        return
    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data:
        await callback.answer("⚠️ День не знайдено", show_alert=True)
        return

    buttons = []
    for i, ex in enumerate(day_data["exercises"]):
        label = ex["name"]
        if len(label) > 45:
            label = label[:42] + "..."
        buttons.append([InlineKeyboardButton(text=f"{i + 1}. {label}", callback_data=f"replace_ex:{day_num}:{i}")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="replace_cancel")])

    await callback.message.edit_text(
        f"🔁 <b>День {day_num} — {day_data['name']}</b>\n\nЯку вправу замінити?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("replace_ex:"))
async def replace_ex(callback: CallbackQuery, state: FSMContext):
    _, day_num_str, idx_str = callback.data.split(":")
    day_num = int(day_num_str)
    idx = int(idx_str)

    data = await state.get_data()
    stored = data.get("current_program")
    equipment = data.get("current_equipment", [])
    level = data.get("current_level", 1)
    goal = data.get("current_goal", "маса")
    days = data.get("current_days", 1)

    if not stored:
        await callback.answer("⚠️ Програма застаріла", show_alert=True)
        return

    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data or idx >= len(day_data["exercises"]):
        await callback.answer("⚠️ Вправу не знайдено", show_alert=True)
        return

    old_ex = day_data["exercises"][idx]
    used_names = {e["name"] for e in day_data["exercises"]}

    candidates = []
    for alt_name in old_ex.get("alternatives", []):
        matches = [e for e in get_exercises(equipment=equipment) if e["name"] == alt_name]
        matches = filter_by_difficulty(matches, level)
        candidates.extend(m for m in matches if m["name"] not in used_names)

    if not candidates:
        fallback = find_exercises(
            muscle_group=old_ex.get("_group", ""),
            ex_type=old_ex.get("ex_type", "isolation"),
            equipment=equipment,
            level=level,
            goal=goal,
            used_names=set(used_names),
            count=1,
        )
        candidates = fallback

    if not candidates:
        await callback.answer("😔 Немає доступної заміни під твоє обладнання", show_alert=True)
        return

    new_ex = random.choice(candidates).copy()
    new_ex["sets"] = old_ex["sets"]
    new_ex["reps"] = old_ex["reps"]
    new_ex["ex_type"] = old_ex.get("ex_type")
    new_ex["_group"] = old_ex.get("_group")
    if "superset_id" in old_ex:
        new_ex["superset_id"] = old_ex["superset_id"]

    day_data["exercises"][idx] = new_ex
    program[day_num] = day_data

    await state.update_data(current_program=program_to_storable(program))

    parts = format_program(program, goal, level, days, equipment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="regen_program")],
        [InlineKeyboardButton(text="🔁 Замінити вправу", callback_data="replace_start")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(f"✅ Замінено: {old_ex['name']} → {new_ex['name']}")

    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    await callback.answer("Вправу замінено ✅")


@router.callback_query(F.data == "replace_cancel")
async def replace_cancel(callback: CallbackQuery):
    await callback.message.edit_text("Гаразд, залишаємо як є 🙂")
    await callback.answer()
