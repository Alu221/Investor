"""Middleware rate limiting."""

import time
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Ограничение частоты сообщений: N сообщений за M секунд."""

    def __init__(self, max_messages: int = 10, window_seconds: int = 300):
        self.max_messages = max_messages
        self.window = window_seconds
        self.user_messages: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0
        now = time.time()

        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id] if now - t < self.window
        ]

        if len(self.user_messages[user_id]) >= self.max_messages:
            remaining = max(1, int(self.window - (now - self.user_messages[user_id][0])))
            logger.warning(f"Rate limit hit: user {user_id}")
            await event.answer(
                f"Слишком много сообщений. Подождите {remaining} секунд."
            )
            return None

        self.user_messages[user_id].append(now)
        return await handler(event, data)
