import asyncio
import glob
import os
import uuid

import yt_dlp
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, FSInputFile

from database import (
    add_saved_track,
    get_saved_tracks,
    get_saved_track,
    delete_saved_track,
    is_track_saved,
)
from keyboards.music import (
    music_menu_kb,
    track_actions_kb,
    search_results_kb,
    saved_tracks_kb,
)

music_router = Router()

TEMP_DIR = "temp_music"
os.makedirs(TEMP_DIR, exist_ok=True)

SEARCH_LIMIT = 100


class MusicStates(StatesGroup):
    waiting_for_query = State()


class TrackNotFoundError(Exception):
    pass


def _format_duration(seconds) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def _run_search(query: str, limit: int) -> list:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "noplaylist": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
        if not info:
            return []
        return info.get("entries") or []


async def search_tracks(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    loop = asyncio.get_event_loop()

    try:
        entries = await loop.run_in_executor(None, _run_search, query, limit)
    except Exception as e:
        print(f"[music] search failed: {e!r}")
        return []

    results = []
    for e in entries:
        if not e:
            continue
        url = e.get("url") or e.get("webpage_url")
        if not url:
            continue
        results.append({
            "url": url,
            "title": (e.get("title") or "Невідомий трек")[:80],
            "uploader": (e.get("uploader") or "Невідомий виконавець")[:60],
            "duration_str": _format_duration(e.get("duration")),
        })
    return results


def _run_download(track_url: str, out_template: str) -> dict:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(track_url, download=True)


async def download_track_by_url(track_url: str) -> tuple[str, str, str]:
    file_id = uuid.uuid4().hex
    out_template = os.path.join(TEMP_DIR, f"{file_id}.%(ext)s")

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _run_download, track_url, out_template)
    if not info:
        raise TrackNotFoundError()

    matches = glob.glob(os.path.join(TEMP_DIR, f"{file_id}.*"))
    if not matches:
        raise TrackNotFoundError()
    file_path = matches[0]

    title = (info.get("track") or info.get("title") or "Невідомий трек")[:60]
    performer = (info.get("artist") or info.get("uploader") or "Невідомий виконавець")[:60]
    return file_path, title, performer


@music_router.callback_query(F.data == "music_menu")
async def music_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎵 <b>Музика</b>\n\nШукай треки за назвою або переглядай збережені.",
        reply_markup=music_menu_kb(),
    )
    await callback.answer()


@music_router.callback_query(F.data == "music_search")
async def music_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MusicStates.waiting_for_query)
    await callback.message.edit_text("🔍 Напиши назву треку або виконавця:")
    await callback.answer()


@music_router.message(MusicStates.waiting_for_query)
async def music_search_process(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Напиши текстовий запит 🙂")
        return

    status_msg = await message.answer("🔎 Шукаю варіанти...")
    try:
        results = await search_tracks(query)
        if not results:
            await status_msg.edit_text("😔 Нічого не знайшов. Спробуй іншу назву.")
            return

        await state.update_data(search_results=results)
        await status_msg.edit_text(
            f"🔍 Знайшов {len(results)} варіантів. Обери потрібний:",
            reply_markup=search_results_kb(results, page=0),
        )
    except Exception as e:
        print(f"[music] search_process error: {e!r}")
        await status_msg.edit_text("⚠️ Помилка пошуку. Спробуй ще раз пізніше.")


@music_router.callback_query(F.data.startswith("music_page:"))
async def music_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    results = data.get("search_results") or []

    if not results:
        await callback.answer("Список застарів, шукай ще раз", show_alert=True)
        return

    await callback.message.edit_text(
        f"🔍 Знайшов {len(results)} варіантів. Обери потрібний:",
        reply_markup=search_results_kb(results, page=page),
    )
    await callback.answer()


@music_router.callback_query(F.data.startswith("music_pick:"))
async def music_pick(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    results = data.get("search_results") or []

    if index >= len(results):
        await callback.answer("Варіант більше недоступний, шукай ще раз", show_alert=True)
        return

    chosen = results[index]
    await callback.answer("⏳ Завантажую...")

    status_msg = await callback.message.answer(f"⬇️ Завантажую: {chosen['title']}...")

    file_path = None
    try:
        file_path, title, performer = await download_track_by_url(chosen["url"])
        audio = FSInputFile(file_path, filename=f"{title}.mp3")

        sent = await callback.message.answer_audio(audio=audio, title=title, performer=performer)

        already = await is_track_saved(callback.from_user.id, sent.audio.file_id)
        await sent.edit_reply_markup(reply_markup=track_actions_kb(already_saved=already))

        await status_msg.delete()
    except TrackNotFoundError:
        await status_msg.edit_text("😔 Не вдалося завантажити цей трек. Спробуй інший варіант.")
    except Exception as e:
        print(f"[music] download error: {e!r}")
        await status_msg.edit_text("⚠️ Не вдалося завантажити трек. Спробуй ще раз пізніше.")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


@music_router.callback_query(F.data == "music_save")
async def music_save(callback: CallbackQuery):
    audio = callback.message.audio
    if not audio:
        await callback.answer("Не вдалось зберегти трек", show_alert=True)
        return

    if await is_track_saved(callback.from_user.id, audio.file_id):
        await callback.answer("Вже збережено ✅")
        return

    await add_saved_track(
        user_id=callback.from_user.id,
        title=audio.title or "Невідомий трек",
        performer=audio.performer or "Невідомий виконавець",
        file_id=audio.file_id,
    )
    await callback.message.edit_reply_markup(reply_markup=track_actions_kb(already_saved=True))
    await callback.answer("Збережено в ❤️")


@music_router.callback_query(F.data == "music_save_noop")
async def music_save_noop(callback: CallbackQuery):
    await callback.answer("Вже у збережених 💚")


@music_router.callback_query(F.data == "music_saved")
async def music_saved_list(callback: CallbackQuery):
    tracks = await get_saved_tracks(callback.from_user.id)
    if not tracks:
        await callback.message.edit_text(
            "❤️ У тебе ще немає збережених треків.\n\nЗнайди трек через 🔍 Пошук і натисни ❤️.",
            reply_markup=music_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            f"❤️ <b>Збережені треки</b> ({len(tracks)})",
            reply_markup=saved_tracks_kb(tracks),
        )
    await callback.answer()


@music_router.callback_query(F.data.startswith("music_saved_play:"))
async def music_saved_play(callback: CallbackQuery):
    track_id = callback.data.split(":", 1)[1]
    track = await get_saved_track(callback.from_user.id, track_id)
    if not track:
        await callback.answer("Трек не знайдено", show_alert=True)
        return
    await callback.message.answer_audio(
        audio=track["file_id"], title=track["title"], performer=track["performer"]
    )
    await callback.answer()


@music_router.callback_query(F.data.startswith("music_saved_del:"))
async def music_saved_delete(callback: CallbackQuery):
    track_id = callback.data.split(":", 1)[1]
    if not await delete_saved_track(callback.from_user.id, track_id):
        await callback.answer("Трек не знайдено", show_alert=True)
        return

    tracks = await get_saved_tracks(callback.from_user.id)
    if not tracks:
        await callback.message.edit_text("❤️ У тебе ще немає збережених треків.", reply_markup=music_menu_kb())
    else:
        await callback.message.edit_text(
            f"❤️ <b>Збережені треки</b> ({len(tracks)})", reply_markup=saved_tracks_kb(tracks)
        )
    await callback.answer("Видалено 🗑")
