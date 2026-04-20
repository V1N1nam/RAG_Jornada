from app.database.repositories.conversation_repository import (
    get_or_create_conversation,
    update_conversation_state,
)
from app.database.repositories.message_repository import create_message


def register_user_message(phone: str, text: str):
    conversation = get_or_create_conversation(phone)
    create_message(conversation["id"], "user", text)
    return conversation


def register_assistant_message(conversation_id: int, text: str):
    create_message(conversation_id, "assistant", text)


def set_conversation_state(phone: str, state: str, intent: str | None = None):
    update_conversation_state(phone, state, intent)