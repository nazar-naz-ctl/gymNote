from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 5


def music_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Пошук треку", callback_data="music_search")
    builder.button(text="❤️ Збережені", callback_data="music_saved")
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def track_actions_kb(already_saved: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if already_saved:
        builder.button(text="💚 Збережено", callback_data="music_save_noop")
    else:
        builder.button(text="❤️ Зберегти", callback_data="music_save")
    builder.adjust(1)
    return builder.as_markup()


def search_results_kb(results: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = results[start:end]

    for i, r in enumerate(page_items, start=start):
        label = f"{r['title']} — {r['uploader']}"
        if r.get("duration_str"):
            label += f" ({r['duration_str']})"
        if len(label) > 55:
            label = label[:52] + "..."
        builder.button(text=label, callback_data=f"music_pick:{i}")

    builder.adjust(1)

    nav_row = []
    if page > 0:
        nav_row.append(("⬆️ Назад", f"music_page:{page - 1}"))
    if end < len(results):
        nav_row.append(("⬇️ Ще", f"music_page:{page + 1}"))

    for text, cb in nav_row:
        builder.button(text=text, callback_data=cb)
    if nav_row:
        builder.adjust(*([1] * len(page_items) + [len(nav_row)]))

    builder.button(text="⬅️ У меню музики", callback_data="music_menu")
    return builder.as_markup()


def saved_tracks_kb(tracks: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in tracks:
        label = f"{t['title']} — {t['performer']}"
        if len(label) > 45:
            label = label[:42] + "..."
        builder.button(text=f"▶️ {label}", callback_data=f"music_saved_play:{t['_id']}")
        builder.button(text="🗑", callback_data=f"music_saved_del:{t['_id']}")
    builder.button(text="⬅️ Назад", callback_data="music_menu")
    rows = [2] * len(tracks) + [1]
    builder.adjust(*rows)
    return builder.as_markup()