"""Конфигурация бота ИНвестбот."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str

    # Claude Code OAuth token (от подписки Claude Max)
    claude_api_key: str  # CLAUDE_API_KEY в .env → передаётся как CLAUDE_CODE_OAUTH_TOKEN

    # Модель
    claude_model: str = "sonnet"

    # Memory
    max_history_messages: int = 10

    # Security
    allowed_user_ids: str = ""
    rate_limit_messages: int = 15
    rate_limit_window: int = 300

    # Папка проекта с CLAUDE.md и knowledge/
    project_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def allowed_ids_list(self) -> list[int]:
        if not self.allowed_user_ids:
            return []
        return [int(x.strip()) for x in self.allowed_user_ids.split(",") if x.strip()]


settings = Settings()
