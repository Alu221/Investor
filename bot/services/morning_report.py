"""Утренний отчёт по вотчлисту — через Claude CLI."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from aiogram import Bot

from services.llm import LLMService
from services.watchlist import WatchlistService

logger = logging.getLogger(__name__)

MSK = timezone(timedelta(hours=3))


async def send_morning_reports(bot: Bot, llm: LLMService, watchlist: WatchlistService, hour_msk: int):
    """Отправить отчёт пользователям с включённым отчётом на этот час."""
    users = watchlist.report_users(hour_msk)
    if not users:
        return

    today = datetime.now(MSK).strftime("%d.%m.%Y")

    for user_id, tickers in users.items():
        try:
            settings = watchlist.get_settings(user_id)
            detail = settings.get("report_detail", "full")
            tickers_str = ", ".join(tickers)

            if detail == "brief":
                prompt = (
                    f"Утренний отчёт {today}. Акции: {tickers_str}.\n"
                    f"Для каждой: get_price(ticker). Формат:\n"
                    f"ТИКЕР: цена (изменение%)\n"
                    f"Кратко, без анализа."
                )
            else:
                prompt = (
                    f"Утренний отчёт {today}. Акции: {tickers_str}.\n\n"
                    f"Для КАЖДОЙ акции:\n"
                    f"1. get_price(ticker) — цена и изменение\n"
                    f"2. WebSearch '[компания] новости' — 1 строка свежих новостей\n"
                    f"3. Ближайшие дивиденды если скоро\n\n"
                    f"Формат — компактный, 2-3 строки на акцию.\n"
                    f"В конце: 1 строка общий вывод (ставка ЦБ, нефть)."
                )

            result = await llm.chat(user_message=prompt, session_id=None)
            answer = result.get("content", "Не удалось сформировать отчёт.")

            header = f"📊 Утренний отчёт {today}\n\n"
            await bot.send_message(user_id, header + answer, parse_mode=None)
            logger.info(f"Morning report sent to {user_id}: {len(tickers)} tickers ({detail})")

        except Exception as e:
            logger.error(f"Morning report failed for {user_id}: {e}")


async def scheduler(bot: Bot, llm: LLMService, watchlist: WatchlistService):
    """Планировщик: проверяет каждый час, есть ли отчёты на отправку."""
    while True:
        now = datetime.now(MSK)
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        wait = (next_hour - now).total_seconds()
        logger.info(f"Report scheduler: next check at {next_hour.strftime('%H:%M')} MSK ({wait / 60:.0f} min)")
        await asyncio.sleep(wait)

        current_hour = datetime.now(MSK).hour
        users = watchlist.report_users(current_hour)
        if users:
            logger.info(f"Report scheduler: {len(users)} users at {current_hour}:00 MSK")
            await send_morning_reports(bot, llm, watchlist, current_hour)
