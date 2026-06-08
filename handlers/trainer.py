from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TRAINER_ID, BOT_TOKEN
from database import get_user, get_all_users, _load, _save, update_user_field
from keyboards import trainer_menu_kb

router = Router()


class TrainerStates(StatesGroup):
    typing_program   = State()
    typing_broadcast = State()
    typing_answer    = State()

class PaymentStates(StatesGroup):
    waiting_screenshot_standard = State()
    waiting_screenshot_premium  = State()

class SettingsStates(StatesGroup):
    typing_requisites = State()
    typing_channel = State()

class PriceStates(StatesGroup):
        typing_standard = State()
        typing_premium = State()


async def get_clients() -> list:
    all_users = await get_all_users()
    clients = []
    for uid, data in all_users.items():
        try:
            user_id = int(uid)
        except ValueError:
            continue
        if user_id != TRAINER_ID and data.get("registered"):
            clients.append({
                "id":           user_id,
                "name":         data.get("name", "Невідомий"),
                "subscription": data.get("subscription", "free"),
            })
    return clients


async def get_inbox() -> list:
    db = await _load()
    questions = db.get("questions", [])
    unanswered = [q for q in questions if not q["answered"]]
    order = {"premium": 0, "standard": 1, "free": 2}
    return sorted(unanswered, key=lambda x: order.get(x["subscription"], 2))


async def save_trainer_program(user_id: int, program: str) -> None:
    db = await _load()
    key = str(user_id)
    if key not in db:
        db[key] = {}
    if "trainer_programs" not in db[key]:
        db[key]["trainer_programs"] = []
    from datetime import datetime
    db[key]["trainer_programs"].append({
        "program": program,
        "date":    datetime.now().strftime("%d.%m.%Y"),
        "read":    False,
    })
    await _save(db)


async def get_trainer_programs(user_id: int) -> list:
    user = await get_user(user_id)
    if not user:
        return []
    return user.get("trainer_programs", [])


# ── Клієнт — від тренера ──────────────────────────

@router.callback_query(F.data == "from_trainer")
async def from_trainer(callback: CallbackQuery):
    programs = await get_trainer_programs(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="menu_trainer_contact")],
    ])
    if not programs:
        await callback.message.edit_text(
            "📬 <b>Від тренера</b>\n\nТренер ще не надіслав програму.",
            reply_markup=kb,
        )
        return
    buttons = []
    for i, p in enumerate(reversed(programs)):
        status = "🆕 " if not p["read"] else ""
        buttons.append([InlineKeyboardButton(
            text=f"{status}📋 Програма від {p['date']}",
            callback_data=f"view_program_{len(programs)-1-i}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        "📬 <b>Від тренера</b>\n\nТвої програми:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("view_program_"))
async def view_program(callback: CallbackQuery):
    index = int(callback.data.replace("view_program_", ""))
    programs = await get_trainer_programs(callback.from_user.id)
    if index >= len(programs):
        await callback.answer("Програму не знайдено.", show_alert=True)
        return
    db = await _load()
    key = str(callback.from_user.id)
    db[key]["trainer_programs"][index]["read"] = True
    await _save(db)
    program = programs[index]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="from_trainer")],
    ])
    await callback.message.edit_text(
        f"📋 <b>Програма від тренера</b>\n"
        f"📅 {program['date']}\n\n"
        f"{program['program']}",
        reply_markup=kb,
    )


# ── Тренер — клієнти ──────────────────────────────

@router.callback_query(F.data == "t_clients")
async def trainer_clients(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        await callback.answer("⛔ Доступ заборонено.", show_alert=True)
        return
    clients = await get_clients()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    if not clients:
        await callback.message.edit_text(
            "👥 <b>Мої клієнти</b>\n\nЩе немає клієнтів.",
            reply_markup=kb,
        )
        return
    sub_icon = {"premium": "👑", "standard": "⭐️", "free": "🆓"}

    # Сортуємо: преміум → стандарт → безкоштовний
    sorted_clients = sorted(clients, key=lambda c: (
        0 if c["subscription"] == "premium" else
        1 if c["subscription"] == "standard" else 2
    ))

    # Групуємо по підписці
    buttons = []
    current_sub = None
    for c in sorted_clients:
        sub = c["subscription"]
        if sub != current_sub:
            current_sub = sub
            if sub == "premium":
                buttons.append([InlineKeyboardButton(text="━━━ 👑 Преміум ━━━", callback_data="ignore")])
            elif sub == "standard":
                buttons.append([InlineKeyboardButton(text="━━━ ⭐️ Стандарт ━━━", callback_data="ignore")])
            else:
                buttons.append([InlineKeyboardButton(text="━━━ 🆓 Безкоштовний ━━━", callback_data="ignore")])
        icon = sub_icon.get(sub, "🆓")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {c['name']}",
            callback_data=f"t_client_{c['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        f"👥 <b>Мої клієнти — {len(clients)}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("t_client_") & ~F.data.startswith("t_client_results_") & ~F.data.startswith("t_client_records_"))
