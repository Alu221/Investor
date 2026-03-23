"""Определения tools для Claude (Anthropic format)."""

SEARCH_WEB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Поиск актуальной информации в интернете через DuckDuckGo. "
            "Используй для поиска свежих новостей, котировок, аналитики, "
            "дивидендных новостей, решений ЦБ, макроданных."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос на русском",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Количество результатов (1-10, по умолч. 5)",
                },
            },
            "required": ["query"],
        },
    },
}

GET_STOCK_PRICE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": (
            "Получить текущую котировку акции с MOEX (Московская биржа). "
            "Возвращает: цену, изменение за день, объём торгов. "
            "Тикер в формате MOEX: SBER, LKOH, GAZP и т.д."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Тикер акции на MOEX (напр. SBER, LKOH, GAZP)",
                },
            },
            "required": ["ticker"],
        },
    },
}

GET_COMPANY_DATA_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_company_data",
        "description": (
            "Получить фундаментальные данные компании из локальной базы: "
            "мультипликаторы (P/E, P/B, EV/EBITDA, ROE, ND/EBITDA), "
            "финансовые показатели (выручка, EBITDA, чистая прибыль, FCF), "
            "дивиденды, капитализация. "
            "Работает по имени компании или тикеру. "
            "ИСПОЛЬЗУЙ для анализа компании перед ответом."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": (
                        "Имя компании (Сбер, Лукойл, Газпром) "
                        "или тикер (SBER, LKOH, GAZP)"
                    ),
                },
            },
            "required": ["company_name"],
        },
    },
}

SCREEN_STOCKS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "screen_stocks",
        "description": (
            "Скрининг акций по фундаментальным критериям из локальной базы (~30 компаний). "
            "Фильтрация по: P/E, ROE, ND/EBITDA, дивидендной доходности, EV/EBITDA, сектору. "
            "ИСПОЛЬЗУЙ когда пользователь просит найти недооценённые акции, "
            "подобрать дивидендные бумаги, отфильтровать по мультипликаторам."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "p_e_max": {
                    "type": "number",
                    "description": "Максимальный P/E (напр. 10)",
                },
                "p_e_min": {
                    "type": "number",
                    "description": "Минимальный P/E (напр. 2, чтобы отсечь подозрительно дешёвые)",
                },
                "roe_min": {
                    "type": "number",
                    "description": "Минимальный ROE (напр. 0.15 = 15%)",
                },
                "nd_ebitda_max": {
                    "type": "number",
                    "description": "Максимальный ND/EBITDA (напр. 2.0)",
                },
                "div_yield_min": {
                    "type": "number",
                    "description": "Минимальная дивидендная доходность (напр. 0.08 = 8%)",
                },
                "ev_ebitda_max": {
                    "type": "number",
                    "description": "Максимальный EV/EBITDA (напр. 6)",
                },
                "sector": {
                    "type": "string",
                    "description": (
                        "Сектор: Нефтегаз, Банки, Черная металлургия, "
                        "Цветная металлургия, Ритейл, Связь, Интернет, "
                        "Золотодобыча, Удобрения"
                    ),
                },
            },
        },
    },
}

CALCULATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "Инвестиционный калькулятор: расчёты по формулам фундаментального анализа. "
            "Типы расчётов: graham_number (число Грэма), peg (PEG ratio), "
            "dcf_simple (упрощённый DCF), div_discount (модель Гордона), "
            "magic_formula (Greenblatt ROIC + EY). "
            "ИСПОЛЬЗУЙ для количественных расчётов по запросу пользователя."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "calculation": {
                    "type": "string",
                    "enum": ["graham_number", "peg", "dcf_simple", "div_discount", "magic_formula"],
                    "description": "Тип расчёта",
                },
                "eps": {
                    "type": "number",
                    "description": "Прибыль на акцию (EPS) — для graham_number, peg",
                },
                "bvps": {
                    "type": "number",
                    "description": "Балансовая стоимость на акцию (BVPS) — для graham_number",
                },
                "pe_ratio": {
                    "type": "number",
                    "description": "Текущий P/E — для peg",
                },
                "growth_rate": {
                    "type": "number",
                    "description": "Ожидаемый темп роста EPS в % — для peg, dcf_simple",
                },
                "fcf": {
                    "type": "number",
                    "description": "Свободный денежный поток (FCF) в млн руб — для dcf_simple",
                },
                "discount_rate": {
                    "type": "number",
                    "description": "Ставка дисконтирования в % (напр. 18) — для dcf_simple",
                },
                "terminal_growth": {
                    "type": "number",
                    "description": "Терминальный темп роста в % (напр. 3) — для dcf_simple",
                },
                "shares_count": {
                    "type": "number",
                    "description": "Количество акций (для расчёта цены на акцию) — для dcf_simple",
                },
                "years": {
                    "type": "integer",
                    "description": "Горизонт прогноза в годах (по умолч. 5) — для dcf_simple",
                },
                "dividend": {
                    "type": "number",
                    "description": "Ожидаемый дивиденд на акцию — для div_discount",
                },
                "required_return": {
                    "type": "number",
                    "description": "Требуемая доходность в % — для div_discount",
                },
                "div_growth": {
                    "type": "number",
                    "description": "Темп роста дивидендов в % — для div_discount",
                },
                "ebit": {
                    "type": "number",
                    "description": "EBIT в млн руб — для magic_formula",
                },
                "invested_capital": {
                    "type": "number",
                    "description": "Invested Capital в млн руб — для magic_formula",
                },
                "enterprise_value": {
                    "type": "number",
                    "description": "Enterprise Value в млн руб — для magic_formula",
                },
            },
            "required": ["calculation"],
        },
    },
}

ALL_TOOLS = [
    SEARCH_WEB_SCHEMA,
    GET_STOCK_PRICE_SCHEMA,
    GET_COMPANY_DATA_SCHEMA,
    SCREEN_STOCKS_SCHEMA,
    CALCULATE_SCHEMA,
]
