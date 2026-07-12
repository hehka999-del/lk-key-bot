from flask import Flask, request
import requests
import random
import string
import os
from datetime import datetime, timedelta

app = Flask(__name__)
TOKEN = "8875608434:AAHSH69VZPwAHbUM4Iu4PAdV7xLrSr-58kk"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Каналы для проверки подписки
MAIN_CHANNEL = "@LKdeltaOFF"      # обязателен для FREE и VIP
EXTRA_CHANNEL = "@LKfreREPEo"     # дополнительно для VIP

# Хранилище ключей (в памяти)
keys_db = {}

def generate_key():
    prefix = "LK-"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return prefix + random_part

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def check_subscription(user_id, channel):
    """Проверяет, подписан ли user_id на канал channel."""
    url = f"{BASE_URL}/getChatMember"
    resp = requests.post(url, json={"chat_id": channel, "user_id": user_id})
    if resp.status_code == 200:
        data = resp.json()
        if data.get("ok"):
            status = data["result"]["status"]
            return status in ["member", "administrator", "creator"]
    return False

def build_main_keyboard():
    """Inline-клавиатура с кнопками выбора ключа."""
    return {
        "inline_keyboard": [
            [{"text": "🔓 Get FREE Key", "callback_data": "get_free"}],
            [{"text": "💎 Get VIP Key", "callback_data": "get_vip"}]
        ]
    }

def send_expiring_key(chat_id, key_type, key, expires_at):
    """Отправляет пользователю сгенерированный ключ с информацией о сроке."""
    days = (expires_at - datetime.now()).days
    text = (
        f"✅ Your {key_type} key:\n\n"
        f"<code>{key}</code>\n\n"
        f"⏳ Expires in {days} day(s)\n"
        f"📅 Expires at: {expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "Enter it in the cheat!"
    )
    send_message(chat_id, text)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    # Обработка CallbackQuery (нажатия на inline-кнопки)
    if "callback_query" in data:
        query = data["callback_query"]
        user_id = query["from"]["id"]
        chat_id = query["message"]["chat"]["id"]
        callback_data = query["data"]

        # Ответим, чтобы убрать "часики" на кнопке
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": query["id"]})

        if callback_data == "get_free":
            if not check_subscription(user_id, MAIN_CHANNEL):
                send_message(chat_id, "❌ Please subscribe to @LKdeltaOFF to get the FREE key.")
                return "ok"
            key = generate_key()
            expires = datetime.now() + timedelta(days=3)
            keys_db[key] = {"type": "FREE", "used": False, "expires_at": expires}
            send_expiring_key(chat_id, "FREE", key, expires)

        elif callback_data == "get_vip":
            if not check_subscription(user_id, MAIN_CHANNEL):
                send_message(chat_id, "❌ Please subscribe to @LKdeltaOFF to get the VIP key.")
                return "ok"
            if not check_subscription(user_id, EXTRA_CHANNEL):
                send_message(chat_id, "❌ Please also subscribe to @LKfreREPEo to get the VIP key.")
                return "ok"
            key = generate_key()
            expires = datetime.now() + timedelta(days=1)
            keys_db[key] = {"type": "VIP", "used": False, "expires_at": expires}
            send_expiring_key(chat_id, "VIP", key, expires)

        return "ok"

    # Обработка обычных сообщений (текст или команда)
    if "message" in data:
        msg = data["message"]
        text = msg.get("text", "")
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]

        if text == "/start":
            send_message(
                chat_id,
                "🔑 LK Key System\n\nChoose your key type:",
                reply_markup=build_main_keyboard()
            )
        else:
            # Проверка ключа (для Lua-скрипта)
            key = text.strip().upper()
            if key in keys_db:
                key_data = keys_db[key]
                # Проверяем, не истёк ли ключ
                if datetime.now() > key_data["expires_at"]:
                    send_message(chat_id, "EXPIRED")
                elif key_data["used"]:
                    send_message(chat_id, "USED")
                else:
                    key_data["used"] = True
                    send_message(chat_id, f"ACTIVATED|{key_data['type']}|{key_data['expires_at'].isoformat()}")
            else:
                send_message(chat_id, "INVALID")
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