async def trainer_client_profile(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    data = callback.data.replace("t_client_", "")
    user_id = int(data) if data.isdigit() else int(data.split("_")[-1])
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    icon = sub_icon.get(user.get("subscription", "free"), "🆓")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Результати тренувань", callback_data=f"t_client_results_{user_id}")],
        [InlineKeyboardButton(text="🏆 Особисті рекорди", callback_data=f"t_client_records_{user_id}")],
        [InlineKeyboardButton(text="📋 Надіслати програму", callback_data=f"t_send_program_{user_id}")],
        [InlineKeyboardButton(text="✉️ Написати клієнту", callback_data=f"t_message_{user_id}")],
        [InlineKeyboardButton(text="💳 Змінити підписку", callback_data=f"t_sub_{user_id}")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_clients")],
    ])

    sub_labels = {"premium": "👑 Преміум", "standard": "⭐️ Стандарт", "free": "🆓 Безкоштовний"}
    sub_end = user.get("subscription_end") or user.get("trial_end") or "—"

    await callback.message.edit_text(
        f"👤 <b>{user.get('name')}</b>\n"
        f"Username: @{user.get('username') or '—'}\n\n"
        f"Підписка: {sub_labels.get(user.get('subscription', 'free'))}\n"
        f"Діє до: {sub_end}\n\n"
        f"Рівень:    {user.get('level', '—')}\n"
        f"Ціль:      {user.get('goal', '—')}\n"
        f"Локація:   {user.get('location', '—')}\n"
        f"Днів/тиж: {user.get('days', '—')}\n"
        f"Травми:    {user.get('injuries_label', 'Немає')}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("t_send_program_"))
async def trainer_send_program_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_send_program_", ""))
    await state.update_data(target_user_id=user_id)
    await state.set_state(TrainerStates.typing_program)
    user = await get_user(user_id)
    name = user.get("name", "Невідомий") if user else "Невідомий"
    await callback.message.edit_text(
        f"📨 <b>Програма для {name}</b>\n\nВведи програму текстом:",
    )


@router.message(TrainerStates.typing_program)
async def trainer_send_program(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    data = await state.get_data()
    user_id = data["target_user_id"]
    program = message.text.strip()
    await save_trainer_program(user_id, program)
    await state.clear()
    user = await get_user(user_id)
    name = user.get("name", "Невідомий") if user else "Невідомий"
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        bot = Bot(token=BOT_TOKEN,
                  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await bot.send_message(
            user_id,
            "📬 <b>Тренер надіслав нову програму!</b>\n\nВідкрий: 📬 Від тренера",
        )
        await bot.session.close()
    except Exception:
        pass
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Клієнти", callback_data="t_clients")],
        [InlineKeyboardButton(text="🏠 Меню",    callback_data="main_menu")],
    ])
    await message.answer(f"✅ <b>Програму надіслано {name}!</b>", reply_markup=kb)


# ── Тренер — вхідні ───────────────────────────────

@router.callback_query(F.data == "t_inbox")
async def trainer_inbox(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    inbox = await get_inbox()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    if not inbox:
        await callback.message.edit_text(
            "📬 <b>Вхідні</b>\n\nНемає нових питань.",
            reply_markup=kb,
        )
        return
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    text = f"📬 <b>Вхідні — {len(inbox)} питань</b>\n\n"
    buttons = []
    for i, q in enumerate(inbox[:10]):
        icon = sub_icon.get(q["subscription"], "🆓")
        text += f"{i+1}. {icon} {q['name']}\n❓ {q['question'][:60]}\n\n"
        buttons.append([InlineKeyboardButton(
            text=f"✍️ Відповісти #{i+1}",
            callback_data=f"t_answer_{i}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("t_answer_"))
async def trainer_answer_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    index = int(callback.data.replace("t_answer_", ""))
    inbox = await get_inbox()
    if index >= len(inbox):
        await callback.answer("Питання не знайдено.", show_alert=True)
        return
    q = inbox[index]
    await state.update_data(answer_index=index, answer_user_id=q["user_id"])
    await state.set_state(TrainerStates.typing_answer)
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    icon = sub_icon.get(q["subscription"], "🆓")
    await callback.message.edit_text(
        f"✍️ <b>Відповідь</b>\n\n"
        f"{icon} {q['name']}\n"
        f"❓ {q['question']}\n\n"
        f"Введи відповідь:",
    )


@router.message(TrainerStates.typing_answer)
async def trainer_send_answer(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    data = await state.get_data()
    index = data.get("answer_index")
    user_id = data.get("answer_user_id") or data.get("message_to_user_id")
    answer = message.text.strip()
    await state.clear()

    if index is not None:
        db = await _load()
        unanswered = [q for q in db.get("questions", []) if not q["answered"]]
        if index < len(unanswered):
            for i, q in enumerate(db["questions"]):
                if q == unanswered[index]:
                    db["questions"][i]["answered"] = True
                    db["questions"][i]["answer"] = answer
                    break
        await _save(db)

    if user_id:
        try:
            from bot import bot
            await bot.send_message(
                user_id,
                f"✉️ <b>Повідомлення від тренера:</b>\n\n{answer}",
            )
        except Exception:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Вхідні", callback_data="t_inbox")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])
    await message.answer("✅ <b>Відповідь надіслана!</b>", reply_markup=kb)
# ── Тренер — статистика ───────────────────────────

@router.callback_query(F.data == "t_stats")
async def trainer_stats(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    from datetime import datetime, timedelta
    clients = await get_clients()
    total    = len(clients)
    premium  = sum(1 for c in clients if c["subscription"] == "premium")
    standard = sum(1 for c in clients if c["subscription"] == "standard")
    free     = sum(1 for c in clients if c["subscription"] == "free")

    # Нові за тиждень і місяць
    db = await _load()
    all_users = await get_all_users()
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    new_week = 0
    new_month = 0
    for uid, data in all_users.items():
        try:
            int(uid)
        except ValueError:
            continue
        if not isinstance(data, dict) or not data.get("registered"):
            continue
        trial = data.get("trial_end")
        if trial:
            try:
                reg_date = datetime.strptime(trial, "%Y-%m-%d") - timedelta(days=7)
                if reg_date >= week_ago:
                    new_week += 1
                if reg_date >= month_ago:
                    new_month += 1
            except ValueError:
                pass

    # Популярні рівні
    levels = {"beginner": 0, "intermediate": 0, "advanced": 0, "athlete": 0}
    locations = {"gym": 0, "outdoor": 0, "home": 0}
    for uid, data in all_users.items():
        try:
            int(uid)
        except ValueError:
            continue
        if not isinstance(data, dict) or not data.get("registered"):
            continue
        lvl = data.get("level", "")
        if lvl in levels:
            levels[lvl] += 1
        loc = data.get("location", "")
        if loc in locations:
            locations[loc] += 1

    top_level = max(levels, key=levels.get) if any(levels.values()) else "—"
    top_location = max(locations, key=locations.get) if any(locations.values()) else "—"

    level_labels = {"beginner": "🟢 Початківець", "intermediate": "🟡 Середній",
                    "advanced": "🔴 Просунутий", "athlete": "🔥 Атлет"}
    location_labels = {"gym": "🏋️ Зал", "outdoor": "🌳 Вулиця", "home": "🏠 Вдома"}

    unanswered = sum(1 for q in db.get("questions", []) if not q["answered"])

    level_counts = (
        f"🟢 Початківець: {levels['beginner']}\n"
        f"🟡 Середній: {levels['intermediate']}\n"
        f"🔴 Просунутий: {levels['advanced']}\n"
        f"🔥 Атлет: {levels['athlete']}"
    )

    location_counts = (
        f"🏋️ Зал: {locations['gym']}\n"
        f"🌳 Вулиця: {locations['outdoor']}\n"
        f"🏠 Вдома: {locations['home']}"
    )

    # Клієнти з простроченою підпискою
    expired = []
    for c in clients:
        sub_end = c.get("subscription_end")
        if sub_end:
            try:
                end_date = datetime.strptime(sub_end, "%Y-%m-%d")
                if end_date < today and c["subscription"] != "free":
                    expired.append(c.get("name", "—"))
            except ValueError:
                pass

    expired_text = "\n".join(f"• {n}" for n in expired[:5]) if expired else "немає"
    if len(expired) > 5:
        expired_text += f"\n...і ще {len(expired) - 5}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 Розсилка", callback_data="t_broadcast")],
        [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всього клієнтів: <b>{total}</b>\n"
        f"👑 Преміум: <b>{premium}</b>\n"
        f"⭐️ Стандарт: <b>{standard}</b>\n"
        f"🆓 Безкоштовних: <b>{free}</b>\n\n"
        f"📅 Нових за тиждень: <b>{new_week}</b>\n"
        f"📅 Нових за місяць: <b>{new_month}</b>\n\n"
        f"📊 <b>Рівні підготовки:</b>\n{level_counts}\n\n"
        f"📍 <b>Локації:</b>\n{location_counts}\n\n"
        f"⚠️ <b>Прострочена підписка ({len(expired)}):</b>\n{expired_text}\n\n"
        f"📬 Без відповіді: <b>{unanswered}</b>",
        reply_markup=kb,
    )


@router.callback_query(F.data == "t_broadcast")
async def trainer_broadcast_prompt(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всім клієнтам", callback_data="t_broadcast_all")],
        [InlineKeyboardButton(text="👑 Тільки Преміум", callback_data="t_broadcast_premium")],
        [InlineKeyboardButton(text="⭐️ Тільки Стандарт", callback_data="t_broadcast_standard")],
        [InlineKeyboardButton(text="🆓 Тільки Безкоштовним", callback_data="t_broadcast_free")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_stats")],
    ])
    await callback.message.edit_text(
        "📣 <b>Розсилка</b>\n\nОбери кому надіслати:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("t_broadcast_"))
async def trainer_broadcast_select(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    target = callback.data.replace("t_broadcast_", "")
    await state.update_data(broadcast_target=target)
    await state.set_state(TrainerStates.typing_broadcast)

    target_labels = {
        "all": "всім клієнтам",
        "premium": "тільки Преміум",
        "standard": "тільки Стандарт",
        "free": "тільки Безкоштовним",
    }
    await callback.message.edit_text(
        f"📣 <b>Розсилка — {target_labels.get(target)}</b>\n\nВведи повідомлення:",
    )


@router.message(TrainerStates.typing_broadcast)
async def trainer_broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    data = await state.get_data()
    target = data.get("broadcast_target", "all")
    clients = await get_clients()
    text = message.text.strip()
    await state.clear()

    # Фільтруємо по підписці
    if target == "all":
        filtered = clients
    else:
        filtered = [c for c in clients if c["subscription"] == target]

    sent = 0
    try:
        from bot import bot
        for c in filtered:
            try:
                await bot.send_message(c["id"], f"📣 <b>Від тренера:</b>\n\n{text}")
                sent += 1
            except Exception:
                pass
    except Exception:
        pass

    target_labels = {
        "all": "всім",
        "premium": "Преміум",
        "standard": "Стандарт",
        "free": "Безкоштовним",
    }
    await message.answer(
        f"✅ Розсилку надіслано {target_labels.get(target)}!\n"
        f"Отримали: {sent} з {len(filtered)} клієнтів.",
        reply_markup=trainer_menu_kb(),
    )


@router.callback_query(F.data == "t_subscriptions")
async def trainer_subscriptions(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    clients = await get_clients()
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    buttons = []
    for c in clients:
        icon = sub_icon.get(c["subscription"], "🆓")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {c['name']}",
            callback_data=f"t_sub_{c['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        "💳 <b>Підписки</b>\n\nОбери клієнта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("t_sub_") & ~F.data.startswith("t_setsub_"))
async def trainer_change_sub(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_sub_", ""))
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    current = user.get("subscription", "free")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Безкоштовний", callback_data=f"t_setsub_free_{user_id}")],
        [InlineKeyboardButton(text="⭐ Стандарт",     callback_data=f"t_setsub_standard_{user_id}")],
        [InlineKeyboardButton(text="👑 Преміум",      callback_data=f"t_setsub_premium_{user_id}")],
        [InlineKeyboardButton(text="← Назад",         callback_data="t_subscriptions")],
    ])
    await callback.message.edit_text(
        f"💳 <b>{user.get('name')}</b>\n\n"
        f"Поточна: {sub_icon.get(current, '🆓')}\n\n"
        f"Обери нову підписку:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("t_setsub_"))
async def trainer_set_sub(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    parts = callback.data.replace("t_setsub_", "").split("_")
    sub = parts[0]
    user_id = int(parts[1])
    db = await _load()
    if str(user_id) in db:
        db[str(user_id)]["subscription"] = sub
        await _save(db)
    user = await get_user(user_id)
    name = user.get("name", "Невідомий") if user else "Невідомий"
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="t_subscriptions")],
    ])
    await callback.message.edit_text(
        f"✅ <b>Підписку змінено!</b>\n\n{name}: {sub_icon.get(sub, '🆓')}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "t_create_workout2")
async def trainer_create_workout(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    clients = await get_clients()
    if not clients:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            "✍️ <b>Скласти тренування</b>\n\nЩе немає клієнтів.",
            reply_markup=kb,
        )
        return
    sub_icon = {"premium": "👑", "standard": "⭐", "free": "🆓"}
    buttons = []
    for c in clients:
        icon = sub_icon.get(c["subscription"], "🆓")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {c['name']}",
            callback_data=f"t_send_program_{c['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        "✍️ <b>Скласти тренування</b>\n\nОбери клієнта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "t_settings")
async def trainer_settings(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    db = await _load()
    requisites = db.get("requisites", "Не вказано")
    prices = db.get("prices", {"standard": "200 грн", "premium": "450 грн"})
    channel = db.get("channel_link", "Не вказано")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Змінити реквізити", callback_data="t_set_requisites")],
        [InlineKeyboardButton(text="💰 Ціни підписок",     callback_data="t_set_prices")],
        [InlineKeyboardButton(text="📢 Змінити канал",     callback_data="t_set_channel")],
        [InlineKeyboardButton(text="← Назад",              callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        f"⚙️ <b>Налаштування</b>\n\n"
        f"⭐️ Стандарт: {prices.get('standard', '200 грн')}\n"
        f"👑 Преміум: {prices.get('premium', '450 грн')}\n\n"
        f"💳 <b>Реквізити:</b>\n{requisites}\n\n"
        f"📢 <b>Канал:</b> {channel}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "t_set_requisites")
async def trainer_set_requisites(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    await state.set_state(SettingsStates.typing_requisites)
    await callback.message.edit_text(
        "💳 Введи нові реквізити:\nНаприклад: Monobank: 4441 1111 2222 3333",
    )


@router.message(SettingsStates.typing_requisites)
async def save_requisites(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    db = await _load()
    db["requisites"] = message.text.strip()
    await _save(db)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="t_settings")],
    ])
    await message.answer("✅ <b>Реквізити оновлено!</b>", reply_markup=kb)


@router.callback_query(F.data == "t_set_prices")
async def trainer_set_prices(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    db = await _load()
    prices = db.get("prices", {"standard": "200 грн", "premium": "450 грн"})
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Стандарт: {prices['standard']}", callback_data="t_price_standard")],
        [InlineKeyboardButton(text=f"👑 Преміум: {prices['premium']}",   callback_data="t_price_premium")],
        [InlineKeyboardButton(text="← Назад", callback_data="t_settings")],
    ])
    await callback.message.edit_text(
        "💰 <b>Ціни підписок</b>",
        reply_markup=kb,
    )


@router.callback_query(F.data == "t_price_standard")
async def set_price_standard(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    await state.set_state(PriceStates.typing_standard)
    await callback.message.edit_text("⭐ Введи нову ціну для Стандарт:")


@router.callback_query(F.data == "t_price_premium")
async def set_price_premium(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    await state.set_state(PriceStates.typing_premium)
    await callback.message.edit_text("👑 Введи нову ціну для Преміум:")


@router.message(PriceStates.typing_standard)
async def save_price_standard(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    db = await _load()
    if "prices" not in db:
        db["prices"] = {}
    db["prices"]["standard"] = message.text.strip()
    await _save(db)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="t_set_prices")],
    ])
    await message.answer(f"✅ Ціна Стандарт: <b>{message.text.strip()}</b>", reply_markup=kb)


@router.message(PriceStates.typing_premium)
async def save_price_premium(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    db = await _load()
    if "prices" not in db:
        db["prices"] = {}
    db["prices"]["premium"] = message.text.strip()
    await _save(db)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="t_set_prices")],
    ])
    await message.answer(f"✅ Ціна Преміум: <b>{message.text.strip()}</b>", reply_markup=kb)


