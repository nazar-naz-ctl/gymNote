from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "tips")
async def tips_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽️ Харчування",      callback_data="tips_nutrition")],
        [InlineKeyboardButton(text="😴 Відновлення",      callback_data="tips_recovery")],
        [InlineKeyboardButton(text="📐 Техніка вправ",    callback_data="tips_technique")],
        [InlineKeyboardButton(text="⚡ До тренування",    callback_data="tips_pre")],
        [InlineKeyboardButton(text="🔋 Після тренування", callback_data="tips_post")],
        [InlineKeyboardButton(text="← Назад",             callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "💡 <b>Поради</b>\n\nОбери розділ:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "tips_nutrition")
async def tips_nutrition(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="tips")],
    ])
    await callback.message.edit_text(
        "🍽️ <b>Харчування</b>\n\n"
        "1️⃣ <b>Білок — основа</b>\n"
        "1.5-2г на кг ваги щодня.\n"
        "М'ясо, риба, яйця, сир.\n\n"
        "2️ <b>Калорії мають значення</b>\n"
        "Схуднення — дефіцит 300-500 ккал.\n"
        "Набір маси — профіцит 200-300 ккал.\n\n"
        "3️⃣ <b>Вуглеводи — паливо</b>\n"
        "Їж до і після тренування.\n"
        "Крупи, рис, картопля.\n\n"
        "4️⃣ <b>Вода</b>\n"
        "30-35мл на кг ваги щодня.\n"
        "При тренуванні +500-700мл.\n\n"
        "5️⃣ <b>Режим харчування</b>\n"
        "4-5 прийомів їжі рівномірно.\n\n"
        "6️⃣ <b>Жири теж потрібні</b>\n"
        "Авокадо, горіхи, оливкова олія.",
        reply_markup=kb,
    )


@router.callback_query(F.data == "tips_recovery")
async def tips_recovery(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="tips")],
    ])
    await callback.message.edit_text(
        "😴 <b>Відновлення</b>\n\n"
        "1️⃣ <b>Сон — головне</b>\n"
        "7-9 годин щоночі.\n\n"
        "2️ <b>Розвантажувальний тиждень</b>\n"
        "Кожні 4-6 тижнів — 50-60% від навантаження.\n\n"
        "3️⃣ <b>Активне відновлення</b>\n"
        "В дні відпочинку — прогулянки, розтяжка.\n\n"
        "4️⃣ <b>Розтяжка після тренування</b>\n"
        "10-15 хвилин стретчингу.\n\n"
        "5️⃣ <b>Холодний душ</b>\n"
        "30-60 секунд після тренування.\n\n"
        "6️⃣ <b>Не тренуй одну групу частіше 2 разів</b>\n"
        "М'язам потрібно 48-72 години.",
        reply_markup=kb,
    )


@router.callback_query(F.data == "tips_technique")
async def tips_technique(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="tips")],
    ])
    await callback.message.edit_text(
        "📐 <b>Техніка вправ</b>\n\n"
        "1️⃣ <b>Техніка важливіша за вагу</b>\n"
        "Краще менша вага з правильною технікою.\n\n"
        "2️⃣ <b>Контрольований рух</b>\n"
        "2 секунди вгору — 3 секунди вниз.\n\n"
        "3️⃣ <b>Повна амплітуда</b>\n"
        "Завжди рухайся в повній амплітуді.\n\n"
        "4️ <b>Дихання</b>\n"
        "Видих на зусиллі. Вдих на опусканні.\n\n"
        "5️⃣ <b>Розминка обов'язкова</b>\n"
        "5-10 хвилин перед тренуванням.\n\n"
        "6️⃣ <b>Відчуй м'яз</b>\n"
        "Думай про м'яз який тренуєш.",
        reply_markup=kb,
    )


@router.callback_query(F.data == "tips_pre")
async def tips_pre(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="tips")],
    ])
    await callback.message.edit_text(
        "⚡ <b>До тренування</b>\n\n"
        "1️⃣ <b>Їж за 1.5-2 години</b>\n"
        "Вуглеводи + білок.\n\n"
        "2 <b>Не тренуйся голодним</b>\n"
        "Банан і горіхи за 30 хвилин.\n\n"
        "3️⃣ <b>Вода</b>\n"
        "400-500мл за годину до тренування.\n\n"
        "4️⃣ <b>Розминка</b>\n"
        "5 хв кардіо + динамічна розтяжка.\n\n"
        "5️⃣ <b>Налаштуйся</b>\n"
        "Знай що будеш робити сьогодні.",
        reply_markup=kb,
    )

@router.callback_query(F.data == "tips_post")
async def tips_post(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="tips")],
    ])
    await callback.message.edit_text(
        "🔋 <b>Після тренування</b>\n\n"
        "1️⃣ <b>Їж протягом 30-60 хвилин</b>\n"
        "Білок + вуглеводи.\n\n"
        "2️⃣ <b>Протеїн одразу</b>\n"
        "Якщо немає часу поїсти.\n\n"
        "3️⃣ <b>Розтяжка</b>\n"
        "10-15 хвилин стретчингу.\n\n"
        "4️⃣ <b>Вода</b>\n"
        "500-700мл після тренування.\n\n"
        "5️⃣ <b>Запиши результати</b>\n"
        "Одразу внеси дані в бота.",
        reply_markup=kb,
    )