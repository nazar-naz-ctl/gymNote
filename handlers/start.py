from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from config import TRAINER_ID
from database import user_exists, get_user, update_user_field, get_channel_link
from keyboards import role_kb, main_reply_kb, trainer_menu_kb

router = Router()


# ══════════════════════════════════════════════════════
# /start, /restart
# ══════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            referrer_id = None

    if user_id == TRAINER_ID:
        await message.answer(
            "👋 З поверненням, тренере!\n\nПанель керування GymNote:",
            reply_markup=trainer_menu_kb(),
        )
        return

    if await user_exists(user_id):
        user = await get_user(user_id)
        name = user.get("name", "") if user else ""

        # Перевірка пробного періоду
        trial_end = user.get("trial_end")
        if trial_end and user.get("subscription") == "premium":
            try:
                trial_date = datetime.strptime(trial_end, "%Y-%m-%d")
                if datetime.now() > trial_date:
                    await update_user_field(user_id, "subscription", "free")
                    await update_user_field(user_id, "trial_end", None)
                    await message.answer(
                        f"👋 З поверненням, {name}!\n\n"
                        f"⚠️ Твій пробний період закінчився.\n"
                        f"Ти перейшов на безкоштовний тариф.",
                        reply_markup=main_reply_kb(),
                    )
                    await _maybe_send_channel_link(message)
                    return
            except ValueError:
                pass

        from database import get_streak
        streak = await get_streak(user_id)
        streak_line = f"\n🔥 Серія: {streak['current']} днів" if streak['current'] > 0 else ""

        await message.answer(
            f"👋 З поверненням, {name}!{streak_line}",
            reply_markup=main_reply_kb(),
        )
        await _maybe_send_channel_link(message)
        return

    # Новий користувач
    if referrer_id:
        await state.update_data(referrer_id=referrer_id)

    await message.answer(
        "👋 Вітаємо в <b>GymNote</b>!\n\nТвій щоденник тренувань.\n\nХто ти?",
        reply_markup=role_kb(),
    )


@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


async def _maybe_send_channel_link(message: Message) -> None:
    """Reply-клавіатура не підтримує URL-кнопки — посилання на канал
    надсилаємо окремим коротким повідомленням одразу після меню."""
    link = await get_channel_link()
    if link:
        await message.answer(
            "📢 Наш канал:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти", url=link)],
            ]),
        )


# ══════════════════════════════════════════════════════
# 🏋️ Створити програму — вхід у генератор (Message-контекст)
# ══════════════════════════════════════════════════════

