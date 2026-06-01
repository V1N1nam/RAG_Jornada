from app.database.repositories.conversation_repository import get_or_create_conversation
from app.services.conversation_service import (
    register_user_message,
    register_assistant_message,
    set_conversation_state,
)
from app.services.intent_service import detect_intent
from app.services.rag_service import ask_question
from app.services.eletrofio_service import buscar_contexto_loja

from app.services.natural_language_service import (
    generate_greeting,
    generate_problem_request,
    generate_human_handoff,
    generate_closing,
    generate_fallback,
)

def handle_chat_message(phone: str, text: str, loja_id: int | None = None) -> dict:
    conversation = register_user_message(phone, text)
    current_state = conversation["current_state"]
    intent = detect_intent(text)

    if intent == "closing":
        answer = generate_closing(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "closed", "closing")
        return {
            "phone": phone,
            "state": "closed",
            "intent": "closing",
            "answer": answer,
        }

    if intent == "human":
        answer = generate_human_handoff(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_human", "human")
        return {
            "phone": phone,
            "state": "awaiting_human",
            "intent": "human",
            "answer": answer,
        }

    if current_state in ("new", "closed") and intent == "greeting":
        answer = generate_greeting(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_intent", "greeting")
        return {
            "phone": phone,
            "state": "awaiting_intent",
            "intent": "greeting",
            "answer": answer,
        }

    if current_state == "awaiting_intent" and intent == "problem":
        answer = generate_problem_request(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_problem_description", "problem")
        return {
            "phone": phone,
            "state": "awaiting_problem_description",
            "intent": "problem",
            "answer": answer,
        }

    eletrofio_ctx = buscar_contexto_loja(loja_id) if loja_id else ""

    if current_state == "awaiting_problem_description":
        rag_result = ask_question(text, k=3, extra_context=eletrofio_ctx)
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
            "loja_id": loja_id,
        }

    if intent in ("question", "problem"):
        rag_result = ask_question(text, k=3, extra_context=eletrofio_ctx)
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
            "loja_id": loja_id,
        }

    answer = generate_fallback(text)
    register_assistant_message(conversation["id"], answer)
    set_conversation_state(phone, "awaiting_intent", "fallback")
    return {
        "phone": phone,
        "state": "awaiting_intent",
        "intent": "fallback",
        "answer": answer,
    }