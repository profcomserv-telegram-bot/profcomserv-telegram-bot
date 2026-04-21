import os
import json
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN1 = os.environ.get('BOT_TOKEN_1')
TOKEN2 = os.environ.get('BOT_TOKEN_2')
TOKEN3 = os.environ.get('BOT_TOKEN_3')
OPERATOR_ID = int(os.environ.get('OPERATOR_ID', 0))

active_chats = {}

def send_message(chat_id, text, token, reply_markup=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=5)
        print(f"Send to {chat_id}: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"Send error: {e}")

def process_update(update, token, bot_num):
    if not update:
        print(f"Bot {bot_num}: empty update")
        return
    print(f"Bot {bot_num} received: {json.dumps(update)[:200]}")
    if 'message' in update:
        msg = update['message']
        chat_id = msg['chat']['id']
        user = msg['chat'].get('username', '')
        text = msg.get('text')
        print(f"Message from {chat_id}: {text}")
        if text == '/start':
            keyboard = {'inline_keyboard': [[{'text': '📞 Связаться с оператором', 'callback_data': 'operator'}]]}
            send_message(chat_id, 'Привет! Нажми кнопку, чтобы связаться с оператором.', token, keyboard)
        elif chat_id in active_chats:
            send_message(OPERATOR_ID, f"📩 От @{user} (id:{chat_id}): {text}", token)
            send_message(chat_id, '✉️ Сообщение отправлено оператору.', token)
        elif text and text != '/start':
            send_message(chat_id, 'Сначала нажмите /start и кнопку.', token)
    elif 'callback_query' in update:
        query = update['callback_query']
        user_id = query['from']['id']
        if query['data'] == 'operator':
            active_chats[user_id] = True
            requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={'callback_query_id': query['id']})
            edit_url = f"https://api.telegram.org/bot{token}/editMessageText"
            payload = {
                'chat_id': query['message']['chat']['id'],
                'message_id': query['message']['message_id'],
                'text': '✅ Вы переведены на оператора. Напишите сообщение.'
            }
            requests.post(edit_url, json=payload)
            send_message(OPERATOR_ID, f"🆕 Новый клиент @{query['from'].get('username', '')} (id:{user_id})", token)

@app.route('/webhook/1', methods=['POST'])
def webhook1():
    process_update(request.get_json(), TOKEN1, 1)
    return 'OK', 200

@app.route('/webhook/2', methods=['POST'])
def webhook2():
    process_update(request.get_json(), TOKEN2, 2)
    return 'OK', 200

@app.route('/webhook/3', methods=['POST'])
def webhook3():
    process_update(request.get_json(), TOKEN3, 3)
    return 'OK', 200

@app.route('/reply', methods=['POST'])
def reply():
    data = request.get_json()
    if not data or 'user_id' not in data or 'text' not in data:
        return 'Bad request', 400
    for token in [TOKEN1, TOKEN2, TOKEN3]:
        send_message(data['user_id'], f"👨‍💼 Оператор: {data['text']}", token)
    return 'OK', 200

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
