"""MOEX ISS API — получение котировок с Московской биржи."""

import logging
import time

import aiohttp

logger = logging.getLogger(__name__)

# Кэш котировок (TTL = 60 сек, чтобы не спамить MOEX)
_price_cache: dict[str, dict] = {}
_PRICE_CACHE_TTL = 60  # секунд


def _get_cached_price(ticker: str) -> dict | None:
    entry = _price_cache.get(ticker.upper())
    if entry is None:
        return None
    if time.time() - entry["ts"] > _PRICE_CACHE_TTL:
        del _price_cache[ticker.upper()]
        return None
    return entry["data"]


def _cache_price(ticker: str, data: dict) -> None:
    if len(_price_cache) > 200:
        oldest = min(_price_cache, key=lambda k: _price_cache[k]["ts"])
        del _price_cache[oldest]
    _price_cache[ticker.upper()] = {"data": data, "ts": time.time()}


async def get_stock_price(ticker: str) -> dict:
    """Получить текущую котировку акции с MOEX ISS API.

    Returns:
        {"ticker": str, "price": float, "change_pct": float,
         "volume": int, "currency": str, "board": str}
    """
    ticker = ticker.upper().strip()

    # Проверяем кэш
    cached = _get_cached_price(ticker)
    if cached:
        logger.info(f"MOEX cache hit: {ticker}")
        return cached

    url = (
        f"https://iss.moex.com/iss/engines/stock/markets/shares/"
        f"boards/TQBR/securities/{ticker}.json"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {"error": f"MOEX API вернул статус {resp.status}", "ticker": ticker}
                data = await resp.json()
    except aiohttp.ClientError as e:
        logger.error(f"MOEX API connection error: {e}")
        return {"error": "Не удалось подключиться к MOEX API", "ticker": ticker}
    except Exception as e:
        logger.error(f"MOEX API error: {e}")
        return {"error": "Ошибка при запросе к MOEX API", "ticker": ticker}

    # Парсинг ответа ISS
    try:
        marketdata = data.get("marketdata", {})
        md_columns = marketdata.get("columns", [])
        md_data = marketdata.get("data", [])

        securities = data.get("securities", {})
        sec_columns = securities.get("columns", [])
        sec_data = securities.get("data", [])

        if not md_data or not sec_data:
            return {"error": f"Тикер {ticker} не найден на MOEX (TQBR)", "ticker": ticker}

        md_row = dict(zip(md_columns, md_data[0]))
        sec_row = dict(zip(sec_columns, sec_data[0]))

        price = md_row.get("LAST") or md_row.get("LCLOSEPRICE")
        open_price = md_row.get("OPEN")
        prev_close = sec_row.get("PREVPRICE")

        change_pct = None
        if price and prev_close and prev_close > 0:
            change_pct = round((price - prev_close) / prev_close * 100, 2)

        result = {
            "ticker": ticker,
            "name": sec_row.get("SHORTNAME", ticker),
            "price": price,
            "open": open_price,
            "prev_close": prev_close,
            "change_pct": change_pct,
            "volume": md_row.get("VOLTODAY"),
            "value": md_row.get("VALTODAY"),  # оборот в рублях
            "high": md_row.get("HIGH"),
            "low": md_row.get("LOW"),
            "currency": sec_row.get("CURRENCYID", "SUR"),
            "board": "TQBR",
            "update_time": md_row.get("UPDATETIME", ""),
        }

        _cache_price(ticker, result)
        logger.info(f"MOEX: {ticker} = {price}")
        return result

    except Exception as e:
        logger.error(f"MOEX parse error for {ticker}: {e}")
        return {"error": f"Ошибка парсинга данных MOEX для {ticker}", "ticker": ticker}


async def get_stock_info(ticker: str) -> dict:
    """Расширенная информация об акции (описание, сектор, лотность)."""
    ticker = ticker.upper().strip()
    url = f"https://iss.moex.com/iss/securities/{ticker}.json"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {"error": f"MOEX API вернул статус {resp.status}"}
                data = await resp.json()
    except Exception as e:
        logger.error(f"MOEX info error: {e}")
        return {"error": "Ошибка при запросе к MOEX API"}

    try:
        description = data.get("description", {})
        desc_columns = description.get("columns", [])
        desc_data = description.get("data", [])

        info = {"ticker": ticker}
        for row in desc_data:
            row_dict = dict(zip(desc_columns, row))
            name = row_dict.get("name", "")
            value = row_dict.get("value", "")
            if name == "NAME":
                info["full_name"] = value
            elif name == "SHORTNAME":
                info["short_name"] = value
            elif name == "ISIN":
                info["isin"] = value
            elif name == "ISSUESIZE":
                info["shares_count"] = value
            elif name == "FACEVALUE":
                info["face_value"] = value
            elif name == "LISTLEVEL":
                info["list_level"] = value
            elif name == "TYPENAME":
                info["type"] = value

        return info

    except Exception as e:
        logger.error(f"MOEX info parse error: {e}")
        return {"error": "Ошибка парсинга информации MOEX"}
