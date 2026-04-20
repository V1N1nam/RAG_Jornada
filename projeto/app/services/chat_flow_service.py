from app.database.repositories.conversation_repository import get_or_create_conversation
from app.services.conversation_service import (
    register_user_message,
    register_assistant_message,
    set_conversation_state,
)
from app.services.intent_service import detect_intent
from app.services.rag_service import ask_question


def handle_chat_message(phone: str, text: str) -> dict:
    conversation = register_user_message(phone, text)
    current_state = conversation["current_state"]
    intent = detect_intent(text)

    if intent == "closing":
        answer = "Perfeito! Se precisar de mais alguma coisa, é só me chamar."
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "closed", "closing")
        return {
            "phone": phone,
            "state": "closed",
            "intent": "closing",
            "answer": answer,
        }

    if intent == "human":
        answer = "Certo. Posso encaminhar seu atendimento para um atendente."
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_human", "human")
        return {
            "phone": phone,
            "state": "awaiting_human",
            "intent": "human",
            "answer": answer,
        }

    if current_state in ("new", "closed") and intent == "greeting":
        answer = (
            "Olá! Posso te ajudar com problemas no equipamento, dúvidas técnicas "
            "ou encaminhamento para um atendente. Como posso ajudar?"
        )
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_intent", "greeting")
        return {
            "phone": phone,
            "state": "awaiting_intent",
            "intent": "greeting",
            "answer": answer,
        }

    if current_state == "awaiting_intent" and intent == "problem":
        answer = "Entendi. Pode me descrever melhor o problema que está acontecendo com o equipamento?"
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_problem_description", "problem")
        return {
            "phone": phone,
            "state": "awaiting_problem_description",
            "intent": "problem",
            "answer": answer,
        }

    if current_state == "awaiting_problem_description":
        rag_result = ask_question(text, k=3)
        answer = rag_result["answer"]
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "in_support", "problem_description")
        return {
            "phone": phone,
            "state": "in_support",
            "intent": "problem_description",
            "answer": answer,
            "sources": rag_result["sources"],
            "context": rag_result["context"],
        }

    if intent in ("question", "problem"):
        rag_result = ask_question(text, k=3)
        answer = rag_result["answer"]
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "in_support", intent)
        return {
            "phone": phone,
            "state": "in_support",
            "intent": intent,
            "answer": answer,
            "sources": rag_result["sources"],
            "context": rag_result["context"],
        }

    answer = "Entendi. Pode me dar mais detalhes para eu te ajudar melhor?"
    register_assistant_message(conversation["id"], answer)
    set_conversation_state(phone, "awaiting_intent", "fallback")
    return {
        "phone": phone,
        "state": "awaiting_intent",
        "intent": "fallback",
        "answer": answer,
    }