@router.callback_query(F.data == "my_subscription")
async def subscription_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    current = user.get("subscription", "free") if user else "free"
    db = await _load()
    prices = db.get("prices", {"standard": "200 грн", "premium": "450 грн"})
    requisites = db.get("requisites", "Реквізити не вказані")
    sub_icon = {"free": "🆓", "standard": "⭐", "premium": "👑"}
    icon = sub_icon.get(current, "🆓")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Купити Стандарт", callback_data="buy_standard")],
        [InlineKeyboardButton(text="👑 Купити Преміум",  callback_data="buy_premium")],
        [InlineKeyboardButton(text="← Назад",           callback_data="menu_profile")],
    ])
    await callback.message.edit_text(
        f"💳 <b>Підписка</b>\n\n"
        f"Поточна: {icon} <b>{current}</b>\n\n"
        f"⭐ Стандарт — {prices.get('standard', '200 грн')}/міс\n"
        f"   Конструктор тренувань\n"
        f"   Статистика і прогрес\n\n"
        f"👑 Преміум — {prices.get('premium', '450 грн')}/міс\n"
        f"   Все зі Стандарту\n"
        f"   Персональна програма від тренера\n\n"
        f"💳 <b>Реквізити:</b>\n{requisites}",
        reply_markup=kb,
    )


