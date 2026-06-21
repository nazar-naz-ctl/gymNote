from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


def back_and_menu(back: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Зберегти день в конструктор", callback_data="import_program")],
        [InlineKeyboardButton(text="← Назад", callback_data=back)],
        [InlineKeyboardButton(text="🏠 Меню",  callback_data="main_menu")],
    ])


def variants_kb(prefix: str, back: str, is_premium: bool = False) -> InlineKeyboardMarkup:
    if is_premium:
        buttons = [
            [InlineKeyboardButton(text="📋 Варіант 1", callback_data=f"{prefix}_v1")],
            [InlineKeyboardButton(text="📋 Варіант 2", callback_data=f"{prefix}_v2")],
            [InlineKeyboardButton(text="📋 Варіант 3", callback_data=f"{prefix}_v3")],
            [InlineKeyboardButton(text="← Назад", callback_data=back)],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📋 Варіант 1", callback_data=f"{prefix}_v1")],
            [InlineKeyboardButton(text="🔒 Варіант 2 — Преміум", callback_data="upgrade_premium")],
            [InlineKeyboardButton(text="🔒 Варіант 3 — Преміум", callback_data="upgrade_premium")],
            [InlineKeyboardButton(text="← Назад", callback_data=back)],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "programs")
async def programs_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал",  callback_data="prog_gym")],
        [InlineKeyboardButton(text="🌳 Вулична площадка", callback_data="prog_outdoor")],
        [InlineKeyboardButton(text="🏠 Вдома",            callback_data="prog_home")],
        [InlineKeyboardButton(text="← Назад",             callback_data="menu_workout")],
    ])
    await callback.message.edit_text(
        "📋 <b>Програми тренувань</b>\n\nОбери місце:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "prog_gym")
async def prog_gym(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Спліт",            callback_data="gym_split")],
        [InlineKeyboardButton(text="🔄 Фулбоді",          callback_data="gym_fullbody")],
        [InlineKeyboardButton(text="😮 Розвантажувальне", callback_data="gym_deload")],
        [InlineKeyboardButton(text="← Назад",             callback_data="programs")],
    ])
    await callback.message.edit_text(
        "🏋️ <b>Тренажерний зал</b>\n\nОбери тип:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "prog_outdoor")
async def prog_outdoor(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Спліт",            callback_data="outdoor_split")],
        [InlineKeyboardButton(text="🔄 Фулбоді",          callback_data="outdoor_fullbody")],
        [InlineKeyboardButton(text="😮 Розвантажувальне", callback_data="outdoor_deload")],
        [InlineKeyboardButton(text="← Назад",             callback_data="programs")],
    ])
    await callback.message.edit_text(
        "🌳 <b>Вулична площадка</b>\n\nОбери тип:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "prog_home")
async def prog_home(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ З гантелями",   callback_data="home_dumbbells")],
        [InlineKeyboardButton(text="🎽 З гумками",      callback_data="home_bands")],
        [InlineKeyboardButton(text="❌ Без обладнання", callback_data="home_bodyweight")],
        [InlineKeyboardButton(text="← Назад",           callback_data="programs")],
    ])
    await callback.message.edit_text(
        "🏠 <b>Вдома</b>\n\nЯке обладнання є?",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gym_split_beginner")
async def gym_split_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Спліт — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_split_beg", "gym_split", is_premium),
    )


@router.callback_query(F.data == "gym_split")
async def gym_split(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="gym_split_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="gym_split_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="gym_split_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="gym_split_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_gym")],
    ])
    await callback.message.edit_text(
        "💪 <b>Спліт — Зал</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gym_split_intermediate")
async def gym_split_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Спліт — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_split_int", "gym_split", is_premium),
    )


@router.callback_query(F.data == "gym_split_advanced")
async def gym_split_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Спліт — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_split_adv", "gym_split", is_premium),
    )


@router.callback_query(F.data == "gym_split_athlete")
async def gym_split_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Спліт — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_split_ath", "gym_split", is_premium),
    )


@router.callback_query(F.data == "gym_split_beg_v1")
async def gym_split_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим штанги лежачи — 3×10\n"
        "• Жим гантелей під кутом 30° — 3×12\n"
        "• Зведення в кросовері — 3×15\n"
        "• Французький жим — 3×12\n"
        "• Розгинання на блоці — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Тяга штанги в нахилі — 3×10\n"
        "• Підтягування або тяга верхнього блоку — 3×10\n"
        "• Горизонтальна тяга — 3×12\n"
        "• Підйом штанги на біцепс — 3×12\n"
        "• Молоткові підйоми — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги + Плечі</b>\n"
        "• Присідання зі штангою — 3×10\n"
        "• Жим ногами — 3×12\n"
        "• Розгинання ніг — 3×15\n"
        "• Армійський жим — 3×10\n"
        "• Підйом гантелей в сторони — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок між підходами 60-90 сек.\n"
        "Вага: комфортна, техніка важливіша за вагу.\n"
        "Прогресія: +2.5 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_beginner"))


@router.callback_query(F.data == "gym_split_beg_v2")
async def gym_split_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Поштовхові м'язи</b>\n"
        "• Жим штанги лежачи — 3×10\n"
        "• Жим гантелей сидячи — 3×12\n"
        "• Віджимання на брусах — 3×10\n"
        "• Підйом гантелей перед собою — 3×12\n"
        "• Розгинання з гантеллю з-за голови — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тягові м'язи</b>\n"
        "• Станова тяга — 3×8\n"
        "• Тяга гантелі однією рукою — 3×12\n"
        "• Тяга нижнього блоку — 3×12\n"
        "• Підйом гантелей на біцепс сидячи — 3×12\n"
        "• Підйом штанги зворотним хватом — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги + Прес</b>\n"
        "• Присідання — 3×12\n"
        "• Випади з гантелями — 3×12\n"
        "• Румунська тяга — 3×12\n"
        "• Підйом литок стоячи — 4×20\n"
        "• Скручування — 3×20\n"
        "• Планка — 3×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Фокус на техніці виконання.\n"
        "Прогресія: +2.5 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_beginner"))


@router.callback_query(F.data == "gym_split_beg_v3")
async def gym_split_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Верх тіла A</b>\n"
        "• Жим штанги лежачи — 3×10\n"
        "• Тяга штанги в нахилі — 3×10\n"
        "• Жим гантелей сидячи — 3×12\n"
        "• Підйом штанги на біцепс — 3×12\n"
        "• Французький жим — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Низ тіла</b>\n"
        "• Присідання зі штангою — 4×10\n"
        "• Жим ногами — 3×12\n"
        "• Румунська тяга — 3×12\n"
        "• Згинання ніг лежачи — 3×15\n"
        "• Підйом литок — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Верх тіла Б</b>\n"
        "• Жим штанги під кутом — 3×10\n"
        "• Підтягування вузьким хватом — 3×8\n"
        "• Розведення гантелей лежачи — 3×12\n"
        "• Підйом гантелей в сторони — 3×15\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Чергуй тижні А-Б для різноманіття.\n"
        "Прогресія: +2.5 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_beginner"))


@router.callback_query(F.data == "gym_split_int_v1")
async def gym_split_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Середній — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим штанги лежачи — 4×8\n"
        "• Жим гантелей під кутом 30° — 4×10\n"
        "• Жим гантелей під кутом 45° — 3×12\n"
        "• Зведення в кросовері — 3×15\n"
        "• Французький жим — 4×10\n"
        "• Розгинання на блоці — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Станова тяга — 4×6\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Тяга верхнього блоку — 3×10\n"
        "• Горизонтальна тяга — 3×12\n"
        "• Підйом штанги на біцепс — 4×10\n"
        "• Концентровані підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання зі штангою — 4×8\n"
        "• Жим ногами — 4×10\n"
        "• Випади з гантелями — 3×12\n"
        "• Румунська тяга — 4×10\n"
        "• Згинання ніг лежачи — 3×12\n"
        "• Підйом литок стоячи — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Армійський жим — 4×8\n"
        "• Тяга штанги до підборіддя — 3×10\n"
        "• Підйом гантелей в сторони — 4×15\n"
        "• Підйом гантелей перед собою — 3×12\n"
        "• Скручування — 4×20\n"
        "• Підйом ніг у висі — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +2.5 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_intermediate"))


@router.callback_query(F.data == "gym_split_int_v2")
async def gym_split_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Поштовхові м'язи</b>\n"
        "• Жим штанги лежачи — 4×8\n"
        "• Армійський жим стоячи — 4×8\n"
        "• Жим гантелей під кутом — 3×10\n"
        "• Підйом гантелей в сторони — 4×15\n"
        "• Французький жим — 3×10\n"
        "• Розгинання на блоці — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тягові м'язи</b>\n"
        "• Підтягування — 4×8\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Тяга гантелі однією рукою — 3×10\n"
        "• Тяга нижнього блоку — 3×12\n"
        "• Підйом штанги на біцепс — 4×10\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Квадрицепс + Литки</b>\n"
        "• Присідання зі штангою — 5×6\n"
        "• Жим ногами — 4×10\n"
        "• Розгинання ніг — 3×15\n"
        "• Випади зворотні — 3×12\n"
        "• Підйом литок стоячи — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Задня поверхня + Прес</b>\n"
        "• Румунська тяга — 4×10\n"
        "• Згинання ніг лежачи — 4×12\n"
        "• Гіперекстензія — 3×15\n"
        "• Планка — 4×60 сек\n"
        "• Скручування з вагою — 3×20\n"
        "• Підйом ніг у висі — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +2.5 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_intermediate"))


@router.callback_query(F.data == "gym_split_int_v3")
async def gym_split_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Середній — Варіант 3</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Біцепс</b>\n"
        "• Жим штанги лежачи — 4×8\n"
        "• Похилий жим гантелей — 3×10\n"
        "• Зведення гантелей лежачи — 3×12\n"
        "• Віджимання на брусах — 3×12\n"
        "• Підйом штанги на біцепс — 4×10\n"
        "• Підйом гантелей почергово — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Трицепс</b>\n"
        "• Підтягування широким хватом — 4×8\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Тяга верхнього блоку — 3×10\n"
        "• Тяга нижнього блоку — 3×12\n"
        "• Французький жим — 4×10\n"
        "• Віджимання від лавки — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги повністю</b>\n"
        "• Присідання — 4×8\n"
        "• Жим ногами — 4×10\n"
        "• Румунська тяга — 3×10\n"
        "• Випади з гантелями — 3×12\n"
        "• Згинання ніг — 3×12\n"
        "• Підйом литок — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Армійський жим — 4×8\n"
        "• Підйом гантелей в сторони — 4×15\n"
        "• Тяга до підборіддя — 3×12\n"
        "• Підйом гантелей перед собою — 3×12\n"
        "• Скручування — 4×20\n"
        "• Підйом ніг у висі — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +2.5 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_intermediate"))


@router.callback_query(F.data == "gym_split_adv_v1")
async def gym_split_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Просунутий — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди</b>\n"
        "• Жим штанги лежачи — 5×5\n"
        "• Похилий жим гантелей — 4×8\n"
        "• Жим гантелей горизонт — 4×10\n"
        "• Зведення в кросовері (верх) — 3×12\n"
        "• Зведення в кросовері (низ) — 3×12\n"
        "• Віджимання на брусах з вагою — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина</b>\n"
        "• Станова тяга — 5×5\n"
        "• Підтягування з вагою — 4×6\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Тяга верхнього блоку — 3×10\n"
        "• Горизонтальна тяга — 3×12\n"
        "• Шраги зі штангою — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання зі штангою — 5×5\n"
        "• Жим ногами — 4×10\n"
        "• Гакприсідання — 3×12\n"
        "• Румунська тяга — 4×8\n"
        "• Згинання ніг лежачи — 4×12\n"
        "• Підйом литок стоячи — 6×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі</b>\n"
        "• Армійський жим стоячи — 5×5\n"
        "• Жим гантелей сидячи — 4×8\n"
        "• Підйом гантелей в сторони — 5×15\n"
        "• Тяга до підборіддя — 4×10\n"
        "• Підйом гантелей перед собою — 3×12\n"
        "• Зворотні розведення — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки</b>\n"
        "• Підйом штанги на біцепс — 4×8\n"
        "• Молоткові підйоми — 4×10\n"
        "• Підйом гантелей на біцепс сидячи — 3×12\n"
        "• Французький жим — 4×8\n"
        "• Розгинання на блоці — 4×10\n"
        "• Віджимання від лавки з вагою — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Прогресія: +2.5 кг щотижня.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_advanced"))


@router.callback_query(F.data == "gym_split_adv_v2")
async def gym_split_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Просунутий — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим штанги лежачи — 5×5\n"
        "• Похилий жим — 4×8\n"
        "• Зведення гантелей — 4×12\n"
        "• Французький жим — 4×8\n"
        "• Розгинання на блоці — 4×12\n"
        "• Суперсет: віджимання + розгинання — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Підтягування з вагою — 4×6\n"
        "• Станова тяга — 4×6\n"
        "• Тяга в нахилі — 4×8\n"
        "• Тяга нижнього блоку — 3×12\n"
        "• Підйом штанги на біцепс — 4×8\n"
        "• Суперсет: молотки + концентровані — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги передня поверхня</b>\n"
        "• Присідання — 5×5\n"
        "• Жим ногами — 4×10\n"
        "• Розгинання ніг — 4×15\n"
        "• Випади з гантелями — 4×12\n"
        "• Підйом литок — 6×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі повністю</b>\n"
        "• Армійський жим — 5×5\n"
        "• Жим Арнольда — 4×10\n"
        "• Підйом в сторони — 5×15\n"
        "• Тяга до підборіддя — 4×10\n"
        "• Зворотні розведення — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Ноги задня поверхня + Прес</b>\n"
        "• Румунська тяга — 4×8\n"
        "• Згинання ніг — 4×12\n"
        "• Гіперекстензія з вагою — 4×15\n"
        "• Підйом ніг у висі — 4×15\n"
        "• Скручування з вагою — 4×20\n"
        "• Планка з вагою — 3×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети без відпочинку між вправами.\n"
        "Прогресія: +2.5 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_advanced"))


@router.callback_query(F.data == "gym_split_adv_v3")
async def gym_split_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкі груди</b>\n"
        "• Жим штанги лежачи — 6×4\n"
        "• Похилий жим гантелей — 4×8\n"
        "• Зведення в кросовері — 4×12\n"
        "• Суперсет: жим вузьким хватом + відмова — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Важка спина</b>\n"
        "• Станова тяга — 6×4\n"
        "• Підтягування з вагою — 4×6\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Суперсет: тяга блоку + шраги — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Важкі ноги</b>\n"
        "• Присідання — 6×4\n"
        "• Жим ногами — 5×8\n"
        "• Румунська тяга — 4×8\n"
        "• Суперсет: розгинання + згинання — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Важкі плечі</b>\n"
        "• Армійський жим — 6×4\n"
        "• Жим гантелей сидячи — 4×8\n"
        "• Підйом в сторони — 5×15\n"
        "• Суперсет: тяга до підборіддя + розведення — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підйом штанги + французький жим — 5×8\n"
        "• Суперсет: молотки + розгинання на блоці — 4×10\n"
        "• Суперсет: концентровані + відмова — 3×12\n"
        "• Підйом ніг у висі — 4×15\n"
        "• Скручування з вагою — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2-3 хв між важкими підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +2.5 кг щотижня на базових."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_advanced"))


