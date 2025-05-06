from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_URL = "https://rest.justsend.pl/sender/singlemessage/send"
API_KEY = os.getenv("JS_API_KEY")

@app.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get("phone")
    text = data.get("text")

    if not phone or not text:
        return jsonify({"error": "Brakuje numeru telefonu lub treści"}), 400

    payload = {
        "recipient": phone,
        "messageText": text,
        "sender": os.getenv("JS_SENDER"),
        "messageCustomId": "msg-" + phone[-4:]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    return jsonify({
        "status": response.status_code,
        "response": response.text
    })

@app.route("/", methods=["GET"])
def home():
    return "JustSend SMS API działa ✅"

# ⬇️ TO JEST NAJWAŻNIEJSZY FRAGMENT DLA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