@router.callback_query(F.data == "buy_standard")
async def buy_standard(callback: CallbackQuery):
    db = await _load()
    prices = db.get("prices", {"standard": "200 грн"})
    requisites = db.get("requisites", "Реквізити не вказані")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Надіслати скріншот", callback_data="send_payment_standard")],
        [InlineKeyboardButton(text="← Назад", callback_data="my_subscription")],
    ])
    await callback.message.edit_text(
        f"⭐ <b>Стандарт — {prices.get('standard', '200 грн')}/міс</b>\n\n"
        f"1. Оплати на реквізити:\n{requisites}\n\n"
        f"2. Натисни кнопку і надішли скріншот\n"
        f"3. Тренер підтвердить і підписка активується",
        reply_markup=kb,
    )


@router.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery):
    db = await _load()
    prices = db.get("prices", {"premium": "450 грн"})
    requisites = db.get("requisites", "Реквізити не вказані")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Надіслати скріншот", callback_data="send_payment_premium")],
        [InlineKeyboardButton(text="← Назад", callback_data="my_subscription")],
    ])
    await callback.message.edit_text(
        f"👑 <b>Преміум — {prices.get('premium', '450 грн')}/міс</b>\n\n"
        f"1. Оплати на реквізити:\n{requisites}\n\n"
        f"2. Натисни кнопку і надішли скріншот\n"
        f"3. Тренер підтвердить і підписка активується",
        reply_markup=kb,
    )

    @router.callback_query(F.data == "send_payment_standard")
    async def send_payment_standard(callback: CallbackQuery, state: FSMContext):
        await state.update_data(payment_type="standard")
        await state.set_state(PaymentStates.waiting_screenshot_standard)
        await callback.message.edit_text("📸 Надішли скріншот оплати:")

    @router.callback_query(F.data == "send_payment_premium")
    async def send_payment_premium(callback: CallbackQuery, state: FSMContext):
        await state.update_data(payment_type="premium")
        await state.set_state(PaymentStates.waiting_screenshot_premium)
        await callback.message.edit_text("📸 Надішли скріншот оплати:")

    @router.message(PaymentStates.waiting_screenshot_standard)
    @router.message(PaymentStates.waiting_screenshot_premium)
    async def receive_payment_screenshot(message: Message, state: FSMContext):
        data = await state.get_data()
        payment_type = data.get("payment_type", "standard")
        user_id = message.from_user.id
        user = await get_user(user_id)
        name = user.get("name", "Невідомий") if user else "Невідомий"
        await state.clear()

        try:
            from bot import bot
            sub_text = "⭐️ Стандарт" if payment_type == "standard" else "👑 Преміум"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Підтвердити Стандарт",
                                         callback_data=f"confirm_payment_standard_{user_id}"),
                ],
                [
                    InlineKeyboardButton(text="✅ Підтвердити Преміум",
                                         callback_data=f"confirm_payment_premium_{user_id}"),
                ],
                [
                    InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_payment_{user_id}"),
                ],
            ])

            await bot.send_message(
                TRAINER_ID,
                f"💳 <b>Нова оплата!</b>\n\n"
                f"Від: <b>{name}</b>\n"
                f"ID: <code>{user_id}</code>\n"
                f"Тип: {sub_text}\n\n"
                f"Підтвердь або відхили:",
                reply_markup=kb,
            )
            if message.photo:
                await bot.send_photo(TRAINER_ID, message.photo[-1].file_id)
            elif message.document:
                await bot.send_document(TRAINER_ID, message.document.file_id)
        except Exception:
            pass

        kb_client = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ])
        await message.answer(
            "✅ <b>Скріншот надіслано!</b>\n\n"
            "Тренер перевірить і активує підписку.",
            reply_markup=kb_client,
        )

    @router.callback_query(F.data.startswith("confirm_payment_"))
    async def confirm_payment(callback: CallbackQuery):
        if callback.from_user.id != TRAINER_ID:
            return
        parts = callback.data.split("_")
        sub_type = parts[2]
        user_id = int(parts[3])

        from datetime import datetime, timedelta
        sub_end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        await update_user_field(user_id, "subscription", sub_type)
        await update_user_field(user_id, "subscription_end", sub_end)
        await update_user_field(user_id, "trial_end", None)

        sub_text = "⭐️ Стандарт" if sub_type == "standard" else "👑 Преміум"

        try:
            from bot import bot
            await bot.send_message(
                user_id,
                f"🎉 <b>Підписку активовано!</b>\n\n"
                f"Тариф: {sub_text}\n"
                f"Діє до: {sub_end}\n\n"
                f"Дякуємо за оплату! 💪"
            )
        except Exception:
            pass

        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ <b>Підтверджено: {sub_text}</b>"
        )
        await callback.answer("✅ Підписку активовано!")

    @router.callback_query(F.data.startswith("reject_payment_"))
    async def reject_payment(callback: CallbackQuery):
        if callback.from_user.id != TRAINER_ID:
            return
        user_id = int(callback.data.split("_")[2])

        try:
            from bot import bot
            await bot.send_message(
                user_id,
                "❌ <b>Оплату не підтверджено.</b>\n\n"
                "Зв'яжись з тренером для уточнення."
            )
        except Exception:
            pass

        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>Відхилено</b>"
        )
        await callback.answer("❌ Відхилено")