@router.callback_query(F.data == "gym_split_ath_v1")
async def gym_split_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Атлет — Варіант 1</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди (об'єм)</b>\n"
        "• Жим штанги лежачи — 6×4\n"
        "• Похилий жим штанги — 5×6\n"
        "• Похилий жим гантелей — 4×8\n"
        "• Зведення в кросовері (верх) — 4×12\n"
        "• Зведення в кросовері (низ) — 4×12\n"
        "• Суперсет: віджимання на брусах з вагою + відмова — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина (об'єм)</b>\n"
        "• Станова тяга — 6×4\n"
        "• Підтягування з вагою — 5×6\n"
        "• Тяга штанги в нахилі — 4×8\n"
        "• Тяга гантелі однією рукою — 4×10\n"
        "• Тяга верхнього блоку — 4×12\n"
        "• Суперсет: горизонтальна тяга + шраги — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (квадрицепс)</b>\n"
        "• Присідання зі штангою — 6×4\n"
        "• Жим ногами — 5×8\n"
        "• Гакприсідання — 4×10\n"
        "• Розгинання ніг — 4×15\n"
        "• Суперсет: випади + стрибки — 4×12\n"
        "• Підйом литок стоячи — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (об'єм)</b>\n"
        "• Армійський жим стоячи — 6×4\n"
        "• Жим Арнольда — 4×8\n"
        "• Підйом гантелей в сторони — 6×15\n"
        "• Тяга до підборіддя — 4×10\n"
        "• Суперсет: підйом перед собою + зворотні розведення — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Ноги (задня поверхня)</b>\n"
        "• Румунська тяга — 5×6\n"
        "• Згинання ніг лежачи — 5×10\n"
        "• Гіперекстензія з вагою — 4×15\n"
        "• Суперсет: підйом литок сидячи + стоячи — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Руки + Прес</b>\n"
        "• Суперсет: підйом штанги на біцепс + французький жим — 5×8\n"
        "• Суперсет: молотки + розгинання на блоці — 4×10\n"
        "• Суперсет: концентровані + відмова трицепс — 3×12\n"
        "• Підйом ніг у висі — 5×15\n"
        "• Скручування з вагою — 5×20\n"
        "• Планка з вагою — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2-3 хв на базових.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +2.5 кг щотижня на базових.\n"
        "День 7 — повний відпочинок або кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_athlete"))


@router.callback_query(F.data == "gym_split_ath_v2")
async def gym_split_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Атлет — Варіант 2</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Жимовий день (сила)</b>\n"
        "• Жим штанги лежачи — 7×3\n"
        "• Похилий жим штанги — 5×5\n"
        "• Армійський жим — 4×6\n"
        "• Суперсет: французький жим + розгинання — 5×10\n"
        "• Підйом гантелей в сторони — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тяговий день (сила)</b>\n"
        "• Станова тяга — 7×3\n"
        "• Підтягування з вагою — 5×5\n"
        "• Тяга штанги в нахилі — 5×5\n"
        "• Суперсет: підйом штанги на біцепс + молотки — 5×10\n"
        "• Шраги зі штангою — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (сила)</b>\n"
        "• Присідання — 7×3\n"
        "• Жим ногами — 5×6\n"
        "• Румунська тяга — 5×6\n"
        "• Суперсет: розгинання + згинання ніг — 5×12\n"
        "• Підйом литок — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Груди + Плечі (об'єм)</b>\n"
        "• Жим гантелей похилий — 5×10\n"
        "• Зведення в кросовері — 5×15\n"
        "• Жим Арнольда — 5×10\n"
        "• Суперсет: підйом в сторони + зворотні розведення — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Спина (об'єм)</b>\n"
        "• Підтягування різним хватом — 5×10\n"
        "• Тяга гантелі однією рукою — 5×10\n"
        "• Тяга верхнього блоку — 5×12\n"
        "• Суперсет: горизонтальна тяга + пулловер — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Руки + Прес (об'єм)</b>\n"
        "• Суперсет: EZ-підйом + французький жим — 5×10\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Суперсет: концентровані + відмова — 3×15\n"
        "• Підйом ніг у висі — 5×20\n"
        "• Скручування з вагою — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 3-4 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +2.5 кг щотижня на базових.\n"
        "День 7 — відпочинок або легке кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_athlete"))


@router.callback_query(F.data == "gym_split_ath_v3")
async def gym_split_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди (максимальний об'єм)</b>\n"
        "• Жим штанги лежачи — 5×5\n"
        "• Похилий жим штанги — 5×6\n"
        "• Похилий жим гантелей — 4×10\n"
        "• Суперсет: зведення верх + зведення низ — 4×15\n"
        "• Суперсет: брусья з вагою + відмова — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина (максимальний об'єм)</b>\n"
        "• Станова тяга — 5×5\n"
        "• Підтягування з вагою — 5×6\n"
        "• Тяга в нахилі — 5×8\n"
        "• Суперсет: тяга гантелі + тяга блоку — 4×10\n"
        "• Суперсет: пулловер + шраги — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (максимальний об'єм)</b>\n"
        "• Присідання — 5×5\n"
        "• Жим ногами — 5×10\n"
        "• Суперсет: розгинання + згинання — 5×15\n"
        "• Румунська тяга — 4×8\n"
        "• Суперсет: випади + стрибкові присідання — 4×12\n"
        "• Підйом литок — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (максимальний об'єм)</b>\n"
        "• Армійський жим — 5×5\n"
        "• Жим Арнольда — 4×10\n"
        "• Суперсет: підйом в сторони + тяга до підборіддя — 5×12\n"
        "• Суперсет: підйом перед собою + зворотні розведення — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки (максимальний об'єм)</b>\n"
        "• Суперсет: підйом штанги + французький жим — 5×8\n"
        "• Суперсет: похилі підйоми + брусья — 4×10\n"
        "• Суперсет: молотки + розгинання на блоці — 4×12\n"
        "• Суперсет: концентровані + відмова — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом ніг у висі — 5×20\n"
        "• Скручування з вагою — 5×25\n"
        "• Планка з вагою — 4×90 сек\n"
        "• Бокові скручування — 4×20\n"
        "• Кардіо: 20 хв помірний темп\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2-3 хв на базових.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +2.5 кг щотижня.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_split_athlete"))


@router.callback_query(F.data == "gym_fullbody")
async def gym_fullbody(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="gym_full_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="gym_full_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="gym_full_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="gym_full_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_gym")],
    ])
    await callback.message.edit_text(
        "🔄 <b>Фулбоді — Зал</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gym_full_beginner")
async def gym_full_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Фулбоді — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_full_beg", "gym_fullbody", is_premium),
    )


@router.callback_query(F.data == "gym_full_intermediate")
async def gym_full_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Фулбоді — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_full_int", "gym_fullbody", is_premium),
    )


@router.callback_query(F.data == "gym_full_advanced")
async def gym_full_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Фулбоді — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_full_adv", "gym_fullbody", is_premium),
    )


@router.callback_query(F.data == "gym_full_athlete")
async def gym_full_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Фулбоді — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_full_ath", "gym_fullbody", is_premium),
    )


@router.callback_query(F.data == "gym_full_beg_v1")
async def gym_full_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Присідання зі штангою — 3×10\n"
        "• Жим штанги лежачи — 3×10\n"
        "• Тяга штанги в нахилі — 3×10\n"
        "• Армійський жим — 3×10\n"
        "• Підйом штанги на біцепс — 3×12\n"
        "• Французький жим — 3×12\n"
        "• Підйом литок — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Вага легка — фокус на техніці.\n"
        "Прогресія: +2.5 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_beginner"))


@router.callback_query(F.data == "gym_full_beg_v2")
async def gym_full_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Жим ногами — 3×12\n"
        "• Жим гантелей лежачи — 3×12\n"
        "• Тяга верхнього блоку — 3×12\n"
        "• Жим гантелей сидячи — 3×12\n"
        "• Підйом гантелей на біцепс — 3×12\n"
        "• Розгинання на блоці — 3×12\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Ідеально для тих хто боїться штанги.\n"
        "Прогресія: +1-2 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_beginner"))


@router.callback_query(F.data == "gym_full_beg_v3")
async def gym_full_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A і День Б — чергуємо</b>\n\n"
        "<b>День A:</b>\n"
        "• Присідання — 3×10\n"
        "• Жим штанги лежачи — 3×10\n"
        "• Тяга штанги в нахилі — 3×10\n"
        "• Підйом литок — 3×20\n"
        "• Планка — 3×30 сек\n\n"
        "<b>День Б:</b>\n"
        "• Жим ногами — 3×12\n"
        "• Армійський жим — 3×10\n"
        "• Підтягування або тяга блоку — 3×10\n"
        "• Підйом на біцепс — 3×12\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Прогресія: +2.5 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_beginner"))


@router.callback_query(F.data == "gym_full_int_v1")
async def gym_full_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Середній — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Присідання зі штангою — 4×8\n"
        "• Жим штанги лежачи — 4×8\n"
        "• Станова тяга — 4×6\n"
        "• Армійський жим — 4×8\n"
        "• Підтягування — 4×8\n"
        "• Підйом штанги на біцепс — 3×10\n"
        "• Французький жим — 3×10\n"
        "• Підйом литок — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +2.5 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_intermediate"))


@router.callback_query(F.data == "gym_full_int_v2")
async def gym_full_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A — Сила</b>\n"
        "• Присідання — 5×5\n"
        "• Жим лежачи — 5×5\n"
        "• Тяга в нахилі — 5×5\n"
        "• Армійський жим — 4×6\n\n"
        "📌 <b>День Б — Об'єм</b>\n"
        "• Жим ногами — 4×12\n"
        "• Похилий жим гантелей — 4×10\n"
        "• Тяга верхнього блоку — 4×12\n"
        "• Підйом гантелей в сторони — 4×15\n"
        "• Підйом на біцепс — 3×12\n"
        "• Розгинання на блоці — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "День А: відпочинок 2 хв.\n"
        "День Б: відпочинок 90 сек.\n"
        "Прогресія: +2.5 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_intermediate"))


@router.callback_query(F.data == "gym_full_int_v3")
async def gym_full_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Середній — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1</b>\n"
        "• Присідання — 4×8\n"
        "• Жим лежачи — 4×8\n"
        "• Підтягування — 4×8\n"
        "• Суперсет: підйом на біцепс + французький жим — 3×10\n"
        "• Підйом литок — 4×20\n\n"
        "📌 <b>День 2</b>\n"
        "• Станова тяга — 4×6\n"
        "• Армійський жим — 4×8\n"
        "• Тяга в нахилі — 4×8\n"
        "• Суперсет: молотки + розгинання на блоці — 3×12\n"
        "• Скручування — 3×20\n\n"
        "📌 <b>День 3</b>\n"
        "• Жим ногами — 4×10\n"
        "• Похилий жим гантелей — 4×10\n"
        "• Тяга верхнього блоку — 4×10\n"
        "• Суперсет: підйом в сторони + зворотні розведення — 4×15\n"
        "• Підйом ніг у висі — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети без відпочинку.\n"
        "Прогресія: +2.5 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_intermediate"))


@router.callback_query(F.data == "gym_full_adv_v1")
async def gym_full_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Просунутий — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила</b>\n"
        "• Присідання — 5×5\n"
        "• Жим лежачи — 5×5\n"
        "• Станова тяга — 5×5\n"
        "• Армійський жим — 4×6\n"
        "• Підтягування з вагою — 4×6\n\n"
        "📌 <b>День 2 — Об'єм верх</b>\n"
        "• Похилий жим штанги — 4×8\n"
        "• Тяга в нахилі — 4×8\n"
        "• Жим Арнольда — 4×10\n"
        "• Суперсет: підйом на біцепс + французький жим — 4×10\n"
        "• Підйом в сторони — 4×15\n\n"
        "📌 <b>День 3 — Об'єм низ</b>\n"
        "• Жим ногами — 5×10\n"
        "• Румунська тяга — 4×10\n"
        "• Розгинання ніг — 4×15\n"
        "• Згинання ніг — 4×12\n"
        "• Підйом литок — 6×20\n\n"
        "📌 <b>День 4 — Повне тіло</b>\n"
        "• Присідання — 4×8\n"
        "• Жим лежачи — 4×8\n"
        "• Підтягування — 4×8\n"
        "• Суперсет: молотки + розгинання — 3×12\n"
        "• Підйом ніг у висі — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "День сили: відпочинок 2-3 хв.\n"
        "День об'єму: відпочинок 90 сек.\n"
        "Прогресія: +2.5 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_advanced"))


@router.callback_query(F.data == "gym_full_adv_v2")
async def gym_full_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Просунутий — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкий низ + легкий верх</b>\n"
        "• Присідання — 6×4\n"
        "• Румунська тяга — 4×8\n"
        "• Жим лежачи — 3×12\n"
        "• Тяга верхнього блоку — 3×12\n"
        "• Підйом литок — 5×20\n\n"
        "📌 <b>День 2 — Важкий верх + легкий низ</b>\n"
        "• Жим лежачи — 6×4\n"
        "• Станова тяга — 4×6\n"
        "• Жим ногами — 3×15\n"
        "• Армійський жим — 3×10\n"
        "• Підтягування — 3×10\n\n"
        "📌 <b>День 3 — Об'єм все тіло A</b>\n"
        "• Суперсет: присідання + жим лежачи — 4×10\n"
        "• Суперсет: тяга в нахилі + армійський жим — 4×10\n"
        "• Суперсет: підйом на біцепс + французький жим — 4×12\n"
        "• Підйом литок — 4×20\n\n"
        "📌 <b>День 4 — Об'єм все тіло Б</b>\n"
        "• Суперсет: жим ногами + похилий жим — 4×12\n"
        "• Суперсет: підтягування + армійський жим — 4×10\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Підйом ніг у висі — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Важкі дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: суперсети без відпочинку.\n"
        "Прогресія: +2.5 кг щотижня на базових."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_advanced"))


@router.callback_query(F.data == "gym_full_adv_v3")
async def gym_full_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила низ</b>\n"
        "• Присідання — 6×4\n"
        "• Станова тяга — 5×5\n"
        "• Підйом литок — 5×20\n\n"
        "📌 <b>День 2 — Сила верх</b>\n"
        "• Жим лежачи — 6×4\n"
        "• Підтягування з вагою — 5×5\n"
        "• Армійський жим — 4×6\n\n"
        "📌 <b>День 3 — Об'єм все тіло</b>\n"
        "• Жим ногами — 4×12\n"
        "• Похилий жим — 4×10\n"
        "• Тяга блоку — 4×10\n"
        "• Суперсет: підйом на біцепс + французький жим — 4×12\n"
        "• Підйом в сторони — 4×15\n\n"
        "📌 <b>День 4 — Сила все тіло</b>\n"
        "• Присідання — 4×5\n"
        "• Жим лежачи — 4×5\n"
        "• Тяга в нахилі — 4×5\n"
        "• Армійський жим — 4×6\n\n"
        "📌 <b>День 5 — Об'єм + Прес</b>\n"
        "• Суперсет: жим ногами + румунська тяга — 4×12\n"
        "• Суперсет: зведення + тяга блоку — 4×12\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Підйом ніг у висі — 4×20\n"
        "• Скручування з вагою — 4×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +2.5 кг щотижня на базових."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_advanced"))


