from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# JustSend konfiguracja
JS_URL = "https://justsend.io/api/sender/singlemessage/send"
JS_KEY = os.getenv("JS_APP_KEY")
JS_SENDER = os.getenv("JS_SENDER", "ENERTIA")
JS_VARIANT = os.getenv("JS_VARIANT", "PRO")

@app.route("/", methods=["GET"])
def home():
    return "✅ API działa – odbiera webhook i wysyła SMS"

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    try:
        data = request.get_json()
        print("Webhook payload:", data)

        # Przykład: weź pierwszy komunikat użytkownika jako treść
        transcript = data.get("data", {}).get("transcript", [])
        user_message = next((t["message"] for t in transcript if t["role"] == "user"), None)
        phone = data.get("data", {}).get("metadata", {}).get("phone", None)

        if not phone or not user_message:
            return jsonify({"error": "Brakuje numeru telefonu lub treści"}), 400

        # Wyślij SMS
        payload = {
            "sender": JS_SENDER,
            "msisdn": phone,
            "bulkVariant": JS_VARIANT,
            "content": f"Twoja rozmowa: {user_message}"
        }

        headers = {
            "App-Key": JS_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(JS_URL, json=payload, headers=headers)

        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "SMS wysłany"}), 200
        else:
            return jsonify({"status": "Błąd", "code": response.status_code, "response": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500
