from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)


def main_reply_kb() -> ReplyKeyboardMarkup:
    """Головне меню User App — персистентна Reply-клавіатура над полем
    вводу. 4 кнопки за узгодженою Target Architecture:
    Створити програму / Почати тренування / Мій прогрес / Профіль."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏋️ Створити програму"), KeyboardButton(text="▶️ Почати тренування")],
            [KeyboardButton(text="📊 Мій прогрес"), KeyboardButton(text="👤 Профіль")],
        ],
        resize_keyboard=True,
    )


def trainer_menu_kb() -> InlineKeyboardMarkup:
    """Trainer Panel — 5 кнопок за узгодженою Target Architecture:
    Dashboard / Клієнти / Програми / Повідомлення / Статистика."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Dashboard",     callback_data="t_dashboard")],
        [InlineKeyboardButton(text="👥 Клієнти",       callback_data="t_clients")],
        [InlineKeyboardButton(text="🏋️ Програми",      callback_data="t_programs")],
        [InlineKeyboardButton(text="📬 Повідомлення",  callback_data="t_inbox")],
        [InlineKeyboardButton(text="📈 Статистика",    callback_data="t_stats")],
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