@router.message(F.text == "🏋️ Створити програму")
async def start_create_program(message: Message, state: FSMContext) -> None:
    from datetime import timedelta
    from config import PREMIUM_ENABLED
    from handlers.generator import GeneratorStates

    if PREMIUM_ENABLED:
        user = await get_user(message.from_user.id)
        sub = user.get("subscription", "free") if user else "free"
        if sub == "free":
            last_gen = user.get("last_generation_date", "") if user else ""
            if last_gen:
                try:
                    last_date = datetime.strptime(last_gen, "%d.%m.%Y")
                    if datetime.now() - last_date < timedelta(days=7):
                        next_date = (last_date + timedelta(days=7)).strftime("%d.%m.%Y")
                        await message.answer(
                            f"❌ Безкоштовно — 1 генерація на тиждень.\nНаступна: {next_date}"
                        )
                        return
                except ValueError:
                    pass

    await state.set_state(GeneratorStates.location)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал", callback_data="loc_gym")],
        [InlineKeyboardButton(text="🏠 Вдома", callback_data="loc_home")],
        [InlineKeyboardButton(text="🌳 Вулиця / Майданчик", callback_data="loc_outdoor")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await message.answer(
        "🤖 <b>Генератор програм</b>\n\n"
        "Крок 1/5 — Де будеш тренуватись?",
        reply_markup=kb,
    )


# ══════════════════════════════════════════════════════
# ▶️ Почати тренування — автоматична логіка (в межах сесії)
# ══════════════════════════════════════════════════════

@router.message(F.text == "▶️ Почати тренування")
async def start_begin_workout(message: Message, state: FSMContext) -> None:
    from handlers.workout import WorkoutStates
    from backend.generator import program_from_storable

    current_state = await state.get_state()

    # 1. Є незавершене тренування (в межах поточної сесії бота)
    if current_state == WorkoutStates.in_progress.state:
        await message.answer(
            "🔄 <b>У тебе є незавершене тренування</b>\n\nПродовжити з того ж місця?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Продовжити", callback_data="continue_unfinished")],
                [InlineKeyboardButton(text="🆕 Почати нове", callback_data="discard_and_new")],
            ]),
        )
        return

    data = await state.get_data()
    stored = data.get("current_program")
    focus_workout = data.get("current_focus_workout")

    user = await get_user(message.from_user.id)
    assigned = user.get("assigned_program") if user else None
    assigned_focus = user.get("assigned_focus_workout") if user else None

    buttons = []

    # 2а. Є ПРИЗНАЧЕНА ТРЕНЕРОМ програма (персистентна, з MongoDB —
    # переживає рестарт бота, на відміну від власної сесійної)
    if assigned:
        assigned_program = program_from_storable(assigned)
        for day_num, day_data in assigned_program.items():
            if not day_data.get("exercises"):
                continue
            buttons.append([InlineKeyboardButton(
                text=f"🎯 Від тренера — День {day_num} — {day_data['name']}",
                callback_data=f"starttrainerday:{day_num}",
            )])

    # 2б. Є ПРИЗНАЧЕНЕ ТРЕНЕРОМ Фокус-тренування (персистентне)
    if assigned_focus and assigned_focus.get("exercises"):
        buttons.append([InlineKeyboardButton(
            text=f"🎯 Від тренера — {assigned_focus['name']}",
            callback_data="starttrainerfocus",
        )])

    # 2в. Є власна багатоденна програма (згенерована цієї ж сесії)
    if stored:
        program = program_from_storable(stored)
        for day_num, day_data in program.items():
            if not day_data.get("exercises"):
                continue
            buttons.append([InlineKeyboardButton(
                text=f"День {day_num} — {day_data['name']}",
                callback_data=f"startday:{day_num}",
            )])

    # 2г. Є власне Фокус-тренування (генерація на 1+ груп м'язів) —
    # окрема, НЕ багатоденна ціль, зберігається у власному ключі стану
    if focus_workout and focus_workout.get("exercises"):
        buttons.append([InlineKeyboardButton(
            text=f"🎯 {focus_workout['name']}",
            callback_data="startfocus",
        )])

    if buttons:
        buttons.append([InlineKeyboardButton(text="🏋️ Створити нову програму", callback_data="open_generator")])
        await message.answer(
            "📋 <b>Твоя активна програма</b>\n\nОбери, що тренувати:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        return

    # 3. Немає програми — на створення
    await message.answer(
        "У тебе ще немає програми тренувань.\nСтвори її зараз 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏋️ Створити програму", callback_data="open_generator")],
        ]),
    )


async def _begin_workout_session(target_message, state: FSMContext, user_id: int, workout: dict) -> None:
    """Спільна логіка запуску тренувальної сесії — використовується і
    для дня багатоденної програми (startday:), і для Фокус-тренування
    (startfocus). target_message — повідомлення, яке редагуємо
    (callback.message), user_id — для пошуку минулого результату."""
    from handlers.workout import reps_kb_workout, make_dots, WorkoutStates, get_last_result

    await state.update_data(
        workout=workout,
        workout_index=-1,
        exercise_index=0,
        set_index=0,
        completed_sets={},
        current_weight=0.0,
        start_time=datetime.now().strftime("%H:%M"),
    )
    await state.set_state(WorkoutStates.in_progress)

    exercise = workout["exercises"][0]
    ex_name = exercise["name"]
    total_sets = exercise["sets"]
    target_reps = exercise["reps"]

    last = await get_last_result(user_id, ex_name)
    last_text = ""
    if last:
        last_text = "\n⏮ <i>Минулого разу: "
        last_text += " · ".join([f"{r['weight']}кг×{r['reps']}" for r in last])
        last_text += "</i>"

    dots = make_dots(total_sets, 0)
    await target_message.edit_text(
        f"🏋️ <b>{ex_name}</b>\n"
        f"<i>{workout['name']} · Вправа 1/{len(workout['exercises'])}</i>\n\n"
        f"Підхід <b>1</b>/{total_sets} · Ціль: {target_reps} повт\n"
        f"{dots}\n\n"
        f"⚖️ Вага: <b>не вказана</b>\n"
        f"<i>Напиши вагу в чат щоб змінити</i>"
        f"{last_text}",
        reply_markup=reps_kb_workout(),
    )


@router.callback_query(F.data.startswith("startday:"))
async def start_program_day(callback: CallbackQuery, state: FSMContext) -> None:
    from backend.generator import program_from_storable

    day_num = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    stored = data.get("current_program")
    if not stored:
        await callback.answer("⚠️ Програма більше не активна, згенеруй нову.", show_alert=True)
        return

    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data or not day_data.get("exercises"):
        await callback.answer("⚠️ У цьому дні немає вправ.", show_alert=True)
        return

    workout = {"name": day_data["name"], "exercises": day_data["exercises"]}
    await _begin_workout_session(callback.message, state, callback.from_user.id, workout)
    await callback.answer()


