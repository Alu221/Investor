"""Поиск информации через DuckDuckGo."""

import asyncio
import logging
import time

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# In-memory кэш с TTL
_cache: dict[str, dict] = {}
_CACHE_TTL = 4 * 60 * 60  # 4 часа (финансовые данные устаревают быстрее)


def _normalize_query(query: str) -> str:
    return query.strip().lower()


def _get_from_cache(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() - entry["ts"] > _CACHE_TTL:
        del _cache[key]
        return None
    return entry["data"]


def _put_to_cache(key: str, data: list[dict]) -> None:
    if len(_cache) > 500:
        oldest = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest]
    _cache[key] = {"data": data, "ts": time.time()}


def _search_sync(full_query: str, backend: str, num_results: int) -> list[dict]:
    """Синхронный поиск через DDGS (вызывается в thread pool)."""
    ddgs = DDGS(timeout=15)
    raw = ddgs.text(
        keywords=full_query,
        region="ru-ru",
        safesearch="off",
        backend=backend,
        max_results=num_results,
    )
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in (raw or [])
    ]


async def search_web(query: str, num_results: int = 5) -> dict:
    """Поиск в интернете через DuckDuckGo.

    Бесплатный, без лимитов. Для финансовой информации.
    """
    cache_key = _normalize_query(query)
    cached = _get_from_cache(cache_key)
    if cached is not None:
        logger.info(f"DDG cache hit: {query!r}")
        return {"provider": "DuckDuckGo", "query": query, "results": cached, "cached": True}

    # Добавляем финансовый контекст к запросу
    full_query = query
    backends = ["auto", "google", "bing"]

    for attempt, backend in enumerate(backends):
        try:
            results = await asyncio.to_thread(
                _search_sync, full_query, backend, num_results
            )

            if results:
                _put_to_cache(cache_key, results)
            logger.info(f"DDG search ({backend}): {query!r} -> {len(results)} results")
            return {"provider": "DuckDuckGo", "query": query, "results": results}

        except Exception as e:
            err_name = type(e).__name__
            if "Ratelimit" in err_name or "RatelimitE" in err_name:
                logger.warning(f"DDG rate limit (backend={backend}), attempt {attempt + 1}/3")
                if attempt < len(backends) - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                return {"provider": "DuckDuckGo", "query": query, "results": [], "error": "rate_limit"}
            elif "Timeout" in err_name:
                logger.warning(f"DDG timeout (backend={backend})")
                if attempt < len(backends) - 1:
                    continue
                return {"provider": "DuckDuckGo", "query": query, "results": [], "error": "timeout"}
            else:
                logger.error(f"DDG error ({backend}): {e}", exc_info=True)
                if attempt < len(backends) - 1:
                    continue
                return {"provider": "DuckDuckGo", "query": query, "results": [], "error": "search_error"}

    return {"provider": "DuckDuckGo", "query": query, "results": []}