@router.callback_query(F.data == "gym_full_ath_v1")
async def gym_full_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Атлет — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила (все тіло)</b>\n"
        "• Присідання — 6×3\n"
        "• Жим лежачи — 6×3\n"
        "• Станова тяга — 5×3\n"
        "• Армійський жим — 4×5\n"
        "• Підтягування з вагою — 4×5\n\n"
        "📌 <b>День 2 — Гіпертрофія верх</b>\n"
        "• Похилий жим штанги — 5×8\n"
        "• Тяга в нахилі — 5×8\n"
        "• Жим Арнольда — 4×10\n"
        "• Суперсет: підйом на біцепс + французький жим — 5×10\n"
        "• Суперсет: підйом в сторони + зворотні розведення — 5×15\n\n"
        "📌 <b>День 3 — Гіпертрофія низ</b>\n"
        "• Жим ногами — 5×10\n"
        "• Румунська тяга — 5×8\n"
        "• Суперсет: розгинання + згинання ніг — 5×15\n"
        "• Випади з гантелями — 4×12\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 4 — Силова витривалість</b>\n"
        "• Суперсет: присідання + жим лежачи — 5×10\n"
        "• Суперсет: тяга в нахилі + армійський жим — 5×10\n"
        "• Суперсет: підтягування + брусья — 4×10\n"
        "• Підйом ніг у висі — 5×20\n\n"
        "📌 <b>День 5 — Повний об'єм</b>\n"
        "• Присідання — 4×10\n"
        "• Жим лежачи — 4×10\n"
        "• Тяга блоку — 4×10\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Скручування з вагою — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "День сили: відпочинок 3-4 хв.\n"
        "Гіпертрофія: відпочинок 90 сек.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 6-7 — відпочинок або кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_athlete"))


@router.callback_query(F.data == "gym_full_ath_v2")
async def gym_full_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Атлет — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкий низ</b>\n"
        "• Присідання — 7×3\n"
        "• Станова тяга — 5×3\n"
        "• Жим лежачи — 3×12\n"
        "• Тяга блоку — 3×12\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 2 — Важкий верх</b>\n"
        "• Жим лежачи — 7×3\n"
        "• Підтягування з вагою — 5×5\n"
        "• Армійський жим — 5×5\n"
        "• Жим ногами — 3×15\n"
        "• Румунська тяга — 3×12\n\n"
        "📌 <b>День 3 — Об'єм все тіло</b>\n"
        "• Суперсет: присідання + жим похилий — 5×10\n"
        "• Суперсет: тяга в нахилі + жим Арнольда — 5×10\n"
        "• Суперсет: підйом на біцепс + французький жим — 5×10\n"
        "• Суперсет: підйом в сторони + підйом ніг — 5×15\n\n"
        "📌 <b>День 4 — Силова витривалість</b>\n"
        "• Присідання — 5×8\n"
        "• Жим лежачи — 5×8\n"
        "• Тяга в нахилі — 5×8\n"
        "• Армійський жим — 4×10\n"
        "• Підтягування — 4×10\n\n"
        "📌 <b>День 5 — Прес + Слабкі місця</b>\n"
        "• Підйом ніг у висі — 5×20\n"
        "• Скручування з вагою — 5×25\n"
        "• Планка з вагою — 4×90 сек\n"
        "• 3 вправи на слабку групу — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Важкі дні: відпочинок 3-4 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +2.5 кг щотижня на базових."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_athlete"))


@router.callback_query(F.data == "gym_full_ath_v3")
async def gym_full_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила низ</b>\n"
        "• Присідання — 7×3\n"
        "• Станова тяга — 5×3\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 2 — Сила верх</b>\n"
        "• Жим лежачи — 7×3\n"
        "• Підтягування з вагою — 5×5\n"
        "• Армійський жим — 5×5\n\n"
        "📌 <b>День 3 — Об'єм низ</b>\n"
        "• Жим ногами — 5×12\n"
        "• Румунська тяга — 5×10\n"
        "• Суперсет: розгинання + згинання — 5×15\n"
        "• Суперсет: випади + підйом литок — 4×15\n\n"
        "📌 <b>День 4 — Об'єм верх</b>\n"
        "• Похилий жим — 5×10\n"
        "• Тяга в нахилі — 5×10\n"
        "• Суперсет: жим Арнольда + підйом в сторони — 5×12\n"
        "• Суперсет: підйом на біцепс + французький жим — 5×10\n\n"
        "📌 <b>День 5 — Силова витривалість</b>\n"
        "• Суперсет: присідання + жим лежачи — 6×8\n"
        "• Суперсет: тяга + армійський жим — 5×8\n"
        "• Суперсет: підтягування + брусья — 4×10\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом ніг у висі — 5×20\n"
        "• Скручування з вагою — 5×25\n"
        "• Планка з вагою — 4×90 сек\n"
        "• Кардіо 20 хв помірний темп\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 3-4 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_full_athlete"))


@router.callback_query(F.data == "gym_deload")
async def gym_deload(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="gym_del_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="gym_del_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="gym_del_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="gym_del_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_gym")],
    ])
    await callback.message.edit_text(
        "😮 <b>Розвантажувальне — Зал</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gym_del_beginner")
async def gym_del_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Розвантажувальне — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_del_beg", "gym_deload", is_premium),
    )


@router.callback_query(F.data == "gym_del_intermediate")
async def gym_del_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Розвантажувальне — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_del_int", "gym_deload", is_premium),
    )


@router.callback_query(F.data == "gym_del_advanced")
async def gym_del_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Розвантажувальне — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_del_adv", "gym_deload", is_premium),
    )


@router.callback_query(F.data == "gym_del_athlete")
async def gym_del_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Розвантажувальне — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_del_ath", "gym_deload", is_premium),
    )


@router.callback_query(F.data == "gym_del_beg_v1")
async def gym_del_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Початківець — Варіант 1</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Присідання — 2×15 (50% ваги)\n"
        "• Жим лежачи — 2×15 (50% ваги)\n"
        "• Тяга блоку — 2×15 (50% ваги)\n"
        "• Підйом литок — 2×20\n"
        "• Розтяжка — 10 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 50% від робочої.\n"
        "Фокус на техніці та відновленні.\n"
        "Жодного тренування до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_beginner"))


@router.callback_query(F.data == "gym_del_beg_v2")
async def gym_del_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Початківець — Варіант 2</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Жим ногами — 2×15 (50% ваги)\n"
        "• Жим гантелей лежачи — 2×15\n"
        "• Тяга верхнього блоку — 2×15\n"
        "• Планка — 2×30 сек\n"
        "• Розтяжка — 10 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 50% від робочої.\n"
        "Тренування не більше 40 хв.\n"
        "Більше сну і відпочинку."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_beginner"))


@router.callback_query(F.data == "gym_del_beg_v3")
async def gym_del_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Початківець — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба на біговій доріжці — 20 хв\n"
        "• Присідання з власною вагою — 3×20\n"
        "• Віджимання — 3×15\n"
        "• Планка — 3×30 сек\n"
        "• Розтяжка все тіло — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Без обтяжень цього тижня.\n"
        "Акцент на рухливості суглобів.\n"
        "Більше сну і правильного харчування."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_beginner"))


@router.callback_query(F.data == "gym_del_int_v1")
async def gym_del_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Середній — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Присідання — 3×10 (60% ваги)\n"
        "• Жим лежачи — 3×10 (60% ваги)\n"
        "• Тяга в нахилі — 3×10 (60% ваги)\n"
        "• Армійський жим — 3×10 (60% ваги)\n"
        "• Розтяжка — 10 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 60% від робочої.\n"
        "Жодного підходу до відмови.\n"
        "Відновлення — пріоритет тижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_intermediate"))


@router.callback_query(F.data == "gym_del_int_v2")
async def gym_del_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Середній — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Жим ногами — 3×12 (60% ваги)\n"
        "• Похилий жим гантелей — 3×12\n"
        "• Тяга блоку — 3×12\n"
        "• Підйом в сторони — 3×15\n"
        "• Планка — 3×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 60% від робочої.\n"
        "Тренування не більше 45 хв.\n"
        "Додай 20 хв легкого кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_intermediate"))


@router.callback_query(F.data == "gym_del_int_v3")
async def gym_del_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Середній — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Кардіо — 25 хв помірний темп\n"
        "• Присідання з вагою тіла — 3×20\n"
        "• Віджимання — 3×15\n"
        "• Підтягування — 3×8\n"
        "• Розтяжка все тіло — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Мінімум навантаження цього тижня.\n"
        "Акцент на відновленні м'язів.\n"
        "Сон 8+ годин обов'язково."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_intermediate"))


@router.callback_query(F.data == "gym_del_adv_v1")
async def gym_del_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Розвантажувальне — Просунутий — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Присідання — 3×8 (50% ваги)\n"
        "• Жим лежачи — 3×8 (50% ваги)\n"
        "• Станова тяга — 3×6 (50% ваги)\n"
        "• Армійський жим — 3×8 (50% ваги)\n"
        "• Підтягування — 3×8\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 50% від робочої.\n"
        "Жодного підходу до відмови.\n"
        "Після тижня — повернення до повного навантаження."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_advanced"))


@router.callback_query(F.data == "gym_del_adv_v2")
async def gym_del_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Розвантажувальне — Просунутий — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Кардіо — 20 хв\n"
        "• Жим ногами — 3×12 (50% ваги)\n"
        "• Похилий жим — 3×12 (50% ваги)\n"
        "• Тяга блоку — 3×12 (50% ваги)\n"
        "• Планка — 3×60 сек\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 50% від робочої.\n"
        "Тренування не більше 50 хв.\n"
        "Більше білка і сну цього тижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_advanced"))


@router.callback_query(F.data == "gym_del_adv_v3")
async def gym_del_adv_v3(callback: CallbackQuery):
    text = ("🔴 <b>Розвантажувальне — Просунутий — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Плавання або велосипед — 30 хв\n"
        "• Присідання з вагою тіла — 3×20\n"
        "• Віджимання — 3×20\n"
        "• Підтягування — 3×10\n"
        "• Розтяжка все тіло — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повна відмова від важких ваг.\n"
        "Акцент на рухливості та відновленні.\n"
        "Після тижня — новий силовий цикл."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_advanced"))


@router.callback_query(F.data == "gym_del_ath_v1")
async def gym_del_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Атлет — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Присідання — 4×6 (40% ваги)\n"
        "• Жим лежачи — 4×6 (40% ваги)\n"
        "• Станова тяга — 3×5 (40% ваги)\n"
        "• Армійський жим — 3×6 (40% ваги)\n"
        "• Підтягування — 3×8\n"
        "• Розтяжка — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 40% від робочої.\n"
        "Фокус на техніці і рухливості.\n"
        "Масаж і контрастний душ вітаються."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_athlete"))


@router.callback_query(F.data == "gym_del_ath_v2")
async def gym_del_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Атлет — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Кардіо — 25 хв помірний темп\n"
        "• Жим ногами — 3×12 (40% ваги)\n"
        "• Жим гантелей — 3×12 (40% ваги)\n"
        "• Тяга блоку — 3×12 (40% ваги)\n"
        "• Планка — 3×60 сек\n"
        "• Розтяжка — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Вага 40% від робочої.\n"
        "Тренування не більше 50 хв.\n"
        "Сон 9 годин і більше білка."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_athlete"))


@router.callback_query(F.data == "gym_del_ath_v3")
async def gym_del_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Атлет — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Плавання — 30 хв\n"
        "• Присідання з вагою тіла — 3×25\n"
        "• Віджимання — 3×25\n"
        "• Підтягування — 3×12\n"
        "• Йога або розтяжка — 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повна відмова від важких ваг.\n"
        "Масаж і відновні процедури.\n"
        "Після тижня — новий силовий мезоцикл."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("gym_del_athlete"))
    
    
@router.callback_query(F.data == "outdoor_split")
async def outdoor_split(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="out_split_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="out_split_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="out_split_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="out_split_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_outdoor")],
    ])
    await callback.message.edit_text(
        "💪 <b>Спліт — Вулична площадка</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "gym_del_athlete")
async def gym_del_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Розвантажувальне — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("gym_del_ath", "gym_deload", is_premium),
    )


@router.callback_query(F.data == "out_split_intermediate")
async def out_split_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Спліт — Вулиця — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_split_int", "outdoor_split", is_premium),
    )


@router.callback_query(F.data == "out_split_advanced")
async def out_split_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Спліт — Вулиця — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_split_adv", "outdoor_split", is_premium),
    )


@router.callback_query(F.data == "out_split_athlete")
async def out_split_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Спліт — Вулиця — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_split_ath", "outdoor_split", is_premium),
    )


@router.callback_query(F.data == "out_split_beg_v1")
async def out_split_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Вулиця — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Верх тіла (тяга)</b>\n"
        "• Підтягування широким хватом — 3×5\n"
        "• Підтягування вузьким хватом — 3×5\n"
        "• Австралійські підтягування — 3×10\n"
        "• Підйом ніг у висі — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Верх тіла (жим)</b>\n"
        "• Віджимання звичайні — 3×15\n"
        "• Віджимання вузьким хватом — 3×12\n"
        "• Віджимання на брусах — 3×8\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Низ тіла</b>\n"
        "• Присідання з вагою тіла — 4×20\n"
        "• Випади — 3×15\n"
        "• Стрибки на місці — 3×15\n"
        "• Підйом на носки — 4×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Якщо підтягування важко — почни з австралійських.\n"
        "Прогресія: +1-2 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_beginner"))


@router.callback_query(F.data == "out_split_beg_v2")
async def out_split_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Вулиця — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Віджимання — 4×12\n"
        "• Віджимання на брусах — 3×8\n"
        "• Віджимання вузьким хватом — 3×10\n"
        "• Зворотні віджимання від лавки — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Підтягування — 4×5\n"
        "• Австралійські підтягування — 3×12\n"
        "• Підтягування зворотним хватом — 3×8\n"
        "• Підйом ніг у висі — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги + Прес</b>\n"
        "• Присідання — 4×20\n"
        "• Болгарські присідання — 3×12\n"
        "• Підйом на носки — 4×25\n"
        "• Скручування — 3×20\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Прогресія: +1-2 повтори щотижня.\n"
        "Фокус на техніці виконання."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_beginner"))


@router.callback_query(F.data == "out_split_beg_v3")
async def out_split_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Спліт — Вулиця — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Верх A</b>\n"
        "• Австралійські підтягування — 4×10\n"
        "• Віджимання — 4×15\n"
        "• Планка — 3×30 сек\n"
        "• Підйом колін у висі — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Низ тіла</b>\n"
        "• Присідання — 4×20\n"
        "• Випади з кроком — 3×12\n"
        "• Стрибки вгору — 3×10\n"
        "• Підйом на носки — 4×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Верх Б</b>\n"
        "• Підтягування — 4×5\n"
        "• Віджимання на брусах — 3×8\n"
        "• Зворотні віджимання — 3×12\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Прогресія: +1-2 повтори щотижня.\n"
        "Чергуй дні А і Б для різноманіття."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_beginner"))


