from flask import Flask, request
import requests
import random
import string
import os

app = Flask(__name__)
TOKEN = "8875608434:AAHSH69VZPwAHbUM4Iu4PAdV7xLrSr-58kk"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
keys_db = {}

def generate_key():
    prefix = "LK-"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return prefix + random_part

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.route("/", methods=["POST"])
def webhook():
    update = request.json
    if "message" in update:
        msg = update["message"]
        text = msg.get("text", "")
        chat_id = msg["chat"]["id"]
        
        if text == "/start":
            send_message(chat_id, "🔑 LK Key System\n\n/free - FREE ключ (3 дня)\n/vip - VIP ключ (3 дня)")
        elif text == "/free":
            key = generate_key()
            keys_db[key] = {"type": "FREE", "used": False}
            send_message(chat_id, f"✅ Твой FREE ключ:\n\n{key}\n\nВведи его в чит!")
        elif text == "/vip":
            key = generate_key()
            keys_db[key] = {"type": "VIP", "used": False}
            send_message(chat_id, f"💎 Твой VIP ключ:\n\n{key}\n\nВведи его в чит!")
        else:
            key = text.upper()
            if key in keys_db:
                if keys_db[key]["used"]:
                    send_message(chat_id, "USED")
                else:
                    keys_db[key]["used"] = True
                    send_message(chat_id, f"ACTIVATED|{keys_db[key]['type']}")
            else:
                send_message(chat_id, "INVALID")
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
