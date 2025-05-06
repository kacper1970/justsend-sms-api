from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfiguracja
API_URL = "https://api.justsend.pl/sender/singlemessage/send"
API_KEY = os.getenv("JS_API_KEY")           # Twój Bearer Token z JustSend
SENDER = os.getenv("JS_SENDER", "ENERTIA")  # Nazwa nadawcy SMS
VARIANT = os.getenv("JS_VARIANT", "FULL")    # Typ wiadomości: ECO, PRO, itd.

@app.route("/send_sms", methods=["POST"])
def send_sms():
    data = request.get_json()

    msisdn = data.get("phone")
    content = data.get("text")

    if not API_KEY:
        return jsonify({"error": "Brak klucza API (JS_API_KEY)"}), 500
    if not msisdn or not content:
        return jsonify({"error": "Brakuje numeru telefonu lub treści"}), 400

    payload = {
        "sender": SENDER,
        "msisdn": msisdn,
        "bulkVariant": VARIANT,
        "content": content
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "SMS został wysłany pomyślnie."}), 200
        elif response.status_code == 400:
            return jsonify({"status": "Błąd", "code": 400, "message": "Nieprawidłowe dane wejściowe."}), 400
        elif response.status_code == 403:
            return jsonify({"status": "Błąd", "code": 403, "message": "Brak autoryzacji – sprawdź Bearer Token."}), 403
        else:
            return jsonify({"status": "Błąd", "code": response.status_code, "response": response.text}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Błąd połączenia z JustSend", "details": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ JustSend SMS API v2 działa"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
