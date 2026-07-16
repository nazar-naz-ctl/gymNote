from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from database import update_user_field


class ActivityMiddleware(BaseMiddleware):
    """
    Оновлює last_active користувача на кожній дії (повідомлення чи
    натискання кнопки) — незалежно від того, який саме хендлер
    обробляє подію. Дозволяє відстежувати, хто реально заходить
    у бот, а хто просто зареєстрований і не користується.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            try:
                await update_user_field(user.id, "last_active", datetime.utcnow().isoformat())
            except Exception:
                pass
        return await handler(event, data)