from fastapi import FastAPI, Request
import aiohttp
import asyncio
import json
from datetime import datetime
import re

app = FastAPI()

JUSTSEND_API_URL = "https://api.justsend.pl/api/sender/singlemessage/send"
JUSTSEND_API_KEY = "Twój_Klucz_API_Tutaj"  # <-- Wstaw swój klucz API

LOG_FILE = "webhook_logs.txt"

# Zapisz webhook do pliku logów
def log_to_file(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

# Formatuj numer telefonu do formatu 48793930991
def format_phone_number(phone: str) -> str:
    phone_digits_only = re.sub(r"\D", "", phone)
    if not phone_digits_only.startswith("48"):
        phone_digits_only = f"48{phone_digits_only}"
    return phone_digits_only

# Główna funkcja do wysyłki SMS
async def send_sms(payload: dict):
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JUSTSEND_API_KEY}"
        }
        async with session.post(JUSTSEND_API_URL, json=payload, headers=headers) as response:
            response_text = await response.text()
            return response.status, response_text

@app.post("/")
async def webhook_listener(request: Request):
    headers = dict(request.headers)
    body = await request.json()

    # Logujemy webhooka
    log_text = f"===== NOWY WEBHOOK =====\nHeaders:\n{json.dumps(headers, indent=2)}\n\nBody:\n{json.dumps(body, indent=2, ensure_ascii=False)}"
    log_to_file(log_text)

    # Wyciągamy dane
    data = body.get("data", {})
    extracted = data.get("analysis", {}).get("data_collection_results", {})

    # Jeśli nie ma wymaganych danych – kończymy
    if not extracted:
        return {"status": "ignored - no data"}

    date = extracted.get("text", {}).get("value", "N/N")
    address = extracted.get("adres", {}).get("value", "N/N")
    phone = extracted.get("phone", {}).get("value", "N/N")
    problem = extracted.get("problem", {}).get("value", "N/N")

    # Formatowanie numeru telefonu
    msisdn = format_phone_number(phone)

    # Treść wiadomości
    content = (
        f"Potwierdzenie wizyty:\n"
        f"📅 Termin: {date}\n"
        f"📍 Adres: {address}\n"
        f"📞 Tel: {msisdn}\n"
        f"🛠️ Problem: {problem}"
    )

    # Payload SMS
    sms_payload = {
        "sender": "WEB",
        "msisdn": msisdn,
        "bulkVariant": "PRO",
        "content": content
    }

    # Wysyłka SMS i log
    status, response_text = await send_sms(sms_payload)
    sms_log = f"===== WYSYŁKA SMS =====\nPayload:\n{json.dumps(sms_payload, indent=2, ensure_ascii=False)}\n\nResponse:\nStatus code: {status}\n{response_text}"
    log_to_file(sms_log)

    return {"status": "ok", "sms_status": status}
