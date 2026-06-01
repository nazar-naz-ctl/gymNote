from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TRAINER_ID, BOT_TOKEN
from database import get_user, _load, _save

router = Router()


class ContactStates(StatesGroup):
    waiting_question = State()


async def save_question(user_id: int, question: str) -> int:
    db = await _load()
    if "questions" not in db:
        db["questions"] = []
    user = await get_user(user_id)
    sub = user.get("subscription", "free") if user else "free"
    db["questions"].append({
        "user_id":      user_id,
        "name":         user.get("name", "Невідомий") if user else "Невідомий",
        "subscription": sub,
        "question":     question,
        "answered":     False,
        "answer":       None,
    })
    await _save(db)
    position = sum(
        1 for q in db["questions"]
        if not q["answered"] and q["subscription"] == sub
    )
    return position


async def get_my_questions(user_id: int) -> list:
    db = await _load()
    return [q for q in db.get("questions", []) if q["user_id"] == user_id]


@router.callback_query(F.data == "contact_trainer")
async def contact_trainer(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написати питання", callback_data="contact_ask")],
        [InlineKeyboardButton(text="📋 Мої питання",      callback_data="contact_my")],
        [InlineKeyboardButton(text="← Назад",             callback_data="menu_trainer_contact")],
    ])
    await callback.message.edit_text(
        "📞 <b>Зв'язок з тренером</b>\n\n"
        "👑 Преміум — відповідь першою\n"
        "⭐ Стандарт — відповідь другою\n"
        "🆓 Безкоштовний — при можливості",
        reply_markup=kb,
    )


@router.callback_query(F.data == "contact_ask")
async def contact_ask(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ContactStates.waiting_question)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="contact_trainer")],
    ])
    await callback.message.edit_text(
        "💬 Введи своє питання:",
        reply_markup=kb,
    )


@router.message(ContactStates.waiting_question)
async def receive_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    question = message.text.strip()
    position = await save_question(user_id, question)
    user = await get_user(user_id)
    sub = user.get("subscription", "free") if user else "free"
    await state.clear()
    sub_text = {
        "premium":  "👑 Преміум",
        "standard": "⭐ Стандарт",
        "free":     "🆓 Безкоштовний",
    }.get(sub, "🆓")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мої питання", callback_data="contact_my")],
        [InlineKeyboardButton(text="🏠 Меню",        callback_data="main_menu")],
    ])
    await message.answer(
        f"✅ <b>Питання надіслано!</b>\n\n"
        f"Статус: {sub_text}\n"
        f"Ти #{position} в черзі",
        reply_markup=kb,
    )
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        bot = Bot(token=BOT_TOKEN,
                  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        name = user.get("name", "Невідомий") if user else "Невідомий"
        await bot.send_message(
            TRAINER_ID,
            f"📬 <b>Нове питання!</b>\n\n"
            f"Від: {name} ({sub_text})\n\n"
            f"❓ {question}",
        )
        await bot.session.close()
    except Exception:
        pass


@router.callback_query(F.data == "contact_my")
async def contact_my(callback: CallbackQuery):
    user_id = callback.from_user.id
    questions = await get_my_questions(user_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Нове питання", callback_data="contact_ask")],
        [InlineKeyboardButton(text="← Назад", callback_data="contact_trainer")],
    ])
    if not questions:
        await callback.message.edit_text(
            "📋 <b>Мої питання</b>\n\nЩе немає питань.",
            reply_markup=kb,
        )
        return
    text = "📋 <b>Мої питання</b>\n\n"
    for q in reversed(questions[-5:]):
        status = "✅ Відповідь отримана" if q["answered"] else "⏳ Очікує"
        text += f"{status}\n❓ {q['question']}\n"
        if q["answered"] and q["answer"]:
            text += f"💬 {q['answer']}\n"
        text += "\n"
    await callback.message.edit_text(text, reply_markup=kb)
    