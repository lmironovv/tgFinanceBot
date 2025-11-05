# 💸 Telegram Finance Bot

Простой Telegram-бот для учёта личных доходов и расходов с интеграцией Google Sheets.

## 🚀 Установка и запуск

1. Создай таблицу **Finance** в Google Sheets.
   В ней должен быть лист `Transactions` с колонками:
   ID | Date | Month | Type | Category | Amount | Note
   
2. В Replit → Secrets добавь:
- `BOT_TOKEN` — токен от @BotFather
- `SERVICE_ACCOUNT_JSON` — весь JSON ключ от Google API

3. Установи зависимости:
pip install -r requirements.txt

4. Запусти бота:
python3 bot.py

Бот будет работать 24/7, если проект открыт в Replit или подключен UptimeRobot.
