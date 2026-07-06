from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb(subscription: str = "free", channel_link: str = None) -> InlineKeyboardMarkup:
    buttons = []

    buttons.append([InlineKeyboardButton(text="💪 Тренування", callback_data="menu_workout")])

    if subscription in ("premium"):
        buttons.append([InlineKeyboardButton(text="📊 Мій прогрес", callback_data="progress")])

    buttons.append([InlineKeyboardButton(text="💡 Поради", callback_data="tips")])
    buttons.append([InlineKeyboardButton(text="🎵 Музика", callback_data="music_menu")])

    if subscription == "premium":
        buttons.append([InlineKeyboardButton(text="📬 Від тренера", callback_data="menu_trainer_contact")])
    else:
        buttons.append([InlineKeyboardButton(text="📬 Зв'язок з тренером", callback_data="contact_trainer")])

    buttons.append([InlineKeyboardButton(text="💬 Підтримка", callback_data="support")])
    buttons.append([InlineKeyboardButton(text="👤 Профіль", callback_data="menu_profile")])

    if channel_link:
        buttons.append([InlineKeyboardButton(text="📢 Наш канал", url=channel_link)])

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