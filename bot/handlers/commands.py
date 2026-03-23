"""Команды с inline-кнопками, навыками и сессиями."""

import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from services.memory import MemoryService

logger = logging.getLogger(__name__)
router = Router()


# ─── Клавиатуры ───

def _main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Анализ", callback_data="menu:analyze"),
            InlineKeyboardButton(text="⚖️ Сравнить", callback_data="menu:compare"),
        ],
        [
            InlineKeyboardButton(text="🔍 Скрининг", callback_data="menu:screen"),
            InlineKeyboardButton(text="💼 Портфель", callback_data="menu:portfolio"),
        ],
        [
            InlineKeyboardButton(text="🧠 Навыки", callback_data="menu:skills"),
            InlineKeyboardButton(text="📈 Макро", callback_data="menu:macro"),
        ],
        [
            InlineKeyboardButton(text="🆕 Новая тема", callback_data="session:new"),
            InlineKeyboardButton(text="📂 Мои сессии", callback_data="session:list"),
        ],
        [
            InlineKeyboardButton(text="❓ Справка", callback_data="menu:help"),
        ],
    ])


def _skills_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Анализ компании", callback_data="skill:analyze"),
            InlineKeyboardButton(text="⚖️ Сравнение", callback_data="skill:compare"),
        ],
        [
            InlineKeyboardButton(text="🔍 Скрининг", callback_data="skill:screen"),
            InlineKeyboardButton(text="💰 DCF оценка", callback_data="skill:dcf"),
        ],
        [
            InlineKeyboardButton(text="📈 Макроанализ", callback_data="skill:macro"),
            InlineKeyboardButton(text="💼 Портфель", callback_data="skill:portfolio"),
        ],
        [
            InlineKeyboardButton(text="⚠️ Риски", callback_data="skill:risks"),
            InlineKeyboardButton(text="🎯 Сигналы", callback_data="skill:signals"),
        ],
        [
            InlineKeyboardButton(text="📋 Стратегии", callback_data="skill:strategy"),
            InlineKeyboardButton(text="💰 Дивиденды", callback_data="skill:dividends"),
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu:main"),
        ],
    ])


def _groups_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Группа 1", callback_data="group:1"),
            InlineKeyboardButton(text="✅ Группа 2", callback_data="group:2"),
        ],
        [
            InlineKeyboardButton(text="📋 Группа 3", callback_data="group:3"),
            InlineKeyboardButton(text="⚠️ Группа 4", callback_data="group:4"),
        ],
        [
            InlineKeyboardButton(text="🔴 Группа 5", callback_data="group:5"),
        ],
    ])


# ─── /start ───

@router.message(Command("start"))
async def cmd_start(message: Message, **kwargs):
    await message.answer(
        "👋 <b>Привет! Я — инвестиционный аналитик.</b>\n"
        "Специализация: российский рынок (MOEX).\n\n"
        "Просто напишите вопрос:\n"
        "• <i>Проанализируй Сбербанк</i>\n"
        "• <i>Сравни Лукойл и Роснефть</i>\n"
        "• <i>Собери портфель на 1 млн</i>\n\n"
        "Или выберите действие 👇",
        reply_markup=_main_menu_kb(),
    )


# ─── /help ───

@router.message(Command("help"))
async def cmd_help(message: Message, **kwargs):
    await message.answer(
        "<b>📖 Что я умею:</b>\n\n"
        "📊 Фундаментальный анализ 50 компаний MOEX\n"
        "⚖️ Сравнение компаний бок о бок\n"
        "🔍 Скрининг по любым критериям\n"
        "💼 Подбор портфеля под ваш профиль\n"
        "📈 Макроанализ (ставка ЦБ, нефть, рубль)\n"
        "💰 Дивиденды, DCF, Graham Number\n"
        "🌐 Поиск свежих новостей в интернете\n"
        "🧠 12 навыков (нажмите Навыки)\n\n"
        "💡 Просто пишите обычным текстом!",
        reply_markup=_main_menu_kb(),
    )


# ─── Навыки ───

@router.callback_query(F.data == "menu:skills")
async def cb_skills(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "🧠 <b>Мои навыки:</b>\n\n"
        "Каждый навык — отдельный алгоритм анализа.\n"
        "Нажмите чтобы узнать подробнее 👇",
        reply_markup=_skills_kb(),
    )
    await callback.answer()


