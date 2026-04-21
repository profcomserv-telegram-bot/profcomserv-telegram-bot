import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8684012503:AAHcBc1ggVUGEHv7dY1M-YcGIuxviWwTLh0"
OPERATOR_ID = int(os.environ.get("OPERATOR_ID", 7137220733))  # твой ID

active_chats = {}  # user_id: True

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
    # Эта функция вызывается только для сообщений от оператора
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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("operator", operator_cmd))
    app.add_handler(CommandHandler("end", end_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_operator))
    app.add_handler(MessageHandler(filters.USER(OPERATOR_ID) & filters.TEXT, forward_to_user))
    print("Бот с оператором запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
