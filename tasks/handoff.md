# Передача контекста: ИНвестбот

## Последнее обновление: 2026-03-22

## Что сделано в этой сессии

### Тестирование бота (основная работа)
- Создано 125 + 200 = **325 тестовых вопросов** разной сложности
- 4 раунда тестирования: 8.7 → 8.8 → 8.2 → **9.03/10** (финальный)
- Найдены и закрыты все пробелы в knowledge и скиллах

### Knowledge база: 25 → 31 файл
- Новые: tax_and_iis.md, market_history_ru.md, ipo_and_delisting.md, em_comparison.md, investor_protection.md, correlation_matrix.md
- Расширены: fundamentals_basics.md (+МСФО/РСБУ таблица), balance_sheet.md (+банковская специфика Н1/NPL/NIM), bonds_basics.md (+замещающие облигации, carry trade)

### Данные: 30 → 50 компаний, 15 → ~40 полей
- Все компании из Excel "Сортировка 2026"
- Новые поля: ebit, eps, bvps, payout_ratio, debt_equity, current_ratio, total_assets, ocf, working_capital, eps_growth_yoy, beta, sigma_12m, invested_capital, target_price, target_upside, group_2026, dividend_ex_month, lot_size, lot_cost, prev_year (7 подполей), revenue_growth_yoy
- Live-цены с MOEX ISS API (2026-03-22)
- Сплиты исправлены: ВТБ (1:5000), Норникель (1:100), Полюс (~1:5), НоваБев (1:13)

### Скиллы: 11 → 12 (7 обновлены + 1 новый)
- Новый: stress_test.md
- Обновлены: dcf (ветвления), analyze (null/банки), compare (вне-MOEX), screen (Z-Score/аномалии), buy_signals (формулы), portfolio (лоты), report (F-Score 9/9)

### CLAUDE.md: протокол провокаций, правило даты данных

### Инфраструктура
- scripts/update_data.js — обновление цен MOEX ISS API (бесплатно)
- Task Scheduler: автообновление 19:00 ежедневно
- Проект запушен на GitHub: https://github.com/Alu221/Investor
- VPS настроен: 82.22.35.210 (Ubuntu 22.04, SSH root, Node.js 20, проект скопирован в /root/Investor/)

### Исследование деплоя бота
- iia — платная платформа, решили не использовать
- Claude Code Channels — оказалось это пульт к ПК, а не бот для группы
- **Решение: свой бот на Python (как юрист)** — копируем архитектуру из e:\mon-ptogekt\юрист корманный\bot\

## Что дальше (СЛЕДУЮЩАЯ СЕССИЯ)
1. **Написать Telegram бота на Python** на базе архитектуры юриста:
   - Скопировать структуру из `e:\mon-ptogekt\юрист корманный\bot\`
   - Заменить юридический system prompt → CLAUDE.md
   - Заменить юридические tools → финансовые (MOEX API, скрининг, DCF)
   - Заменить RAG законодательной базы → knowledge/ файлы (31 шт)
   - Настроить DuckDuckGo поиск (уже есть в юристе)
2. **Задеплоить на VPS** (82.22.35.210, SSH настроен, Node.js есть, Python нужно поставить)
3. **Тестировать в Telegram** с группой инвесторов

## Текущее состояние
- **Ветка**: main
- **Работает ли**: Knowledge база готова на 9.03/10. Бот-код ещё не написан
- **Незакоммиченные изменения**: только bot/package.json (начали писать Node.js бот, потом решили Python)
- **Блокеры**: нет

## Договорённости с пользователем
- Бот на Python (aiogram) как юрист — проверенная архитектура
- Claude API через Anthropic напрямую (sk-ant-...) или OpenRouter
- DuckDuckGo для поиска (бесплатно)
- MOEX ISS API для котировок (бесплатно)
- Стоимость: ~$30-60/мес на Sonnet для 5-10 инвесторов
- VPS: 82.22.35.210 (Ubuntu 22.04, root, оплачен до 2027)

## Контекст который легко потерять
- **VPS доступ**: SSH root@82.22.35.210, ключ уже добавлен, пароль в .env
- **Бот юриста** — готовый шаблон: `e:\mon-ptogekt\юрист корманный\bot\` (aiogram + OpenRouter + DuckDuckGo + PostgreSQL + Tool Calling Loop)
- **OpenRouter vs Anthropic API**: юрист работает через OpenRouter (OpenAI-совместимый), у нас sk-ant ключ (прямой Anthropic). Нужно либо взять OpenRouter ключ, либо использовать @anthropic-ai/sdk
- **MOEX ISS API** бесплатный, без авторизации: https://iss.moex.com/iss/
- **Сплиты**: скрипт update_data.js НЕ учитывает сплиты автоматически
- **5 тикеров не обновляются**: Тинькофф (TCSG), Русагро (AGRO), ДОМ.РФ (DOMR), Россети (RSTI), ЦИАН — нет на TQBR
- **Telegram Bot Token**: 8713126629:AAGx4KqsIoMUni6UGjBo7N853eyuz8S47Nk (в .env)
- **prev_year данные приблизительные** — из growth rates, не из реальных отчётов
- **bot/package.json** — начали Node.js бот, потом решили Python. Можно удалить

## Memory flush
- Проект = knowledge-based инвестиционный аналитик для Telegram
- 50 компаний × ~40 полей, 31 knowledge файл, 12 скиллов
- Финальный тест 200 сложных вопросов: **9.03/10**
- Архитектура бота: копируем юриста (Python/aiogram), меняем контент
- Ключевые файлы юриста для копирования: main.py, config.py, services/llm.py (Tool Calling Loop), services/tools/, handlers/chat.py, utils/text_splitter.py
- Claude Code Channels и iia отвергнуты (Channels = пульт к ПК, iia = платная)
- Пользователь — инвестор, группа 5-10 человек

---
*Обновлять в конце каждой сессии.*