@router.callback_query(F.data.startswith("t_client_results_"))
async def trainer_client_results(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_client_results_", ""))
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    results = user.get("results", {})
    if not results:
        await callback.answer("Немає результатів тренувань.", show_alert=True)
        return
    text = f"📊 <b>Результати — {user.get('name')}</b>\n\n"
    for exercise, sets in list(results.items())[:10]:
        text += f"💪 <b>{exercise}</b>\n"
        last_sets = sets[-3:] if len(sets) >= 3 else sets
        for s in last_sets:
            text += f"  {s.get('date', '—')}: {s.get('weight', 0)}кг × {s.get('reps', 0)}\n"
        text += "\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data=f"t_client_{user_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("t_client_records_"))
async def trainer_client_records(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_client_records_", ""))
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    results = user.get("results", {})
    if not results:
        await callback.answer("Немає рекордів.", show_alert=True)
        return
    text = f"🏆 <b>Рекорди — {user.get('name')}</b>\n\n"
    for exercise, sets in results.items():
        if sets:
            best = max(sets, key=lambda s: s.get("weight", 0))
            text += f"💪 {exercise}: <b>{best.get('weight', 0)}кг × {best.get('reps', 0)}</b>\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data=f"t_client_{user_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("t_sub_"))
async def trainer_client_sub(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_sub_", ""))
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Безкоштовний", callback_data=f"t_set_sub_free_{user_id}")],
        [InlineKeyboardButton(text="⭐️ Стандарт 30 днів", callback_data=f"t_set_sub_standard_{user_id}")],
        [InlineKeyboardButton(text="👑 Преміум 30 днів", callback_data=f"t_set_sub_premium_{user_id}")],
        [InlineKeyboardButton(text="➕ +7 днів", callback_data=f"t_add_days_7_{user_id}")],
        [InlineKeyboardButton(text="➕ +14 днів", callback_data=f"t_add_days_14_{user_id}")],
        [InlineKeyboardButton(text="➕ +30 днів", callback_data=f"t_add_days_30_{user_id}")],
        [InlineKeyboardButton(text="← Назад", callback_data=f"t_client_{user_id}")],
    ])
    sub = user.get("subscription", "free")
    sub_end = user.get("subscription_end") or user.get("trial_end") or "—"
    await callback.message.edit_text(
        f"💳 <b>Підписка — {user.get('name')}</b>\n\n"
        f"Поточний тариф: {sub}\n"
        f"Діє до: {sub_end}\n\n"
        f"Обери дію:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("t_set_sub_"))
async def trainer_set_sub(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    from datetime import datetime, timedelta
    parts = callback.data.replace("t_set_sub_", "").split("_")
    sub_type = parts[0]
    user_id = int(parts[1])
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    await update_user_field(user_id, "subscription", sub_type)
    await update_user_field(user_id, "trial_end", None)
    if sub_type in ("standard", "premium"):
        sub_end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        await update_user_field(user_id, "subscription_end", sub_end)
    else:
        await update_user_field(user_id, "subscription_end", None)
    try:
        from bot import bot
        sub_labels = {"free": "🆓 Безкоштовний", "standard": "⭐️ Стандарт", "premium": "👑 Преміум"}
        await bot.send_message(user_id, f"💳 Тренер змінив твою підписку на {sub_labels.get(sub_type)}!")
    except Exception:
        pass
    await callback.answer(f"✅ Підписку змінено на {sub_type}!")
    await trainer_client_sub(callback)


@router.callback_query(F.data.startswith("t_add_days_"))
async def trainer_add_days(callback: CallbackQuery):
    if callback.from_user.id != TRAINER_ID:
        return
    from datetime import datetime, timedelta
    parts = callback.data.replace("t_add_days_", "").split("_")
    days = int(parts[0])
    user_id = int(parts[1])
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    sub_end = user.get("subscription_end") or user.get("trial_end")
    today = datetime.now()
    if sub_end:
        try:
            current = datetime.strptime(sub_end, "%Y-%m-%d")
            if current < today:
                current = today
        except ValueError:
            current = today
    else:
        current = today
    new_end = (current + timedelta(days=days)).strftime("%Y-%m-%d")
    await update_user_field(user_id, "subscription_end", new_end)
    await update_user_field(user_id, "trial_end", None)
    try:
        from bot import bot
        await bot.send_message(user_id, f"🎁 Тренер додав тобі {days} днів підписки!\nДіє до: {new_end}")
    except Exception:
        pass
    await callback.answer(f"✅ Додано {days} днів!")
    await trainer_client_sub(callback)


@router.callback_query(F.data.startswith("t_message_"))
async def trainer_message_client(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    user_id = int(callback.data.replace("t_message_", ""))
    user = await get_user(user_id)
    if not user:
        await callback.answer("Клієнта не знайдено.", show_alert=True)
        return
    await state.update_data(message_to_user_id=user_id)
    await state.set_state(TrainerStates.typing_answer)
    await callback.message.edit_text(
        f"✉️ <b>Написати {user.get('name')}</b>\n\nВведи повідомлення:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data=f"t_client_{user_id}")],
        ])
    )

    @router.message(TrainerStates.typing_answer)
    async def trainer_send_message_client(message: Message, state: FSMContext):
        if message.from_user.id != TRAINER_ID:
            return
        data = await state.get_data()
        user_id = data.get("message_to_user_id")
        await state.clear()

        if user_id:
            try:
                from bot import bot
                await bot.send_message(
                    user_id,
                    f"✉️ <b>Повідомлення від тренера:</b>\n\n{message.text}",
                    parse_mode="HTML"
                )
                await message.answer(
                    "✅ Повідомлення надіслано!",
                    reply_markup=trainer_menu_kb()
                )
            except Exception:
                await message.answer("❌ Не вдалось надіслати.", reply_markup=trainer_menu_kb())
        else:
            await message.answer("❌ Клієнта не знайдено.", reply_markup=trainer_menu_kb())



@router.callback_query(F.data == "t_set_channel")
async def trainer_set_channel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != TRAINER_ID:
        return
    await state.set_state(SettingsStates.typing_channel)
    await callback.message.edit_text(
        "📢 Введи посилання на канал:\nНаприклад: https://t.me/gymnote_news",
    )

@router.message(SettingsStates.typing_channel)
async def trainer_save_channel(message: Message, state: FSMContext):
    if message.from_user.id != TRAINER_ID:
        return
    db = await _load()
    db["channel_link"] = message.text.strip()
    await _save(db)
    await state.clear()
    await message.answer("✅ Посилання на канал збережено!")