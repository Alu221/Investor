"""Вотчлист акций для утреннего отчёта. Хранится на диске."""

import json
import logging
import os

logger = logging.getLogger(__name__)

WATCHLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "watchlist.json")


class WatchlistService:
    def __init__(self):
        self._data: dict[int, list[str]] = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._data = {int(k): v for k, v in raw.items()}
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

    def add(self, user_id: int, ticker: str) -> bool:
        ticker = ticker.upper()
        if user_id not in self._data:
            self._data[user_id] = []
        if ticker in self._data[user_id]:
            return False
        self._data[user_id].append(ticker)
        self._save()
        return True

    def remove(self, user_id: int, ticker: str) -> bool:
        ticker = ticker.upper()
        if user_id not in self._data or ticker not in self._data[user_id]:
            return False
        self._data[user_id].remove(ticker)
        if not self._data[user_id]:
            del self._data[user_id]
        self._save()
        return True

    def get(self, user_id: int) -> list[str]:
        return self._data.get(user_id, [])

    def all_users(self) -> dict[int, list[str]]:
        return {uid: tickers for uid, tickers in self._data.items() if tickers}
