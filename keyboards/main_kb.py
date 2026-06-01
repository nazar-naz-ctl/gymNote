from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb(subscription: str = "free") -> InlineKeyboardMarkup:
    buttons = []

    # Тренування — всім
    buttons.append([InlineKeyboardButton(text="💪 Тренування", callback_data="menu_workout")])

    # Прогрес — стандарт і преміум
    if subscription in ("standard", "premium"):
        buttons.append([InlineKeyboardButton(text="📊 Мій прогрес", callback_data="progress")])

    # Поради — всім
    buttons.append([InlineKeyboardButton(text="💡 Поради", callback_data="tips")])

    # Від тренера — преміум
    if subscription == "premium":
        buttons.append([InlineKeyboardButton(text="📬 Від тренера", callback_data="menu_trainer_contact")])
    else:
        buttons.append([InlineKeyboardButton(text="📬 Зв'язок з тренером", callback_data="contact_trainer")])

    # Профіль — всім
    buttons.append([InlineKeyboardButton(text="💬 Підтримка", callback_data="support")])
    buttons.append([InlineKeyboardButton(text="👤 Профіль", callback_data="menu_profile")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def trainer_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Мої клієнти",         callback_data="t_clients")],
        [InlineKeyboardButton(text="✍️ Скласти тренування",  callback_data="t_create_workout2")],
        [InlineKeyboardButton(text="📬 Вхідні повідомлення", callback_data="t_inbox")],
        [InlineKeyboardButton(text="📊 Статистика",          callback_data="t_stats")],
        [InlineKeyboardButton(text="💳 Підписки",            callback_data="t_subscriptions")],
        [InlineKeyboardButton(text="⚙️ Налаштування",        callback_data="t_settings")],
    ])


def role_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Я клієнт", callback_data="role_client")],
        [InlineKeyboardButton(text="🏋 Я тренер", callback_data="role_trainer")],
    ])


def back_kb(cb: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data=cb)],
    ])