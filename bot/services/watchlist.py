"""Вотчлист + настройки утреннего отчёта. Хранится на диске."""

import json
import logging
import os

logger = logging.getLogger(__name__)

WATCHLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "watchlist.json")

# Настройки по умолчанию
DEFAULT_SETTINGS = {
    "report_enabled": False,  # выключен пока пользователь не включит
    "report_hour_msk": 10,    # 10:00 МСК
    "report_detail": "full",  # full = с анализом, brief = только цены
}


class WatchlistService:
    def __init__(self):
        self._data: dict[int, dict] = {}  # {user_id: {"tickers": [...], "settings": {...}}}
        self._load()

    def _load(self):
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for k, v in raw.items():
                    uid = int(k)
                    # Миграция: старый формат (list) → новый (dict)
                    if isinstance(v, list):
                        self._data[uid] = {"tickers": v, "settings": dict(DEFAULT_SETTINGS)}
                    else:
                        settings = dict(DEFAULT_SETTINGS)
                        settings.update(v.get("settings", {}))
                        self._data[uid] = {"tickers": v.get("tickers", []), "settings": settings}
                logger.info(f"Watchlist loaded: {len(self._data)} users")
        except Exception as e:
            logger.error(f"Failed to load watchlist: {e}")

    def _save(self):
        try:
            tmp = WATCHLIST_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in self._data.items()}, f, ensure_ascii=False, indent=2)
            os.replace(tmp, WATCHLIST_FILE)
        except Exception as e:
            logger.error(f"Failed to save watchlist: {e}")

    def _ensure_user(self, user_id: int):
        if user_id not in self._data:
            self._data[user_id] = {"tickers": [], "settings": dict(DEFAULT_SETTINGS)}

    def add(self, user_id: int, ticker: str) -> bool:
        ticker = ticker.upper()
        self._ensure_user(user_id)
        if ticker in self._data[user_id]["tickers"]:
            return False
        self._data[user_id]["tickers"].append(ticker)
        self._save()
        return True

    def remove(self, user_id: int, ticker: str) -> bool:
        ticker = ticker.upper()
        self._ensure_user(user_id)
        if ticker not in self._data[user_id]["tickers"]:
            return False
        self._data[user_id]["tickers"].remove(ticker)
        self._save()
        return True

    def get(self, user_id: int) -> list[str]:
        if user_id not in self._data:
            return []
        return self._data[user_id]["tickers"]

    def get_settings(self, user_id: int) -> dict:
        self._ensure_user(user_id)
        return self._data[user_id]["settings"]

    def set_setting(self, user_id: int, key: str, value) -> bool:
        self._ensure_user(user_id)
        if key not in DEFAULT_SETTINGS:
            return False
        self._data[user_id]["settings"][key] = value
        self._save()
        return True

    def report_users(self, hour_msk: int) -> dict[int, list[str]]:
        """Пользователи с включённым отчётом на конкретный час."""
        result = {}
        for uid, data in self._data.items():
            s = data["settings"]
            if s.get("report_enabled") and data["tickers"] and s.get("report_hour_msk") == hour_msk:
                result[uid] = data["tickers"]
        return result

    def all_report_hours(self) -> set[int]:
        """Все часы на которые есть подписки."""
        hours = set()
        for data in self._data.values():
            if data["settings"].get("report_enabled") and data["tickers"]:
                hours.add(data["settings"].get("report_hour_msk", 10))
        return hours
