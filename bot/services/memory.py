"""Сервис памяти диалогов: in-memory (без PostgreSQL)."""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryService:
    """In-memory хранилище истории чатов."""

    def __init__(self, max_messages: int = 15):
        self.max_messages = max_messages
        self._history: dict[int, list[dict]] = defaultdict(list)

    async def get_history(self, chat_id: int, limit: int | None = None) -> list[dict]:
        """Получить последние N сообщений для чата."""
        lim = limit or self.max_messages
        return self._history[chat_id][-lim:]

    async def add_message(self, chat_id: int, role: str, content: str):
        """Сохранить сообщение в историю."""
        self._history[chat_id].append({
            "role": role,
            "content": content[:20000],
        })
        # Автообрезка
        if len(self._history[chat_id]) > self.max_messages * 2:
            self._history[chat_id] = self._history[chat_id][-self.max_messages:]

    async def clear_history(self, chat_id: int):
        """Очистить историю чата."""
        self._history[chat_id] = []

    async def get_message_count(self, chat_id: int) -> int:
        """Количество сообщений в чате."""
        return len(self._history[chat_id])
