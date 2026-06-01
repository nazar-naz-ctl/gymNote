from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="♂ Чоловік", callback_data="reg_gender_male"),
            InlineKeyboardButton(text="♀ Жінка",   callback_data="reg_gender_female"),
        ]
    ])


def age_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="16–20", callback_data="reg_age_16-20"),
            InlineKeyboardButton(text="21–25", callback_data="reg_age_21-25"),
            InlineKeyboardButton(text="26–30", callback_data="reg_age_26-30"),
        ],
        [
            InlineKeyboardButton(text="31–35", callback_data="reg_age_31-35"),
            InlineKeyboardButton(text="36–40", callback_data="reg_age_36-40"),
            InlineKeyboardButton(text="40+",   callback_data="reg_age_40+"),
        ],
    ])


def level_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець — менше 6 місяців", callback_data="reg_level_beginner")],
        [InlineKeyboardButton(text="🟡 Середній — 6 місяців–2 роки",   callback_data="reg_level_intermediate")],
        [InlineKeyboardButton(text="🔴 Просунутий — понад 2 роки",     callback_data="reg_level_advanced")],
    ])


def goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Схуднення",      callback_data="reg_goal_weight_loss")],
        [InlineKeyboardButton(text="💪 Набір маси",     callback_data="reg_goal_muscle_gain")],
        [InlineKeyboardButton(text="✨ Рельєф і тонус", callback_data="reg_goal_toning")],
        [InlineKeyboardButton(text="🏃 Витривалість",   callback_data="reg_goal_endurance")],
        [InlineKeyboardButton(text="🏋️ Сила",          callback_data="reg_goal_strength")],
    ])


def location_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал",  callback_data="reg_location_gym")],
        [InlineKeyboardButton(text="🌳 Вулична площадка", callback_data="reg_location_outdoor")],
        [InlineKeyboardButton(text="🏠 Вдома",            callback_data="reg_location_home")],
    ])


def days_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="2 дні",  callback_data="reg_days_2"),
            InlineKeyboardButton(text="3 дні",  callback_data="reg_days_3"),
            InlineKeyboardButton(text="4 дні",  callback_data="reg_days_4"),
        ],
        [
            InlineKeyboardButton(text="5 днів", callback_data="reg_days_5"),
            InlineKeyboardButton(text="6 днів", callback_data="reg_days_6"),
        ],
    ])


def injuries_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Немає",       callback_data="reg_injuries_none")],
        [
            InlineKeyboardButton(text="🦵 Коліна",   callback_data="reg_injuries_knees"),
            InlineKeyboardButton(text="🔙 Поперек",  callback_data="reg_injuries_back"),
        ],
        [
            InlineKeyboardButton(text="🦴 Плечі",    callback_data="reg_injuries_shoulders"),
            InlineKeyboardButton(text="✏️ Написати", callback_data="reg_injuries_custom"),
        ],
    ])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Все вірно — почати!",   callback_data="reg_confirm")],
        [InlineKeyboardButton(text="✏️ Змінити стать",         callback_data="reg_edit_gender")],
        [InlineKeyboardButton(text="✏️ Змінити вік",           callback_data="reg_edit_age")],
        [InlineKeyboardButton(text="✏️ Змінити рівень",        callback_data="reg_edit_level")],
        [InlineKeyboardButton(text="✏️ Змінити ціль",          callback_data="reg_edit_goal")],
        [InlineKeyboardButton(text="✏️ Змінити локацію", callback_data="reg_edit_location")],
        [InlineKeyboardButton(text="✏️ Змінити дні тренувань", callback_data="reg_edit_days")],
        [InlineKeyboardButton(text="✏️ Змінити травми", callback_data="reg_edit_injuries")],
    ])
