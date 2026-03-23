"""Инвестиционный калькулятор: формулы фундаментального анализа."""

import math
import logging

logger = logging.getLogger(__name__)


def run_calculator(args: dict) -> dict:
    """Выполнить расчёт по выбранной формуле."""
    calc_type = args.get("calculation", "")

    try:
        if calc_type == "graham_number":
            return _graham_number(args)
        elif calc_type == "peg":
            return _peg_ratio(args)
        elif calc_type == "dcf_simple":
            return _dcf_simple(args)
        elif calc_type == "div_discount":
            return _dividend_discount(args)
        elif calc_type == "magic_formula":
            return _magic_formula(args)
        else:
            return {"error": f"Неизвестный тип расчёта: {calc_type}"}
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return {"error": f"Ошибка расчёта: {e}"}


def _graham_number(args: dict) -> dict:
    """Graham Number = sqrt(22.5 * EPS * BVPS)."""
    eps = args.get("eps")
    bvps = args.get("bvps")

    if not eps or not bvps:
        return {"error": "Нужны параметры: eps и bvps"}
    if eps <= 0 or bvps <= 0:
        return {"error": "EPS и BVPS должны быть положительными для формулы Грэма"}

    graham = math.sqrt(22.5 * eps * bvps)

    return {
        "calculation": "Graham Number",
        "formula": "√(22.5 × EPS × BVPS)",
        "inputs": {"EPS": eps, "BVPS": bvps},
        "result": round(graham, 2),
        "interpretation": (
            f"Максимальная справедливая цена по Грэму: {graham:.2f} руб. "
            f"Покупать ниже этой цены = маржа безопасности."
        ),
    }


def _peg_ratio(args: dict) -> dict:
    """PEG = P/E / EPS Growth Rate."""
    pe = args.get("pe_ratio")
    growth = args.get("growth_rate")

    if not pe or not growth:
        return {"error": "Нужны параметры: pe_ratio и growth_rate"}
    if growth <= 0:
        return {"error": "Темп роста должен быть положительным"}

    peg = pe / growth

    interpretation = ""
    if peg < 0.5:
        interpretation = "Сильно недооценена (PEG < 0.5) — редкость"
    elif peg < 1.0:
        interpretation = "Недооценена (PEG < 1.0) — покупать"
    elif peg <= 1.5:
        interpretation = "Справедливо оценена (PEG ~1.0)"
    elif peg <= 2.0:
        interpretation = "Переоценена (PEG > 1.5) — не покупать"
    else:
        interpretation = "Опасно дорого (PEG > 2.0)"

    return {
        "calculation": "PEG Ratio (Lynch)",
        "formula": "P/E ÷ EPS Growth Rate (%)",
        "inputs": {"P/E": pe, "EPS Growth %": growth},
        "result": round(peg, 3),
        "interpretation": interpretation,
    }


