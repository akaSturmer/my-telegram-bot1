import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === ТВОИ ДАННЫЕ (уже вставлены) ===
TELEGRAM_TOKEN = "7426748624:AAGHSRTPl3mkK6rVXN86lbaQN5Y1mCv17YE"
GROQ_API_KEY = "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"

# === ВСТРОЕННАЯ БАЗА ТОВАРОВ (вместо CSV) ===
PRODUCTS = [
    {
        "Имя": "Клей-пена профессиональная ТЕХНОНИКОЛЬ для кладки блоков 700 мл",
        "Артикул": "303000000",
        "Описание": "Клей-Цемент ТЕХНОНИКОЛЬ MASTER — однокомпонентный полиуретановый клей. Подходит для кладки из газобетонных, керамических блоков. Температура применения: от -10°C до +35°C.",
        "Подходит для": "блоки, газобетон, перегородки, керамика, стены",
        "Ссылка": "https://baucenter.ru/product/kley-pena-professionalnaya-tekhnonikol-dlya-kladki-blokov-700-ml-ctg-36829-36841-38020-303000000/"
    }
    # Добавляй сюда новые товары по такому же шаблону
]

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Напиши, что нужно склеить, или задай вопрос о товаре."
    )

# === Обработка сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    # Поиск по "Подходит для"
    matches = []
    for p in PRODUCTS:
        suitable = p.get("Подходит для", "").lower()
        for keyword in suitable.split(","):
            if keyword.strip() in user_text:
                matches.append(p)
                break

    # Показываем товары
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
        prompt = f"Пользователь спрашивает: '{user_text}'. Вот наши товары: {PRODUCTS}. Подскажи, что может подойти."
        ai_response = get_ai_response(prompt)
        await update.message.reply_text(ai_response)

# === Запрос к Groq (ИИ) ===
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
            return "Не могу ответить. Попробуй позже."
    except Exception as e:
        return f"Ошибка: {str(e)}"

# === Запуск бота ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен...")
    app.run_polling()