import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== 1. НАСТРОЙКИ ==========
TOKEN_1 = os.environ.get("BOT_TOKEN_1", "8684012503:AAHcBc1ggVUGEHv7dY1M-YcGIuxviWwTLh0")
TOKEN_2 = os.environ.get("BOT_TOKEN_2", "8223022364:AAEu31BylYStpxHxg06yyW_JY2NX32WgEPo")
TOKEN_3 = os.environ.get("BOT_TOKEN_3", "8764025967:AAFS_kgxV6y9Zcg3THrrG-JNb6nErL3KrA4")
OPERATOR_ID = int(os.environ.get("OPERATOR_ID", 7137220733))
PORT = int(os.environ.get("PORT", 8000))  # Порт из переменной окружения Render

active_chats = {}

# ========== 2. ЛОГИКА ТВОИХ БОТОВ (без изменений) ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код обработчика start)
    keyboard = [[InlineKeyboardButton("📞 Связаться с оператором", callback_data="operator")]]
    await update.message.reply_text(
        "Привет! Я бот ProfComServ.\nНажми кнопку, чтобы связаться с живым оператором.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код обработчика кнопок)
    query = update.callback_query
    await query.answer()
    if query.data == "operator":
        user_id = query.from_user.id
        active_chats[user_id] = True
        await query.edit_message_text("✅ Вы переведены на оператора. Ожидайте ответа.\nЧтобы завершить, напишите /end")
        await context.bot.send_message(OPERATOR_ID, f"🆕 Новый клиент @{query.from_user.username or query.from_user.first_name} (id: {user_id})")

async def operator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код команды /operator)
    user_id = update.effective_user.id
    active_chats[user_id] = True
    await update.message.reply_text("✅ Вы переведены на оператора. Ожидайте ответа.\nЧтобы завершить, напишите /end")
    await context.bot.send_message(OPERATOR_ID, f"🆕 Новый клиент @{update.effective_user.username or update.effective_user.first_name} (id: {user_id})")

async def end_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код команды /end)
    user_id = update.effective_user.id
    if user_id in active_chats:
        del active_chats[user_id]
        await update.message.reply_text("Диалог завершён. Если понадоблюсь снова — /operator")
        await context.bot.send_message(OPERATOR_ID, f"❌ Клиент {user_id} завершил диалог.")
    else:
        await update.message.reply_text("У вас нет активного диалога.")

async def forward_to_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код пересылки оператору)
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("Сначала нажмите /operator, чтобы связаться с оператором.")
        return
    text = update.message.text
    if text:
        await context.bot.send_message(OPERATOR_ID, f"📩 Сообщение от {user_id} (@{update.effective_user.username}):\n{text}")
        await update.message.reply_text("✉️ Отправлено оператору. Ожидайте ответа.")

async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код получения ответов оператора)
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
    """Создаёт и настраивает приложение для одного бота"""
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("operator", operator_cmd))
    app.add_handler(CommandHandler("end", end_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_operator))
    app.add_handler(MessageHandler(filters.User(user_id=OPERATOR_ID) & filters.TEXT, forward_to_user))
    return app

# ========== 3. НОВЫЙ HTTP-СЕРВЕР ДЛЯ RENDER ==========
async def health_check(request):
    """Простой эндпоинт для проверки здоровья Render"""
    return web.Response(text="OK")

async def start_http_server():
    """Запускает aiohttp сервер, слушающий порт из переменной окружения"""
    app = web.Application()
    app.router.add_get('/health', health_check)  # Render будет проверять этот путь
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT) # Слушаем на всех интерфейсах
    await site.start()
    print(f"HTTP сервер для Render запущен на порту {PORT}")

# ========== 4. ЗАПУСК ==========
async def run_bots():
    """Запускает всех ботов параллельно"""
    tokens = [TOKEN_1, TOKEN_2, TOKEN_3]
    apps = [create_bot_app(token) for token in tokens if token]
    tasks = [app.run_polling() for app in apps]
    await asyncio.gather(*tasks)

async def main():
    """Главная функция, запускающая HTTP-сервер и ботов"""
    print("Запуск HTTP-сервера и трёх ботов...")
    # Запускаем HTTP-сервер как отдельную задачу
    http_task = asyncio.create_task(start_http_server())
    # Запускаем ботов как другую задачу
    bots_task = asyncio.create_task(run_bots())
    # Ждем выполнения обеих задач
    await asyncio.gather(http_task, bots_task)

if __name__ == "__main__":
    asyncio.run(main())
