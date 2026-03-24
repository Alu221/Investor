"""LLM сервис: Claude Code CLI (stream-json) с сессиями. Python 3.10+."""

import asyncio
import json
import logging
import os
import pathlib

logger = logging.getLogger(__name__)


def _read_fresh_token() -> str | None:
    """Читает свежий OAuth токен из credentials Claude Code CLI."""
    home = pathlib.Path.home()
    paths_and_keys = [
        (home / ".claude" / ".credentials.json", ("claudeAiOauth", "accessToken")),
        (home / ".claude" / "credentials.json", ("claudeAiOauth", "accessToken")),
        (home / ".claude.json", ("oauthToken",)),
    ]
    for path, keys in paths_and_keys:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            val = data
            for k in keys:
                val = val.get(k, {}) if isinstance(val, dict) else None
                if val is None:
                    break
            if val and isinstance(val, str) and val.startswith("sk-ant-"):
                return val
        except Exception:
            continue
    return None


class LLMService:
    def __init__(self, oauth_token: str, project_dir: str,
                 model: str = "sonnet", max_turns: int = 25):
        self.fallback_token = oauth_token
        self.project_dir = project_dir
        self.model = model
        self.max_turns = max_turns

    def _get_token(self) -> str:
        fresh = _read_fresh_token()
        if fresh:
            logger.info(f"Token: fresh from credentials (..{fresh[-8:]})")
            return fresh
        logger.info(f"Token: fallback from .env (..{self.fallback_token[-8:]})")
        return self.fallback_token

    async def chat(self, user_message: str, session_id: str | None = None,
                   append_prompt: str = "") -> dict:
        return await self._call_claude(user_message, session_id, append_prompt)

    async def _call_claude(self, user_message: str, session_id: str | None = None,
                           append_prompt: str = "") -> dict:
        token = self._get_token()

        env = {}
        for key in ["PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "TEMP", "TMP",
                     "APPDATA", "LOCALAPPDATA", "PROGRAMFILES", "HOMEDRIVE",
                     "HOMEPATH", "XDG_CONFIG_HOME", "NODE_PATH"]:
            if key in os.environ:
                env[key] = os.environ[key]

        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
        env["CI"] = "1"
        env["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "90"

        tg_fmt = (
            "ФОРМАТ: Telegram чат. Plain text, без markdown (**, ##, ```). "
            "Структура: переносы, тире, нумерация, эмодзи. "
            "Компактно, до 3000 символов. Дисклеймер в конце анализа. "
            "Если вопрос непонятен — уточни у пользователя, не отвечай наугад."
        )
        full_append = tg_fmt + (" " + append_prompt if append_prompt else "")

        cmd = [
            "claude", "-p", user_message,
            "--output-format", "stream-json",
            "--verbose",
            "--max-turns", str(self.max_turns),
            "--model", self.model,
            "--permission-mode", "acceptEdits",
            "--allowedTools", "Bash,WebSearch,WebFetch,Read,Glob,Grep",
            "--disallowedTools", "Bash(rm -rf *),Bash(sudo *)",
            "--append-system-prompt", full_append,
        ]
        if session_id:
            cmd.extend(["--resume", session_id])

        logger.info(f"CLI: '{user_message[:60]}...' session={'resume' if session_id else 'new'}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                cwd=self.project_dir, env=env,
            )

            result_text = ""
            assistant_text = ""
            new_session_id = None
            tools_used = []

            # Python 3.10 compatible — no asyncio.timeout
            deadline = asyncio.get_event_loop().time() + 1800  # 30 мин
            try:
                while True:
                    remaining = deadline - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        raise asyncio.TimeoutError()
                    try:
                        line_bytes = await asyncio.wait_for(
                            process.stdout.readline(), timeout=min(remaining, 30)
                        )
                    except asyncio.TimeoutError:
                        if process.returncode is not None:
                            break
                        continue
                    if not line_bytes:
                        break

                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        etype = event.get("type", "")
                        if etype == "system" and event.get("subtype") == "init":
                            new_session_id = event.get("session_id")
                        elif etype == "assistant":
                            for block in event.get("message", {}).get("content", []):
                                if block.get("type") == "text":
                                    assistant_text += block.get("text", "")
                        elif etype == "tool":
                            tools_used.append(event.get("name", "?"))
                        elif etype == "result":
                            result_text = event.get("result", "")
                            if not new_session_id:
                                new_session_id = event.get("session_id")
                    except json.JSONDecodeError:
                        continue

            except asyncio.TimeoutError:
                logger.error("Timeout 1800s")
                try:
                    process.kill()
                except Exception:
                    pass
                return {
                    "content": assistant_text or "Таймаут. Попробуйте короче.",
                    "session_id": new_session_id, "error": "timeout"
                }

            await process.wait()

            # stderr
            try:
                stderr_bytes = await asyncio.wait_for(process.stderr.read(), timeout=5)
                stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            except Exception:
                stderr_text = ""

            final = result_text or assistant_text

            if not final:
                if stderr_text:
                    logger.error(f"stderr: {stderr_text[:300]}")
                    if "401" in stderr_text or "expired" in stderr_text.lower():
                        return {"content": "Токен истёк. Обновите.", "session_id": None, "error": "expired"}
                    if "429" in stderr_text or "rate" in stderr_text.lower():
                        return {"content": "Лимит. Подождите 5 мин.", "session_id": None, "error": "rate"}
                # Если совсем пусто — попросить переформулировать
                return {
                    "content": "Не удалось получить ответ. Попробуйте переформулировать вопрос или уточнить что именно хотите узнать.",
                    "session_id": new_session_id, "error": "empty"
                }

            if tools_used:
                logger.info(f"Tools: {', '.join(tools_used)}")
            logger.info(f"OK: {len(final)} chars")
            return {"content": final, "session_id": new_session_id, "error": None}

        except FileNotFoundError:
            return {"content": "Claude CLI не найден на сервере.", "session_id": None, "error": "not_found"}
        except Exception as e:
            logger.error(f"Exception: {e}", exc_info=True)
            return {"content": "Ошибка. Попробуйте позже.", "session_id": None, "error": str(e)}
