"""Middleware проверки whitelist пользователей."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class WhitelistMiddleware(BaseMiddleware):
    """Блокирует сообщения от пользователей вне whitelist. Outer middleware."""

    def __init__(self, allowed_ids: list[int]):
        self.allowed_ids = set(allowed_ids)

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not self.allowed_ids:
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id not in self.allowed_ids:
            logger.warning(f"Blocked user {user_id} (not in whitelist)")
            await event.answer(
                "Доступ ограничен. Этот бот предназначен для ограниченного круга инвесторов."
            )
            return None

        return await handler(event, data)
