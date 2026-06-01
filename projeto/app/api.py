from flask import Flask, request, jsonify
from dotenv import load_dotenv

from app.services.chat_flow_service import handle_chat_message

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
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    question = data.get("question", "").strip()
    loja_id_raw = data.get("loja_id")

    if not phone:
        return jsonify({"error": "Campo 'phone' é obrigatório"}), 400

    if not question:
        return jsonify({"error": "Campo 'question' é obrigatório"}), 400

    loja_id = int(loja_id_raw) if loja_id_raw is not None else None

    result = handle_chat_message(phone, question, loja_id=loja_id)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)