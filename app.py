import os
from flask import Flask
from threading import Thread
import telegram
from telegram.ext import Application, CommandHandler

app = Flask(__name__)
TOKEN = "8684012503:AAHcBc1ggVUGEHv7dY1M-YcGIuxviWwTLh0"

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

async def start(update, context):
    await update.message.reply_text('Привет! Я бот ProfComServ и я работаю!')

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