@router.callback_query(F.data == "out_split_int_v1")
async def out_split_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Вулиця — Середній — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина + Біцепс</b>\n"
        "• Підтягування широким хватом — 4×8\n"
        "• Підтягування вузьким хватом — 4×8\n"
        "• Австралійські підтягування з вагою — 4×12\n"
        "• Підтягування зворотним хватом — 3×10\n"
        "• Підйом ніг у висі — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Груди + Трицепс</b>\n"
        "• Віджимання на брусах — 4×12\n"
        "• Віджимання з підняттям ніг — 4×10\n"
        "• Зворотні віджимання з вагою — 4×12\n"
        "• Віджимання вузьким хватом — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з обтяженням — 4×15\n"
        "• Болгарські присідання — 4×12\n"
        "• Стрибкові присідання — 4×12\n"
        "• Підйом на носки з вагою — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Віджимання в стійці на руках (нахил) — 4×10\n"
        "• Підйом в сторони (з пляшками) — 4×15\n"
        "• Підйом ніг у висі — 4×15\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +1-2 повтори щотижня.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_intermediate"))


@router.callback_query(F.data == "out_split_int_v2")
async def out_split_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Вулиця — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Тягові м'язи</b>\n"
        "• Підтягування з обтяженням — 5×6\n"
        "• Австралійські підтягування — 4×12\n"
        "• Підтягування одною рукою (з допомогою) — 3×5\n"
        "• Підйом ніг у висі — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Жимові м'язи</b>\n"
        "• Віджимання на брусах з обтяженням — 5×8\n"
        "• Віджимання з ногами на лавці — 4×12\n"
        "• Зворотні віджимання з обтяженням — 4×12\n"
        "• Планка з підняттям руки — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги повністю</b>\n"
        "• Пістолет (з допомогою) — 4×6\n"
        "• Болгарські присідання — 4×12\n"
        "• Стрибки на лавку — 4×10\n"
        "• Підйом на носки — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Верх + Прес</b>\n"
        "• Суперсет: підтягування + брусья — 4×8\n"
        "• Суперсет: віджимання + австралійські — 4×10\n"
        "• Підйом ніг прямих у висі — 4×12\n"
        "• Скручування з обтяженням — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети без відпочинку між вправами.\n"
        "Прогресія: +1-2 повтори або +ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_intermediate"))


@router.callback_query(F.data == "out_split_int_v3")
async def out_split_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Спліт — Вулиця — Середній — Варіант 3</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина</b>\n"
        "• Підтягування широким хватом — 5×8\n"
        "• Підтягування нейтральним хватом — 4×8\n"
        "• Австралійські з обтяженням — 4×12\n"
        "• Підйом ніг у висі — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Груди</b>\n"
        "• Брусья з обтяженням — 5×8\n"
        "• Віджимання похилі (ноги вгору) — 4×12\n"
        "• Віджимання горизонтальні — 4×15\n"
        "• Віджимання вузькі — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з обтяженням — 5×15\n"
        "• Пістолет з допомогою — 4×6\n"
        "• Стрибки на лавку — 4×10\n"
        "• Підйом на носки — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Піку-пушап — 4×12\n"
        "• Суперсет: підйом в сторони + планка — 4×15\n"
        "• Підйом прямих ніг у висі — 4×15\n"
        "• Скручування — 4×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: ускладнення вправ або +обтяження.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_intermediate"))


@router.callback_query(F.data == "out_split_adv_v1")
async def out_split_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Вулиця — Просунутий — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина</b>\n"
        "• Підтягування з обтяженням — 5×6\n"
        "• Підтягування одною рукою (з допомогою) — 4×5\n"
        "• Австралійські з обтяженням — 4×10\n"
        "• Підйом прямих ніг у висі — 5×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Груди</b>\n"
        "• Брусья з обтяженням — 5×8\n"
        "• Віджимання похилі з обтяженням — 4×12\n"
        "• Суперсет: вузькі + широкі віджимання — 4×12\n"
        "• Планка з обтяженням — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Пістолет — 5×6\n"
        "• Болгарські присідання з обтяженням — 4×10\n"
        "• Стрибки на лавку — 4×12\n"
        "• Підйом на носки з обтяженням — 6×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі</b>\n"
        "• Стійка на руках біля стіни — 4×30 сек\n"
        "• Піку-пушап — 4×12\n"
        "• Підйом в сторони з обтяженням — 5×15\n"
        "• Зворотні розведення — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підтягування вузько + брусья — 5×8\n"
        "• Суперсет: зворотні віджимання + австралійські — 4×10\n"
        "• Підйом прямих ніг у висі — 5×15\n"
        "• Скручування з обтяженням — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +обтяження або ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_advanced"))


@router.callback_query(F.data == "out_split_adv_v2")
async def out_split_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Вулиця — Просунутий — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важка спина</b>\n"
        "• Підтягування з обтяженням — 6×5\n"
        "• Підтягування одною рукою — 4×4\n"
        "• Австралійські одною рукою — 4×8\n"
        "• Підйом ніг у висі — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Важкі груди</b>\n"
        "• Брусья з обтяженням — 6×6\n"
        "• Віджимання з обтяженням — 5×10\n"
        "• Суперсет: похилі + горизонтальні — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Важкі ноги</b>\n"
        "• Пістолет з обтяженням — 5×6\n"
        "• Стрибки на лавку — 5×10\n"
        "• Суперсет: болгарські + підйом на носки — 5×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Важкі плечі</b>\n"
        "• Віджимання в стійці на руках — 5×8\n"
        "• Піку-пушап з обтяженням — 4×12\n"
        "• Суперсет: підйом в сторони + зворотні — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підтягування + брусья — 5×8\n"
        "• Суперсет: зворотні + австралійські — 4×10\n"
        "• Підйом прямих ніг — 5×15\n"
        "• Скручування — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +обтяження щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_advanced"))


@router.callback_query(F.data == "out_split_adv_v3")
async def out_split_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Спліт — Вулиця — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина (об'єм)</b>\n"
        "• Підтягування різним хватом — 6×6\n"
        "• Суперсет: австралійські + підйом ніг — 5×10\n"
        "• Підтягування до грудей — 4×8\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Груди (об'єм)</b>\n"
        "• Суперсет: брусья + похилі віджимання — 5×10\n"
        "• Суперсет: широкі + вузькі віджимання — 5×12\n"
        "• Планка з обтяженням — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (об'єм)</b>\n"
        "• Суперсет: пістолет + стрибки — 5×8\n"
        "• Суперсет: болгарські + підйом литок — 5×12\n"
        "• Берпі — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (об'єм)</b>\n"
        "• Стійка на руках — 5×30 сек\n"
        "• Суперсет: піку + підйом в сторони — 5×12\n"
        "• Зворотні розведення — 5×15\n\n"
        "📌 <b>День 5 — Руки + Прес (об'єм)</b>\n"
        "• Суперсет: підтягування вузько + брусья — 5×10\n"
        "• Суперсет: австралійські + зворотні — 4×12\n"
        "• Підйом прямих ніг — 5×20\n"
        "• Скручування — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_advanced"))


@router.callback_query(F.data == "out_split_ath_v1")
async def out_split_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Вулиця — Атлет — Варіант 1</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина (максимум)</b>\n"
        "• Підтягування з обтяженням — 6×5\n"
        "• Підтягування одною рукою — 5×4\n"
        "• Австралійські одною рукою — 5×8\n"
        "• Підйом прямих ніг у висі — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Груди (максимум)</b>\n"
        "• Брусья з обтяженням — 6×6\n"
        "• Віджимання в стійці на руках — 5×8\n"
        "• Суперсет: похилі + горизонтальні — 5×12\n"
        "• Суперсет: вузькі + широкі — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (максимум)</b>\n"
        "• Пістолет з обтяженням — 6×6\n"
        "• Стрибки на лавку з обтяженням — 5×10\n"
        "• Суперсет: болгарські + стрибкові присідання — 5×12\n"
        "• Підйом литок з обтяженням — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (максимум)</b>\n"
        "• Віджимання в стійці на руках — 6×8\n"
        "• Суперсет: піку + підйом в сторони — 5×12\n"
        "• Суперсет: зворотні розведення + планка — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки (максимум)</b>\n"
        "• Суперсет: підтягування вузько + брусья — 6×8\n"
        "• Суперсет: одна рука підтягування + зворотні — 5×6\n"
        "• Суперсет: австралійські + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом прямих ніг — 6×20\n"
        "• Скручування з обтяженням — 5×25\n"
        "• Планка з обтяженням — 5×90 сек\n"
        "• Біг або стрибки — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2-3 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 7 — повний відпочинок."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_athlete"))


@router.callback_query(F.data == "out_split_ath_v2")
async def out_split_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Вулиця — Атлет — Варіант 2</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила спина</b>\n"
        "• Підтягування з обтяженням — 7×4\n"
        "• Підтягування одною рукою — 5×3\n"
        "• Підйом ніг у висі — 5×15\n\n"
        "📌 <b>День 2 — Сила груди</b>\n"
        "• Брусья з обтяженням — 7×4\n"
        "• Віджимання в стійці — 5×6\n"
        "• Планка з обтяженням — 4×90 сек\n\n"
        "📌 <b>День 3 — Сила ноги</b>\n"
        "• Пістолет з обтяженням — 6×5\n"
        "• Стрибки на лавку — 5×10\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 4 — Об'єм верх</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: похилі + австралійські — 5×12\n"
        "• Суперсет: піку + підйом в сторони — 5×15\n\n"
        "📌 <b>День 5 — Об'єм низ</b>\n"
        "• Суперсет: пістолет + стрибки — 5×8\n"
        "• Суперсет: болгарські + підйом литок — 5×15\n"
        "• Берпі — 5×10\n\n"
        "📌 <b>День 6 — Прес + Слабкі місця</b>\n"
        "• Підйом прямих ніг — 5×20\n"
        "• Скручування з обтяженням — 5×25\n"
        "• 3 вправи на слабку групу — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "День 7 — відпочинок або легке кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_athlete"))


@router.callback_query(F.data == "out_split_ath_v3")
async def out_split_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Спліт — Вулиця — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Спина об'єм</b>\n"
        "• Суперсет: широкі + вузькі підтягування — 6×8\n"
        "• Суперсет: одна рука + австралійські — 5×8\n"
        "• Підйом прямих ніг — 5×20\n\n"
        "📌 <b>День 2 — Груди об'єм</b>\n"
        "• Суперсет: брусья + похилі — 6×10\n"
        "• Суперсет: горизонтальні + вузькі — 5×12\n"
        "• Планка з обтяженням — 5×90 сек\n\n"
        "📌 <b>День 3 — Ноги об'єм</b>\n"
        "• Суперсет: пістолет + стрибки — 6×8\n"
        "• Суперсет: болгарські + берпі — 5×10\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 4 — Плечі об'єм</b>\n"
        "• Суперсет: стійка + піку — 5×10\n"
        "• Суперсет: підйом в сторони + зворотні — 6×15\n"
        "• Планка бокова — 4×60 сек\n\n"
        "📌 <b>День 5 — Руки об'єм</b>\n"
        "• Суперсет: підтягування вузько + брусья — 6×10\n"
        "• Суперсет: одна рука + зворотні — 5×8\n"
        "• Суперсет: австралійські + відмова — 4×12\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом прямих ніг — 6×20\n"
        "• Скручування з обтяженням — 6×25\n"
        "• Планка з обтяженням — 5×90 сек\n"
        "• Біг 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_split_athlete"))


@router.callback_query(F.data == "outdoor_fullbody")
async def outdoor_fullbody(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="out_full_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="out_full_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="out_full_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="out_full_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_outdoor")],
    ])
    await callback.message.edit_text(
        "🔄 <b>Фулбоді — Вулиця</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "out_full_beginner")
async def out_full_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Фулбоді — Вулиця — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_full_beg", "outdoor_fullbody", is_premium),
    )


@router.callback_query(F.data == "out_full_intermediate")
async def out_full_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Фулбоді — Вулиця — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_full_int", "outdoor_fullbody", is_premium),
    )


@router.callback_query(F.data == "out_full_advanced")
async def out_full_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Фулбоді — Вулиця — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_full_adv", "outdoor_fullbody", is_premium),
    )


@router.callback_query(F.data == "out_full_athlete")
async def out_full_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Фулбоді — Вулиця — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_full_ath", "outdoor_fullbody", is_premium),
    )


@router.callback_query(F.data == "out_full_beg_v1")
async def out_full_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Вулиця — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Австралійські підтягування — 3×10\n"
        "• Віджимання — 3×12\n"
        "• Присідання — 3×20\n"
        "• Віджимання на брусах — 3×8\n"
        "• Підйом колін у висі — 3×10\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Фокус на техніці виконання.\n"
        "Прогресія: +1-2 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_beginner"))


@router.callback_query(F.data == "out_full_beg_v2")
async def out_full_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Вулиця — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Підтягування (з допомогою) — 3×5\n"
        "• Віджимання вузьким хватом — 3×12\n"
        "• Випади — 3×12\n"
        "• Зворотні віджимання від лавки — 3×12\n"
        "• Підйом ніг у висі — 3×8\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Якщо підтягування важко — замінити австралійськими.\n"
        "Прогресія: +1-2 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_beginner"))


@router.callback_query(F.data == "out_full_beg_v3")
async def out_full_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Фулбоді — Вулиця — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A і День Б — чергуємо</b>\n\n"
        "<b>День A:</b>\n"
        "• Австралійські підтягування — 3×10\n"
        "• Віджимання — 3×15\n"
        "• Присідання — 3×20\n"
        "• Планка — 3×30 сек\n\n"
        "<b>День Б:</b>\n"
        "• Підтягування (з допомогою) — 3×5\n"
        "• Брусья — 3×8\n"
        "• Випади — 3×12\n"
        "• Підйом колін у висі — 3×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Прогресія: +1-2 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_beginner"))


@router.callback_query(F.data == "out_full_int_v1")
async def out_full_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Вулиця — Середній — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Підтягування широким хватом — 4×8\n"
        "• Брусья — 4×10\n"
        "• Пістолет (з допомогою) — 4×6\n"
        "• Піку-пушап — 4×12\n"
        "• Підйом прямих ніг у висі — 4×12\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +1-2 повтори або ускладнення.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_intermediate"))


@router.callback_query(F.data == "out_full_int_v2")
async def out_full_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Вулиця — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A — Сила</b>\n"
        "• Підтягування з обтяженням — 5×5\n"
        "• Брусья з обтяженням — 5×6\n"
        "• Пістолет — 4×6\n"
        "• Стійка на руках (біля стіни) — 4×20 сек\n\n"
        "📌 <b>День Б — Об'єм</b>\n"
        "• Австралійські підтягування — 4×12\n"
        "• Віджимання з ногами на лавці — 4×12\n"
        "• Болгарські присідання — 4×12\n"
        "• Суперсет: підйом ніг + планка — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "День А: відпочинок 2 хв.\n"
        "День Б: відпочинок 90 сек.\n"
        "Прогресія: +обтяження або ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_intermediate"))


