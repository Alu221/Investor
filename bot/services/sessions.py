"""Управление сессиями Claude Code CLI.

Сессии сохраняются на диск (sessions.json) и переживают рестарты бота.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sessions.json")


@dataclass
class UserSession:
    session_id: str | None = None
    topic: str = ""
    message_count: int = 0


@dataclass
class UserData:
    active_session: UserSession = field(default_factory=UserSession)
    saved_sessions: dict[str, UserSession] = field(default_factory=dict)


class SessionManager:
    def __init__(self):
        self._users: dict[int, UserData] = {}
        self._load()

    def _load(self):
        """Загрузить сессии с диска."""
        try:
            if os.path.exists(SESSIONS_FILE):
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid_str, udata in data.items():
                    uid = int(uid_str)
                    active = udata.get("active_session", {})
                    self._users[uid] = UserData(
                        active_session=UserSession(
                            session_id=active.get("session_id"),
                            topic=active.get("topic", ""),
                            message_count=active.get("message_count", 0),
                        ),
                        saved_sessions={
                            t: UserSession(
                                session_id=s.get("session_id"),
                                topic=s.get("topic", t),
                                message_count=s.get("message_count", 0),
                            )
                            for t, s in udata.get("saved_sessions", {}).items()
                        },
                    )
                logger.info(f"Sessions loaded: {len(self._users)} users")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")

    def _save(self):
        """Сохранить сессии на диск."""
        try:
            data = {}
            for uid, udata in self._users.items():
                data[str(uid)] = {
                    "active_session": asdict(udata.active_session),
                    "saved_sessions": {t: asdict(s) for t, s in udata.saved_sessions.items()},
                }
            tmp = SESSIONS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, SESSIONS_FILE)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _get_user(self, user_id: int) -> UserData:
        if user_id not in self._users:
            self._users[user_id] = UserData()
        return self._users[user_id]

    def get_session_id(self, user_id: int) -> str | None:
        return self._get_user(user_id).active_session.session_id

    def update_session_id(self, user_id: int, session_id: str):
        user = self._get_user(user_id)
        if user.active_session.session_id != session_id:
            user.active_session.session_id = session_id
            logger.info(f"User {user_id}: session updated to {session_id[:12]}...")
        user.active_session.message_count += 1
        self._save()

    def set_topic(self, user_id: int, topic: str):
        self._get_user(user_id).active_session.topic = topic
        self._save()

    def new_session(self, user_id: int) -> str | None:
        user = self._get_user(user_id)
        old = user.active_session
        if old.session_id and old.topic:
            user.saved_sessions[old.topic] = old
            logger.info(f"User {user_id}: saved session '{old.topic}' ({old.session_id[:12]}...)")
        user.active_session = UserSession()
        self._save()
        return old.session_id

    def switch_session(self, user_id: int, topic: str) -> str | None:
        user = self._get_user(user_id)
        old = user.active_session
        if old.session_id and old.topic:
            user.saved_sessions[old.topic] = old
        if topic in user.saved_sessions:
            user.active_session = user.saved_sessions.pop(topic)
            logger.info(f"User {user_id}: switched to '{topic}'")
            self._save()
            return user.active_session.session_id
        user.active_session = UserSession(topic=topic)
        self._save()
        return None

    def list_sessions(self, user_id: int) -> list[dict]:
        user = self._get_user(user_id)
        sessions = []
        if user.active_session.session_id:
            sessions.append({
                "topic": user.active_session.topic or "Текущая",
                "messages": user.active_session.message_count,
                "active": True,
            })
        for topic, sess in user.saved_sessions.items():
            sessions.append({
                "topic": topic,
                "messages": sess.message_count,
                "active": False,
            })
        return sessions

    def delete_session(self, user_id: int, topic: str) -> bool:
        user = self._get_user(user_id)
        if topic in user.saved_sessions:
            del user.saved_sessions[topic]
            logger.info(f"User {user_id}: deleted session '{topic}'")
            self._save()
            return True
        return False

    def clear_all(self, user_id: int):
        self._users[user_id] = UserData()
        self._save()
