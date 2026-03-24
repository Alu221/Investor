/**
 * Парсинг фундаментальных данных со smart-lab.ru.
 * Без API ключей, через HTTP + cheerio.
 */

import * as cheerio from "cheerio";

// Кэш на 1 час
const cache = new Map();
const CACHE_TTL = 60 * 60 * 1000;

async function fetchHTML(url) {
  const cached = cache.get(url);
  if (cached && Date.now() - cached.time < CACHE_TTL) return cached.html;

  const res = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; InvestBot/1.0)",
      "Accept-Language": "ru-RU,ru;q=0.9",
    },
  });
  if (!res.ok) throw new Error(`smart-lab ${res.status}: ${url}`);
  const html = await res.text();
  cache.set(url, { html, time: Date.now() });
  return html;
}

// Маппинг field-атрибутов smart-lab → наши поля
const FIELD_MAP = {
  revenue: "revenue",
  operating_income: "operating_income",
  ebitda: "ebitda",
  net_income: "net_income",
  ocf: "ocf",
  capex: "capex",
  fcf: "fcf",
  assets: "total_assets",
  net_assets: "net_assets",
  debt: "total_debt",
  net_debt: "net_debt",
  cash: "cash",
  amortization: "depreciation",
  div: "dividend_per_share",
  div_yield: "div_yield_pct",
  payout: "payout_pct",
  op_expenses: "operating_expenses",
  cost: "cost_of_goods",
  staff_expenses: "personnel_expenses",
  interest_expenses: "interest_expense",
};

/**
 * Парсит годовую финотчётность МСФО со smart-lab.
 * @param {string} ticker
 * @returns {Object}
 */
export async function getFundamentals(ticker) {
  const t = ticker.toUpperCase();
  const url = `https://smart-lab.ru/q/${t}/f/y/`;
  const html = await fetchHTML(url);
  const $ = cheerio.load(html);

  const result = {
    ticker: t,
    source: "smart-lab.ru",
    period: "LTM",
    data: {},
    computed: {},
  };

  // Smart-lab использует <tr field="xxx"> с данными в <td>
  $("tr[field]").each((_, tr) => {
    const field = $(tr).attr("field");
    const ourField = FIELD_MAP[field];
    if (!ourField) return;

    // Берём все td (кроме первых двух — label и ?)
    const tds = $(tr).find("td");
    if (tds.length < 1) return;

    // Последний td = LTM или последний год
    const lastTd = $(tds[tds.length - 1]).text().trim();
    // Предпоследний — предыдущий год (если нужно)
    const prevTd = tds.length > 1 ? $(tds[tds.length - 2]).text().trim() : null;

    const value = parseNumber(lastTd);
    if (value !== null) {
      result.data[ourField] = value;
    }
  });

  // Вычисляемые поля
  const d = result.data;

  if (d.total_assets && d.net_assets) {
    result.computed.total_liabilities = round(d.total_assets - d.net_assets);
    // current_assets приближённо
    const liabilities = d.total_assets - d.net_assets;
    // Грубая оценка: оборотные ≈ 30-40% от активов для промышленных, 60-70% для ритейла
    result.computed.current_assets_approx = round(d.total_assets * 0.35);
    result.computed.current_assets_note = "Оценка. Для точных данных — МСФО отчёт.";
  }

  if (d.operating_expenses) {
    result.computed.sga_expenses_approx = d.operating_expenses;
    result.computed.sga_note = "Приблизительно = операционные расходы со smart-lab";
  }

  if (d.net_income && d.depreciation && d.ocf && d.fcf) {
    const capex = d.ocf - d.fcf;
    const maintenanceCapex = round(capex * 0.6);
    result.computed.owner_earnings = round(d.net_income + d.depreciation - maintenanceCapex);
  }

  result.computed.receivables_note = "Недоступно. Для M-Score — МСФО на e-disclosure.ru";

  return result;
}

function parseNumber(str) {
  if (!str) return null;
  const cleaned = str.replace(/\s/g, "").replace(",", ".").replace("%", "");
  const num = parseFloat(cleaned);
  return isNaN(num) ? null : num;
}

function round(n) {
  return Math.round(n * 100) / 100;
}
