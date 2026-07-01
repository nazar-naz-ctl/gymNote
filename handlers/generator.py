from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import random

from database import get_user, update_user_field
from exercises_db import get_exercises

router = Router()


class GeneratorStates(StatesGroup):
    location    = State()
    equipment   = State()
    goal        = State()
    level       = State()
    days        = State()


# ── МАПИ ──────────────────────────────────────────────────────────────────────

LOCATION_MAP = {
    "loc_gym":     ("зал", "🏋️ Зал"),
    "loc_home":    ("дома", "🏠 Дома"),
    "loc_outdoor": ("вулиця", "🌳 Вулиця"),
}

EQUIPMENT_MAP = {
    "eq_barbell":     "штанга",
    "eq_dumbbells":   "гантелі",
    "eq_machines":    "тренажер",
    "eq_bodyweight":  "власна вага",
    "eq_bands":       "резинки",
    "eq_kettlebell":  "гиря",
    "eq_pullup":      "турнік",
    "eq_bars":        "бруси",
    "eq_trx":         "TRX",
    "eq_rings":       "кільця",
}

GOAL_MAP = {
    "goal_mass":        "маса",
    "goal_relief":      "рельєф",
    "goal_strength":    "сила",
    "goal_loss":        "схуднення",
    "goal_endurance":   "витривалість",
}

LEVEL_MAP = {
    "lvl_1": (1, "🟢 Початківець"),
    "lvl_2": (2, "🟡 Середній"),
    "lvl_3": (3, "🔴 Просунутий"),
    "lvl_4": (4, "🔥 Атлет"),
}

MUSCLE_GROUPS = {
    1: {"name": "День 1 — Груди + Трицепс", "muscles": ["груди", "трицепс"]},
    2: {"name": "День 2 — Спина + Біцепс", "muscles": ["широчайні", "біцепс", "трапеція"]},
    3: {"name": "День 3 — Ноги", "muscles": ["квадрицепс", "сідниці", "біцепс стегна", "литки"]},
    4: {"name": "День 4 — Плечі + Прес", "muscles": ["передні дельти", "середні дельти", "задні дельти", "прес"]},
    5: {"name": "День 5 — Фулбоді A", "muscles": ["груди", "широчайні", "квадрицепс", "прес"]},
    6: {"name": "День 6 — Фулбоді B", "muscles": ["сідниці", "трицепс", "біцепс", "плечі"]},
}

EXERCISES_PER_DAY = {1: 5, 2: 5, 3: 6, 4: 6, 5: 7, 6: 7}

DAY_SPLITS = {
    1: [5],
    2: [1, 2],
    3: [1, 2, 3],
    4: [1, 2, 3, 4],
    5: [1, 2, 3, 4, 5],
    6: [1, 2, 3, 4, 5, 6],
}


# ── КРОК 1 — ЛОКАЦІЯ ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "open_generator")
async def generator_start(callback: CallbackQuery, state: FSMContext):
    # Перевірка ліміту для free
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"

    if sub == "free":
        last_gen = user.get("last_generation_date", "") if user else ""
        if last_gen:
            last_date = datetime.strptime(last_gen, "%d.%m.%Y")
            if datetime.now() - last_date < timedelta(days=7):
                next_date = (last_date + timedelta(days=7)).strftime("%d.%m.%Y")
                await callback.answer(
                    f"❌ Безкоштовно — 1 генерація на тиждень.\nНаступна: {next_date}",
                    show_alert=True
                )
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


# ── КРОК 2 — ОБЛАДНАННЯ ───────────────────────────────────────────────────────

