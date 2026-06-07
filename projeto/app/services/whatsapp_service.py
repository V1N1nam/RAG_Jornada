import os
import requests

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "rag-evolution-key")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "rag-bot")


def send_message(phone: str, text: str) -> bool:
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": phone, "text": text}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[send_message] status={resp.status_code} body={resp.text[:300]}", flush=True)
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[send_message] exception={e}", flush=True)
        return False
