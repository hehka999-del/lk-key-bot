from flask import Flask, request, jsonify
import requests
import random
import string
import os
from datetime import datetime, timedelta

app = Flask(__name__)
TOKEN = "8875608434:AAHSH69VZPwAHbUM4Iu4PAdV7xLrSr-58kk"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
MAIN_CHANNEL = "@LKdeltaOFF"
EXTRA_CHANNEL = "@LKfreREPEo"
keys_db = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def generate_key():
    return "LK-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def check_subscription(user_id, channel):
    resp = requests.post(f"{BASE_URL}/getChatMember", json={"chat_id": channel, "user_id": user_id})
    if resp.status_code == 200:
        data = resp.json()
        if data.get("ok") and data["result"]["status"] in ["member","administrator","creator"]:
            return True
    return False

# ========== ENDPOINT ДЛЯ LUA-СКРИПТА ==========
@app.route("/check", methods=["POST"])
def check_key():
    data = request.json
    if not data or "key" not in data:
        return jsonify({"status": "INVALID", "type": None})
    key = data["key"].strip().upper()
    if key in keys_db:
        kd = keys_db[key]
        if datetime.now() > kd["expires_at"]:
            return jsonify({"status": "EXPIRED", "type": kd["type"]})
        if kd["used"]:
            return jsonify({"status": "USED", "type": kd["type"]})
        kd["used"] = True
        return jsonify({"status": "ACTIVATED", "type": kd["type"], "expires": kd["expires_at"].isoformat()})
    else:
        return jsonify({"status": "INVALID", "type": None})

# ========== WEBHOOK TELEGRAM ==========
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if "callback_query" in data:
        q = data["callback_query"]
        user_id = q["from"]["id"]
        chat_id = q["message"]["chat"]["id"]
        cb = q["data"]
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": q["id"]})

        if cb == "get_free":
            if not check_subscription(user_id, MAIN_CHANNEL):
                send_message(chat_id, "❌ Please subscribe to @LKdeltaOFF to get the FREE key.")
                return "ok"
            key = generate_key()
            expires = datetime.now() + timedelta(days=3)
            keys_db[key] = {"type":"FREE","used":False,"expires_at":expires}
            send_message(chat_id,
                f"✅ Your FREE key:\n\n<code>{key}</code>\n\nExpires: {expires.strftime('%Y-%m-%d %H:%M UTC')}",
                reply_markup={"inline_keyboard":[[{"text":"📋 Copy key","callback_data":"copy_"+key}]]}
            )
        elif cb == "get_vip":
            if not check_subscription(user_id, MAIN_CHANNEL):
                send_message(chat_id, "❌ Please subscribe to @LKdeltaOFF to get the VIP key.")
                return "ok"
            if not check_subscription(user_id, EXTRA_CHANNEL):
                send_message(chat_id, "❌ Please also subscribe to @LKfreREPEo to get the VIP key.")
                return "ok"
            key = generate_key()
            expires = datetime.now() + timedelta(days=1)
            keys_db[key] = {"type":"VIP","used":False,"expires_at":expires}
            send_message(chat_id,
                f"💎 Your VIP key:\n\n<code>{key}</code>\n\nExpires: {expires.strftime('%Y-%m-%d %H:%M UTC')}",
                reply_markup={"inline_keyboard":[[{"text":"📋 Copy key","callback_data":"copy_"+key}]]}
            )
        elif cb.startswith("copy_"):
            # Показываем всплывающее уведомление с ключом (копирование в буфер обмена недоступно через бота,
            # но можно отправить ключ отдельным сообщением для выделения)
            key = cb[5:]
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"<code>{key}</code>",
                "parse_mode": "HTML"
            })
        return "ok"

    if "message" in data:
        msg = data["message"]
        text = msg.get("text","")
        chat_id = msg["chat"]["id"]
        if text == "/start":
            send_message(chat_id,
                "🔑 LK Key System\n\nChoose your key type:",
                reply_markup={"inline_keyboard":[
                    [{"text":"🔓 Get FREE Key","callback_data":"get_free"}],
                    [{"text":"💎 Get VIP Key","callback_data":"get_vip"}]
                ]}
            )
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
