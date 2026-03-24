"""ИНвестбот — инвестиционный аналитик через Claude Code CLI."""

import asyncio
import logging
import logging.handlers
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import settings
from middlewares.whitelist import WhitelistMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from handlers import commands, chat
from services.memory import MemoryService
from services.watchlist import WatchlistService
from services.morning_report import scheduler as morning_scheduler

# Логирование
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOGS_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(_LOGS_DIR, "bot.log"),
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Память
    memory = MemoryService(max_messages=settings.max_history_messages)
    dp.workflow_data["memory"] = memory

    # Вотчлист
    watchlist = WatchlistService()
    dp.workflow_data["watchlist"] = watchlist

    # Whitelist (первый — блокирует чужих до всего остального)
    if settings.allowed_ids_list:
        dp.message.middleware(WhitelistMiddleware(settings.allowed_ids_list))
        logger.info(f"Whitelist: {settings.allowed_ids_list}")
    else:
        logger.info("Whitelist: отключён (все допущены)")

    # Rate limiting
    dp.message.middleware(RateLimitMiddleware(
        settings.rate_limit_messages, settings.rate_limit_window
    ))

    # Handlers (commands первый — перехватывает /start, /help и т.д.)
    dp.include_router(commands.router)
    dp.include_router(chat.router)

    # Меню команд (кнопка ☰ в Telegram)
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="skills", description="🧠 Навыки бота"),
        BotCommand(command="sessions", description="📂 Мои темы"),
        BotCommand(command="new", description="🆕 Новая тема"),
        BotCommand(command="watch", description="👁 Добавить в вотчлист"),
        BotCommand(command="watchlist", description="📋 Мой вотчлист"),
        BotCommand(command="report", description="⚙️ Утренний отчёт"),
        BotCommand(command="help", description="📖 Справка"),
        BotCommand(command="clear", description="🗑 Очистить всё"),
    ])

    logger.info(f"ИНвестбот запущен | модель={settings.claude_model} | dir={settings.project_dir}")

    # Утренний отчёт (по настройкам каждого пользователя)
    from handlers.chat import llm
    report_task = asyncio.create_task(morning_scheduler(bot, llm, watchlist))
    logger.info("Morning report scheduler started")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"],
                               drop_pending_updates=True)
    finally:
        report_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
