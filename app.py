import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
TOKEN = "8684012503:AAHcBc1ggVUGEHv7dY1M-YcGIuxviWwTLh0"

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот ProfComServ и я работаю!')

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False, threaded=True)

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке (не daemon, чтобы он не убился)
    flask_thread = threading.Thread(target=run_flask, daemon=False)
    flask_thread.start()
    
    # Запускаем бота в главном потоке
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Бот запускается...")
    application.run_polling()
