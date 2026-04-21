from flask import Flask, request, jsonify
from dotenv import load_dotenv

from app.services.chat_flow_service import handle_chat_message

import requests

EVOLUTION_URL = "http://localhost:8080"
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
    data = request.json

    try:
        key = data["data"]["key"]
        message_data = data["data"]["message"]

        phone_full = key["remoteJid"]

        # ❌ ignora grupos
        if "@g.us" in phone_full:
            return jsonify({"status": "ignored group"}), 200

        # ✔ número limpo
        phone = phone_full.split("@")[0]

        # ✔ pega texto da mensagem (forma segura)
        message = ""
        if "conversation" in message_data:
            message = message_data["conversation"]
        elif "extendedTextMessage" in message_data:
            message = message_data["extendedTextMessage"]["text"]

        if not message:
            return jsonify({"status": "no text"}), 200

    except Exception as e:
        print("Erro ao processar entrada:", e)
        return jsonify({"status": "ignored"}), 200

    # 🔥 chama seu sistema
    result = handle_chat_message(phone, message)
    answer = result if isinstance(result, str) else result.get("answer", "")

    # ❌ evita responder vazio
    if not answer:
        return jsonify({"status": "no answer"}), 200

    # 🚀 envia resposta pro WhatsApp
    try:
        requests.post(
            f"{EVOLUTION_URL}/message/sendText/{INSTANCE}",
            headers={
                "apikey": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "number": phone,
                "text": answer
            },
            timeout=10
        )
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)