SKILL_DESCRIPTIONS = {
    "analyze": (
        "📊 <b>Анализ компании</b>\n\n"
        "Полный разбор: МАКРО → СЕКТОР → КОМПАНИЯ\n"
        "Мультипликаторы, дивиденды, риски, вывод.\n\n"
        "<i>Пример: Проанализируй Сбербанк</i>"
    ),
    "compare": (
        "⚖️ <b>Сравнение компаний</b>\n\n"
        "Таблица мультипликаторов, финансы, дивиденды.\n"
        "Итоговый вердикт — кого покупать.\n\n"
        "<i>Пример: Сравни Лукойл и Роснефть</i>"
    ),
    "screen": (
        "🔍 <b>Скрининг акций</b>\n\n"
        "Фильтрация 50 компаний по любым критериям:\n"
        "P/E, ROE, дивиденды, долг, рост.\n\n"
        "<i>Пример: Найди акции с P/E < 5 и дивидендами > 10%</i>"
    ),
    "dcf": (
        "💰 <b>Оценка стоимости</b>\n\n"
        "DCF, Graham Number, модель Гордона, SOTP.\n"
        "Для банков — Residual Income.\n\n"
        "<i>Пример: Рассчитай справедливую цену Лукойла</i>"
    ),
    "macro": (
        "📈 <b>Макроанализ</b>\n\n"
        "Ставка ЦБ, инфляция, нефть, рубль, санкции.\n"
        "Какие секторы выигрывают/проигрывают.\n\n"
        "<i>Пример: Что будет с рынком при снижении ставки?</i>"
    ),
    "portfolio": (
        "💼 <b>Подбор портфеля</b>\n\n"
        "Под ваш профиль: горизонт, риск, сумма.\n"
        "С расчётом лотов и конкретными тикерами.\n\n"
        "<i>Пример: Консервативный портфель на 1 млн</i>"
    ),
    "risks": (
        "⚠️ <b>Оценка рисков</b>\n\n"
        "Z-Score, stress-test, матрица рисков.\n"
        "Финансовые, санкционные, политические.\n\n"
        "<i>Пример: Какие риски у Газпрома?</i>"
    ),
    "signals": (
        "🎯 <b>Сигналы покупки/продажи</b>\n\n"
        "F-Score Пиотроски, Graham Number, PEG.\n"
        "Фундаментальные + макро + циклические.\n\n"
        "<i>Пример: Есть ли сигнал покупки по Сберу?</i>"
    ),
    "strategy": (
        "📋 <b>Стратегии инвесторов</b>\n\n"
        "Баффетт, Грэм, Линч, Гринблатт, Маркс, Далио.\n"
        "Scorecard по критериям каждого.\n\n"
        "<i>Пример: Оцени Лукойл по Баффетту</i>"
    ),
    "dividends": (
        "💰 <b>Дивидендный анализ</b>\n\n"
        "Календарь, доходность, payout, гэп.\n"
        "Стратегии: до/после отсечки.\n\n"
        "<i>Пример: Топ дивидендных акций с доходностью > 10%</i>"
    ),
}


@router.callback_query(F.data.startswith("skill:"))
async def cb_skill(callback: CallbackQuery, **kwargs):
    skill = callback.data.split(":")[1]
    text = SKILL_DESCRIPTIONS.get(skill, "Навык не найден.")
    await callback.message.answer(text)
    await callback.answer()


# ─── Меню callbacks ───

