"""
Trainer → Програми → Згенерувати
══════════════════════════════════
Підключає тренера до того самого розумного генератора, яким
користується клієнт (backend.generator), замість ручного набору
тексту (TrainerStates.typing_program в trainer.py — лишається як
є, не видаляємо, це окремий, більш простий і швидкий спосіб для
коротких приміток).

Призначена тренером програма зберігається ПЕРСИСТЕНТНО в MongoDB
(user["assigned_program"]) — на відміну від самостійної генерації
клієнта (яка живе лише в FSM-стані сесії бота). Це означає, що
клієнт побачить призначену тренером програму навіть після рестарту
бота — глибший рівень надійності, ніж власна генерація.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import random

from config import TRAINER_ID
from database import get_user, update_user_field

from backend.generator import (
    generate_optimized_program,
    format_program,
    program_to_storable,
    program_from_storable,
    find_exercises,
    filter_by_difficulty,
    generate_focus_workout,
    format_focus_workout,
)
from exercises_db import get_exercises
from handlers.generator import (
    LOCATION_MAP, EQUIPMENT_MAP, GOAL_MAP, LEVEL_MAP,
    FOCUS_GROUP_MAP, FOCUS_GROUP_LABELS,
)
from handlers.trainer import get_clients

router = Router()


class TrainerGenStates(StatesGroup):
    select_client  = State()
    location       = State()
    equipment      = State()
    goal           = State()
    level          = State()
    days           = State()
    focus_muscles  = State()
    focus_hardcore = State()


# ══════════════════════════════════════════════════════
# 1. Вибір клієнта
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "t_gen_start")
async def trainer_gen_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return

    clients = await get_clients()
    if not clients:
        await callback.answer("У тебе ще немає клієнтів.", show_alert=True)
        return

    await state.set_state(TrainerGenStates.select_client)
    buttons = [
        [InlineKeyboardButton(text=f"{c['name']}", callback_data=f"t_gen_client:{c['id']}")]
        for c in clients
    ]
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="t_programs")])
    await callback.message.edit_text(
        "🎯 <b>Згенерувати програму</b>\n\nОбери клієнта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(TrainerGenStates.select_client, F.data.startswith("t_gen_client:"))
async def trainer_gen_pick_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":", 1)[1])
    client = await get_user(client_id)
    client_name = client.get("name", "Клієнт") if client else "Клієнт"

    await state.update_data(target_client_id=client_id, target_client_name=client_name, selected_equipment=[])
    await state.set_state(TrainerGenStates.location)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал", callback_data="loc_gym")],
        [InlineKeyboardButton(text="🏠 Вдома", callback_data="loc_home")],
        [InlineKeyboardButton(text="🌳 Вулиця / Майданчик", callback_data="loc_outdoor")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
    ])
    await callback.message.edit_text(
        f"🎯 Клієнт: <b>{client_name}</b>\n\n"
        f"Крок 1/5 — Де тренується клієнт?",
        reply_markup=kb,
    )


# ══════════════════════════════════════════════════════
# 2. Локація → Обладнання
# ══════════════════════════════════════════════════════

@router.callback_query(TrainerGenStates.location, F.data.startswith("loc_"))
async def trainer_gen_location(callback: CallbackQuery, state: FSMContext):
    location, loc_name = LOCATION_MAP[callback.data]
    await state.update_data(location=location, selected_equipment=[])

    if location == "зал":
        buttons = [
            [InlineKeyboardButton(text="🏋️ Штанга", callback_data="eq_barbell"),
             InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells")],
            [InlineKeyboardButton(text="⚙️ Тренажери", callback_data="eq_machines"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx"),
             InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
        ]
    elif location == "дома":
        buttons = [
            [InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx")],
            [InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔝 Турнік", callback_data="eq_pullup"),
             InlineKeyboardButton(text="🤸 Бруси", callback_data="eq_bars")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
        ]

    await state.set_state(TrainerGenStates.equipment)
    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(TrainerGenStates.equipment, F.data.startswith("eq_"))
async def trainer_gen_equipment(callback: CallbackQuery, state: FSMContext):
    if callback.data == "eq_done":
        data = await state.get_data()
        selected = data.get("selected_equipment", [])
        if not selected:
            selected = ["власна вага"]
            await state.update_data(selected_equipment=selected)

        await state.set_state(TrainerGenStates.goal)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💪 Набір маси", callback_data="goal_mass")],
            [InlineKeyboardButton(text="✂ Рельєф / Сушка", callback_data="goal_relief")],
            [InlineKeyboardButton(text="🏋️ Сила", callback_data="goal_strength")],
            [InlineKeyboardButton(text="🔥 Схуднення", callback_data="goal_loss")],
            [InlineKeyboardButton(text="🏃 Витривалість", callback_data="goal_endurance")],
            [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
        ])
        await callback.message.edit_text("Крок 3/5 — Яка ціль клієнта?", reply_markup=kb)
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
    selected_text = ", ".join(selected) if selected else "нічого"
    await callback.message.edit_text(
        f"🏋️ Обрано: <b>{selected_text}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=callback.message.reply_markup,
    )


# ══════════════════════════════════════════════════════
# 3. Ціль → Рівень → Дні → Генерація
# ══════════════════════════════════════════════════════

@router.callback_query(TrainerGenStates.goal, F.data.startswith("goal_"))
async def trainer_gen_goal(callback: CallbackQuery, state: FSMContext):
    goal = GOAL_MAP[callback.data]
    await state.update_data(goal=goal)
    await state.set_state(TrainerGenStates.level)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець", callback_data="lvl_1")],
        [InlineKeyboardButton(text="🟡 Середній", callback_data="lvl_2")],
        [InlineKeyboardButton(text="🔴 Просунутий", callback_data="lvl_3")],
        [InlineKeyboardButton(text="🔥 Атлет", callback_data="lvl_4")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
    ])
    await callback.message.edit_text("Крок 4/5 — Рівень підготовки клієнта?", reply_markup=kb)


@router.callback_query(TrainerGenStates.level, F.data.startswith("lvl_"))
async def trainer_gen_level(callback: CallbackQuery, state: FSMContext):
    level_num, _ = LEVEL_MAP[callback.data]
    await state.update_data(level=level_num)
    await state.set_state(TrainerGenStates.days)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день", callback_data="days_1"),
         InlineKeyboardButton(text="2 дні", callback_data="days_2"),
         InlineKeyboardButton(text="3 дні", callback_data="days_3")],
        [InlineKeyboardButton(text="4 дні", callback_data="days_4"),
         InlineKeyboardButton(text="5 днів", callback_data="days_5"),
         InlineKeyboardButton(text="6 днів", callback_data="days_6")],
        [InlineKeyboardButton(text="🎯 Одна/кілька груп м'язів", callback_data="days_focus")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
    ])
    await callback.message.edit_text(
        "Крок 5/5 — Скільки днів на тиждень?\n\n"
        "<i>Або обери конкретну групу м'язів для фокус-тренування</i>",
        reply_markup=kb,
    )


@router.callback_query(TrainerGenStates.days, F.data.startswith("days_") & (F.data != "days_focus"))
async def trainer_gen_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.replace("days_", ""))
    data = await state.get_data()

    location = data["location"]
    equipment = data["selected_equipment"]
    goal = data["goal"]
    level = data["level"]
    client_id = data["target_client_id"]
    client_name = data["target_client_name"]

    await callback.message.edit_text("⏳ Генерую програму...")

    program, report = generate_optimized_program(location, equipment, goal, level, days)

    if not program:
        await callback.message.edit_text(
            "❌ Не вдалося знайти вправи для цих параметрів.\nСпробуй інше обладнання.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Спробувати ще раз", callback_data="t_gen_start")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
        return

    await state.update_data(
        generated_program=program_to_storable(program),
        gen_goal=goal, gen_level=level, gen_days=days, gen_equipment=equipment,
    )

    parts = format_program(program, goal, level, days, equipment, score=report["score"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Призначити клієнту", callback_data="t_gen_assign")],
        [InlineKeyboardButton(text="🔁 Замінити вправу", callback_data="t_replace_start")],
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data=f"t_gen_client:{client_id}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    for i, part in enumerate(parts):
        if i == 0:
            await callback.message.edit_text(
                f"🎯 Для клієнта: <b>{client_name}</b>\n\n{part}",
                reply_markup=kb if len(parts) == 1 else None,
            )
        elif i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)


# ══════════════════════════════════════════════════════
# 4а. Фокус-тренування (одна/кілька груп м'язів)
# ══════════════════════════════════════════════════════

@router.callback_query(TrainerGenStates.days, F.data == "days_focus")
async def trainer_gen_focus_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(selected_focus_groups=[])
    await state.set_state(TrainerGenStates.focus_muscles)

    buttons = []
    row = []
    for key, group_value in FOCUS_GROUP_MAP.items():
        label = FOCUS_GROUP_LABELS.get(group_value, group_value)
        row.append(InlineKeyboardButton(text=label, callback_data=key))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✅ Далі →", callback_data="tfocus_done")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")])

    await callback.message.edit_text(
        "🎯 <b>Фокус-тренування</b>\n\n"
        "Обери одну або кілька груп м'язів:\n"
        "<i>Вибери → натисни Далі</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(TrainerGenStates.focus_muscles, F.data.startswith("fg_"))
async def trainer_gen_focus_toggle(callback: CallbackQuery, state: FSMContext):
    group_value = FOCUS_GROUP_MAP.get(callback.data)
    if not group_value:
        return

    data = await state.get_data()
    selected = data.get("selected_focus_groups", [])
    label = FOCUS_GROUP_LABELS.get(group_value, group_value)

    if group_value in selected:
        selected.remove(group_value)
        await callback.answer(f"❌ {label} прибрано")
    else:
        selected.append(group_value)
        await callback.answer(f"✅ {label} додано")

    await state.update_data(selected_focus_groups=selected)
    selected_text = ", ".join(FOCUS_GROUP_LABELS.get(g, g) for g in selected) if selected else "нічого"

    buttons = []
    row = []
    for key, gv in FOCUS_GROUP_MAP.items():
        lbl = FOCUS_GROUP_LABELS.get(gv, gv)
        prefix = "✅ " if gv in selected else ""
        row.append(InlineKeyboardButton(text=f"{prefix}{lbl}", callback_data=key))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✅ Далі →", callback_data="tfocus_done")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")])

    await callback.message.edit_text(
        f"🎯 <b>Фокус-тренування</b>\n\n"
        f"Обрано: <b>{selected_text}</b>\n\n"
        f"Обери одну або кілька груп м'язів:\n"
        f"<i>Вибери → натисни Далі</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(TrainerGenStates.focus_muscles, F.data == "tfocus_done")
async def trainer_gen_focus_muscles_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_focus_groups", [])
    if not selected:
        await callback.answer("⚠️ Обери хоча б одну групу м'язів", show_alert=True)
        return

    await state.set_state(TrainerGenStates.focus_hardcore)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Просте", callback_data="tfh_1")],
        [InlineKeyboardButton(text="🟡 Середнє", callback_data="tfh_2")],
        [InlineKeyboardButton(text="🟠 Важке", callback_data="tfh_3")],
        [InlineKeyboardButton(text="🔴 Хардкор", callback_data="tfh_4")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_gen_start")],
    ])
    groups_text = ", ".join(FOCUS_GROUP_LABELS.get(g, g) for g in selected)
    await callback.message.edit_text(
        f"🎯 Групи: <b>{groups_text}</b>\n\nОбери рівень інтенсивності:",
        reply_markup=kb,
    )


@router.callback_query(TrainerGenStates.focus_hardcore, F.data.startswith("tfh_"))
async def trainer_gen_focus_hardcore(callback: CallbackQuery, state: FSMContext):
    hardcore = int(callback.data.replace("tfh_", ""))
    data = await state.get_data()

    muscle_groups = data.get("selected_focus_groups", [])
    equipment = data.get("selected_equipment", [])
    level = data.get("level", 2)
    goal = data.get("goal", "маса")
    client_id = data["target_client_id"]
    client_name = data["target_client_name"]

    await callback.message.edit_text("⏳ Генерую тренування...")

    day = generate_focus_workout(muscle_groups, equipment, level, hardcore, goal)

    if not day["exercises"]:
        await callback.message.edit_text(
            "❌ Не вдалося знайти вправи для цих груп м'язів під це обладнання.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Спробувати ще раз", callback_data="t_gen_start")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
        return

    await state.update_data(generated_focus_workout=day)

    text = format_focus_workout(day, muscle_groups, hardcore, equipment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Призначити клієнту", callback_data="t_gen_assign_focus")],
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data=f"t_gen_client:{client_id}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        f"🎯 Для клієнта: <b>{client_name}</b>\n\n{text}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "t_gen_assign_focus")
async def trainer_gen_assign_focus(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    day = data.get("generated_focus_workout")
    client_id = data.get("target_client_id")
    client_name = data.get("target_client_name", "Клієнт")

    if not day or not client_id:
        await callback.answer("⚠️ Дані втрачено, згенеруй ще раз.", show_alert=True)
        return

    await update_user_field(client_id, "assigned_focus_workout", day)

    try:
        from bot import bot
        await bot.send_message(
            client_id,
            "🎯 <b>Тренер призначив тобі Фокус-тренування!</b>\n\n"
            "Відкрий \"▶️ Почати тренування\" в головному меню, щоб побачити його.",
        )
    except Exception:
        pass

    await callback.answer("✅ Фокус-тренування призначено клієнту!", show_alert=True)
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ]))


# ══════════════════════════════════════════════════════
# 4б. Призначення клієнту (персистентно в MongoDB)
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "t_gen_assign")
async def trainer_gen_assign(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stored = data.get("generated_program")
    client_id = data.get("target_client_id")
    client_name = data.get("target_client_name", "Клієнт")

    if not stored or not client_id:
        await callback.answer("⚠️ Дані програми втрачено, згенеруй ще раз.", show_alert=True)
        return

    # Архів: якщо в клієнта вже була призначена програма — переносимо
    # її в архів ПЕРЕД перезаписом, а не втрачаємо назавжди. Це і є
    # джерело даних для "📋 Архів" і "🔁 Клонувати" — нічого окремо
    # не потрібно вести, історія формується сама по собі природним
    # чином при кожному новому призначенні.
    client = await get_user(client_id)
    old_program = client.get("assigned_program") if client else None
    if old_program:
        archive = client.get("archived_programs", []) or []
        archive.append({
            "program": old_program,
            "goal": client.get("assigned_program_goal"),
            "level": client.get("assigned_program_level"),
            "days": client.get("assigned_program_days"),
            "equipment": client.get("assigned_program_equipment"),
            "archived_date": datetime.now().strftime("%d.%m.%Y"),
        })
        await update_user_field(client_id, "archived_programs", archive)

    await update_user_field(client_id, "assigned_program", stored)
    await update_user_field(client_id, "assigned_program_goal", data.get("gen_goal"))
    await update_user_field(client_id, "assigned_program_level", data.get("gen_level"))
    await update_user_field(client_id, "assigned_program_days", data.get("gen_days"))
    await update_user_field(client_id, "assigned_program_equipment", data.get("gen_equipment"))

    try:
        from bot import bot
        await bot.send_message(
            client_id,
            "🎯 <b>Тренер призначив тобі нову програму!</b>\n\n"
            "Відкрий \"▶️ Почати тренування\" в головному меню, щоб побачити її.",
        )
    except Exception:
        pass

    await callback.answer("✅ Програму призначено клієнту!", show_alert=True)
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ]))


# ══════════════════════════════════════════════════════
# 5. Замінити вправу (в ще НЕ призначеній, щойно згенерованій програмі)
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "t_replace_start")
async def t_replace_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stored = data.get("generated_program")
    if not stored:
        await callback.answer("⚠️ Спочатку згенеруй програму.", show_alert=True)
        return
    program = program_from_storable(stored)

    buttons = []
    for day_num, day_data in program.items():
        if not day_data.get("exercises"):
            continue
        buttons.append([InlineKeyboardButton(
            text=f"День {day_num} — {day_data['name']}",
            callback_data=f"t_replace_day:{day_num}",
        )])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="t_replace_cancel")])

    await callback.message.answer(
        "🔁 <b>Заміна вправи</b>\n\nОбери день:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("t_replace_day:"))
async def t_replace_day(callback: CallbackQuery, state: FSMContext):
    day_num = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    stored = data.get("generated_program")
    if not stored:
        await callback.answer("⚠️ Програма застаріла.", show_alert=True)
        return
    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data:
        await callback.answer("⚠️ День не знайдено.", show_alert=True)
        return

    buttons = []
    for i, ex in enumerate(day_data["exercises"]):
        label = ex["name"]
        if len(label) > 45:
            label = label[:42] + "..."
        buttons.append([InlineKeyboardButton(text=f"{i + 1}. {label}", callback_data=f"t_replace_ex:{day_num}:{i}")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="t_replace_cancel")])

    await callback.message.edit_text(
        f"🔁 <b>День {day_num} — {day_data['name']}</b>\n\nЯку вправу замінити?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("t_replace_ex:"))
async def t_replace_ex(callback: CallbackQuery, state: FSMContext):
    _, day_num_str, idx_str = callback.data.split(":")
    day_num = int(day_num_str)
    idx = int(idx_str)

    data = await state.get_data()
    stored = data.get("generated_program")
    equipment = data.get("gen_equipment", [])
    level = data.get("gen_level", 1)
    goal = data.get("gen_goal", "маса")
    days = data.get("gen_days", 1)
    client_id = data.get("target_client_id")
    client_name = data.get("target_client_name", "Клієнт")

    if not stored:
        await callback.answer("⚠️ Програма застаріла.", show_alert=True)
        return

    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data or idx >= len(day_data["exercises"]):
        await callback.answer("⚠️ Вправу не знайдено.", show_alert=True)
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
        await callback.answer("😔 Немає доступної заміни під це обладнання.", show_alert=True)
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

    await state.update_data(generated_program=program_to_storable(program))

    parts = format_program(program, goal, level, days, equipment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Призначити клієнту", callback_data="t_gen_assign")],
        [InlineKeyboardButton(text="🔁 Замінити ще", callback_data="t_replace_start")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(f"✅ Замінено: {old_ex['name']} → {new_ex['name']}")

    for i, part in enumerate(parts):
        if i == 0:
            await callback.message.answer(f"🎯 Для клієнта: <b>{client_name}</b>\n\n{part}")
        elif i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    await callback.answer("Вправу замінено ✅")


@router.callback_query(F.data == "t_replace_cancel")
async def t_replace_cancel(callback: CallbackQuery):
    await callback.message.edit_text("Гаразд, залишаємо як є 🙂")
    await callback.answer()


# ══════════════════════════════════════════════════════
# 6. Архів і Клонування
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "t_archive_start")
async def t_archive_start(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    clients = await get_clients()
    if not clients:
        await callback.answer("У тебе ще немає клієнтів.", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton(text=c["name"], callback_data=f"t_archive_client:{c['id']}")]
        for c in clients
    ]
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="t_programs")])
    await callback.message.edit_text(
        "📋 <b>Архів програм</b>\n\nОбери клієнта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("t_archive_client:"))
async def t_archive_client(callback: CallbackQuery):
    client_id = int(callback.data.split(":", 1)[1])
    client = await get_user(client_id)
    archive = (client.get("archived_programs") or []) if client else []

    if not archive:
        await callback.message.edit_text(
            "📋 <b>Архів</b>\n\nУ цього клієнта ще немає архівних програм "
            "(з'являються автоматично при призначенні нової замість попередньої).",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="t_archive_start")],
            ]),
        )
        return

    buttons = []
    for i, entry in enumerate(archive):
        label = f"{entry.get('archived_date', '—')} — {entry.get('goal', '—')}, {entry.get('days', '—')} дн."
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"t_archive_view:{client_id}:{i}")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="t_archive_start")])

    await callback.message.edit_text(
        f"📋 <b>Архів програм — {client.get('name', 'Клієнт')}</b>\n\nОбери запис:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("t_archive_view:"))
async def t_archive_view(callback: CallbackQuery):
    _, client_id_str, idx_str = callback.data.split(":")
    client_id = int(client_id_str)
    idx = int(idx_str)

    client = await get_user(client_id)
    archive = (client.get("archived_programs") or []) if client else []
    if idx >= len(archive):
        await callback.answer("⚠️ Запис не знайдено.", show_alert=True)
        return

    entry = archive[idx]
    program = program_from_storable(entry["program"])
    parts = format_program(
        program, entry.get("goal", "маса"), entry.get("level", 1),
        entry.get("days", 1), entry.get("equipment", []),
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Клонувати (призначити знову)", callback_data=f"t_archive_clone:{client_id}:{idx}")],
        [InlineKeyboardButton(text="← Назад", callback_data=f"t_archive_client:{client_id}")],
    ])

    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)
    await callback.answer()


@router.callback_query(F.data.startswith("t_archive_clone:"))
async def t_archive_clone(callback: CallbackQuery):
    """Клонування — призначає архівну програму тому самому клієнту
    знову (стає його поточною assigned_program), а те, що було
    призначено щойно перед цим, автоматично йде в архів за тією ж
    логікою, що й у t_gen_assign."""
    _, client_id_str, idx_str = callback.data.split(":")
    client_id = int(client_id_str)
    idx = int(idx_str)

    client = await get_user(client_id)
    archive = (client.get("archived_programs") or []) if client else []
    if idx >= len(archive):
        await callback.answer("⚠️ Запис не знайдено.", show_alert=True)
        return
    entry = archive[idx]

    old_program = client.get("assigned_program") if client else None
    if old_program:
        new_archive = list(archive)
        new_archive.append({
            "program": old_program,
            "goal": client.get("assigned_program_goal"),
            "level": client.get("assigned_program_level"),
            "days": client.get("assigned_program_days"),
            "equipment": client.get("assigned_program_equipment"),
            "archived_date": datetime.now().strftime("%d.%m.%Y"),
        })
        await update_user_field(client_id, "archived_programs", new_archive)

    await update_user_field(client_id, "assigned_program", entry["program"])
    await update_user_field(client_id, "assigned_program_goal", entry.get("goal"))
    await update_user_field(client_id, "assigned_program_level", entry.get("level"))
    await update_user_field(client_id, "assigned_program_days", entry.get("days"))
    await update_user_field(client_id, "assigned_program_equipment", entry.get("equipment"))

    try:
        from bot import bot
        await bot.send_message(
            client_id,
            "🎯 <b>Тренер призначив тобі програму!</b>\n\n"
            "Відкрий \"▶️ Почати тренування\" в головному меню, щоб побачити її.",
        )
    except Exception:
        pass

    await callback.answer("✅ Клоновано й призначено клієнту!", show_alert=True)