@router.callback_query(GeneratorStates.location, F.data.startswith("loc_"))
async def generator_location(callback: CallbackQuery, state: FSMContext):
    loc_key = callback.data
    location, loc_name = LOCATION_MAP[loc_key]
    await state.update_data(location=location, selected_equipment=[])

    # Кнопки обладнання залежно від локації
    if location == "зал":
        buttons = [
            [InlineKeyboardButton(text="🏋️ Штанга", callback_data="eq_barbell"),
             InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells")],
            [InlineKeyboardButton(text="⚙ Тренажери", callback_data="eq_machines"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx"),
             InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands")],
        ]
    elif location == "дома":
        buttons = [
            [InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx")],
            [InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
        ]
    else:  # вулиця
        buttons = [
            [InlineKeyboardButton(text="🔝 Турнік", callback_data="eq_pullup"),
             InlineKeyboardButton(text="🤸 Бруси", callback_data="eq_bars")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="⭕ Кільця", callback_data="eq_rings")],
        ]

    buttons.append([InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")])

    await state.set_state(GeneratorStates.equipment)
    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Можна вибрати кілька</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


# ── КРОК 2 — МУЛЬТИВИБІР ОБЛАДНАННЯ ──────────────────────────────────────────

@router.callback_query(GeneratorStates.equipment, F.data.startswith("eq_"))
async def generator_equipment(callback: CallbackQuery, state: FSMContext):
    if callback.data == "eq_done":
        data = await state.get_data()
        selected = data.get("selected_equipment", [])
        if not selected:
            await callback.answer("❌ Вибери хоча б одне обладнання!", show_alert=True)
            return
        await ask_goal(callback, state)
        return

    data = await state.get_data()
    selected = data.get("selected_equipment", [])
    eq_name = EQUIPMENT_MAP.get(callback.data, "")

    if eq_name in selected:
        selected.remove(eq_name)
        await callback.answer(f"❌ {eq_name} прибрано")
    else:
        selected.append(eq_name)
        await callback.answer(f"✅ {eq_name} додано")

    await state.update_data(selected_equipment=selected)

    selected_text = ", ".join(selected) if selected else "нічого не вибрано"
    data = await state.get_data()
    loc_name = {"зал": "🏋️ Зал", "дома": "🏠 Дома", "вулиця": "🌳 Вулиця"}.get(data["location"], "")

    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n"
        f"🏋️ Обрано: <b>{selected_text}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Можна вибрати кілька → натисни Далі</i>",
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


# ── КРОК 3 — ЦІЛЬ ────────────────────────────────────────────────────────────

@router.callback_query(GeneratorStates.goal, F.data.startswith("goal_"))
async def generator_goal(callback: CallbackQuery, state: FSMContext):
    goal = GOAL_MAP[callback.data]
    await state.update_data(goal=goal)
    await state.set_state(GeneratorStates.level)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець (до 6 міс)", callback_data="lvl_1")],
        [InlineKeyboardButton(text="🟡 Середній (6-18 міс)", callback_data="lvl_2")],
        [InlineKeyboardButton(text="🔴 Просунутий (1.5-3 роки)", callback_data="lvl_3")],
        [InlineKeyboardButton(text="🔥 Атлет (3+ роки)", callback_data="lvl_4")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 4/5 — Твій рівень підготовки?",
        reply_markup=kb,
    )


# ── КРОК 4 — РІВЕНЬ ──────────────────────────────────────────────────────────

@router.callback_query(GeneratorStates.level, F.data.startswith("lvl_"))
async def generator_level(callback: CallbackQuery, state: FSMContext):
    level_num, level_name = LEVEL_MAP[callback.data]
    await state.update_data(level=level_num)
    await state.set_state(GeneratorStates.days)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день", callback_data="days_1"),
         InlineKeyboardButton(text="2 дні", callback_data="days_2"),
         InlineKeyboardButton(text="3 дні", callback_data="days_3")],
        [InlineKeyboardButton(text="4 дні", callback_data="days_4"),
         InlineKeyboardButton(text="5 днів", callback_data="days_5"),
         InlineKeyboardButton(text="6 днів", callback_data="days_6")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 5/5 — Скільки днів на тиждень?",
        reply_markup=kb,
    )


# ── КРОК 5 — ГЕНЕРАЦІЯ ───────────────────────────────────────────────────────

@router.callback_query(GeneratorStates.days, F.data.startswith("days_"))
async def generator_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.replace("days_", ""))
    data = await state.get_data()
    await state.clear()

    equipment = data["selected_equipment"]
    goal = data["goal"]
    level = data["level"]

    await callback.message.edit_text("⏳ Генерую програму...")

    # Генерація програми
    program = generate_program(equipment, goal, level, days)

    if not program:
        await callback.message.edit_text(
            "❌ Не вдалося знайти достатньо вправ для твоїх параметрів.\n"
            "Спробуй додати більше обладнання.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Спробувати ще раз", callback_data="open_generator")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
        return

    # Формуємо текст програми
    goal_names = {"маса": "💪 Набір маси", "рельєф": "✂️ Рельєф", "сила": "🏋️ Сила", "схуднення": "🔥 Схуднення", "витривалість": "🏃 Витривалість"}
    level_names = {1: "🟢 Початківець", 2: "🟡 Середній", 3: "🔴 Просунутий", 4: "🔥 Атлет"}

    text = f"🤖 <b>Твоя програма тренувань</b>\n\n"
    text += f"🎯 Ціль: {goal_names.get(goal, goal)}\n"
    text += f"⚡ Рівень: {level_names.get(level, level)}\n"
    text += f"📅 Днів: {days}\n"
    text += f"🏋️ Обладнання: {', '.join(equipment)}\n\n"
    text += "━━━━━━━━━━━━━━━━\n"

    for day_num, day_data in program.items():
        text += f"\n📌 <b>{day_data['name']}</b>\n"
        for i, ex in enumerate(day_data["exercises"], 1):
            sets = ex.get("sets", 3)
            reps = ex.get("reps", 10)
            text += f"• {ex['name']} — {sets}×{reps}\n"
        text += "\n"

    # Зберігаємо дату генерації для free користувачів
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        await update_user_field(
            callback.from_user.id,
            "last_generation_date",
            datetime.now().strftime("%d.%m.%Y")
        )

    # Відправляємо по частинах якщо текст великий
    if len(text) > 4000:
        parts = []
        lines = text.split("\n")
        current = ""
        for line in lines:
            if len(current) + len(line) > 3800:
                parts.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            parts.append(current)

        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part)
            else:
                await callback.message.answer(part)

        await callback.message.answer(
            "✅ Програма готова!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="open_generator")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="open_generator")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )


# ── ГЕНЕРАТОР ─────────────────────────────────────────────────────────────────

def generate_program(equipment: list, goal: str, level: int, days: int) -> dict:
    day_indices = DAY_SPLITS.get(days, [5])
    program = {}

    for day_num, muscle_idx in enumerate(day_indices, 1):
        muscle_data = MUSCLE_GROUPS[muscle_idx]
        target_muscles = muscle_data["muscles"]
        ex_count = EXERCISES_PER_DAY.get(days, 5)

        # Знаходимо вправи
        day_exercises = []
        for muscle in target_muscles:
            found = get_exercises(
                equipment=equipment,
                muscles=[muscle],
                level=level,
                goal=goal,
                ex_type="сила",
            )
            # Якщо не знайшли для рівня — шукаємо без рівня
            if not found:
                found = get_exercises(
                    equipment=equipment,
                    muscles=[muscle],
                    goal=goal,
                    ex_type="сила",
                )
            if found:
                # Беремо 1-2 вправи на м'яз
                picks = random.sample(found, min(2, len(found)))
                day_exercises.extend(picks)

        # Прибираємо дублі
        seen = set()
        unique = []
        for ex in day_exercises:
            if ex["name"] not in seen:
                seen.add(ex["name"])
                unique.append(ex)

        # Обмежуємо кількість
        final = unique[:ex_count]

        if not final:
            continue

        # Додаємо підходи і повтори залежно від цілі
        sets_reps = {
            "маса": (4, 8),
            "сила": (5, 5),
            "рельєф": (3, 12),
            "схуднення": (3, 15),
            "витривалість": (3, 20),
        }
        sets, reps = sets_reps.get(goal, (3, 10))

        for ex in final:
            ex["sets"] = sets
            ex["reps"] = reps

        program[day_num] = {
            "name": muscle_data["name"],
            "exercises": final,
        }

    return program
