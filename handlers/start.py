from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from config import TRAINER_ID
from database import user_exists, get_user, update_user_field, get_channel_link
from keyboards import role_kb, main_menu_kb, trainer_menu_kb
from handlers.registration import start_registration

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    # Зчитуємо реферальний код з посилання
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            print(f"DEBUG: referrer_id={referrer_id} for new user {user_id}")
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
                    user["subscription"] = "free"
                    await message.answer(
                        f"👋 З поверненням, {name}!\n\n"
                        f"⚠️ Твій пробний період закінчився.\n"
                        f"Ти перейшов на безкоштовний тариф.\n\n"
                        f"Обирай:",
                        reply_markup=main_menu_kb("free", channel_link=await get_channel_link()),
                    )
                    return
            except ValueError:
                pass

        await message.answer(
            f"👋 З поверненням, {name}!\n\nОбирай:",
            reply_markup=main_menu_kb(user.get("subscription", "free"), channel_link=await get_channel_link()),
        )
        return

    # Новий користувач — зберігаємо реферера перед реєстрацією
    if referrer_id:
        await state.update_data(referrer_id=referrer_id)

    await message.answer(
        "👋 Вітаємо в <b>GymNote</b>!\n\nТвій щоденник тренувань.\n\nХто ти?",
        reply_markup=role_kb(),
    )


@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.callback_query(F.data == "menu_workout")
async def menu_workout(callback: CallbackQuery):
    from database import get_user
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"

    buttons = [
        [InlineKeyboardButton(text="📋 Програми тренувань", callback_data="programs")],
        [InlineKeyboardButton(text="🔄 Повторити останнє", callback_data="repeat_last_workout")],
    ]
    if sub in ("standard", "premium"):
        buttons.append([InlineKeyboardButton(text="🛠 Конструктор", callback_data="constructor")])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="main_menu")])

    await callback.message.edit_text(
        "💪 <b>Тренування</b>\n\nОбирай:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мій профіль", callback_data="profile")],
        [InlineKeyboardButton(text="💳 Підписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="🏆 Реферали", callback_data="referral_menu")],
        [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "👤 <b>Профіль</b>\n\nОбирай:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "menu_trainer_contact")
async def menu_trainer_contact(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Від тренера", callback_data="from_trainer")],
        [InlineKeyboardButton(text="📞 Зв'язок з тренером", callback_data="contact_trainer")],
        [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "📬 <b>Тренер</b>\n\nОбирай:",
        reply_markup=kb,
    )