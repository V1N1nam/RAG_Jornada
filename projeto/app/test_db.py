from app.database.init_db import init_db
from app.database.repositories.conversation_repository import get_or_create_conversation, update_conversation_state
from app.database.repositories.message_repository import create_message, list_messages_by_conversation


def main():
    init_db()

    phone = "5511999999999"

    conversation = get_or_create_conversation(phone)
    print("Conversa:")
    print(conversation)

    create_message(conversation["id"], "user", "Oi")
    create_message(conversation["id"], "assistant", "Olá! Como posso ajudar?")
    update_conversation_state(phone, "awaiting_intent", "greeting")

    messages = list_messages_by_conversation(conversation["id"])
    print("\nMensagens:")
    for msg in messages:
        print(msg)


if __name__ == "__main__":
    main()