"""Утренний отчёт по вотчлисту — через Claude CLI."""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from services.llm import LLMService
from services.watchlist import WatchlistService

logger = logging.getLogger(__name__)


async def send_morning_reports(bot: Bot, llm: LLMService, watchlist: WatchlistService):
    """Отправить утренний отчёт всем пользователям с вотчлистом."""
    users = watchlist.all_users()
    if not users:
        logger.info("Morning report: no watchlists")
        return

    today = datetime.now().strftime("%d.%m.%Y")

    for user_id, tickers in users.items():
        try:
            tickers_str = ", ".join(tickers)
            prompt = (
                f"Утренний отчёт на {today}. Акции в вотчлисте: {tickers_str}.\n\n"
                f"Для КАЖДОЙ акции:\n"
                f"1. get_price(ticker) — текущая цена и изменение\n"
                f"2. WebSearch '[компания] новости' — свежие новости (1 строка)\n"
                f"3. Ближайшие дивиденды если есть\n\n"
                f"Формат ответа — компактный, по 2-3 строки на акцию:\n"
                f"ТИКЕР: цена (изменение%)\n"
                f"Новость: ...\n"
                f"Дивиденды: ... (если скоро)\n\n"
                f"В конце: 1 строка общий вывод по рынку (ставка ЦБ, нефть)."
            )

            result = await llm.chat(user_message=prompt, session_id=None)
            answer = result.get("content", "Не удалось сформировать отчёт.")

            header = f"📊 Утренний отчёт {today}\n\n"
            await bot.send_message(user_id, header + answer, parse_mode=None)
            logger.info(f"Morning report sent to {user_id}: {len(tickers)} tickers")

        except Exception as e:
            logger.error(f"Morning report failed for {user_id}: {e}")


async def scheduler(bot: Bot, llm: LLMService, watchlist: WatchlistService,
                    hour: int = 7, minute: int = 0):
    """Планировщик: ждёт нужного времени (UTC) и запускает отчёт."""
    # 10:00 МСК = 07:00 UTC
    while True:
        now = datetime.utcnow()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= target:
            # уже прошло сегодня — ждём завтра
            target = target.replace(day=target.day + 1)

        wait_seconds = (target - now).total_seconds()
        logger.info(f"Morning report scheduler: next run in {wait_seconds / 3600:.1f} hours")
        await asyncio.sleep(wait_seconds)

        await send_morning_reports(bot, llm, watchlist)
        # после отправки подождать минуту чтобы не сработать дважды
        await asyncio.sleep(60)
