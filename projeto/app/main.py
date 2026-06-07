from dotenv import load_dotenv
from app.services.chat_flow_service import handle_chat_message
from app.database.repositories.conversation_repository import update_conversation_state

load_dotenv()

PHONE_TEST = "5511999990000"


def main():
    # Reset para "new" a cada execução no terminal
    update_conversation_state(PHONE_TEST, "new", None)

    print("=" * 50)
    print("  Teste do fluxo de chat (terminal)")
    print(f"  Telefone simulado: {PHONE_TEST}")
    print("  Digite 'sair' para encerrar.")
    print("=" * 50)
    print()

    while True:
        user_text = input("Você: ").strip()

        if not user_text:
            continue

        if user_text.lower() == "sair":
            print("Encerrando.")
            break

        result = handle_chat_message(PHONE_TEST, user_text)

        print(f"\nAssistente: {result['answer']}")
        print(f"  [estado={result['state']} | intent={result['intent']}", end="")
        if result.get("loja_id"):
            print(f" | loja_id={result['loja_id']}", end="")
        print("]")

        if result.get("sources"):
            print("  Fontes:")
            for i, s in enumerate(result["sources"], 1):
                print(f"    [{i}] {s['source']} | dist={s['distance']:.4f}")
        print()


if __name__ == "__main__":
    main()