def _dcf_simple(args: dict) -> dict:
    """Упрощённый DCF: дисконтированные FCF + терминальная стоимость."""
    fcf = args.get("fcf")
    discount = args.get("discount_rate", 18)
    terminal_g = args.get("terminal_growth", 3)
    shares = args.get("shares_count")
    growth = args.get("growth_rate", 5)
    years = args.get("years", 5)

    if not fcf:
        return {"error": "Нужен параметр: fcf (в млн руб)"}
    if discount <= terminal_g:
        return {"error": "Ставка дисконтирования должна быть больше терминального роста"}

    r = discount / 100
    g = growth / 100
    tg = terminal_g / 100

    # Прогноз FCF
    pv_fcf_total = 0
    fcf_projections = []
    current_fcf = fcf

    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + g)
        pv = current_fcf / ((1 + r) ** year)
        pv_fcf_total += pv
        fcf_projections.append({
            "year": year,
            "fcf": round(current_fcf, 0),
            "pv": round(pv, 0),
        })

    # Терминальная стоимость
    terminal_fcf = current_fcf * (1 + tg)
    tv = terminal_fcf / (r - tg)
    pv_tv = tv / ((1 + r) ** years)

    total_value = pv_fcf_total + pv_tv

    result = {
        "calculation": "Simplified DCF",
        "inputs": {
            "FCF (млн руб)": fcf,
            "Growth Rate %": growth,
            "Discount Rate %": discount,
            "Terminal Growth %": terminal_g,
            "Years": years,
        },
        "fcf_projections": fcf_projections,
        "pv_fcf_total": round(pv_fcf_total, 0),
        "terminal_value": round(tv, 0),
        "pv_terminal_value": round(pv_tv, 0),
        "total_company_value_mln": round(total_value, 0),
    }

    if shares:
        fair_price = total_value * 1_000_000 / shares
        result["shares_count"] = shares
        result["fair_price_per_share"] = round(fair_price, 2)
        result["interpretation"] = (
            f"Справедливая стоимость компании: {total_value:,.0f} млн руб. "
            f"Справедливая цена акции: {fair_price:.2f} руб."
        )
    else:
        result["interpretation"] = (
            f"Справедливая стоимость компании: {total_value:,.0f} млн руб. "
            f"Укажите shares_count для расчёта цены акции."
        )

    return result


def _dividend_discount(args: dict) -> dict:
    """Модель Гордона: P = D1 / (r - g)."""
    dividend = args.get("dividend")
    req_return = args.get("required_return", 18)
    div_growth = args.get("div_growth", 5)

    if not dividend:
        return {"error": "Нужен параметр: dividend (дивиденд на акцию)"}

    r = req_return / 100
    g = div_growth / 100

    if r <= g:
        return {"error": "Требуемая доходность (r) должна быть больше темпа роста дивидендов (g)"}

    fair_price = dividend / (r - g)

    return {
        "calculation": "Gordon Growth Model (DDM)",
        "formula": "P = D1 / (r - g)",
        "inputs": {
            "Дивиденд (D1)": dividend,
            "Требуемая доходность (r) %": req_return,
            "Рост дивидендов (g) %": div_growth,
        },
        "result": round(fair_price, 2),
        "interpretation": (
            f"Справедливая цена по модели Гордона: {fair_price:.2f} руб. "
            f"Дивидендная доходность при этой цене: {dividend / fair_price * 100:.1f}%."
        ),
    }


def _magic_formula(args: dict) -> dict:
    """Magic Formula (Greenblatt): ROIC + Earnings Yield."""
    ebit = args.get("ebit")
    ic = args.get("invested_capital")
    ev = args.get("enterprise_value")

    if not ebit or not ic or not ev:
        return {"error": "Нужны параметры: ebit, invested_capital, enterprise_value"}

    roic = ebit / ic * 100 if ic > 0 else 0
    ey = ebit / ev * 100 if ev > 0 else 0

    interpretation_parts = []
    if roic > 15:
        interpretation_parts.append(f"ROIC {roic:.1f}% > 15% — высокая отдача")
    else:
        interpretation_parts.append(f"ROIC {roic:.1f}% < 15% — невысокая отдача")

    if ey > 10:
        interpretation_parts.append(f"EY {ey:.1f}% > 10% — дёшево")
    else:
        interpretation_parts.append(f"EY {ey:.1f}% < 10% — недёшево")

    passed = roic > 15 and ey > 10

    return {
        "calculation": "Magic Formula (Greenblatt)",
        "formulas": {
            "ROIC": "EBIT / Invested Capital",
            "Earnings Yield": "EBIT / Enterprise Value",
        },
        "inputs": {
            "EBIT (млн руб)": ebit,
            "Invested Capital (млн руб)": ic,
            "Enterprise Value (млн руб)": ev,
        },
        "roic_pct": round(roic, 2),
        "earnings_yield_pct": round(ey, 2),
        "passes_magic_formula": passed,
        "interpretation": ". ".join(interpretation_parts) + (
            ". Проходит Magic Formula!" if passed else ". Не проходит Magic Formula."
        ),
    }
