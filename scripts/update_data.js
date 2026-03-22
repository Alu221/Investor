#!/usr/bin/env node
/**
 * Скрипт обновления companies_data.json из MOEX ISS API
 *
 * Использование:
 *   node scripts/update_data.js              # обновить все компании
 *   node scripts/update_data.js SBER LKOH    # обновить конкретные тикеры
 *
 * Что обновляет:
 *   - price (текущая цена)
 *   - mcap (капитализация)
 *   - shares_count (кол-во акций)
 *   - last_updated (дата обновления)
 *
 * API: https://iss.moex.com/ (бесплатный, без авторизации)
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const JSON_PATH = path.join(__dirname, '..', 'knowledge', 'companies_data.json');

// Маппинг имя компании → тикер MOEX
const TICKER_MAP = {
  'АЛРОСА': 'ALRS',
  'ГМК Норникель': 'GMKN',
  'Русал': 'RUAL',
  'ММК': 'MAGN',
  'НЛМК': 'NLMK',
  'Северсталь': 'CHMF',
  'ТМК': 'TRMK',
  'Полюс золото': 'PLZL',
  'Фосагро': 'PHOR',
  'Газпром': 'GAZP',
  'Новатэк': 'NVTK',
  'Роснефть': 'ROSN',
  'Газпромнефть': 'SIBN',
  'Башнефть': 'BANE',
  'ЛУКОЙЛ': 'LKOH',
  'Сургутнефтегаз': 'SNGS',
  'Татнефть': 'TATN',
  'ВК': 'VKCO',
  'Яндекс': 'YDEX',
  'БСП': 'BSPB',
  'Сбер': 'SBER',
  'ВТБ': 'VTBR',
  'Совкомбанк': 'SVCB',
  'Тинькофф': 'TCSG',
  'Х5': 'X5',
  'Магнит': 'MGNT',
  'НоваБев': 'BELU',
  'Ростелеком': 'RTKM',
  'МТС': 'MTSS',
  'Мосбиржа': 'MOEX',
  'Позитив': 'POSI',
  'Астра': 'ASTR',
  'OZON': 'OZON',
  'HeadHunter': 'HEAD',
  'ПИК': 'PIKK',
  'Самолёт': 'SMLT',
  'Аэрофлот': 'AFLT',
  'Камаз': 'KMAZ',
  'Лента': 'LENT',
  'Сегежа': 'SGZH',
  'Мечел': 'MTLR',
  'Русагро': 'AGRO',
  'Whoosh': 'WUSH',
  'Интер РАО': 'IRAO',
  'ДОМ.РФ': 'DOMR',
  'Мать и Дитя': 'MDMG',
  'Транснефть': 'TRNFP',
  'Россети': 'RSTI',
  'АФК Система': 'AFKS',
  'ЦИАН': 'CIAN'
};

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'InvestBot/1.0' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error(`Parse error: ${e.message}`)); }
      });
    }).on('error', reject);
  });
}

async function getStockData(ticker) {
  const url = `https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/${ticker}.json?iss.meta=off`;
  try {
    const data = await fetchJSON(url);
    const marketdata = data.marketdata;
    if (!marketdata || !marketdata.data || marketdata.data.length === 0) {
      // Try TQBR for preferred shares
      return null;
    }
    const cols = marketdata.columns;
    const row = marketdata.data[0];
    const get = (col) => row[cols.indexOf(col)];

    return {
      price: get('LAST') || get('LCLOSEPRICE'),
      volume: get('VALTODAY'), // оборот в рублях
      change: get('LASTTOPREVPRICE'), // изменение к предыдущему закрытию %
    };
  } catch (e) {
    console.error(`  Error fetching ${ticker}: ${e.message}`);
    return null;
  }
}

async function getSecurityInfo(ticker) {
  const url = `https://iss.moex.com/iss/securities/${ticker}.json?iss.meta=off`;
  try {
    const data = await fetchJSON(url);
    const desc = data.description;
    if (!desc || !desc.data) return null;

    const info = {};
    for (const row of desc.data) {
      if (row[0] === 'ISSUESIZE') info.shares_count = parseInt(row[2]);
      if (row[0] === 'CAPITALISATION') info.mcap = parseFloat(row[2]) / 1000000; // в млн руб
    }
    return info;
  } catch (e) {
    return null;
  }
}

async function main() {
  console.log('=== Обновление companies_data.json из MOEX ISS API ===\n');

  // Загрузить текущий JSON
  const rawData = fs.readFileSync(JSON_PATH, 'utf8');
  const data = JSON.parse(rawData);

  // Определить какие тикеры обновлять
  const args = process.argv.slice(2);
  let companiesToUpdate = data.companies;

  if (args.length > 0) {
    const tickers = args.map(t => t.toUpperCase());
    companiesToUpdate = data.companies.filter(c => {
      const ticker = TICKER_MAP[c.name];
      return ticker && tickers.includes(ticker.toUpperCase());
    });
    console.log(`Обновляю ${companiesToUpdate.length} компаний: ${tickers.join(', ')}\n`);
  } else {
    console.log(`Обновляю все ${companiesToUpdate.length} компаний...\n`);
  }

  let updated = 0;
  let errors = 0;

  for (const company of companiesToUpdate) {
    const ticker = TICKER_MAP[company.name];
    if (!ticker) {
      console.log(`  ${company.name}: тикер не найден, пропускаю`);
      continue;
    }

    process.stdout.write(`  ${company.name} (${ticker})... `);

    const stockData = await getStockData(ticker);
    if (stockData && stockData.price) {
      const oldPrice = company.price;
      company.price = stockData.price;

      // Пересчитать mcap если есть shares_count
      if (company.shares_count) {
        company.mcap = Math.round(company.shares_count * stockData.price / 1000000);
      }

      const change = oldPrice ? ((stockData.price - oldPrice) / oldPrice * 100).toFixed(1) : '?';
      console.log(`${stockData.price} руб (${change > 0 ? '+' : ''}${change}%)`);
      updated++;
    } else {
      console.log('нет данных');
      errors++;
    }

    // Пауза чтобы не спамить API
    await new Promise(r => setTimeout(r, 200));
  }

  // Обновить дату
  const today = new Date().toISOString().split('T')[0];
  data.last_updated = today;

  // Сохранить
  fs.writeFileSync(JSON_PATH, JSON.stringify(data, null, 2), 'utf8');

  console.log(`\n=== Готово ===`);
  console.log(`Обновлено: ${updated} компаний`);
  console.log(`Ошибок: ${errors}`);
  console.log(`last_updated: ${today}`);
  console.log(`Файл: ${JSON_PATH}`);
}

main().catch(console.error);