@router.callback_query(F.data == "out_full_int_v3")
async def out_full_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Фулбоді — Вулиця — Середній — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1</b>\n"
        "• Підтягування — 4×8\n"
        "• Брусья — 4×10\n"
        "• Пістолет з допомогою — 4×6\n"
        "• Суперсет: підйом ніг + скручування — 3×15\n\n"
        "📌 <b>День 2</b>\n"
        "• Підтягування зворотним хватом — 4×8\n"
        "• Піку-пушап — 4×12\n"
        "• Стрибки на лавку — 4×10\n"
        "• Суперсет: планка + бокова планка — 4×45 сек\n\n"
        "📌 <b>День 3</b>\n"
        "• Суперсет: підтягування + брусья — 4×8\n"
        "• Суперсет: болгарські + підйом литок — 4×12\n"
        "• Стійка на руках біля стіни — 4×20 сек\n"
        "• Підйом прямих ніг — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети без відпочинку.\n"
        "Прогресія: +1-2 повтори або ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_intermediate"))


@router.callback_query(F.data == "out_full_adv_v1")
async def out_full_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Вулиця — Просунутий — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила</b>\n"
        "• Підтягування з обтяженням — 5×5\n"
        "• Брусья з обтяженням — 5×6\n"
        "• Пістолет з обтяженням — 5×5\n"
        "• Віджимання в стійці на руках — 4×6\n\n"
        "📌 <b>День 2 — Об'єм верх</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: похилі + піку-пушап — 4×12\n"
        "• Суперсет: австралійські + зворотні — 4×12\n"
        "• Підйом прямих ніг — 4×15\n\n"
        "📌 <b>День 3 — Об'єм низ</b>\n"
        "• Пістолет — 5×6\n"
        "• Стрибки на лавку — 5×10\n"
        "• Болгарські присідання — 4×12\n"
        "• Підйом литок з обтяженням — 6×20\n\n"
        "📌 <b>День 4 — Повне тіло</b>\n"
        "• Суперсет: підтягування + пістолет — 4×8\n"
        "• Суперсет: брусья + стрибки — 4×10\n"
        "• Суперсет: піку + підйом ніг — 4×12\n"
        "• Планка з обтяженням — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "День сили: відпочинок 2-3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +обтяження або ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_advanced"))


@router.callback_query(F.data == "out_full_adv_v2")
async def out_full_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Вулиця — Просунутий — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкий верх</b>\n"
        "• Підтягування з обтяженням — 6×4\n"
        "• Брусья з обтяженням — 6×5\n"
        "• Стійка на руках — 5×30 сек\n"
        "• Підйом ніг у висі — 4×15\n\n"
        "📌 <b>День 2 — Важкий низ</b>\n"
        "• Пістолет з обтяженням — 6×5\n"
        "• Стрибки на лавку з обтяженням — 5×8\n"
        "• Болгарські з обтяженням — 4×10\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 3 — Об'єм все тіло A</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: пістолет + стрибки — 5×8\n"
        "• Суперсет: піку + підйом ніг — 4×12\n\n"
        "📌 <b>День 4 — Об'єм все тіло Б</b>\n"
        "• Суперсет: австралійські + похилі — 5×12\n"
        "• Суперсет: болгарські + підйом литок — 5×12\n"
        "• Суперсет: планка + бокова планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Важкі дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: суперсети без відпочинку.\n"
        "Прогресія: +обтяження щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_advanced"))


@router.callback_query(F.data == "out_full_adv_v3")
async def out_full_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Фулбоді — Вулиця — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила верх</b>\n"
        "• Підтягування з обтяженням — 6×4\n"
        "• Брусья з обтяженням — 5×5\n"
        "• Стійка на руках — 4×30 сек\n\n"
        "📌 <b>День 2 — Сила низ</b>\n"
        "• Пістолет з обтяженням — 6×5\n"
        "• Стрибки на лавку — 5×10\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 3 — Об'єм все тіло</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: пістолет + болгарські — 5×10\n"
        "• Суперсет: піку + підйом ніг — 4×12\n\n"
        "📌 <b>День 4 — Сила все тіло</b>\n"
        "• Підтягування з обтяженням — 4×5\n"
        "• Брусья з обтяженням — 4×6\n"
        "• Пістолет з обтяженням — 4×5\n"
        "• Стійка на руках — 4×30 сек\n\n"
        "📌 <b>День 5 — Об'єм + Прес</b>\n"
        "• Суперсет: австралійські + похилі — 5×12\n"
        "• Суперсет: болгарські + стрибки — 5×10\n"
        "• Підйом прямих ніг — 5×20\n"
        "• Скручування з обтяженням — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +обтяження щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_advanced"))


@router.callback_query(F.data == "out_full_ath_v1")
async def out_full_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Вулиця — Атлет — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила все тіло</b>\n"
        "• Підтягування з обтяженням — 6×4\n"
        "• Брусья з обтяженням — 6×4\n"
        "• Пістолет з обтяженням — 6×4\n"
        "• Віджимання в стійці — 5×6\n\n"
        "📌 <b>День 2 — Гіпертрофія верх</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: австралійські + похилі — 5×12\n"
        "• Суперсет: піку + підйом в сторони — 5×15\n"
        "• Підйом прямих ніг — 5×15\n\n"
        "📌 <b>День 3 — Гіпертрофія низ</b>\n"
        "• Пістолет — 5×8\n"
        "• Суперсет: болгарські + стрибки — 5×10\n"
        "• Суперсет: берпі + підйом литок — 5×12\n\n"
        "📌 <b>День 4 — Силова витривалість</b>\n"
        "• Суперсет: підтягування + пістолет — 5×10\n"
        "• Суперсет: брусья + стрибки — 5×10\n"
        "• Суперсет: піку + підйом ніг — 4×12\n"
        "• Планка з обтяженням — 5×60 сек\n\n"
        "📌 <b>День 5 — Повний об'єм</b>\n"
        "• Підтягування різним хватом — 5×10\n"
        "• Брусья — 5×12\n"
        "• Пістолет — 4×8\n"
        "• Суперсет: підйом ніг + скручування — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "День сили: відпочинок 3 хв.\n"
        "Гіпертрофія: відпочинок 90 сек.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 6-7 — відпочинок або кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_athlete"))


@router.callback_query(F.data == "out_full_ath_v2")
async def out_full_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Вулиця — Атлет — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкий верх</b>\n"
        "• Підтягування з обтяженням — 7×3\n"
        "• Брусья з обтяженням — 6×4\n"
        "• Стійка на руках — 5×30 сек\n"
        "• Підйом ніг у висі — 5×15\n\n"
        "📌 <b>День 2 — Важкий низ</b>\n"
        "• Пістолет з обтяженням — 7×4\n"
        "• Стрибки з обтяженням — 5×8\n"
        "• Болгарські з обтяженням — 5×8\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 3 — Об'єм все тіло</b>\n"
        "• Суперсет: підтягування + брусья — 5×10\n"
        "• Суперсет: пістолет + стрибки — 5×10\n"
        "• Суперсет: піку + підйом ніг — 5×12\n\n"
        "📌 <b>День 4 — Силова витривалість</b>\n"
        "• Підтягування — 5×10\n"
        "• Брусья — 5×12\n"
        "• Пістолет — 5×8\n"
        "• Берпі — 5×10\n\n"
        "📌 <b>День 5 — Прес + Слабкі місця</b>\n"
        "• Підйом прямих ніг — 6×20\n"
        "• Скручування з обтяженням — 5×25\n"
        "• Планка з обтяженням — 5×90 сек\n"
        "• 3 вправи на слабку групу — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Важкі дні: відпочинок 3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "День 6-7 — відпочинок або легке кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_athlete"))


@router.callback_query(F.data == "out_full_ath_v3")
async def out_full_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Фулбоді — Вулиця — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила верх</b>\n"
        "• Підтягування з обтяженням — 7×3\n"
        "• Брусья з обтяженням — 6×4\n"
        "• Стійка на руках — 5×30 сек\n\n"
        "📌 <b>День 2 — Сила низ</b>\n"
        "• Пістолет з обтяженням — 7×4\n"
        "• Стрибки з обтяженням — 5×8\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 3 — Об'єм верх</b>\n"
        "• Суперсет: підтягування + брусья — 6×10\n"
        "• Суперсет: австралійські + похилі — 5×12\n"
        "• Суперсет: піку + підйом в сторони — 5×15\n\n"
        "📌 <b>День 4 — Об'єм низ</b>\n"
        "• Суперсет: пістолет + болгарські — 6×8\n"
        "• Суперсет: стрибки + берпі — 5×10\n"
        "• Підйом литок — 6×25\n\n"
        "📌 <b>День 5 — Силова витривалість</b>\n"
        "• Суперсет: підтягування + пістолет — 6×8\n"
        "• Суперсет: брусья + стрибки — 5×10\n"
        "• Суперсет: піку + підйом ніг — 5×12\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом прямих ніг — 6×20\n"
        "• Скручування з обтяженням — 6×25\n"
        "• Планка з обтяженням — 5×90 сек\n"
        "• Біг 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_full_athlete"))
    
    
@router.callback_query(F.data == "outdoor_deload")
async def outdoor_deload(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="out_del_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="out_del_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="out_del_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="out_del_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_outdoor")],
    ])
    await callback.message.edit_text(
        "😮 <b>Розвантажувальне — Вулиця</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "out_del_beginner")
async def out_del_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Розвантажувальне — Вулиця — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_del_beg", "outdoor_deload", is_premium),
    )


@router.callback_query(F.data == "out_del_intermediate")
async def out_del_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Розвантажувальне — Вулиця — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_del_int", "outdoor_deload", is_premium),
    )


@router.callback_query(F.data == "out_del_advanced")
async def out_del_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Розвантажувальне — Вулиця — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_del_adv", "outdoor_deload", is_premium),
    )


@router.callback_query(F.data == "out_del_athlete")
async def out_del_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Розвантажувальне — Вулиця — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("out_del_ath", "outdoor_deload", is_premium),
    )


@router.callback_query(F.data == "out_del_beg_v1")
async def out_del_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Вулиця — Початківець — Варіант 1</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба — 20 хв\n"
        "• Австралійські підтягування — 2×8\n"
        "• Віджимання — 2×10\n"
        "• Присідання — 2×15\n"
        "• Розтяжка — 10 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Мінімальне навантаження.\n"
        "Фокус на відновленні і розтяжці.\n"
        "Більше сну цього тижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_beginner"))


@router.callback_query(F.data == "out_del_beg_v2")
async def out_del_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Вулиця — Початківець — Варіант 2</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Легкий біг — 15 хв\n"
        "• Присідання з вагою тіла — 2×15\n"
        "• Планка — 2×30 сек\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Без підтягувань і брусів цього тижня.\n"
        "Акцент на рухливості суглобів.\n"
        "Більше води і правильного харчування."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_beginner"))


@router.callback_query(F.data == "out_del_beg_v3")
async def out_del_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Розвантажувальне — Вулиця — Початківець — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба на свіжому повітрі — 30 хв\n"
        "• Розтяжка все тіло — 20 хв\n"
        "• Дихальні вправи — 10 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повний відпочинок від силових.\n"
        "Сон 8-9 годин обов'язково.\n"
        "Наступного тижня — повернення до програми."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_beginner"))


@router.callback_query(F.data == "out_del_int_v1")
async def out_del_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Вулиця — Середній — Варіант 1</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Легкий біг — 20 хв\n"
        "• Підтягування — 2×5 (50% від макс)\n"
        "• Віджимання — 2×10\n"
        "• Присідання — 2×15\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "50% від звичайного навантаження.\n"
        "Жодного підходу до відмови.\n"
        "Відновлення — пріоритет тижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_intermediate"))


@router.callback_query(F.data == "out_del_int_v2")
async def out_del_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Вулиця — Середній — Варіант 2</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Велосипед або плавання — 25 хв\n"
        "• Австралійські підтягування — 2×10\n"
        "• Брусья — 2×8\n"
        "• Планка — 2×45 сек\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Тренування не більше 40 хв.\n"
        "Акцент на рухливості суглобів.\n"
        "Більше білка і сну цього тижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_intermediate"))


@router.callback_query(F.data == "out_del_int_v3")
async def out_del_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Розвантажувальне — Вулиця — Середній — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба — 30 хв\n"
        "• Присідання з вагою тіла — 2×20\n"
        "• Віджимання — 2×15\n"
        "• Розтяжка все тіло — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Мінімум навантаження цього тижня.\n"
        "Сон 8+ годин обов'язково.\n"
        "Після тижня — повернення до програми."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_intermediate"))


@router.callback_query(F.data == "out_del_adv_v1")
async def out_del_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Розвантажувальне — Вулиця — Просунутий — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Легкий біг — 20 хв\n"
        "• Підтягування — 3×5 (50% від макс)\n"
        "• Брусья — 3×6 (50% від макс)\n"
        "• Пістолет з допомогою — 3×5\n"
        "• Розтяжка — 15 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "50% від звичайного навантаження.\n"
        "Жодного підходу до відмови.\n"
        "Після тижня — новий силовий цикл."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_advanced"))


@router.callback_query(F.data == "out_del_adv_v2")
async def out_del_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Розвантажувальне — Вулиця — Просунутий — Варіант 2</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Плавання або велосипед — 30 хв\n"
        "• Австралійські підтягування — 3×10\n"
        "• Віджимання — 3×15\n"
        "• Планка — 3×60 сек\n"
        "• Розтяжка — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повна відмова від важких вправ.\n"
        "Масаж і контрастний душ.\n"
        "Більше білка і сну."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_advanced"))


@router.callback_query(F.data == "out_del_adv_v3")
async def out_del_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Розвантажувальне — Вулиця — Просунутий — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба на свіжому повітрі — 40 хв\n"
        "• Присідання з вагою тіла — 3×20\n"
        "• Розтяжка все тіло — 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повний відпочинок від складних вправ.\n"
        "Акцент на рухливості та відновленні.\n"
        "Після тижня — новий мезоцикл."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_advanced"))


@router.callback_query(F.data == "out_del_ath_v1")
async def out_del_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Вулиця — Атлет — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Легкий біг — 25 хв\n"
        "• Підтягування — 3×5 (40% від макс)\n"
        "• Брусья — 3×5 (40% від макс)\n"
        "• Пістолет з допомогою — 3×4\n"
        "• Розтяжка — 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "40% від звичайного навантаження.\n"
        "Фокус на техніці і рухливості.\n"
        "Масаж і відновні процедури вітаються."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_athlete"))


@router.callback_query(F.data == "out_del_ath_v2")
async def out_del_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Вулиця — Атлет — Варіант 2</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Плавання — 30 хв\n"
        "• Австралійські підтягування — 3×10\n"
        "• Віджимання — 3×15\n"
        "• Планка — 3×60 сек\n"
        "• Йога або розтяжка — 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повна відмова від важких вправ.\n"
        "Масаж і контрастний душ.\n"
        "Сон 9+ годин обов'язково."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_athlete"))


@router.callback_query(F.data == "out_del_ath_v3")
async def out_del_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Розвантажувальне — Вулиця — Атлет — Варіант 3</b>\n"
        "📅 2 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування</b>\n"
        "• Ходьба або велосипед — 40 хв\n"
        "• Присідання з вагою тіла — 3×20\n"
        "• Йога — 30 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Повний відпочинок від складних вправ.\n"
        "Масаж і відновні процедури.\n"
        "Після тижня — новий силовий мезоцикл."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("out_del_athlete"))


