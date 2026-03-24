#!/usr/bin/env node
/**
 * MCP-сервер moex-fundamentals
 * Инструменты: get_price, get_fundamentals, get_dividends, get_return_12m
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { getPrice, getDividends, getReturn12m } from "./moex-api.js";
import { getFundamentals } from "./smart-lab.js";

const server = new McpServer({
  name: "moex-fundamentals",
  version: "1.0.0",
});

// --- get_price ---
server.tool(
  "get_price",
  "Текущая котировка акции с MOEX. Возвращает: цена, изменение за день, объём торгов, капитализация.",
  { ticker: z.string().describe("Тикер акции (SBER, LKOH, GAZP, YNDX)") },
  async ({ ticker }) => {
    try {
      const data = await getPrice(ticker);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Ошибка: ${e.message}` }], isError: true };
    }
  }
);

// --- get_fundamentals ---
server.tool(
  "get_fundamentals",
  "Фундаментальные данные компании со smart-lab.ru: выручка, EBITDA, прибыль, активы, долг, амортизация, операционные расходы. Приблизительные: SGA, оборотные активы.",
  { ticker: z.string().describe("Тикер акции (SBER, LKOH, GAZP)") },
  async ({ ticker }) => {
    try {
      const data = await getFundamentals(ticker);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Ошибка: ${e.message}` }], isError: true };
    }
  }
);

// --- get_dividends ---
server.tool(
  "get_dividends",
  "История дивидендов компании с MOEX: даты отсечки, размер выплат.",
  { ticker: z.string().describe("Тикер акции (SBER, LKOH, GAZP)") },
  async ({ ticker }) => {
    try {
      const data = await getDividends(ticker);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Ошибка: ${e.message}` }], isError: true };
    }
  }
);

// --- get_return_12m ---
server.tool(
  "get_return_12m",
  "Доходность акции за 12 месяцев (для Momentum-анализа). Использует месячные свечи MOEX.",
  { ticker: z.string().describe("Тикер акции (SBER, LKOH, GAZP)") },
  async ({ ticker }) => {
    try {
      const data = await getReturn12m(ticker);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Ошибка: ${e.message}` }], isError: true };
    }
  }
);

// Запуск
const transport = new StdioServerTransport();
await server.connect(transport);
