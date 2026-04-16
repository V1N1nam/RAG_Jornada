from flask import Flask, request, jsonify
from dotenv import load_dotenv

from app.services.rag_service import ask_question

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
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Campo 'question' é obrigatório"}), 400

    result = ask_question(question)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)