@router.callback_query(F.data == "home_dumbbells")
async def home_dumbbells(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="home_db_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="home_db_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="home_db_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="home_db_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_home")],
    ])
    await callback.message.edit_text(
        "🏋️ <b>Вдома — З гантелями</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "home_db_beginner")
async def home_db_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Гантелі — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_db_beg", "home_dumbbells", is_premium),
    )


@router.callback_query(F.data == "home_db_intermediate")
async def home_db_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Гантелі — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_db_int", "home_dumbbells", is_premium),
    )


@router.callback_query(F.data == "home_db_advanced")
async def home_db_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Гантелі — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_db_adv", "home_dumbbells", is_premium),
    )


@router.callback_query(F.data == "home_db_athlete")
async def home_db_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Гантелі — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_db_ath", "home_dumbbells", is_premium),
    )


@router.callback_query(F.data == "home_db_beg_v1")
async def home_db_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Гантелі — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Присідання з гантелями — 3×12\n"
        "• Жим гантелей лежачи (підлога) — 3×12\n"
        "• Тяга гантелей у нахилі — 3×12\n"
        "• Жим гантелей сидячи — 3×12\n"
        "• Підйом гантелей на біцепс — 3×12\n"
        "• Розгинання з гантеллю з-за голови — 3×12\n"
        "• Підйом на носки — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Вага легка — фокус на техніці.\n"
        "Прогресія: +1-2 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_beginner"))


@router.callback_query(F.data == "home_db_beg_v2")
async def home_db_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Гантелі — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A і День Б — чергуємо</b>\n\n"
        "<b>День A — Верх тіла:</b>\n"
        "• Жим гантелей лежачи — 3×12\n"
        "• Тяга гантелі однією рукою — 3×12\n"
        "• Жим гантелей сидячи — 3×12\n"
        "• Підйом на біцепс — 3×12\n"
        "• Французький жим з гантеллю — 3×12\n\n"
        "<b>День Б — Низ тіла:</b>\n"
        "• Присідання з гантелями — 3×15\n"
        "• Випади з гантелями — 3×12\n"
        "• Румунська тяга з гантелями — 3×12\n"
        "• Підйом на носки — 3×20\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Прогресія: +1-2 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_beginner"))


@router.callback_query(F.data == "home_db_beg_v3")
async def home_db_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Гантелі — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Випади з гантелями — 3×12\n"
        "• Розведення гантелей лежачи — 3×12\n"
        "• Тяга гантелей до пояса — 3×12\n"
        "• Підйом гантелей в сторони — 3×15\n"
        "• Молоткові підйоми — 3×12\n"
        "• Розгинання однієї руки — 3×12\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60-90 сек між підходами.\n"
        "Контролюй рух в обох напрямках.\n"
        "Прогресія: +1-2 кг кожні 2 тижні."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_beginner"))


@router.callback_query(F.data == "home_db_int_v1")
async def home_db_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Гантелі — Середній — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим гантелей лежачи — 4×10\n"
        "• Жим гантелей похилий — 4×10\n"
        "• Розведення гантелей лежачи — 3×12\n"
        "• Французький жим з гантеллю — 4×10\n"
        "• Розгинання однієї руки — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Тяга гантелі однією рукою — 4×10\n"
        "• Тяга двох гантелей у нахилі — 4×10\n"
        "• Пулловер з гантеллю — 3×12\n"
        "• Підйом гантелей на біцепс — 4×10\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з гантелями — 4×12\n"
        "• Випади з гантелями — 4×12\n"
        "• Румунська тяга з гантелями — 4×10\n"
        "• Сумо присідання з гантеллю — 3×15\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Жим гантелей сидячи — 4×10\n"
        "• Підйом гантелей в сторони — 4×15\n"
        "• Підйом гантелей перед собою — 3×12\n"
        "• Зворотні розведення — 3×15\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +1-2 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_intermediate"))


@router.callback_query(F.data == "home_db_int_v2")
async def home_db_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Гантелі — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Поштовхові м'язи</b>\n"
        "• Жим гантелей лежачи — 4×10\n"
        "• Жим гантелей сидячи — 4×10\n"
        "• Розведення гантелей — 3×12\n"
        "• Підйом в сторони — 4×15\n"
        "• Французький жим — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тягові м'язи</b>\n"
        "• Тяга гантелі однією рукою — 4×10\n"
        "• Тяга двох гантелей — 4×10\n"
        "• Зворотні розведення — 4×15\n"
        "• Підйом на біцепс — 4×10\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Квадрицепс</b>\n"
        "• Присідання з гантелями — 5×10\n"
        "• Випади з гантелями — 4×12\n"
        "• Сумо з гантеллю — 4×12\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Задня поверхня + Прес</b>\n"
        "• Румунська тяга — 4×10\n"
        "• Згинання ніг (з гантеллю між ніг) — 4×12\n"
        "• Гіперекстензія з гантеллю — 3×15\n"
        "• Планка — 4×60 сек\n"
        "• Скручування з гантеллю — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +1-2 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_intermediate"))


@router.callback_query(F.data == "home_db_int_v3")
async def home_db_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Гантелі — Середній — Варіант 3</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Біцепс</b>\n"
        "• Жим гантелей лежачи — 4×10\n"
        "• Похилий жим гантелей — 4×10\n"
        "• Розведення гантелей — 3×12\n"
        "• Підйом на біцепс — 4×10\n"
        "• Концентровані підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Трицепс</b>\n"
        "• Тяга гантелі однією рукою — 4×10\n"
        "• Тяга двох гантелей — 4×10\n"
        "• Пулловер — 3×12\n"
        "• Французький жим — 4×10\n"
        "• Розгинання однієї руки — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги повністю</b>\n"
        "• Присідання — 4×12\n"
        "• Румунська тяга — 4×10\n"
        "• Випади — 4×12\n"
        "• Сумо — 3×15\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Жим гантелей сидячи — 4×10\n"
        "• Підйом в сторони — 4×15\n"
        "• Підйом перед собою — 3×12\n"
        "• Зворотні розведення — 3×15\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +1-2 кг кожні 1-2 тижні.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_intermediate"))


@router.callback_query(F.data == "home_db_adv_v1")
async def home_db_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Гантелі — Просунутий — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди</b>\n"
        "• Жим гантелей лежачи — 5×8\n"
        "• Похилий жим гантелей — 4×10\n"
        "• Розведення гантелей лежачи — 4×12\n"
        "• Суперсет: жим вузько + розведення — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина</b>\n"
        "• Тяга гантелі однією рукою — 5×8\n"
        "• Тяга двох гантелей у нахилі — 4×10\n"
        "• Пулловер з гантеллю — 4×12\n"
        "• Суперсет: зворотні розведення + шраги — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з гантелями — 5×10\n"
        "• Румунська тяга — 4×10\n"
        "• Випади з гантелями — 4×12\n"
        "• Суперсет: сумо + підйом на носки — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі</b>\n"
        "• Жим гантелей сидячи — 5×8\n"
        "• Підйом в сторони — 5×15\n"
        "• Суперсет: підйом перед собою + зворотні — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підйом на біцепс + французький жим — 5×10\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Скручування з гантеллю — 4×20\n"
        "• Планка з гантеллю — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +1-2 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_advanced"))


@router.callback_query(F.data == "home_db_adv_v2")
async def home_db_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Гантелі — Просунутий — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим гантелей лежачи — 5×8\n"
        "• Похилий жим — 4×10\n"
        "• Суперсет: розведення + французький жим — 4×12\n"
        "• Суперсет: жим вузько + відмова — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Тяга гантелі однією рукою — 5×8\n"
        "• Тяга двох гантелей — 4×10\n"
        "• Суперсет: пулловер + підйом на біцепс — 4×12\n"
        "• Суперсет: молотки + концентровані — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги передня поверхня</b>\n"
        "• Присідання — 5×10\n"
        "• Випади — 4×12\n"
        "• Суперсет: сумо + стрибки — 4×12\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі повністю</b>\n"
        "• Жим гантелей сидячи — 5×8\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 5×15\n"
        "• Суперсет: зворотні розведення + шраги — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Ноги задня + Прес</b>\n"
        "• Румунська тяга — 5×10\n"
        "• Суперсет: випади зворотні + підйом литок — 4×12\n"
        "• Скручування з гантеллю — 5×20\n"
        "• Планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +1-2 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_advanced"))


@router.callback_query(F.data == "home_db_adv_v3")
async def home_db_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Гантелі — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкі груди</b>\n"
        "• Жим гантелей лежачи — 6×6\n"
        "• Похилий жим — 5×8\n"
        "• Суперсет: розведення верх + розведення низ — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Важка спина</b>\n"
        "• Тяга гантелі однією рукою — 6×6\n"
        "• Тяга двох гантелей — 5×8\n"
        "• Суперсет: пулловер + зворотні розведення — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Важкі ноги</b>\n"
        "• Присідання з гантелями — 6×8\n"
        "• Румунська тяга — 5×8\n"
        "• Суперсет: випади + сумо — 4×12\n"
        "• Підйом на носки — 6×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Важкі плечі</b>\n"
        "• Жим гантелей сидячи — 6×6\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 5×15\n"
        "• Зворотні розведення — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підйом на біцепс + французький жим — 5×10\n"
        "• Суперсет: молотки + розгинання — 4×12\n"
        "• Суперсет: концентровані + відмова — 3×12\n"
        "• Скручування з гантеллю — 5×20\n"
        "• Планка з гантеллю — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +1-2 кг щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_advanced"))


@router.callback_query(F.data == "home_db_ath_v1")
async def home_db_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Гантелі — Атлет — Варіант 1</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди (об'єм)</b>\n"
        "• Жим гантелей лежачи — 6×6\n"
        "• Похилий жим — 5×8\n"
        "• Суперсет: розведення верх + розведення низ — 5×12\n"
        "• Суперсет: жим вузько + відмова — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина (об'єм)</b>\n"
        "• Тяга гантелі однією рукою — 6×6\n"
        "• Тяга двох гантелей — 5×8\n"
        "• Суперсет: пулловер + зворотні розведення — 5×12\n"
        "• Суперсет: шраги + тяга до підборіддя — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (об'єм)</b>\n"
        "• Присідання з гантелями — 6×8\n"
        "• Румунська тяга — 5×8\n"
        "• Суперсет: випади + сумо — 5×12\n"
        "• Суперсет: стрибкові присідання + підйом литок — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (об'єм)</b>\n"
        "• Жим гантелей сидячи — 6×6\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 6×15\n"
        "• Суперсет: зворотні розведення + шраги — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки (об'єм)</b>\n"
        "• Суперсет: підйом на біцепс + французький жим — 6×10\n"
        "• Суперсет: молотки + розгинання — 5×12\n"
        "• Суперсет: концентровані + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Скручування з гантеллю — 5×25\n"
        "• Планка з гантеллю — 5×90 сек\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Кардіо 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +1-2 кг щотижня.\n"
        "День 7 — повний відпочинок."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_athlete"))


@router.callback_query(F.data == "home_db_ath_v2")
async def home_db_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Гантелі — Атлет — Варіант 2</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Жимовий день (сила)</b>\n"
        "• Жим гантелей лежачи — 7×5\n"
        "• Похилий жим — 5×6\n"
        "• Жим гантелей сидячи — 5×6\n"
        "• Суперсет: французький жим + підйом в сторони — 5×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тяговий день (сила)</b>\n"
        "• Тяга гантелі однією рукою — 7×5\n"
        "• Тяга двох гантелей — 5×6\n"
        "• Суперсет: підйом на біцепс + зворотні — 5×10\n"
        "• Шраги з гантелями — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (сила)</b>\n"
        "• Присідання з гантелями — 7×6\n"
        "• Румунська тяга — 5×6\n"
        "• Суперсет: випади + сумо — 5×12\n"
        "• Підйом на носки — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Груди + Плечі (об'єм)</b>\n"
        "• Похилий жим — 5×10\n"
        "• Суперсет: розведення + підйом в сторони — 5×15\n"
        "• Суперсет: жим вузько + зворотні — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Спина (об'єм)</b>\n"
        "• Тяга гантелі однією рукою — 5×10\n"
        "• Суперсет: пулловер + тяга двох — 5×12\n"
        "• Суперсет: молотки + концентровані — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Руки + Прес (об'єм)</b>\n"
        "• Суперсет: підйом на біцепс + французький жим — 6×10\n"
        "• Суперсет: молотки + розгинання — 5×12\n"
        "• Скручування з гантеллю — 5×25\n"
        "• Планка — 5×90 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "Прогресія: +1-2 кг щотижня.\n"
        "День 7 — відпочинок або легке кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_athlete"))


@router.callback_query(F.data == "home_db_ath_v3")
async def home_db_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Гантелі — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди максимум</b>\n"
        "• Жим гантелей лежачи — 6×6\n"
        "• Суперсет: похилий жим + розведення верх — 5×10\n"
        "• Суперсет: розведення низ + жим вузько — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина максимум</b>\n"
        "• Тяга гантелі однією рукою — 6×6\n"
        "• Суперсет: тяга двох + пулловер — 5×10\n"
        "• Суперсет: зворотні розведення + шраги — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги максимум</b>\n"
        "• Присідання — 6×8\n"
        "• Суперсет: румунська тяга + випади — 5×10\n"
        "• Суперсет: сумо + стрибки — 4×12\n"
        "• Підйом на носки — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі максимум</b>\n"
        "• Жим гантелей сидячи — 6×6\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 6×15\n"
        "• Суперсет: зворотні + шраги — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки максимум</b>\n"
        "• Суперсет: підйом на біцепс + французький жим — 6×10\n"
        "• Суперсет: похилі підйоми + розгинання — 5×12\n"
        "• Суперсет: молотки + концентровані — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Скручування з гантеллю — 6×25\n"
        "• Планка з гантеллю — 5×90 сек\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Кардіо 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: +1-2 кг щотижня.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_db_athlete"))


@router.callback_query(F.data == "home_bands")
async def home_bands(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="home_band_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="home_band_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="home_band_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="home_band_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_home")],
    ])
    await callback.message.edit_text(
        "🎽 <b>Вдома — З гумками</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "home_band_beginner")
async def home_band_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Гумки — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_band_beg", "home_bands", is_premium),
    )


@router.callback_query(F.data == "home_band_intermediate")
async def home_band_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Гумки — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_band_int", "home_bands", is_premium),
    )


@router.callback_query(F.data == "home_band_advanced")
async def home_band_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Гумки — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_band_adv", "home_bands", is_premium),
    )


@router.callback_query(F.data == "home_band_athlete")
async def home_band_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Гумки — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_band_ath", "home_bands", is_premium),
    )


@router.callback_query(F.data == "home_band_beg_v1")
async def home_band_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Гумки — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Присідання з гумкою — 3×15\n"
        "• Жим гумки від грудей — 3×12\n"
        "• Тяга гумки до пояса — 3×12\n"
        "• Підйом гумки над головою — 3×12\n"
        "• Підйом на біцепс з гумкою — 3×12\n"
        "• Розгинання на трицепс з гумкою — 3×12\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60 сек між підходами.\n"
        "Обирай гумку середнього опору.\n"
        "Прогресія: перехід на важчу гумку."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_beginner"))


