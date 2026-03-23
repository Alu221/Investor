"""Управление сессиями Claude Code CLI.

Каждый пользователь имеет активную сессию + историю сессий.
Сессии хранятся Claude Code на диске (~/.claude/projects/...).
Мы храним только session_id для каждого пользователя.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Сессия пользователя."""
    session_id: str | None = None  # UUID от Claude CLI
    topic: str = ""  # Тема сессии (определяется из первого сообщения)
    message_count: int = 0


@dataclass
class UserData:
    """Данные пользователя."""
    active_session: UserSession = field(default_factory=UserSession)
    saved_sessions: dict[str, UserSession] = field(default_factory=dict)  # topic -> session


class SessionManager:
    """Менеджер сессий для всех пользователей."""

    def __init__(self):
        self._users: dict[int, UserData] = {}

    def _get_user(self, user_id: int) -> UserData:
        if user_id not in self._users:
            self._users[user_id] = UserData()
        return self._users[user_id]

    def get_session_id(self, user_id: int) -> str | None:
        """Получить session_id для текущей сессии."""
        return self._get_user(user_id).active_session.session_id

    def update_session_id(self, user_id: int, session_id: str):
        """Обновить session_id после ответа Claude CLI."""
        user = self._get_user(user_id)
        if user.active_session.session_id != session_id:
            user.active_session.session_id = session_id
            logger.info(f"User {user_id}: session updated to {session_id[:12]}...")
        user.active_session.message_count += 1

    def set_topic(self, user_id: int, topic: str):
        """Установить тему текущей сессии."""
        self._get_user(user_id).active_session.topic = topic

    def new_session(self, user_id: int) -> str | None:
        """Создать новую сессию, сохранив старую."""
        user = self._get_user(user_id)
        old = user.active_session

        # Сохраняем старую если была
        if old.session_id and old.topic:
            user.saved_sessions[old.topic] = old
            logger.info(f"User {user_id}: saved session '{old.topic}' ({old.session_id[:12]}...)")

        # Новая пустая
        user.active_session = UserSession()
        return old.session_id

    def switch_session(self, user_id: int, topic: str) -> str | None:
        """Переключиться на сохранённую сессию по теме."""
        user = self._get_user(user_id)

        # Сохраняем текущую
        old = user.active_session
        if old.session_id and old.topic:
            user.saved_sessions[old.topic] = old

        # Ищем по теме
        if topic in user.saved_sessions:
            user.active_session = user.saved_sessions.pop(topic)
            logger.info(f"User {user_id}: switched to '{topic}'")
            return user.active_session.session_id

        # Не нашли — новая сессия
        user.active_session = UserSession(topic=topic)
        return None

    def list_sessions(self, user_id: int) -> list[dict]:
        """Список сохранённых сессий."""
        user = self._get_user(user_id)
        sessions = []

        # Текущая
        if user.active_session.session_id:
            sessions.append({
                "topic": user.active_session.topic or "Текущая",
                "messages": user.active_session.message_count,
                "active": True,
            })

        # Сохранённые
        for topic, sess in user.saved_sessions.items():
            sessions.append({
                "topic": topic,
                "messages": sess.message_count,
                "active": False,
            })

        return sessions

    def clear_all(self, user_id: int):
        """Очистить все сессии пользователя."""
        self._users[user_id] = UserData()
