"""Разбивка длинных сообщений для Telegram (лимит 4096 символов).

Корректно закрывает/открывает HTML-теги при разбивке фрагментов.
Поддерживаемые теги: b, i, u, code, pre, a.
"""

import re

_SUPPORTED_TAGS = {"b", "i", "u", "code", "pre", "a"}
_TAG_RE = re.compile(r'<(/?)(\w+)(?:\s[^>]*)?>')


def _get_open_tags(text: str) -> list[str]:
    """Возвращает список незакрытых тегов в порядке открытия."""
    stack: list[str] = []
    for match in _TAG_RE.finditer(text):
        is_closing = match.group(1) == "/"
        tag_name = match.group(2).lower()
        if tag_name not in _SUPPORTED_TAGS:
            continue
        if is_closing:
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx] == tag_name:
                    stack.pop(idx)
                    break
        else:
            stack.append(tag_name)
    return stack


def _close_tags(open_tags: list[str]) -> str:
    return "".join(f"</{tag}>" for tag in reversed(open_tags))


def _reopen_tags(open_tags: list[str]) -> str:
    return "".join(f"<{tag}>" for tag in open_tags)


def _find_safe_split(text: str, max_pos: int) -> int:
    """Находит позицию для разрыва, не разрезая HTML-теги."""
    last_open = text.rfind('<', 0, max_pos)
    if last_open != -1:
        last_close = text.rfind('>', last_open, max_pos)
        if last_close == -1:
            return last_open
    return max_pos


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Разбивает текст на части, не превышающие max_length."""
    if not text or not text.strip():
        return []
    if len(text) <= max_length:
        return [text]

    raw_parts = []
    remaining = text

    while len(remaining) > max_length:
        effective_max = max_length - 50
        if effective_max < max_length * 0.5:
            effective_max = max_length - 20

        chunk = remaining[:effective_max]
        split_pos = None

        pos = chunk.rfind("\n\n")
        if pos > effective_max * 0.3:
            split_pos = pos + 2

        if split_pos is None:
            pos = chunk.rfind("\n")
            if pos > effective_max * 0.3:
                split_pos = pos + 1

        if split_pos is None:
            pos = chunk.rfind(". ")
            if pos > effective_max * 0.3:
                split_pos = pos + 2

        if split_pos is None:
            pos = chunk.rfind(" ")
            if pos > effective_max * 0.3:
                split_pos = pos + 1

        if split_pos is None:
            split_pos = effective_max

        split_pos = _find_safe_split(remaining, split_pos)

        raw_parts.append(remaining[:split_pos].rstrip())
        remaining = remaining[split_pos:].lstrip()

    if remaining.strip():
        raw_parts.append(remaining.strip())

    if len(raw_parts) <= 1:
        return raw_parts

    result = []
    carry_tags: list[str] = []

    for i, part in enumerate(raw_parts):
        if carry_tags:
            part = _reopen_tags(carry_tags) + part

        open_tags = _get_open_tags(part)

        if open_tags:
            part = part + _close_tags(open_tags)
            carry_tags = open_tags
        else:
            carry_tags = []

        result.append(part)

    return result
