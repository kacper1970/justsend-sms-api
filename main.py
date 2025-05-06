from flask import Flask, request, jsonify
import os
import hmac
import hashlib
import time
import json
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# JustSend konfiguracja
JUSTSEND_URL = "https://justsend.io/api/sender/singlemessage/send"
APP_KEY = os.getenv("JS_APP_KEY")
SENDER = os.getenv("JS_SENDER", "WEB")
VARIANT = os.getenv("JS_VARIANT", "PRO")

# Webhook secret do weryfikacji HMAC
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/", methods=["GET"])
def index():
    return "✅ Serwer działa poprawnie"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_body = request.data
        signature = request.headers.get("elevenlabs-signature")

        # Zapisz log webhooka
        with open("logi_webhook.txt", "a") as log_file:
            log_file.write("===== NOWY WEBHOOK =====\n")
            log_file.write("Headers:\n")
            log_file.write(json.dumps(dict(request.headers), indent=2))
            log_file.write("\n\nBody:\n")
            log_file.write(raw_body.decode("utf-8"))
            log_file.write("\n\n")

        if not signature:
            return jsonify({"error": "Brak podpisu"}), 401

        try:
            t = signature.split(",")[0].split("=")[1]
            sig = signature.split(",")[1].split("=")[1]
        except Exception:
            return jsonify({"error": "Nieprawidłowy format podpisu"}), 400

        if abs(int(time.time()) - int(t)) > 7200:
            return jsonify({"error": "Zbyt stary podpis"}), 400

        message = f"{t}.{raw_body.decode()}"
        h = hmac.new(WEBHOOK_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
        if f"v0={h}" != f"v0={sig}":
            print("⚠️ Błąd podpisu HMAC – kontynuuję mimo to")

        data = request.get_json()
        results = data.get("data", {}).get("analysis", {}).get("data_collection_results", {})

        phone = results.get("phone", {}).get("value", "N/N")
        text = results.get("text", {}).get("value", "N/N")
        adres = results.get("adres", {}).get("value", "N/N")
        problem = results.get("problem", {}).get("value", "N/N")

        # Formatuj numer telefonu
        if phone.startswith("0"):
            phone = phone[1:]
        if phone != "N/N" and not phone.startswith("48"):
            phone = "48" + phone

        message_text = (
            f"Potwierdzenie wizyty:\n"
            f"📅 Termin: {text}\n"
            f"📍 Adres: {adres}\n"
            f"📞 Tel: {phone}\n"
            f"🛠️ Problem: {problem}"
        )

        payload = {
            "sender": SENDER,
            "msisdn": phone,
            "bulkVariant": VARIANT,
            "content": message_text
        }

        headers = {
            "App-Key": APP_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(JUSTSEND_URL, json=payload, headers=headers)

        # Zapisz log wysyłki SMS
        with open("logi_webhook.txt", "a") as log_file:
            log_file.write("===== WYSYŁKA SMS =====\n")
            log_file.write("Payload:\n")
            log_file.write(json.dumps(payload, indent=2, ensure_ascii=False))
            log_file.write("\n\nResponse:\n")
            log_file.write(f"Status code: {response.status_code}\n")
            log_file.write(response.text)
            log_file.write("\n\n\n")

        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "SMS wysłany"}), 200
        else:
            return jsonify({
                "status": "Błąd SMS",
                "code": response.status_code,
                "response": response.text
            }), response.status_code

    except Exception as e:
        print("❌ Błąd:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/log", methods=["GET"])
def log():
    try:
        with open("logi_webhook.txt", "r") as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except FileNotFoundError:
        return "Brak logów", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
