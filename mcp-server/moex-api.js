/**
 * MOEX ISS API — котировки и дивиденды.
 * Бесплатно, без ключей.
 */

const MOEX_BASE = "https://iss.moex.com/iss";

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`MOEX API ${res.status}: ${url}`);
  return res.json();
}

/**
 * Текущая цена акции с MOEX.
 * @param {string} ticker — тикер (SBER, LKOH, GAZP)
 * @returns {{ ticker, price, change_pct, volume, last_trade_time }}
 */
export async function getPrice(ticker) {
  const url = `${MOEX_BASE}/engines/stock/markets/shares/boards/TQBR/securities/${ticker.toUpperCase()}.json?iss.meta=off`;
  const data = await fetchJSON(url);

  const cols = data.marketdata.columns;
  const row = data.marketdata.data[0];
  if (!row) throw new Error(`Тикер ${ticker} не найден на MOEX`);

  const get = (name) => row[cols.indexOf(name)];

  return {
    ticker: ticker.toUpperCase(),
    price: get("LAST") || get("LCLOSEPRICE"),
    change_pct: get("LASTTOPREVPRICE"),
    volume_rub: get("VALTODAY"),
    volume_shares: get("VOLTODAY"),
    open: get("OPEN"),
    high: get("HIGH"),
    low: get("LOW"),
    last_trade_time: get("SYSTIME"),
    market_cap: get("ISSUECAPITALIZATION"),
  };
}

/**
 * Дивиденды по тикеру с MOEX.
 * @param {string} ticker
 * @returns {Array<{ date, value, currency }>}
 */
export async function getDividends(ticker) {
  const url = `${MOEX_BASE}/securities/${ticker.toUpperCase()}/dividends.json?iss.meta=off`;
  const data = await fetchJSON(url);

  const cols = data.dividends.columns;
  const rows = data.dividends.data;

  return rows.map((row) => {
    const get = (name) => row[cols.indexOf(name)];
    return {
      record_date: get("registryclosedate"),
      value: get("value"),
      currency: get("currencyid"),
    };
  });
}

/**
 * Свечи за 12 месяцев (для расчёта return_12m).
 * @param {string} ticker
 * @returns {{ return_12m, price_now, price_12m_ago }}
 */
export async function getReturn12m(ticker) {
  const now = new Date();
  const yearAgo = new Date(now);
  yearAgo.setFullYear(yearAgo.getFullYear() - 1);

  const from = yearAgo.toISOString().slice(0, 10);
  const to = now.toISOString().slice(0, 10);

  const url = `${MOEX_BASE}/engines/stock/markets/shares/boards/TQBR/securities/${ticker.toUpperCase()}/candles.json?from=${from}&till=${to}&interval=31&iss.meta=off`;
  const data = await fetchJSON(url);

  const cols = data.candles.columns;
  const rows = data.candles.data;

  if (rows.length < 2) return { return_12m: null, note: "Недостаточно данных" };

  const getClose = (row) => row[cols.indexOf("close")];
  const priceOld = getClose(rows[0]);
  const priceNew = getClose(rows[rows.length - 1]);

  return {
    ticker: ticker.toUpperCase(),
    return_12m: Math.round(((priceNew - priceOld) / priceOld) * 1000) / 10,
    price_12m_ago: priceOld,
    price_now: priceNew,
    period: `${from} — ${to}`,
  };
}
