"""Загрузка базы знаний из knowledge/ директории."""

import json
import logging
import os

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Загружает и хранит базу знаний из markdown-файлов и JSON."""

    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = knowledge_dir
        self.knowledge_texts: dict[str, str] = {}
        self.companies_data: dict = {}

    def load(self):
        """Загрузить все файлы из knowledge/."""
        if not os.path.isdir(self.knowledge_dir):
            logger.warning(f"Knowledge dir not found: {self.knowledge_dir}")
            return

        # Загрузка .md файлов
        for filename in sorted(os.listdir(self.knowledge_dir)):
            filepath = os.path.join(self.knowledge_dir, filename)
            if filename.endswith(".md"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.knowledge_texts[filename] = content
                    logger.info(f"Loaded knowledge: {filename} ({len(content)} chars)")
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

            elif filename == "companies_data.json":
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.companies_data = json.load(f)
                    company_count = len(self.companies_data.get("companies", []))
                    logger.info(f"Loaded companies_data.json: {company_count} companies")
                except Exception as e:
                    logger.error(f"Failed to load companies_data.json: {e}")

    def get_knowledge_summary(self) -> str:
        """Краткое описание доступных знаний (для system prompt)."""
        lines = [
            "## Доступные базы знаний (загружены в память, доступны через tool get_company_data):",
            "",
        ]
        for filename, content in self.knowledge_texts.items():
            # Берём первую строку как заголовок
            first_line = content.split("\n")[0].strip("# ").strip()
            lines.append(f"- **{filename}**: {first_line}")

        if self.companies_data:
            companies = self.companies_data.get("companies", [])
            names = [c["name"] for c in companies[:10]]
            lines.append(
                f"- **companies_data.json**: {len(companies)} компаний "
                f"({', '.join(names)}...)"
            )

        return "\n".join(lines)

    def get_company(self, name: str) -> dict | None:
        """Найти компанию по имени (нечёткий поиск)."""
        companies = self.companies_data.get("companies", [])
        name_lower = name.lower().strip()

        # Точное совпадение
        for c in companies:
            if c["name"].lower() == name_lower:
                return c

        # Частичное совпадение
        for c in companies:
            if name_lower in c["name"].lower() or c["name"].lower() in name_lower:
                return c

        # Поиск по тикеру в имени
        ticker_map = {
            "sber": "Сбер", "lkoh": "ЛУКОЙЛ", "gazp": "Газпром",
            "rosn": "Роснефть", "nvtk": "Новатэк", "tatn": "Татнефть",
            "gmkn": "ГМК Норникель", "yndx": "Яндекс", "mtss": "МТС",
            "plzl": "Полюс золото", "chmf": "Северсталь", "nlmk": "НЛМК",
            "magn": "ММК", "phor": "Фосагро", "alrs": "АЛРОСА",
            "vtbr": "ВТБ", "sibn": "Газпромнефть", "bspb": "БСП",
            "mgnt": "Магнит", "five": "Х5", "ozon": "OZON",
            "rtkm": "Ростелеком", "sngsp": "Сургутнефтегаз",
            "sngs": "Сургутнефтегаз", "trnfp": "Транснефть",
            "bane": "Башнефть",
        }
        if name_lower in ticker_map:
            return self.get_company(ticker_map[name_lower])

        return None

    def screen_stocks(self, filters: dict) -> list[dict]:
        """Скрининг акций по фильтрам.

        Фильтры: p_e_max, p_e_min, roe_min, nd_ebitda_max,
                  div_yield_min, sector, ev_ebitda_max.
        """
        companies = self.companies_data.get("companies", [])
        results = []

        for c in companies:
            m = c.get("multiples", {})
            passed = True

            if "sector" in filters and filters["sector"]:
                if filters["sector"].lower() not in c.get("sector", "").lower():
                    passed = False

            if "p_e_max" in filters and filters["p_e_max"] is not None:
                pe = m.get("p_e")
                if pe is None or pe > filters["p_e_max"]:
                    passed = False

            if "p_e_min" in filters and filters["p_e_min"] is not None:
                pe = m.get("p_e")
                if pe is None or pe < filters["p_e_min"]:
                    passed = False

            if "roe_min" in filters and filters["roe_min"] is not None:
                roe = m.get("roe")
                if roe is None or roe < filters["roe_min"]:
                    passed = False

            if "nd_ebitda_max" in filters and filters["nd_ebitda_max"] is not None:
                nd = m.get("nd_ebitda")
                if nd is not None and nd > filters["nd_ebitda_max"]:
                    passed = False

            if "div_yield_min" in filters and filters["div_yield_min"] is not None:
                dy = c.get("div_yield")
                if dy is None or dy < filters["div_yield_min"]:
                    passed = False

            if "ev_ebitda_max" in filters and filters["ev_ebitda_max"] is not None:
                ev_eb = m.get("ev_ebitda")
                if ev_eb is None or ev_eb > filters["ev_ebitda_max"]:
                    passed = False

            if passed:
                results.append(c)

        return results

    def get_all_knowledge_text(self) -> str:
        """Весь текст knowledge файлов (для контекста). Без JSON."""
        parts = []
        for filename, content in self.knowledge_texts.items():
            parts.append(f"=== {filename} ===\n{content}\n")
        return "\n".join(parts)
