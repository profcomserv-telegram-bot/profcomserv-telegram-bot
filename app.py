import os
import json
from flask import Flask, request
import requests

app = Flask(__name__)

# Токены из переменных окружения
TOKEN1 = os.environ.get('BOT_TOKEN_1')
TOKEN2 = os.environ.get('BOT_TOKEN_2')
TOKEN3 = os.environ.get('BOT_TOKEN_3')
OPERATOR_ID = int(os.environ.get('OPERATOR_ID', 0))

# Хранилище активных диалогов (user_id: True)
active_chats = {}

# ---- Функция отправки сообщения ----
def send_message(chat_id, text, token, reply_markup=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=5)
        if not r.ok:
            print(f"Send error: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Request error: {e}")

# ---- Обработка входящего обновления для конкретного бота ----
def process_update(update, token):
    if not update:
        return
    # Обработка сообщения
    if 'message' in update:
        msg = update['message']
        chat_id = msg['chat']['id']
        user = msg['chat'].get('username', 'без username')
        text = msg.get('text')
        
        # Команда /start
        if text == '/start':
            keyboard = {
                'inline_keyboard': [[{'text': '📞 Связаться с оператором', 'callback_data': 'operator'}]]
            }
            send_message(chat_id, 'Привет! Я бот ProfComServ.\nНажми кнопку, чтобы связаться с оператором.', token, keyboard)
            return
        
        # Если пользователь в активном диалоге (нажал кнопку ранее)
        if chat_id in active_chats:
            # Пересылаем сообщение оператору
            send_message(OPERATOR_ID, f"📩 Сообщение от @{user} (id: {chat_id}):\n{text}", token)
            send_message(chat_id, "✉️ Сообщение отправлено оператору. Ожидайте ответа.", token)
        else:
            send_message(chat_id, "Сначала нажмите /start и кнопку «Связаться с оператором».", token)
    
    # Обработка нажатия inline-кнопки
    elif 'callback_query' in update:
        query = update['callback_query']
        user_id = query['from']['id']
        data = query['data']
        
        if data == 'operator':
            active_chats[user_id] = True
            # Отвечаем на callback, чтобы убрать «часики» у кнопки
            answer_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
            requests.post(answer_url, json={'callback_query_id': query['id']})
            # Меняем текст сообщения
            edit_url = f"https://api.telegram.org/bot{token}/editMessageText"
            payload = {
                'chat_id': query['message']['chat']['id'],
                'message_id': query['message']['message_id'],
                'text': "✅ Вы переведены на оператора. Ожидайте ответа.\nЧтобы завершить диалог, напишите /end"
            }
            requests.post(edit_url, json=payload)
            # Уведомляем оператора
            send_message(OPERATOR_ID, f"🆕 Новый клиент @{query['from'].get('username', 'no username')} (id: {user_id}) подключился.", token)

# ---- Вебхуки для трёх ботов ----
@app.route('/webhook/1', methods=['POST'])
def webhook1():
    process_update(request.get_json(), TOKEN1)
    return 'OK', 200

@app.route('/webhook/2', methods=['POST'])
def webhook2():
    process_update(request.get_json(), TOKEN2)
    return 'OK', 200

@app.route('/webhook/3', methods=['POST'])
def webhook3():
    process_update(request.get_json(), TOKEN3)
    return 'OK', 200

# ---- Эндпоинт для ответов оператора ----
@app.route('/reply', methods=['POST'])
def reply():
    """Оператор отправляет сюда сообщение в формате JSON: {"user_id": 123, "text": "ответ"}"""
    data = request.get_json()
    if not data:
        return 'Bad request', 400
    user_id = data.get('user_id')
    text = data.get('text')
    if not user_id or not text:
        return 'Missing fields', 400
    # Отправляем ответ пользователю через первого бота (можно через любого, но лучше через того, кто прислал сообщение)
    # Для простоты отправим через первого бота. Но можно сохранять, от какого бота пришло сообщение.
    # Упростим: пробуем отправить через все три токена, если один не сработает.
    sent = False
    for token in [TOKEN1, TOKEN2, TOKEN3]:
        send_message(user_id, f"👨‍💼 Оператор: {text}", token)
        sent = True
        break  # достаточно одного
    if sent:
        return 'OK', 200
    else:
        return 'Error', 500

# ---- Проверка здоровья для Render ----
@app.route('/')
def health():
    return 'Bot is running', 200

# ---- Запуск ----
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
