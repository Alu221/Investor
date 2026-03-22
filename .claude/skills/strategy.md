# Применение стратегии инвестора к компании

## Когда использовать
Пользователь спрашивает "оцени Сбер по Баффету", "что скажет Грэм про Лукойл?", "Magic Formula для MOEX"

## Алгоритм

### 1. Определи стратегию
Загрузи из knowledge/:
- **Buffett** → @knowledge/strategies_value.md (moat, owner earnings, margin of safety)
- **Graham** → @knowledge/strategies_value.md (Graham Number, net-net, P/E < 15)
- **Lynch** → @knowledge/strategies_growth.md (PEG, 6 типов акций)
- **Dalio** → @knowledge/strategies_macro.md (All Weather, risk parity)
- **Greenblatt** → @knowledge/strategies_quant.md (Magic Formula: ROIC + EY)
- **Marks** → @knowledge/strategies_cycles.md (цикл, second-level thinking)
- **Fisher** → @knowledge/strategies_growth.md (15 points, scuttlebutt)

### 2. Примени критерии к компании
Для каждого критерия стратегии:
- Рассчитай значение для компании
- Сравни с порогом стратегии
- Вынеси вердикт: ✅ проходит / ❌ не проходит

### 3. Scorecard
| Критерий | Порог | Факт | Вердикт |
|----------|-------|------|---------|
| P/E | < 15 (Graham) | 6.2 | ✅ |
| ROE | > 15% (Buffett) | 24.8% | ✅ |
| ... | ... | ... | ... |

### 4. Итоговая оценка
- Проходит X из Y критериев (%)
- По стратегии {инвестора}: ПОКУПАТЬ / ДЕРЖАТЬ / ИЗБЕГАТЬ
- Главный плюс и главный минус с точки зрения этой стратегии

### 5. Дисклеймер
> Данный анализ не является индивидуальной инвестиционной рекомендацией.
