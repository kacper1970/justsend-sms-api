from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfiguracja JustSend
JUSTSEND_URL = "https://justsend.io/api/sender/singlemessage/send"
APP_KEY = os.getenv("JS_APP_KEY")
SENDER = os.getenv("JS_SENDER", "ENERTIA")
VARIANT = os.getenv("JS_VARIANT", "PRO")

@app.route("/", methods=["GET"])
def home():
    return "✅ API działa – gotowe do odbioru webhooka i wysyłki SMS"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        metadata = data.get("data", {}).get("metadata", {})
        phone = metadata.get("phone")
        text = metadata.get("text")
        adres = metadata.get("adres_problem")
        problem = metadata.get("problem")

        # Walidacja
        if not all([phone, text, adres, problem]):
            return jsonify({"error": "Brakuje jednego lub więcej wymaganych pól w metadata"}), 400

        # Tworzenie treści SMS
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

# Serwer deweloperski
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
