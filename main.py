from flask import Flask, request, jsonify
import requests
import os
import hmac
import hashlib
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# JustSend konfiguracja
JUSTSEND_URL = "https://justsend.io/api/sender/singlemessage/send"
APP_KEY = os.getenv("JS_APP_KEY")
SENDER = os.getenv("JS_SENDER", "ENERTIA")
VARIANT = os.getenv("JS_VARIANT", "PRO")

# Secret z ElevenLabs (Webhook Settings)
WEBHOOK_SECRET = os.getenv("wsec_fc5713b7a90b2061b760cdb06b7bd0b90f48b49435bb536ee43b0b4bc1e8e99e")

@app.route("/", methods=["GET"])
def home():
    return "✅ API działa – HMAC + SMS"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_body = request.data
        signature_header = request.headers.get("elevenlabs-signature")

        if not signature_header:
            return jsonify({"error": "Brak nagłówka elevenlabs-signature"}), 401

        try:
            timestamp_part, signature_part = signature_header.split(",")
            timestamp = timestamp_part.split("=")[1]
            sent_signature = signature_part.split("=")[1]
        except Exception:
            return jsonify({"error": "Nieprawidłowy format nagłówka"}), 400

        # Sprawdź, czy podpis nie jest za stary (np. starszy niż 5 min)
        if abs(int(time.time()) - int(timestamp)) > 300:
            return jsonify({"error": "Zbyt stary podpis"}), 400

        # Oblicz swój podpis
        message = f"{timestamp}.{raw_body.decode('utf-8')}"
        computed_signature = hmac.new(
            key=WEBHOOK_SECRET.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(f"v0={computed_signature}", f"v0={sent_signature}"):
            return jsonify({"error": "Nieprawidłowy podpis"}), 403

        # Odbierz dane i przygotuj SMS
        data = request.get_json()
        metadata = data.get("data", {}).get("metadata", {})

        phone = metadata.get("phone")
        text = metadata.get("text")
        adres = metadata.get("adres_problem")
        problem = metadata.get("problem")

        if not all([phone, text, adres, problem]):
            return jsonify({"error": "Brakuje wymaganych danych"}), 400

        sms_message = (
            "Potwierdzenie wizyty:\n"
            f"📅 Termin: {text}\n"
            f"📍 Adres: {adres}\n"
            f"📞 Tel: {phone}\n"
            f"🛠️ Problem: {problem}"
        )

        payload = {
            "sender": SENDER,
            "msisdn": phone,
            "bulkVariant": VARIANT,
            "content": sms_message
        }

        headers = {
            "App-Key": APP_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(JUSTSEND_URL, json=payload, headers=headers)

        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "SMS wysłany"}), 200
        else:
            return jsonify({
                "status": "Błąd",
                "code": response.status_code,
                "response": response.text
            }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