@router.callback_query(F.data == "home_band_beg_v2")
async def home_band_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Гумки — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A і День Б — чергуємо</b>\n\n"
        "<b>День A — Верх тіла:</b>\n"
        "• Жим гумки від грудей — 3×12\n"
        "• Тяга гумки до пояса — 3×12\n"
        "• Підйом гумки над головою — 3×12\n"
        "• Підйом на біцепс — 3×12\n"
        "• Розгинання на трицепс — 3×12\n\n"
        "<b>День Б — Низ тіла:</b>\n"
        "• Присідання з гумкою — 3×20\n"
        "• Випади з гумкою — 3×12\n"
        "• Відведення ноги назад — 3×15\n"
        "• Підйом на носки — 3×20\n"
        "• Скручування — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "Відпочинок 60 сек між підходами.\n"
        "Прогресія: перехід на важчу гумку."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_beginner"))


@router.callback_query(F.data == "home_band_beg_v3")
async def home_band_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Гумки — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Присідання сумо з гумкою — 3×15\n"
        "• Розведення рук з гумкою — 3×12\n"
        "• Тяга гумки однією рукою — 3×12\n"
        "• Підйом в сторони з гумкою — 3×15\n"
        "• Молоткові підйоми з гумкою — 3×12\n"
        "• Відведення ноги в сторону — 3×15\n"
        "• Планка — 3×30 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60 сек між підходами.\n"
        "Контролюй рух в обох напрямках.\n"
        "Прогресія: перехід на важчу гумку."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_beginner"))


@router.callback_query(F.data == "home_band_int_v1")
async def home_band_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Гумки — Середній — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим гумки від грудей — 4×12\n"
        "• Розведення рук з гумкою — 4×15\n"
        "• Віджимання з гумкою на спині — 4×12\n"
        "• Розгинання на трицепс — 4×15\n"
        "• Розгинання однієї руки — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Тяга гумки до пояса — 4×12\n"
        "• Тяга гумки однією рукою — 4×12\n"
        "• Тяга гумки до підборіддя — 3×15\n"
        "• Підйом на біцепс з гумкою — 4×12\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з гумкою — 4×15\n"
        "• Випади з гумкою — 4×12\n"
        "• Відведення ноги назад — 4×15\n"
        "• Сумо з гумкою — 4×15\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Жим гумки над головою — 4×12\n"
        "• Підйом в сторони з гумкою — 4×15\n"
        "• Підйом перед собою — 3×12\n"
        "• Зворотні розведення — 3×15\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Використовуй гумки різного опору.\n"
        "Прогресія: важча гумка або +повтори."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_intermediate"))


@router.callback_query(F.data == "home_band_int_v2")
async def home_band_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Гумки — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Поштовхові м'язи</b>\n"
        "• Жим гумки від грудей — 4×12\n"
        "• Жим гумки над головою — 4×12\n"
        "• Розведення рук — 3×15\n"
        "• Підйом в сторони — 4×15\n"
        "• Розгинання на трицепс — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тягові м'язи</b>\n"
        "• Тяга гумки до пояса — 4×12\n"
        "• Тяга однієї руки — 4×12\n"
        "• Зворотні розведення — 4×15\n"
        "• Підйом на біцепс — 4×12\n"
        "• Молоткові підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Квадрицепс</b>\n"
        "• Присідання з гумкою — 5×15\n"
        "• Випади з гумкою — 4×12\n"
        "• Сумо з гумкою — 4×15\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Задня поверхня + Прес</b>\n"
        "• Румунська тяга з гумкою — 4×12\n"
        "• Відведення ноги назад — 4×15\n"
        "• Міст з гумкою — 4×20\n"
        "• Планка — 4×60 сек\n"
        "• Скручування — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Використовуй гумки різного опору.\n"
        "Прогресія: важча гумка або +повтори."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_intermediate"))


@router.callback_query(F.data == "home_band_int_v3")
async def home_band_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Гумки — Середній — Варіант 3</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Біцепс</b>\n"
        "• Жим гумки від грудей — 4×12\n"
        "• Розведення рук — 4×15\n"
        "• Віджимання з гумкою — 3×12\n"
        "• Підйом на біцепс — 4×12\n"
        "• Концентровані підйоми — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Трицепс</b>\n"
        "• Тяга до пояса — 4×12\n"
        "• Тяга однієї руки — 4×12\n"
        "• Зворотні розведення — 3×15\n"
        "• Розгинання на трицепс — 4×15\n"
        "• Розгинання однієї руки — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги повністю</b>\n"
        "• Присідання — 4×15\n"
        "• Румунська тяга з гумкою — 4×12\n"
        "• Випади — 4×12\n"
        "• Міст з гумкою — 4×20\n"
        "• Підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі + Прес</b>\n"
        "• Жим над головою — 4×12\n"
        "• Підйом в сторони — 4×15\n"
        "• Підйом перед собою — 3×12\n"
        "• Зворотні розведення — 3×15\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: важча гумка або +повтори.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_intermediate"))


@router.callback_query(F.data == "home_band_adv_v1")
async def home_band_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Гумки — Просунутий — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди</b>\n"
        "• Жим гумки від грудей — 5×10\n"
        "• Похилий жим з гумкою — 4×12\n"
        "• Суперсет: розведення верх + розведення низ — 4×15\n"
        "• Суперсет: віджимання з гумкою + відмова — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина</b>\n"
        "• Тяга гумки до пояса — 5×10\n"
        "• Тяга однієї руки — 4×12\n"
        "• Суперсет: зворотні розведення + тяга до підборіддя — 4×15\n"
        "• Шраги з гумкою — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання з гумкою — 5×15\n"
        "• Румунська тяга з гумкою — 4×12\n"
        "• Суперсет: випади + відведення назад — 4×15\n"
        "• Суперсет: міст + підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі</b>\n"
        "• Жим гумки над головою — 5×10\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 5×15\n"
        "• Суперсет: зворотні розведення + тяга до підборіддя — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підйом на біцепс + розгинання на трицепс — 5×12\n"
        "• Суперсет: молотки + розгинання однієї руки — 4×12\n"
        "• Скручування — 4×20\n"
        "• Планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: важча гумка або +повтори."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_advanced"))


@router.callback_query(F.data == "home_band_adv_v2")
async def home_band_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Гумки — Просунутий — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Жим гумки від грудей — 5×10\n"
        "• Суперсет: розведення + розгинання на трицепс — 4×12\n"
        "• Суперсет: віджимання з гумкою + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Тяга до пояса — 5×10\n"
        "• Суперсет: тяга однієї руки + зворотні — 4×12\n"
        "• Суперсет: підйом на біцепс + молотки — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги передня поверхня</b>\n"
        "• Присідання — 5×15\n"
        "• Суперсет: випади + сумо — 4×15\n"
        "• Суперсет: стрибкові присідання + підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі повністю</b>\n"
        "• Жим над головою — 5×10\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 5×15\n"
        "• Суперсет: зворотні + тяга до підборіддя — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Ноги задня + Прес</b>\n"
        "• Румунська тяга — 5×12\n"
        "• Суперсет: міст + відведення назад — 5×20\n"
        "• Скручування — 5×20\n"
        "• Планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: важча гумка або +повтори."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_advanced"))


@router.callback_query(F.data == "home_band_adv_v3")
async def home_band_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Гумки — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкі груди</b>\n"
        "• Жим від грудей — 6×8\n"
        "• Суперсет: похилий жим + розведення верх — 5×12\n"
        "• Суперсет: розведення низ + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Важка спина</b>\n"
        "• Тяга до пояса — 6×8\n"
        "• Суперсет: тяга однієї руки + зворотні — 5×12\n"
        "• Суперсет: тяга до підборіддя + шраги — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Важкі ноги</b>\n"
        "• Присідання — 6×15\n"
        "• Суперсет: румунська тяга + міст — 5×15\n"
        "• Суперсет: випади + стрибки — 4×12\n"
        "• Підйом на носки — 6×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Важкі плечі</b>\n"
        "• Жим над головою — 6×8\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 6×15\n"
        "• Суперсет: зворотні + тяга до підборіддя — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки + Прес</b>\n"
        "• Суперсет: підйом на біцепс + розгинання — 5×12\n"
        "• Суперсет: молотки + розгинання однієї руки — 4×12\n"
        "• Суперсет: концентровані + відмова — 3×12\n"
        "• Скручування — 5×20\n"
        "• Планка — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: важча гумка або +повтори."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_advanced"))


@router.callback_query(F.data == "home_band_ath_v1")
async def home_band_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Гумки — Атлет — Варіант 1</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди (об'єм)</b>\n"
        "• Жим від грудей — 6×10\n"
        "• Суперсет: похилий жим + розведення верх — 5×12\n"
        "• Суперсет: розведення низ + віджимання з гумкою — 5×12\n"
        "• Суперсет: жим вузько + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина (об'єм)</b>\n"
        "• Тяга до пояса — 6×10\n"
        "• Суперсет: тяга однієї руки + зворотні — 5×12\n"
        "• Суперсет: тяга до підборіддя + шраги — 5×15\n"
        "• Суперсет: пулловер з гумкою + підйом на біцепс — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (об'єм)</b>\n"
        "• Присідання — 6×15\n"
        "• Суперсет: румунська тяга + міст — 5×15\n"
        "• Суперсет: випади + відведення назад — 5×15\n"
        "• Суперсет: стрибки + підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (об'єм)</b>\n"
        "• Жим над головою — 6×10\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 6×15\n"
        "• Суперсет: зворотні + тяга до підборіддя — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Руки (об'єм)</b>\n"
        "• Суперсет: підйом на біцепс + розгинання — 6×12\n"
        "• Суперсет: молотки + розгинання однієї руки — 5×12\n"
        "• Суперсет: концентровані + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Скручування з гумкою — 5×25\n"
        "• Планка — 5×90 сек\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Кардіо 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: важча гумка або +повтори.\n"
        "День 7 — повний відпочинок."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_athlete"))


@router.callback_query(F.data == "home_band_ath_v2")
async def home_band_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Гумки — Атлет — Варіант 2</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Жимовий день</b>\n"
        "• Жим від грудей — 6×10\n"
        "• Жим над головою — 5×10\n"
        "• Суперсет: розведення + підйом в сторони — 5×15\n"
        "• Суперсет: розгинання на трицепс + відмова — 5×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Тяговий день</b>\n"
        "• Тяга до пояса — 6×10\n"
        "• Суперсет: тяга однієї руки + зворотні — 5×12\n"
        "• Суперсет: підйом на біцепс + молотки — 5×12\n"
        "• Шраги з гумкою — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Присідання — 6×15\n"
        "• Румунська тяга — 5×12\n"
        "• Суперсет: випади + міст — 5×15\n"
        "• Суперсет: стрибки + підйом на носки — 5×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Груди + Плечі об'єм</b>\n"
        "• Суперсет: жим + розведення — 5×12\n"
        "• Суперсет: жим над головою + підйом в сторони — 5×15\n"
        "• Суперсет: зворотні + тяга до підборіддя — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Спина об'єм</b>\n"
        "• Суперсет: тяга до пояса + зворотні — 5×12\n"
        "• Суперсет: тяга однієї руки + підйом на біцепс — 5×12\n"
        "• Суперсет: молотки + концентровані — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Руки + Прес</b>\n"
        "• Суперсет: підйом на біцепс + розгинання — 6×12\n"
        "• Суперсет: молотки + розгинання однієї руки — 5×12\n"
        "• Скручування — 5×25\n"
        "• Планка — 5×90 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "День 7 — відпочинок або легке кардіо."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_athlete"))


@router.callback_query(F.data == "home_band_ath_v3")
async def home_band_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Гумки — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди максимум</b>\n"
        "• Жим від грудей — 6×10\n"
        "• Суперсет: похилий жим + розведення верх — 6×12\n"
        "• Суперсет: розведення низ + віджимання — 5×12\n\n"
        "📌 <b>День 2 — Спина максимум</b>\n"
        "• Тяга до пояса — 6×10\n"
        "• Суперсет: тяга однієї руки + зворотні — 6×12\n"
        "• Суперсет: тяга до підборіддя + шраги — 5×15\n\n"
        "📌 <b>День 3 — Ноги максимум</b>\n"
        "• Присідання — 6×15\n"
        "• Суперсет: румунська + міст — 6×15\n"
        "• Суперсет: випади + стрибки — 5×12\n"
        "• Підйом на носки — 6×25\n\n"
        "📌 <b>День 4 — Плечі максимум</b>\n"
        "• Жим над головою — 6×10\n"
        "• Суперсет: підйом в сторони + підйом перед собою — 6×15\n"
        "• Суперсет: зворотні + тяга до підборіддя — 5×15\n\n"
        "📌 <b>День 5 — Руки максимум</b>\n"
        "• Суперсет: підйом на біцепс + розгинання — 6×12\n"
        "• Суперсет: похилі підйоми + розгинання однієї руки — 5×12\n"
        "• Суперсет: молотки + концентровані — 4×12\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Скручування з гумкою — 6×25\n"
        "• Планка — 5×90 сек\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Кардіо 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: важча гумка або +повтори.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_band_athlete"))


@router.callback_query(F.data == "home_bodyweight")
async def home_bodyweight(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець",  callback_data="home_bw_beginner")],
        [InlineKeyboardButton(text="🟡 Середній",     callback_data="home_bw_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий",   callback_data="home_bw_advanced")],
        [InlineKeyboardButton(text="🔥 Атлет",        callback_data="home_bw_athlete")],
        [InlineKeyboardButton(text="← Назад",         callback_data="prog_home")],
    ])
    await callback.message.edit_text(
        "❌ <b>Вдома — Без обладнання</b>\n\nОбери рівень:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "home_bw_beginner")
async def home_bw_beginner(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟢 <b>Без обладнання — Початківець</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_bw_beg", "home_bodyweight", is_premium),
    )


@router.callback_query(F.data == "home_bw_intermediate")
async def home_bw_intermediate(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🟡 <b>Без обладнання — Середній</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_bw_int", "home_bodyweight", is_premium),
    )


@router.callback_query(F.data == "home_bw_advanced")
async def home_bw_advanced(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔴 <b>Без обладнання — Просунутий</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_bw_adv", "home_bodyweight", is_premium),
    )


@router.callback_query(F.data == "home_bw_athlete")
async def home_bw_athlete(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    is_premium = user.get("subscription") in ("premium", "standard") if user else False
    await callback.message.edit_text(
        "🔥 <b>Без обладнання — Атлет</b>\n\nОбери варіант:",
        reply_markup=variants_kb("home_bw_ath", "home_bodyweight", is_premium),
    )


@router.callback_query(F.data == "home_bw_beg_v1")
async def home_bw_beg_v1(callback: CallbackQuery):
    text = (
        "🟢 <b>Без обладнання — Початківець — Варіант 1</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Віджимання — 3×10\n"
        "• Присідання — 3×20\n"
        "• Планка — 3×30 сек\n"
        "• Випади — 3×12\n"
        "• Зворотні віджимання від стільця — 3×10\n"
        "• Скручування — 3×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60 сек між підходами.\n"
        "Фокус на техніці виконання.\n"
        "Прогресія: +2-3 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_beginner"))


@router.callback_query(F.data == "home_bw_beg_v2")
async def home_bw_beg_v2(callback: CallbackQuery):
    text = (
        "🟢 <b>Без обладнання — Початківець — Варіант 2</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День A і День Б — чергуємо</b>\n\n"
        "<b>День A — Верх тіла:</b>\n"
        "• Віджимання — 3×10\n"
        "• Зворотні віджимання від стільця — 3×10\n"
        "• Планка — 3×30 сек\n"
        "• Скручування — 3×15\n\n"
        "<b>День Б — Низ тіла:</b>\n"
        "• Присідання — 3×20\n"
        "• Випади — 3×12\n"
        "• Підйом на носки — 3×20\n"
        "• Міст — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Чергуй А і Б щотренування.\n"
        "Відпочинок 60 сек між підходами.\n"
        "Прогресія: +2-3 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_beginner"))


