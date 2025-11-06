import telebot
import gspread
from datetime import date
import os, json

# === 🔧 НАСТРОЙКИ ===
TOKEN = os.environ["BOT_TOKEN"]  # токен Telegram из Secrets
SERVICE_ACCOUNT_JSON = os.environ["SERVICE_ACCOUNT_JSON"]  # JSON из Secrets
SPREADSHEET_NAME = "Finance"  # имя таблицы в Google Sheets

# === 🧾 ИНИЦИАЛИЗАЦИЯ ===
bot = telebot.TeleBot(TOKEN)

# Подключение к Google Sheets
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open(SPREADSHEET_NAME)
worksheet = sh.worksheet("Transactions")

# === 💰 КАТЕГОРИИ ===
categories = {
    "расход": [
        "обеды", "продукты", "гигиена", "кафе", "транспорт",
        "подписки", "покупки", "развлечения", "здоровье",
        "образование", "путешествия", "подарки", "другое"
    ],
    "доход": [
        "зарплата", "стипендия", "спонсор", "выплаты", "фриланс", "прочие"
    ]
}

# Состояния пользователей
user_state = {}

# === ⚙️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def type_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('доход', 'расход')
    return markup

def categories_keyboard(type_):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in categories[type_]:
        markup.add(c)
    return markup

def yesno_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Да", "Нет")
    return markup

months_nominative = {
    "01": "январь", "02": "февраль", "03": "март", "04": "апрель",
    "05": "май", "06": "июнь", "07": "июль", "08": "август",
    "09": "сентябрь", "10": "октябрь", "11": "ноябрь", "12": "декабрь"
}

# === 🏁 СТАРТ ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Выбери тип транзакции:", reply_markup=type_keyboard())

# === ВЫБОР ТИПА ===
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ['доход', 'расход'])
def select_type(message):
    chat_id = message.chat.id
    t = message.text.lower()
    user_state[chat_id] = {"type": t}
    bot.send_message(chat_id, "📂 Выбери категорию:", reply_markup=categories_keyboard(t))

# === ВЫБОР КАТЕГОРИИ ===
@bot.message_handler(func=lambda m: m.text and any(m.text in v for v in categories.values()))
def select_category(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.send_message(chat_id, "Пожалуйста, сначала выбери тип (доход/расход).", reply_markup=type_keyboard())
        return

    user_state[chat_id]["category"] = message.text
    from telebot.types import ReplyKeyboardRemove
    bot.send_message(chat_id, "💵 Введи сумму (только число):", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_amount)

# === ВВОД СУММЫ ===
def get_amount(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.send_message(chat_id, "Ошибка: начни с выбора типа.", reply_markup=type_keyboard())
        return
    try:
        user_state[chat_id]["amount"] = float(message.text.replace(',', '.'))
    except ValueError:
        bot.send_message(chat_id, "⚠️ Неверный формат суммы. Введи число (например, 1500).")
        bot.register_next_step_handler(message, get_amount)
        return

    bot.send_message(chat_id, "📝 Хочешь добавить комментарий?", reply_markup=yesno_keyboard())
    bot.register_next_step_handler(message, ask_note_choice)

# === ДОБАВИТЬ КОММЕНТАРИЙ ===
def ask_note_choice(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.send_message(chat_id, "Ошибка: начни с выбора типа.", reply_markup=type_keyboard())
        return

    text = message.text.lower()
    if text == "да":
        from telebot.types import ReplyKeyboardRemove
        bot.send_message(chat_id, "✏️ Введи комментарий:", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, finalize_transaction_with_note)
    elif text == "нет":
        finalize_transaction_with_note(message, skip_note=True)
    else:
        bot.send_message(chat_id, "Пожалуйста, выбери 'Да' или 'Нет'.", reply_markup=yesno_keyboard())
        bot.register_next_step_handler(message, ask_note_choice)

# === ФИНАЛЬНОЕ ДОБАВЛЕНИЕ В ГТ ===
def finalize_transaction_with_note(message, skip_note=False):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.send_message(chat_id, "Ошибка: ничего не найдено. Начни заново /start", reply_markup=type_keyboard())
        return

    note = "" if skip_note else message.text
    data = user_state[chat_id]
    id_value = len(worksheet.col_values(1))
    today = date.today()
    month_code = today.strftime("%m")
    month_nominative = months_nominative.get(month_code, today.strftime("%B").lower())

    row = [
        id_value,
        today.strftime("%Y-%m-%d"),
        month_nominative,
        data["type"],
        data["category"],
        data["amount"],
        note
    ]
    worksheet.append_row(row)

    bot.send_message(chat_id, "✅ Добавлено!")
    del user_state[chat_id]
    bot.send_message(chat_id, "Что добавляем дальше?", reply_markup=type_keyboard())

# === 🚀 ЗАПУСК ===
if __name__ == "__main__":
    print("🚀 Бот запущен и готов к работе!")
    bot.polling(non_stop=True, timeout=90)