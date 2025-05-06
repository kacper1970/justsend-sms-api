from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_URL = "https://justsend.io/api/sender/singlemessage/send"
APP_KEY = os.getenv("JS_APP_KEY")
SENDER = os.getenv("JS_SENDER", "ENERTIA")
VARIANT = os.getenv("JS_VARIANT", "PRO")

@app.route("/send_sms", methods=["POST"])
def send_sms():
    data = request.get_json()
    msisdn = data.get("phone")
    content = data.get("text")

    if not APP_KEY:
        return jsonify({"error": "Brakuje klucza App-Key (JS_APP_KEY)"}), 500
    if not msisdn or not content:
        return jsonify({"error": "Brakuje numeru telefonu lub treści"}), 400

    payload = {
        "sender": SENDER,
        "msisdn": msisdn,
        "bulkVariant": VARIANT,
        "content": content
    }

    headers = {
        "App-Key": APP_KEY,
        "Content-Type": "application/json",
        "Accept": "*/*"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "SMS został wysłany pomyślnie."}), 200
        else:
            return jsonify({
                "status": "Błąd",
                "code": response.status_code,
                "response": response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Błąd połączenia z API", "details": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ JustSend SMS API (App-Key) działa poprawnie"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