@router.callback_query(F.data.startswith("starttrainerday:"))
async def start_trainer_day(callback: CallbackQuery, state: FSMContext) -> None:
    """Запуск дня з програми, призначеної тренером — дані читаються
    напряму з MongoDB (не з FSM-стану), бо саме в цьому й сенс
    персистентності: працює навіть після рестарту бота."""
    from backend.generator import program_from_storable

    day_num = int(callback.data.split(":", 1)[1])
    user = await get_user(callback.from_user.id)
    assigned = user.get("assigned_program") if user else None
    if not assigned:
        await callback.answer("⚠️ Тренер ще не призначив тобі програму.", show_alert=True)
        return

    program = program_from_storable(assigned)
    day_data = program.get(day_num)
    if not day_data or not day_data.get("exercises"):
        await callback.answer("⚠️ У цьому дні немає вправ.", show_alert=True)
        return

    workout = {"name": day_data["name"], "exercises": day_data["exercises"]}
    await _begin_workout_session(callback.message, state, callback.from_user.id, workout)
    await callback.answer()


@router.callback_query(F.data == "starttrainerfocus")
async def start_trainer_focus(callback: CallbackQuery, state: FSMContext) -> None:
    """Запуск Фокус-тренування, призначеного тренером — дані читаються
    напряму з MongoDB, як і у starttrainerday:."""
    user = await get_user(callback.from_user.id)
    assigned_focus = user.get("assigned_focus_workout") if user else None
    if not assigned_focus or not assigned_focus.get("exercises"):
        await callback.answer("⚠️ Тренер ще не призначив тобі Фокус-тренування.", show_alert=True)
        return

    workout = {"name": assigned_focus["name"], "exercises": assigned_focus["exercises"]}
    await _begin_workout_session(callback.message, state, callback.from_user.id, workout)
    await callback.answer()


@router.callback_query(F.data == "startfocus")
async def start_focus_workout(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    focus_workout = data.get("current_focus_workout")
    if not focus_workout or not focus_workout.get("exercises"):
        await callback.answer("⚠️ Фокус-тренування більше не активне, згенеруй нове.", show_alert=True)
        return

    workout = {"name": focus_workout["name"], "exercises": focus_workout["exercises"]}
    await _begin_workout_session(callback.message, state, callback.from_user.id, workout)
    await callback.answer()


@router.callback_query(F.data == "continue_unfinished")
async def continue_unfinished(callback: CallbackQuery, state: FSMContext) -> None:
    from handlers.workout import show_current_exercise
    await show_current_exercise(callback, state)


@router.callback_query(F.data == "discard_and_new")
async def discard_and_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("🆕 Гаразд, попереднє тренування скинуто.")
    await start_begin_workout(callback.message, state)


# ══════════════════════════════════════════════════════
# 📊 Мій прогрес
# ══════════════════════════════════════════════════════

@router.message(F.text == "📊 Мій прогрес")
async def start_my_progress(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Мій прогрес",       callback_data="progress_my")],
        [InlineKeyboardButton(text="➕ Записати результат", callback_data="progress_add")],
        [InlineKeyboardButton(text="🏆 Особисті рекорди",  callback_data="progress_records")],
    ])
    await message.answer("📊 <b>Статистика і прогрес</b>\n\nОбирай:", reply_markup=kb)


# ══════════════════════════════════════════════════════
# 👤 Профіль
# ══════════════════════════════════════════════════════

def _build_profile_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мої дані",              callback_data="profile")],
        [InlineKeyboardButton(text="📋 Моя програма",           callback_data="my_active_program")],
        [InlineKeyboardButton(text="⭐ Підписка",               callback_data="my_subscription")],
        [InlineKeyboardButton(text="🎁 Реферальна програма",   callback_data="referral_menu")],
        [InlineKeyboardButton(text="🛠 Розширені інструменти",  callback_data="constructor")],
        [InlineKeyboardButton(text="💬 Підтримка",              callback_data="support")],
    ])


@router.message(F.text == "👤 Профіль")
async def start_profile_menu(message: Message) -> None:
    await message.answer("👤 <b>Профіль</b>\n\nОбирай:", reply_markup=_build_profile_menu_kb())


@router.callback_query(F.data == "menu_profile")
async def menu_profile_callback(callback: CallbackQuery) -> None:
    """Back-таргет для екранів, вкладених у Профіль (profile.py,
    referral.py, trainer.py)."""
    await callback.message.edit_text("👤 <b>Профіль</b>\n\nОбирай:", reply_markup=_build_profile_menu_kb())