@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery, **kwargs):
    await callback.message.answer("Выберите действие 👇", reply_markup=_main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:analyze")
async def cb_analyze(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "📊 <b>Анализ компании</b>\n\n"
        "Напишите название или тикер:\n"
        "• <i>Проанализируй Сбербанк</i>\n"
        "• <i>Что думаешь про Лукойл?</i>",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:compare")
async def cb_compare(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "⚖️ <b>Сравнение</b>\n\nНапишите две компании:\n"
        "• <i>Сравни Лукойл и Роснефть</i>\n"
        "• <i>Сбер vs ВТБ</i>",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:screen")
async def cb_screen(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "🔍 <b>Скрининг</b>\n\nЗадайте критерии или выберите группу 👇",
        reply_markup=_groups_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:portfolio")
async def cb_portfolio(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "💼 <b>Портфель</b>\n\nУкажите:\n"
        "• <i>Консервативный на 1 млн, 3 года</i>\n"
        "• <i>Дивидендный на пенсию</i>",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:macro")
async def cb_macro(callback: CallbackQuery, **kwargs):
    await callback.message.answer(
        "📈 <b>Макро</b>\n\nСпросите:\n"
        "• <i>Что сейчас на рынке?</i>\n"
        "• <i>Как ставка ЦБ влияет на акции?</i>",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery, **kwargs):
    await cmd_help(callback.message, **kwargs)
    await callback.answer()


# ─── Группы ───

@router.callback_query(F.data.startswith("group:"))
async def cb_group(callback: CallbackQuery, bot: Bot, **kwargs):
    group = callback.data.split(":")[1]
    from handlers.chat import process_message
    memory = kwargs.get("memory")
    await process_message(
        callback.message,
        f"Покажи все компании из группы {group} Сортировки 2026 с мультипликаторами и краткой оценкой",
        bot, memory,
    )
    await callback.answer()


# ─── /clear ───

@router.message(Command("skills"))
async def cmd_skills(message: Message, **kwargs):
    await message.answer(
        "🧠 <b>Мои навыки:</b>\n\n"
        "Каждый навык — отдельный алгоритм анализа.\n"
        "Нажмите чтобы узнать подробнее 👇",
        reply_markup=_skills_kb(),
    )


@router.message(Command("sessions"))
async def cmd_sessions(message: Message, **kwargs):
    from handlers.chat import sessions
    user_id = message.from_user.id
    sess_list = sessions.list_sessions(user_id)

    if not sess_list:
        await message.answer("Нет тем. Просто напишите вопрос!", parse_mode=None)
        return

    buttons = []
    for s in sess_list:
        marker = "▶️" if s["active"] else "💾"
        label = f"{marker} {s['topic'][:30]} ({s['messages']})"
        if not s["active"]:
            buttons.append([InlineKeyboardButton(
                text=label, callback_data=f"session:switch:{s['topic'][:30]}"
            )])
        else:
            buttons.append([InlineKeyboardButton(text=label, callback_data="session:current")])

    buttons.append([
        InlineKeyboardButton(text="🆕 Новая тема", callback_data="session:new"),
        InlineKeyboardButton(text="🗑 Очистить всё", callback_data="session:clearall"),
    ])
    await message.answer("📂 <b>Ваши темы:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.message(Command("new"))
async def cmd_new(message: Message, **kwargs):
    from handlers.chat import sessions
    user_id = message.from_user.id
    sessions.new_session(user_id)
    await message.answer("🆕 Новая тема. О чём поговорим?", parse_mode=None)


@router.message(Command("clear"))
async def cmd_clear(message: Message, **kwargs):
    memory: MemoryService | None = kwargs.get("memory")
    if memory:
        count = await memory.get_message_count(message.chat.id)
        if count == 0:
            await message.answer("История уже пуста.", parse_mode=None)
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Да", callback_data="clear:yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="clear:no"),
        ]])
        await message.answer(f"Удалить историю ({count} сообщ.)?", reply_markup=keyboard)
    else:
        await message.answer("Память недоступна.", parse_mode=None)


@router.callback_query(F.data == "clear:yes")
async def cb_clear_yes(callback: CallbackQuery, **kwargs):
    memory = kwargs.get("memory")
    if memory:
        await memory.clear_history(callback.message.chat.id)
    await callback.message.edit_text("🗑 Очищено.")
    await callback.answer()


@router.callback_query(F.data == "session:clearall")
async def cb_clearall_sessions(callback: CallbackQuery, **kwargs):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, удалить все", callback_data="session:clearall:yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="session:clearall:no"),
    ]])
    await callback.message.answer("Удалить ВСЕ темы и историю?", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "session:clearall:yes")
async def cb_clearall_yes(callback: CallbackQuery, **kwargs):
    from handlers.chat import sessions
    user_id = callback.from_user.id
    sessions.clear_all(user_id)
    memory = kwargs.get("memory")
    if memory:
        await memory.clear_history(callback.message.chat.id)
    await callback.message.edit_text("🗑 Все темы и история очищены.")
    await callback.answer()


@router.callback_query(F.data == "session:clearall:no")
async def cb_clearall_no(callback: CallbackQuery, **kwargs):
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(F.data == "clear:no")
async def cb_clear_no(callback: CallbackQuery, **kwargs):
    await callback.message.edit_text("Отменено.")
    await callback.answer()
