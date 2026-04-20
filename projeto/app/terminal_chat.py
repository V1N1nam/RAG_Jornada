from dotenv import load_dotenv
from app.services.chat_flow_service import handle_chat_message

load_dotenv()


def main():
    phone = input("Telefone do usuário: ").strip()

    print("\nChat iniciado. Digite 'sair' para encerrar.\n")

    while True:
        user_text = input("Você: ").strip()

        if user_text.lower() == "sair":
            print("Encerrando chat.")
            break

        result = handle_chat_message(phone, user_text)

        print(f"\nAssistente: {result['answer']}\n")

        if "sources" in result:
            print("Fontes encontradas:")
            for i, source in enumerate(result["sources"], start=1):
                print(f"[{i}] {source['source']} | categoria={source['category']} | distância={source['distance']}")
            print()
            
if __name__ == "__main__":
    main()