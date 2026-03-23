"""Сборка system prompt для инвестиционного аналитика."""

import os
import datetime
import logging

logger = logging.getLogger(__name__)

# Кэш system prompt (формируется один раз при старте)
_system_prompt_cache: str = ""


def build_system_prompt(claude_md_path: str, knowledge_summary: str) -> str:
    """Собрать system prompt из CLAUDE.md + knowledge summary + дата."""
    global _system_prompt_cache

    # Читаем CLAUDE.md
    claude_md_content = ""
    if os.path.exists(claude_md_path):
        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                claude_md_content = f.read()
            logger.info(f"Loaded CLAUDE.md ({len(claude_md_content)} chars)")
        except Exception as e:
            logger.error(f"Failed to read CLAUDE.md: {e}")

    today = datetime.date.today().strftime("%d.%m.%Y")

    prompt_parts = [
        claude_md_content,
        "",
        f"## Текущая дата: {today}",
        "",
        knowledge_summary,
        "",
        "## Правила форматирования ответов в Telegram",
        "- Используй HTML-теги для форматирования: <b>жирный</b>, <i>курсив</i>, <code>моноширинный</code>",
        "- НЕ используй Markdown (**, ##, - ) — Telegram его не поддерживает в HTML-режиме",
        "- Для списков используй обычный текст с тире или нумерацией",
        "- Длинные ответы структурируй с разделителями",
        "",
        "## Доступные инструменты",
        "У тебя есть следующие инструменты:",
        "- <b>get_company_data</b> — фундаментальные данные компании из локальной базы",
        "- <b>screen_stocks</b> — скрининг акций по мультипликаторам",
        "- <b>get_stock_price</b> — текущая котировка с MOEX",
        "- <b>search_web</b> — поиск актуальной информации в интернете",
        "- <b>calculate</b> — расчёты (Graham Number, PEG, DCF, Gordon, Magic Formula)",
        "",
        "ВАЖНО: Перед анализом компании ВСЕГДА вызывай get_company_data для получения данных.",
        "Если данных нет в базе — используй search_web для поиска.",
        "Для актуальной цены — используй get_stock_price.",
    ]

    _system_prompt_cache = "\n".join(prompt_parts)
    return _system_prompt_cache


def get_system_prompt() -> str:
    """Получить кэшированный system prompt."""
    return _system_prompt_cache
