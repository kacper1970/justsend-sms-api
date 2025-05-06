import time
import hmac
import hashlib
import subprocess
import json

# 🔐 Podaj tutaj swój Webhook Secret z ElevenLabs
WEBHOOK_SECRET = "wsec_45c606a6362eb7dfcf6ff8d0ce8c425399be51f587fab54ba9c6cf7e01f41c5c"

# 📦 Testowy webhook payload
payload = {
    "type": "post_call_transcription",
    "data": {
        "metadata": {
            "text": "14.05.2025 o 15:00",
            "adres_problem": "ul. Elektryczna 11, Wrocław",
            "phone": "793930991",
            "problem": "Brak napięcia w gniazdkach"
        }
    }
}

# 🕒 Timestamp i podpis
timestamp = str(int(time.time()))
body = json.dumps(payload)
message = f"{timestamp}.{body}"

signature = hmac.new(
    WEBHOOK_SECRET.encode("utf-8"),
    msg=message.encode("utf-8"),
    digestmod=hashlib.sha256
).hexdigest()

full_signature = f"t={timestamp},v0={signature}"

# 🛰️ curl jako subprocess
curl_command = [
    "curl", "-X", "POST", "https://justsend-sms-api-1.onrender.com/webhook",
    "-H", "Content-Type: application/json",
    "-H", f"elevenlabs-signature: {full_signature}",
    "-d", body
]

print("📡 Wysyłam webhook z podpisem HMAC...")
subprocess.run(curl_command)
