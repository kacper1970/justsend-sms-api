from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_URL = "https://api.justsend.pl/sender/singlemessage/send"
API_KEY = os.getenv("JS_API_KEY")  # Upewnij się, że ta zmienna jest ustawiona w środowisku

@app.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    msisdn = data.get("phone")
    content = data.get("text")
    sender = os.getenv("JS_SENDER", "ENERTIA")  # Domyślny nadawca
    bulk_variant = os.getenv("JS_VARIANT", "ECO")  # Domyślny wariant

    if not API_KEY:
        return jsonify({"error": "Brak klucza API (JS_API_KEY)"}), 500
    if not msisdn or not content:
        return jsonify({"error": "Brakuje numeru telefonu lub treści wiadomości"}), 400

    payload = {
        "sender": sender,
        "msisdn": msisdn,
        "bulkVariant": bulk_variant,
        "content": content
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 204:
            return jsonify({"status": "OK", "message": "Wiadomość została wysłana pomyślnie."})
        else:
            return jsonify({"status": "Błąd", "code": response.status_code, "response": response.text}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "JustSend SMS API działa ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
