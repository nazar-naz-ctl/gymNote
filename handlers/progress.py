from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_all_exercises,
    get_exercise_results,
    get_personal_record,
    save_exercise_result,
)

router = Router()


class ProgressStates(StatesGroup):
    waiting_exercise = State()
    waiting_weight   = State()
    waiting_reps     = State()


@router.callback_query(F.data == "progress")
async def progress_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Мій прогрес",       callback_data="progress_my")],
        [InlineKeyboardButton(text="➕ Записати результат", callback_data="progress_add")],
        [InlineKeyboardButton(text="🏆 Особисті рекорди",  callback_data="records_personal")],
        [InlineKeyboardButton(text="← Назад",              callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "📊 <b>Статистика і прогрес</b>\n\nОбирай:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "progress_my")
async def progress_my(callback: CallbackQuery):
    user_id = callback.from_user.id
    exercises = await get_all_exercises(user_id)
    if not exercises:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Записати перший результат", callback_data="progress_add")],
            [InlineKeyboardButton(text="← Назад", callback_data="progress")],
        ])
        await callback.message.edit_text(
            "📊 <b>Мій прогрес</b>\n\nЩе немає записів.\n"
            "Почни записувати результати після тренувань!",
            reply_markup=kb,
        )
        return
    buttons = []
    for ex in exercises:
        buttons.append([InlineKeyboardButton(
            text=f"📈 {ex}",
            callback_data=f"prog_view_{ex}",
        )])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="progress")])
    await callback.message.edit_text(
        "📊 <b>Мій прогрес</b>\n\nОбери вправу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("prog_view_"))
async def view_exercise_progress(callback: CallbackQuery):
    exercise = callback.data.replace("prog_view_", "")
    user_id = callback.from_user.id
    results = await get_exercise_results(user_id, exercise)
    record = await get_personal_record(user_id, exercise)
    if not results:
        await callback.answer("Немає результатів.", show_alert=True)
        return
    text = f"📈 <b>{exercise}</b>\n\n"
    text += f"🏆 Рекорд: {record.get('weight')}кг × {record.get('reps')} повт ({record.get('date')})\n\n"
    text += "<b>Останні результати:</b>\n"
    for r in results[-10:]:
        text += f"  {r['date']} — {r['weight']}кг × {r['reps']} повт\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="progress_my")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "progress_add")
async def progress_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProgressStates.waiting_exercise)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="progress")],
    ])
    await callback.message.edit_text(
        "➕ <b>Записати результат</b>\n\n"
        "Введи назву вправи:\n"
        "Наприклад: <i>Жим лежачи</i>",
        reply_markup=kb,
    )


@router.message(ProgressStates.waiting_exercise)
async def get_exercise_name(message: Message, state: FSMContext):
    await state.update_data(exercise=message.text.strip())
    await state.set_state(ProgressStates.waiting_weight)
    await message.answer(
        f"💪 <b>{message.text}</b>\n\n"
        f"Введи вагу в кг:\nНаприклад: <i>80</i>",
    )


@router.message(ProgressStates.waiting_weight)
async def get_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.strip().replace(",", "."))
        await state.update_data(weight=weight)
        await state.set_state(ProgressStates.waiting_reps)
        await message.answer(
            f"⚡ Вага: <b>{weight} кг</b>\n\n"
            f"Введи кількість повторів:\nНаприклад: <i>8</i>",
        )
    except ValueError:
        await message.answer("❌ Введи число. Наприклад: <i>80</i>")

    @router.message(ProgressStates.waiting_reps)
    async def get_reps(message: Message, state: FSMContext):
        try:
            reps = int(message.text.strip())
            data = await state.get_data()
            exercise = data["exercise"]
            weight = data["weight"]
            user_id = message.from_user.id
            await save_exercise_result(user_id, exercise, weight, reps)
            record = await get_personal_record(user_id, exercise)
            is_record = (
                    record.get("weight") == weight and
                    record.get("reps") == reps
            )
            await state.clear()
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Ще записати", callback_data="progress_add")],
                [InlineKeyboardButton(text="📊 Прогрес", callback_data="progress_my")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ])
            text = f"✅ <b>Записано!</b>\n\n{exercise}\n{weight}кг × {reps} повт"
            if is_record:
                text += "\n\n🏆 <b>НОВИЙ РЕКОРД!</b> 🎉"
            await message.answer(text, reply_markup=kb)
        except ValueError:
            await message.answer("❌ Введи ціле число. Наприклад: <i>8</i>")

    @router.callback_query(F.data == "records_personal")
    async def progress_records(callback: CallbackQuery):
        print(f">>> progress_records called by {callback.from_user.id}")
        user_id = callback.from_user.id
        exercises = await get_all_exercises(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="progress")],
        ])
        if not exercises:
            await callback.message.edit_text(
                "🏆 <b>Особисті рекорди</b>\n\nЩе немає записів.",
                reply_markup=kb,
            )
            return
        text = "🏆 <b>Особисті рекорди</b>\n\n"
        for ex in exercises:
            record = await get_personal_record(user_id, ex)
            if record:
                text += f"💪 {ex}\n"
                text += f"   {record['weight']}кг × {record['reps']} повт — {record['date']}\n\n"
        await callback.message.edit_text(text, reply_markup=kb)