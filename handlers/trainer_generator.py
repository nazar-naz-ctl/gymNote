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

from config import TRAINER_ID
from database import get_user, update_user_field

from backend.generator import (
    generate_optimized_program,
    format_program,
    program_to_storable,
    generate_focus_workout,
    format_focus_workout,
)
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
            [InlineKeyboardButton(text="✂️ Рельєф / Сушка", callback_data="goal_relief")],
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
# 4. Призначення клієнту (персистентно в MongoDB)
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

    await update_user_field(client_id, "assigned_program", stored)
    await update_user_field(client_id, "assigned_program_goal", data.get("gen_goal"))
    await update_user_field(client_id, "assigned_program_level", data.get("gen_level"))
    await update_user_field(client_id, "assigned_program_days", data.get("gen_days"))

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
# 5. Фокус-тренування (одна/кілька груп м'язів)
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