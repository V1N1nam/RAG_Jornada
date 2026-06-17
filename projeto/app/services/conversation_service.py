from app.database.repositories.conversation_repository import (
    get_or_create_conversation,
    update_conversation_state,
)
from app.database.repositories.message_repository import create_message, get_recent_messages


def register_user_message(phone: str, text: str):
    conversation = get_or_create_conversation(phone)
    create_message(conversation["id"], "user", text)
    return conversation


def register_assistant_message(conversation_id: int, text: str):
    create_message(conversation_id, "assistant", text)


def set_conversation_state(phone: str, state: str, intent: str | None = None):
    update_conversation_state(phone, state, intent)


def get_historico_formatado(conversation_id: int, limit: int = 8) -> str:
    """
    Retorna as últimas trocas da conversa formatadas para o prompt do LLM.
    A mensagem atual do usuário (já registrada no DB) é excluída para evitar duplicação.
    """
    msgs = get_recent_messages(conversation_id, limit=limit + 1)
    # A mensagem atual do usuário foi registrada antes de chamar o LLM — exclui do histórico
    if msgs and msgs[-1]["sender"] == "user":
        msgs = msgs[:-1]
    if not msgs:
        return ""
    lines = []
    for m in msgs:
        role = "Usuário" if m["sender"] == "user" else "Assistente"
        content = m["message_text"]
        if len(content) > 300:
            content = content[:297] + "..."
        lines.append(f"{role}: {content}")
    return "\n".join(lines)