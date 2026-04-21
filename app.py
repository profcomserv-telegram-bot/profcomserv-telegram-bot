import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN_1 = os.environ["BOT_TOKEN_1"]
TOKEN_2 = os.environ["BOT_TOKEN_2"]
TOKEN_3 = os.environ["BOT_TOKEN_3"]
OPERATOR_ID = int(os.environ.get("OPERATOR_ID", 7137220733))

active_chats = {}

# ========== ОБРАБОТЧИКИ БОТОВ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📞 Связаться с оператором", callback_data="operator")]]
    await update.message.reply_text(
        "Привет! Я бот ProfComServ.\nНажми кнопку, чтобы связаться с живым оператором.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "operator":
        user_id = query.from_user.id
        active_chats[user_id] = True
        await query.edit_message_text("✅ Вы переведены на оператора. Ожидайте ответа.\nЧтобы завершить, напишите /end")
        await context.bot.send_message(OPERATOR_ID, f"🆕 Новый клиент @{query.from_user.username or query.from_user.first_name} (id: {user_id})")

async def operator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_chats[user_id] = True
    await update.message.reply_text("✅ Вы переведены на оператора. Ожидайте ответа.\nЧтобы завершить, напишите /end")
    await context.bot.send_message(OPERATOR_ID, f"🆕 Новый клиент @{update.effective_user.username or update.effective_user.first_name} (id: {user_id})")

async def end_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        del active_chats[user_id]
        await update.message.reply_text("Диалог завершён. Если понадоблюсь снова — /operator")
        await context.bot.send_message(OPERATOR_ID, f"❌ Клиент {user_id} завершил диалог.")
    else:
        await update.message.reply_text("У вас нет активного диалога.")

async def forward_to_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("Сначала нажмите /operator, чтобы связаться с оператором.")
        return
    text = update.message.text
    if text:
        await context.bot.send_message(OPERATOR_ID, f"📩 Сообщение от {user_id} (@{update.effective_user.username}):\n{text}")
        await update.message.reply_text("✉️ Отправлено оператору. Ожидайте ответа.")

async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OPERATOR_ID:
        return
    if not update.message or not update.message.text:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Формат: `ID_пользователя текст`\nПример: `123456 Привет!`")
        return
    try:
        target_user_id = int(parts[0])
        reply_text = parts[1]
    except ValueError:
        await update.message.reply_text("ID должно быть числом.")
        return
    await context.bot.send_message(target_user_id, f"👨‍💼 Оператор: {reply_text}")
    await update.message.reply_text(f"✅ Ответ отправлен пользователю {target_user_id}")

def create_bot_app(token: str):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("operator", operator_cmd))
    app.add_handler(CommandHandler("end", end_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_operator))
    app.add_handler(MessageHandler(filters.User(user_id=OPERATOR_ID) & filters.TEXT, forward_to_user))
    return app

async def run_bots():
    tokens = [TOKEN_1, TOKEN_2, TOKEN_3]
    apps = [create_bot_app(token) for token in tokens]
    tasks = [app.run_polling() for app in apps]
    await asyncio.gather(*tasks)

# ========== HTTP-СЕРВЕР ДЛЯ RENDER (FLASK) ==========
app_flask = Flask(__name__)

@app_flask.route('/')
@app_flask.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host='0.0.0.0', port=port, use_reloader=False, threaded=True)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("Запуск Flask сервера в потоке...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("Запуск трёх ботов...")
    asyncio.run(run_bots())
