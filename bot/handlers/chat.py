"""Обработчик сообщений с сессиями, навигацией и обновлением токена."""

import asyncio
import logging
import re

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

from config import settings
from services.llm import LLMService
from services.sessions import SessionManager
from services.memory import MemoryService
from utils.text_splitter import split_message

logger = logging.getLogger(__name__)
router = Router()

llm = LLMService(
    oauth_token=settings.claude_api_key,
    project_dir=settings.project_dir,
    model=settings.claude_model,
    anthropic_api_key=settings.anthropic_api_key,
)
sessions = SessionManager()

_KNOWN_COMMANDS = {"/start", "/help", "/clear", "/skills", "/sessions", "/new"}
_OAUTH_RE = re.compile(r"^sk-ant-(?!api)[\w]+-")
_admin_notified = False  # уведомлять админа только 1 раз


def _after_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Меню", callback_data="menu:main"),
        InlineKeyboardButton(text="🆕 Новая тема", callback_data="session:new"),
    ]])


async def _notify_admin(bot: Bot, text: str):
    """Отправить уведомление админу (один раз)."""
    global _admin_notified
    if _admin_notified or not settings.admin_user_id:
        return
    try:
        await bot.send_message(int(settings.admin_user_id), text, parse_mode=None)
        _admin_notified = True
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")


async def process_message(message: Message, text: str, bot: Bot,
                          memory: MemoryService | None = None):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else chat_id

    typing_task = asyncio.create_task(_keep_typing(bot, chat_id))

    try:
        session_id = sessions.get_session_id(user_id)
        result = await llm.chat(user_message=text, session_id=session_id)
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    answer = result["content"]
    new_session_id = result.get("session_id")

    if new_session_id:
        sessions.update_session_id(user_id, new_session_id)
        if not sessions._get_user(user_id).active_session.topic:
            sessions.set_topic(user_id, text[:40].strip())

    # Уведомление о протухшем токене
    if result.get("token_expired"):
        global _admin_notified
        fallback_note = ""
        if result.get("via_api"):
            fallback_note = "\n(Ответ через API fallback — без инструментов)"
        else:
            fallback_note = "\n(Нет API fallback — бот не может отвечать)"

        await _notify_admin(
            bot,
            f"⚠️ OAuth токен подписки истёк!{fallback_note}\n\n"
            f"Отправь новый токен (sk-ant-oat01-...) в чат бота "
            f"или обнови на сервере: claude setup-token"
        )

    if result.get("error"):
        logger.warning(f"LLM: {result['error']}")

    if memory:
        await memory.add_message(chat_id, "user", text[:2000])
        await memory.add_message(chat_id, "assistant", answer[:2000])

    # Пометка если ответ через API fallback
    if result.get("via_api"):
        answer += "\n\n⚡ Ответ через резервный канал (без инструментов анализа)"

    parts = split_message(answer, max_length=4000)
    for i, part in enumerate(parts):
        kb = _after_kb() if i == len(parts) - 1 else None
        try:
            await message.answer(part, parse_mode=None, reply_markup=kb)
        except Exception:
            try:
                await message.answer(part[:3900], parse_mode=None)
            except Exception:
                await message.answer("Ошибка отправки.", parse_mode=None)


async def _keep_typing(bot: Bot, chat_id: int):
    try:
        while True:
            await bot.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


# ─── Обновление токена через чат ───

@router.message(F.text.startswith("sk-ant-"))
async def handle_token_update(message: Message, **kwargs):
    """Принимает OAuth токен из чата, валидирует, сохраняет."""
    token = message.text.strip()

    # Проверка: это OAuth токен, не API ключ
    if not (_OAUTH_RE.match(token) and len(token) >= 40):
        await message.answer(
            "Неверный формат токена. Нужен OAuth токен подписки: sk-ant-oat01-...",
            parse_mode=None,
        )
        return

    # Проверка: только админ или whitelist
    user_id = message.from_user.id if message.from_user else 0
    allowed = not settings.allowed_ids_list or user_id in settings.allowed_ids_list
    if not allowed:
        return

    await message.answer("Проверяю токен...", parse_mode=None)

    if llm.update_oauth_token(token):
        global _admin_notified
        _admin_notified = False  # сбросить флаг уведомления

        await message.answer(
            "✅ Токен обновлён! Бот снова работает через подписку.\n"
            "Удалите сообщение с токеном из чата.",
            parse_mode=None,
        )
        logger.info(f"Token updated by user {user_id}")

        # Удалить сообщение с токеном (безопасность)
        try:
            await message.delete()
        except Exception:
            pass
    else:
        await message.answer("❌ Токен не прошёл проверку формата.", parse_mode=None)


# ─── Сессии ───

@router.callback_query(F.data == "session:new")
async def cb_new_session(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    sessions.new_session(user_id)
    await callback.message.answer("🆕 Новая тема. О чём поговорим?", parse_mode=None)
    await callback.answer()


@router.callback_query(F.data == "session:list")
async def cb_list_sessions(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    sess_list = sessions.list_sessions(user_id)

    if not sess_list:
        await callback.message.answer("Нет сохранённых тем. Просто напишите вопрос!", parse_mode=None)
        await callback.answer()
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

    buttons.append([InlineKeyboardButton(text="🆕 Новая тема", callback_data="session:new")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer("📂 <b>Ваши темы:</b>", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("session:switch:"))
async def cb_switch_session(callback: CallbackQuery, **kwargs):
    topic = callback.data.replace("session:switch:", "")
    user_id = callback.from_user.id
    session_id = sessions.switch_session(user_id, topic)
    if session_id:
        await callback.message.answer(f"📂 Переключено на: {topic}", parse_mode=None)
    else:
        await callback.message.answer(f"Тема '{topic}' не найдена. Создана новая.", parse_mode=None)
    await callback.answer()


@router.callback_query(F.data == "session:current")
async def cb_current(callback: CallbackQuery, **kwargs):
    await callback.answer("Это текущая тема")


# ─── Текст ───

@router.message(F.text)
async def handle_text(message: Message, bot: Bot, **kwargs):
    text = (message.text or "").strip()
    if not text:
        return

    if text.startswith("/"):
        cmd = text.split()[0].split("@")[0].lower()
        if cmd in _KNOWN_COMMANDS:
            return

    user = message.from_user
    logger.info(f"[{user.full_name if user else '?'}] {text[:100]}")
    memory = kwargs.get("memory")
    await process_message(message, text, bot, memory)


@router.message(F.voice | F.video_note)
async def handle_voice(message: Message, **kwargs):
    await message.answer("Голосовые пока не поддерживаются.", parse_mode=None)
