import os
import requests
from flask import Flask, request, jsonify
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
    return "API JustSend V2 działa ✅"