@router.callback_query(F.data == "my_active_program")
async def my_active_program(callback: CallbackQuery, state: FSMContext) -> None:
    """Показує і власну сесійну програму, і персистентну програму
    від тренера (з MongoDB), якщо є — включно з Фокус-тренуванням.
    Кожне джерело можна видалити окремо, якщо воно більше не
    потрібне (не чекає автоматично на заміну)."""
    from backend.generator import program_from_storable

    data = await state.get_data()
    stored = data.get("current_program")
    user = await get_user(callback.from_user.id)
    assigned = user.get("assigned_program") if user else None
    assigned_focus = user.get("assigned_focus_workout") if user else None

    if not stored and not assigned and not assigned_focus:
        await callback.message.edit_text(
            "У тебе ще немає активної програми.\nСтвори її через головне меню 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="menu_profile")],
            ]),
        )
        return

    lines = []
    if assigned or assigned_focus:
        lines.append("🎯 <b>Від тренера:</b>")
        if assigned:
            assigned_program = program_from_storable(assigned)
            for day_num, day_data in assigned_program.items():
                lines.append(f"День {day_num} — {day_data['name']}")
        if assigned_focus:
            lines.append(f"Фокус-тренування — {assigned_focus['name']}")
        lines.append("")

    if stored:
        program = program_from_storable(stored)
        lines.append("📋 <b>Твоя власна програма:</b>")
        for day_num, day_data in program.items():
            lines.append(f"День {day_num} — {day_data['name']}")

    buttons = []
    if assigned:
        buttons.append([InlineKeyboardButton(text="🗑 Видалити програму від тренера", callback_data="delcheck:assigned_program")])
    if assigned_focus:
        buttons.append([InlineKeyboardButton(text="🗑 Видалити Фокус-тренування від тренера", callback_data="delcheck:assigned_focus")])
    if stored:
        buttons.append([InlineKeyboardButton(text="🗑 Видалити свою програму", callback_data="delcheck:own_program")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu_profile")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


_DELETE_LABELS = {
    "assigned_program": "програму від тренера",
    "assigned_focus": "Фокус-тренування від тренера",
    "own_program": "свою програму",
}


@router.callback_query(F.data.startswith("delcheck:"))
async def delete_program_confirm(callback: CallbackQuery) -> None:
    """Проміжне підтвердження — видалення незворотне (особливо для
    призначеної тренером програми), тому не видаляємо одразу."""
    target = callback.data.split(":", 1)[1]
    label = _DELETE_LABELS.get(target, "тренування")
    await callback.message.edit_text(
        f"⚠️ Точно видалити <b>{label}</b>?\nЦю дію не можна скасувати.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Так, видалити", callback_data=f"delconfirm:{target}")],
            [InlineKeyboardButton(text="← Скасувати", callback_data="my_active_program")],
        ]),
    )


@router.callback_query(F.data.startswith("delconfirm:"))
async def delete_program_execute(callback: CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if target == "assigned_program":
        await update_user_field(user_id, "assigned_program", None)
    elif target == "assigned_focus":
        await update_user_field(user_id, "assigned_focus_workout", None)
    elif target == "own_program":
        await state.update_data(current_program=None)
    else:
        await callback.answer("⚠️ Невідомий тип.", show_alert=True)
        return

    await callback.answer("🗑 Видалено", show_alert=True)
    await my_active_program(callback, state)


# ══════════════════════════════════════════════════════
# Універсальний "← Меню" (використовується як back-таргет по всьому боту)
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Reply-клавіатуру не можна прикріпити через edit_text — надсилаємо
    нове повідомлення. Старе інлайн-повідомлення просто прибираємо
    клавіатуру, щоб не лишалось 'мертвих' кнопок на екрані.

    Окремо обробляє тренера (TRAINER_ID) — у нього своя, інша
    навігація (Trainer Panel), а не User App reply-меню."""
    if callback.from_user.id == TRAINER_ID:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer(
            "👋 Панель керування GymNote:",
            reply_markup=trainer_menu_kb(),
        )
        await callback.answer()
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer("🏠 Головне меню:", reply_markup=main_reply_kb())
    await callback.answer()


@router.callback_query(F.data == "menu_workout")
async def menu_workout_bridge(callback: CallbackQuery, state: FSMContext) -> None:
    """Місток для старих 'Назад' кнопок у workout.py (constructor_menu,
    delete_workout_menu), що досі посилаються на застарілий callback
    'menu_workout' — перенаправляє в новий потік '▶️ Почати тренування'."""
    await callback.answer()
    await start_begin_workout(callback.message, state)
