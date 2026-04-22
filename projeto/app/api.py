from flask import Flask, request, jsonify
from dotenv import load_dotenv

from app.services.chat_flow_service import handle_chat_message

import requests

EVOLUTION_URL = "http://projeto-evolution-api:8080"
INSTANCE = "rag-bot"
API_KEY = "123456"

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API RAG online"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True) or {}

    phone = str(data.get("phone", "")).strip()
    question = str(data.get("question", "")).strip()

    if not phone:
        return jsonify({"error": "Campo 'phone' é obrigatório"}), 400

    if not question:
        return jsonify({"error": "Campo 'question' é obrigatório"}), 400

    result = handle_chat_message(phone, question)

    return jsonify({
        "answer": result
    })

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        data = request.get_json(force=True)

        message = data.get("data", {}).get("message", {})
        key = data.get("data", {}).get("key", {})

        phone_full = key.get("remoteJid", "")

        if "@g.us" in phone_full:
            return jsonify({"status": "ignored group"}), 200
        
        if not phone_full or "@g.us" in phone_full:
            return jsonify({"status": "ignored"}), 200

        phone = phone_full.split("@")[0]

        # 🔥 captura qualquer texto possível
        message_text = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("imageMessage", {}).get("caption")
            or message.get("videoMessage", {}).get("caption")
            or ""
        )

        if not message_text:
            return jsonify({"status": "no text"}), 200

        # 🔥 processa IA/RAG
        result = handle_chat_message(phone, message_text)

        answer = result.get("answer") if isinstance(result, dict) else str(result)

        if not answer:
            return jsonify({"status": "no answer"}), 200

        # 🔥 envia resposta
        requests.post(
            f"{EVOLUTION_URL}/message/sendText/{INSTANCE}",
            headers={"apikey": API_KEY},
            json={
                "number": phone,
                "text": answer
            },
            timeout=10
        )

        return jsonify({"status": "ok"})

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return jsonify({"status": "error"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)