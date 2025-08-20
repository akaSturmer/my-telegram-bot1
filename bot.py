import requests
import csv
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === ЗАМЕНИ НА СВОИ ДАННЫЕ ===
TELEGRAM_TOKEN = "7426748624:AAGHSRTPl3mkK6rVXN86lbaQN5Y1mCv17YE"
GROQ_API_KEY = "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"
GOOGLE_SHEETS_CSV_URL = "https://drive.google.com/file/d/1-0lkI-amiiz8TDcMt0TiVqVBkD73dV_B/view?usp=drivesdk"

# === ЗАГРУЗКА ТОВАРОВ ИЗ GOOGLE ТАБЛИЦЫ ===
def load_products():
    try:
        r = requests.get(GOOGLE_SHEETS_CSV_URL)
        r.encoding = 'utf-8'
        reader = csv.DictReader(io.StringIO(r.text))
        return list(reader)
    except Exception as e:
        print("Ошибка загрузки товаров:", e)
        return []

# === КОМАНДА /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Напиши, что нужно склеить, или задай вопрос о товаре."
    )

# === ОБРАБОТКА СООБЩЕНИЙ ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()
    products = load_products()

    if not products:
        await update.message.reply_text("Сейчас не могу загрузить товары. Попробуй позже.")
        return

    # Поиск по "Подходит для"
    matches = []
    for p in products:
        suitable = p.get("Подходит для", "").lower()
        for keyword in suitable.split(","):
            if keyword.strip() in user_text:
                matches.append(p)
                break

    # Если нашли — покажем товары
    if matches:
        response = "Подходящие товары:\n\n"
        for p in matches:
            name = p["Имя"]
            sku = p["Артикул"]
            link = p["Ссылка"]
            response += f"🔹 <a href='{link}'>{name}</a> (артикул: {sku})\n"
        response += "\nМожешь спросить, подойдёт ли он для чего-то конкретного."
        await update.message.reply_html(response)
    else:
        # Спросим у ИИ
        prompt = f"Пользователь спрашивает: '{user_text}'. Вот товары: {products}. Подскажи, что подойдёт."
        ai_response = get_ai_response(prompt)
        await update.message.reply_text(ai_response)

# === ЗАПРОС К GROQ (ИИ) ===
def get_ai_response(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    try:
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return "Пока не могу ответить. Попробуй позже."
    except Exception as e:
        return f"Ошибка: {str(e)}"

# === ЗАПУСК БОТА ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()
