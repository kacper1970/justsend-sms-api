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

# Webhook Secret z ElevenLabs
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/", methods=["GET"])
def home():
    return "✅ API działa – webhook + HMAC + SMS"

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
        except Exception as e:
            return jsonify({"error": "Nieprawidłowy format nagłówka", "details": str(e)}), 400

        # Sprawdzenie czy podpis nie jest za stary (300s = 5 min)
        if abs(int(time.time()) - int(timestamp)) > 300:
            return jsonify({"error": "Zbyt stary podpis"}), 400

        # Oblicz własny podpis HMAC
        message = f"{timestamp}.{raw_body.decode('utf-8')}"
        computed_signature = hmac.new(
            key=WEBHOOK_SECRET.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(f"v0={computed_signature}", f"v0={sent_signature}"):
            return jsonify({"error": "Nieprawidłowy podpis HMAC"}), 403

        # Parsowanie danych JSON
        data = request.get_json()
        metadata = data.get("data", {}).get("metadata", {})

        phone = metadata.get("phone")
        text = metadata.get("text")
        adres = metadata.get("adres_problem")
        problem = metadata.get("problem")

        if not all([phone, text, adres, problem]):
            return jsonify({"error": "Brakuje wymaganych danych", "metadata": metadata}), 400

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
                "status": "Błąd przy wysyłaniu SMS",
                "code": response.status_code,
                "response": response.text
            }), response.status_code

    except Exception as e:
        return jsonify({"error": "Błąd krytyczny aplikacji", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