@router.callback_query(F.data == "home_bw_beg_v3")
async def home_bw_beg_v3(callback: CallbackQuery):
    text = (
        "🟢 <b>Без обладнання — Початківець — Варіант 3</b>\n"
        "📅 3 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>Кожне тренування — все тіло</b>\n\n"
        "• Віджимання вузьким хватом — 3×10\n"
        "• Присідання з паузою — 3×15\n"
        "• Планка — 3×30 сек\n"
        "• Берпі — 3×8\n"
        "• Скручування — 3×15\n"
        "• Підйом на носки — 3×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 60 сек між підходами.\n"
        "Берпі можна замінити стрибками.\n"
        "Прогресія: +2-3 повтори щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_beginner"))


@router.callback_query(F.data == "home_bw_int_v1")
async def home_bw_int_v1(callback: CallbackQuery):
    text = (
        "🟡 <b>Без обладнання — Середній — Варіант 1</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Верх тіла A</b>\n"
        "• Віджимання широким хватом — 4×15\n"
        "• Віджимання вузьким хватом — 4×12\n"
        "• Зворотні віджимання — 4×15\n"
        "• Планка — 4×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Низ тіла A</b>\n"
        "• Присідання з паузою — 4×20\n"
        "• Випади з кроком — 4×15\n"
        "• Міст на одній нозі — 4×15\n"
        "• Підйом на носки — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Верх тіла Б</b>\n"
        "• Віджимання з ногами на підвищенні — 4×12\n"
        "• Піку-пушап — 4×12\n"
        "• Зворотні від стільця з ногами прямо — 4×12\n"
        "• Скручування — 4×20\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Низ тіла Б</b>\n"
        "• Стрибкові присідання — 4×15\n"
        "• Болгарські присідання — 4×12\n"
        "• Міст з підйомом — 4×20\n"
        "• Берпі — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Прогресія: +2-3 повтори або ускладнення.\n"
        "Останній підхід до відмови."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_intermediate"))


@router.callback_query(F.data == "home_bw_int_v2")
async def home_bw_int_v2(callback: CallbackQuery):
    text = (
        "🟡 <b>Без обладнання — Середній — Варіант 2</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди + Трицепс</b>\n"
        "• Віджимання — 4×15\n"
        "• Віджимання з ногами на підвищенні — 4×12\n"
        "• Зворотні віджимання — 4×15\n"
        "• Суперсет: вузькі + широкі віджимання — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Ноги</b>\n"
        "• Присідання з паузою — 5×20\n"
        "• Болгарські присідання — 4×12\n"
        "• Стрибкові присідання — 4×15\n"
        "• Підйом на носки — 5×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Плечі + Прес</b>\n"
        "• Піку-пушап — 4×12\n"
        "• Відведення рук стоячи — 4×15\n"
        "• Планка — 4×60 сек\n"
        "• Скручування — 4×20\n"
        "• Підйом ніг лежачи — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Все тіло + Кардіо</b>\n"
        "• Берпі — 4×10\n"
        "• Суперсет: присідання + віджимання — 4×12\n"
        "• Суперсет: випади + зворотні — 4×12\n"
        "• Планка бокова — 3×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети без відпочинку між вправами.\n"
        "Прогресія: +2-3 повтори або ускладнення."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_intermediate"))


@router.callback_query(F.data == "home_bw_int_v3")
async def home_bw_int_v3(callback: CallbackQuery):
    text = (
        "🟡 <b>Без обладнання — Середній — Варіант 3</b>\n"
        "📅 4 дні на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1</b>\n"
        "• Віджимання — 4×15\n"
        "• Присідання — 4×20\n"
        "• Суперсет: піку-пушап + планка — 4×12\n"
        "• Скручування — 4×20\n\n"
        "📌 <b>День 2</b>\n"
        "• Віджимання з підвищенням — 4×12\n"
        "• Болгарські присідання — 4×12\n"
        "• Суперсет: зворотні + міст — 4×15\n"
        "• Підйом ніг лежачи — 4×15\n\n"
        "📌 <b>День 3</b>\n"
        "• Стрибкові присідання — 4×15\n"
        "• Віджимання вузькі — 4×12\n"
        "• Суперсет: берпі + планка — 4×10\n"
        "• Скручування з поворотом — 4×20\n\n"
        "📌 <b>День 4</b>\n"
        "• Суперсет: присідання + віджимання — 5×12\n"
        "• Суперсет: випади + зворотні — 4×12\n"
        "• Суперсет: піку + підйом ніг — 4×12\n"
        "• Планка бокова — 3×45 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети без відпочинку між вправами.\n"
        "Прогресія: ускладнення вправ щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_intermediate"))


@router.callback_query(F.data == "home_bw_adv_v1")
async def home_bw_adv_v1(callback: CallbackQuery):
    text = (
        "🔴 <b>Без обладнання — Просунутий — Варіант 1</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди</b>\n"
        "• Віджимання широким хватом — 5×20\n"
        "• Віджимання з ногами на підвищенні — 5×15\n"
        "• Суперсет: вузькі + широкі — 4×15\n"
        "• Суперсет: алмазні + відмова — 3×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина + Біцепс</b>\n"
        "• Австралійські підтягування — 5×15\n"
        "• Австралійські вузьким хватом — 4×12\n"
        "• Суперсет: зворотні віджимання + міст — 4×15\n"
        "• Підйом рук лежачи — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги</b>\n"
        "• Пістолет з допомогою — 5×8\n"
        "• Болгарські присідання — 5×12\n"
        "• Суперсет: стрибкові + міст — 5×15\n"
        "• Підйом на носки — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі</b>\n"
        "• Піку-пушап — 5×15\n"
        "• Стійка на руках біля стіни — 4×30 сек\n"
        "• Суперсет: відведення рук + планка — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Все тіло + Прес</b>\n"
        "• Суперсет: присідання + віджимання — 5×15\n"
        "• Суперсет: берпі + піку — 4×12\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Планка з підняттям руки — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 90 сек між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_advanced"))


@router.callback_query(F.data == "home_bw_adv_v2")
async def home_bw_adv_v2(callback: CallbackQuery):
    text = (
        "🔴 <b>Без обладнання — Просунутий — Варіант 2</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Важкі груди</b>\n"
        "• Віджимання з підвищенням — 6×15\n"
        "• Суперсет: широкі + вузькі — 5×15\n"
        "• Суперсет: алмазні + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Важкі ноги</b>\n"
        "• Пістолет — 5×6\n"
        "• Стрибки на підвищення — 5×10\n"
        "• Суперсет: болгарські + міст — 5×12\n"
        "• Підйом на носки — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Важкі плечі</b>\n"
        "• Стійка на руках біля стіни — 5×30 сек\n"
        "• Піку-пушап — 5×15\n"
        "• Суперсет: відведення рук + планка — 5×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Об'єм все тіло</b>\n"
        "• Суперсет: присідання + віджимання — 5×15\n"
        "• Суперсет: випади + піку — 5×12\n"
        "• Суперсет: берпі + австралійські — 4×10\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Прес</b>\n"
        "• Підйом ніг у висі (дверна рама) — 5×15\n"
        "• Скручування з поворотом — 5×20\n"
        "• Планка з підняттям — 4×12\n"
        "• Планка бокова — 4×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_advanced"))


@router.callback_query(F.data == "home_bw_adv_v3")
async def home_bw_adv_v3(callback: CallbackQuery):
    text = (
        "🔴 <b>Без обладнання — Просунутий — Варіант 3</b>\n"
        "📅 5 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди об'єм</b>\n"
        "• Суперсет: широкі + вузькі + алмазні — 5×10\n"
        "• Суперсет: похилі + горизонтальні — 5×12\n"
        "• Відмова — 3 підходи\n\n"
        "📌 <b>День 2 — Ноги об'єм</b>\n"
        "• Суперсет: пістолет + стрибки — 5×8\n"
        "• Суперсет: болгарські + міст — 5×12\n"
        "• Суперсет: берпі + підйом на носки — 5×15\n\n"
        "📌 <b>День 3 — Плечі об'єм</b>\n"
        "• Суперсет: стійка + піку — 5×12\n"
        "• Суперсет: відведення рук + планка — 5×15\n"
        "• Бокова планка — 4×60 сек\n\n"
        "📌 <b>День 4 — Сила все тіло</b>\n"
        "• Пістолет — 5×6\n"
        "• Стійка на руках — 5×30 сек\n"
        "• Австралійські — 5×12\n"
        "• Суперсет: берпі + присідання — 4×10\n\n"
        "📌 <b>День 5 — Прес + Кардіо</b>\n"
        "• Підйом ніг лежачи — 5×20\n"
        "• Скручування з поворотом — 5×25\n"
        "• Планка з підняттям — 4×12\n"
        "• Кардіо 20 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_advanced"))


@router.callback_query(F.data == "home_bw_ath_v1")
async def home_bw_ath_v1(callback: CallbackQuery):
    text = (
        "🔥 <b>Без обладнання — Атлет — Варіант 1</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди (максимум)</b>\n"
        "• Суперсет: широкі + вузькі + алмазні — 6×12\n"
        "• Суперсет: похилі + горизонтальні — 5×15\n"
        "• Суперсет: з підвищенням + відмова — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 2 — Спина (максимум)</b>\n"
        "• Австралійські широким хватом — 6×15\n"
        "• Австралійські вузьким хватом — 5×12\n"
        "• Суперсет: зворотні + міст — 5×15\n"
        "• Підйом рук лежачи — 4×15\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 3 — Ноги (максимум)</b>\n"
        "• Пістолет — 6×8\n"
        "• Суперсет: болгарські + стрибки — 5×12\n"
        "• Суперсет: міст + берпі — 5×15\n"
        "• Підйом на носки — 6×25\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 4 — Плечі (максимум)</b>\n"
        "• Стійка на руках — 6×30 сек\n"
        "• Суперсет: піку + відведення рук — 5×15\n"
        "• Суперсет: планка + бокова планка — 5×60 сек\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 5 — Все тіло (витривалість)</b>\n"
        "• Суперсет: пістолет + віджимання — 6×10\n"
        "• Суперсет: берпі + піку — 5×10\n"
        "• Суперсет: стрибки + австралійські — 4×12\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом ніг лежачи — 6×20\n"
        "• Скручування з поворотом — 5×25\n"
        "• Планка з підняттям — 5×12\n"
        "• Кардіо 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня.\n"
        "День 7 — повний відпочинок."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_athlete"))


@router.callback_query(F.data == "home_bw_ath_v2")
async def home_bw_ath_v2(callback: CallbackQuery):
    text = (
        "🔥 <b>Без обладнання — Атлет — Варіант 2</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Сила груди</b>\n"
        "• Відмова широкі — 7 підходів\n"
        "• Суперсет: похилі + алмазні — 5×12\n"
        "• Суперсет: з підвищенням + зворотні — 4×12\n\n"
        "📌 <b>День 2 — Сила ноги</b>\n"
        "• Пістолет — 7×6\n"
        "• Стрибки на підвищення — 5×10\n"
        "• Суперсет: болгарські + міст — 5×12\n"
        "• Підйом на носки — 6×25\n\n"
        "📌 <b>День 3 — Сила плечі</b>\n"
        "• Стійка на руках — 7×30 сек\n"
        "• Суперсет: піку + відведення — 5×15\n"
        "• Планка з підняттям — 5×12\n\n"
        "📌 <b>День 4 — Об'єм все тіло</b>\n"
        "• Суперсет: широкі + пістолет — 5×12\n"
        "• Суперсет: берпі + піку — 5×10\n"
        "• Суперсет: австралійські + зворотні — 4×12\n\n"
        "📌 <b>День 5 — Витривалість</b>\n"
        "• Берпі — 5×15\n"
        "• Суперсет: стрибки + присідання — 5×15\n"
        "• Суперсет: віджимання + піку — 5×12\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом ніг — 6×20\n"
        "• Скручування з поворотом — 5×25\n"
        "• Планка бокова — 5×60 сек\n"
        "• Кардіо 25 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Силові дні: відпочинок 2-3 хв.\n"
        "Об'ємні дні: відпочинок 90 сек.\n"
        "День 7 — повний відпочинок."
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_athlete"))


@router.callback_query(F.data == "home_bw_ath_v3")
async def home_bw_ath_v3(callback: CallbackQuery):
    text = (
        "🔥 <b>Без обладнання — Атлет — Варіант 3</b>\n"
        "📅 6 днів на тиждень\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📌 <b>День 1 — Груди об'єм</b>\n"
        "• Суперсет: широкі + вузькі + алмазні — 6×12\n"
        "• Суперсет: похилі + горизонтальні — 5×15\n"
        "• Відмова — 3 підходи\n\n"
        "📌 <b>День 2 — Ноги об'єм</b>\n"
        "• Суперсет: пістолет + стрибки — 6×8\n"
        "• Суперсет: болгарські + берпі — 5×10\n"
        "• Суперсет: міст + підйом на носки — 5×20\n\n"
        "📌 <b>День 3 — Плечі об'єм</b>\n"
        "• Суперсет: стійка + піку — 6×12\n"
        "• Суперсет: відведення + планка — 6×15\n"
        "• Бокова планка — 5×60 сек\n\n"
        "📌 <b>День 4 — Сила все тіло</b>\n"
        "• Пістолет — 6×6\n"
        "• Стійка на руках — 5×30 сек\n"
        "• Австралійські — 5×12\n"
        "• Суперсет: берпі + присідання — 4×12\n\n"
        "📌 <b>День 5 — Витривалість</b>\n"
        "• Суперсет: берпі + пістолет — 5×10\n"
        "• Суперсет: стрибки + піку — 5×12\n"
        "• Суперсет: віджимання + австралійські — 5×12\n\n"
        "📌 <b>День 6 — Прес + Кардіо</b>\n"
        "• Підйом ніг — 6×20\n"
        "• Скручування з поворотом — 6×25\n"
        "• Планка з підняттям — 5×12\n"
        "• Кардіо 30 хв\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 <b>Рекомендації:</b>\n"
        "Відпочинок 2 хв між підходами.\n"
        "Суперсети: 30 сек між вправами.\n"
        "Прогресія: ускладнення вправ щотижня.\n"
        "День 7 — повний відпочинок обов'язково!"
    )
    await callback.message.edit_text(text, reply_markup=back_and_menu("home_bw_athlete"))


@router.callback_query(F.data == "upgrade_premium")
async def upgrade_premium(callback: CallbackQuery):
    await callback.answer(
        "👑 Це доступно тільки з Преміум підпискою!\nОформи підписку в розділі 💳 Підписка.",
        show_alert=True,
    )


