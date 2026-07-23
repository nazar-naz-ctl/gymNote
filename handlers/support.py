from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TRAINER_ID
from database import get_user

router = Router()


class SupportStates(StatesGroup):
    waiting_bug = State()
    waiting_idea = State()
    waiting_review = State()


@router.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐛 Знайшов помилку", callback_data="support_bug")],
        [InlineKeyboardButton(text="💡 Є ідея", callback_data="support_idea")],
        [InlineKeyboardButton(text="⭐️ Залишити відгук", callback_data="support_review")],
        [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "💬 <b>Підтримка</b>\n\nОбирай:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "support_bug")
async def support_bug(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_bug)
    await callback.message.edit_text(
        "🐛 <b>Опиши помилку</b>\n\nЩо сталось? Напиши детально:",
    )


@router.callback_query(F.data == "support_idea")
async def support_idea(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_idea)
    await callback.message.edit_text(
        "💡 <b>Твоя ідея</b>\n\nОпиши що хотів би покращити або додати:",
    )


@router.callback_query(F.data == "support_review")
async def support_review(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_review)
    await callback.message.edit_text(
        "⭐️ <b>Відгук</b>\n\nНапиши свій відгук про бота:",
    )


@router.message(SupportStates.waiting_bug)
async def support_bug_send(message: Message, state: FSMContext):
    await _send_to_trainer(message, state, "🐛 Помилка")


@router.message(SupportStates.waiting_idea)
async def support_idea_send(message: Message, state: FSMContext):
    await _send_to_trainer(message, state, "💡 Ідея")


@router.message(SupportStates.waiting_review)
async def support_review_send(message: Message, state: FSMContext):
    await _send_to_trainer(message, state, "⭐️ Відгук")


async def _send_to_trainer(message: Message, state: FSMContext, category: str):
    if not message.text:
        await message.answer("✏️ Опиши текстом, будь ласка.")
        return
    user = await get_user(message.from_user.id)
    name = user.get("name", "Невідомий") if user else "Невідомий"
    sub = user.get("subscription", "free") if user else "free"
    sub_icons = {"premium": "👑", "standard": "⭐️", "free": "🆓"}

    await state.clear()

    try:
        from bot import bot
        await bot.send_message(
            TRAINER_ID,
            f"{category}\n\n"
            f"Від: {name} {sub_icons.get(sub, '🆓')}\n"
            f"ID: <code>{message.from_user.id}</code>\n\n"
            f"💬 {message.text}",
        )
    except Exception:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])
    await message.answer(
        "✅ Дякуємо! Повідомлення надіслано тренеру.",
        reply_markup=kb,
    )