from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Dodanie obsługi CORS

@app.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get("phone")
    text = data.get("text")

    if not phone or not text:
        return jsonify({"error": "Brakuje numeru telefonu lub treści"}), 400

    payload = {
        "username": os.getenv("JS_LOGIN"),
        "password": os.getenv("JS_PASS"),
        "sender": os.getenv("JS_SENDER"),
        "text": text,
        "phone": phone,
        "type": "eco"
    }

    response = requests.post("https://rest.justsend.pl/api/rest/message",
                             json=payload,
                             headers={"Content-Type": "application/json"})

    return jsonify({
        "status": response.status_code,
        "response": response.text
    })

@app.route("/", methods=["GET"])
def home():
    return "JustSend SMS API działa ✅"
