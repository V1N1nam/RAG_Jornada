import requests

API_URL = "https://rag-jornada.onrender.com/ask"


def should_end(answer: str) -> bool:
    """
    Fallback caso backend não envie 'end'
    """
    triggers = [
        "até mais",
        "encerrando",
        "fico à disposição",
        "posso ajudar em mais alguma coisa",
        "qualquer coisa estou por aqui"
    ]

    answer_lower = answer.lower()
    return any(trigger in answer_lower for trigger in triggers)


def main():
    phone = input("Telefone: ").strip()

    print("\nChat iniciado (digite 'sair' para encerrar)\n")

    while True:
        msg = input("Você: ").strip()

        if msg.lower() == "sair":
            print("Encerrando.")
            break

        try:
            response = requests.post(
                API_URL,
                json={
                    "phone": phone,
                    "question": msg
                },
                timeout=60
            )

            if response.status_code != 200:
                print(f"\nErro {response.status_code}: {response.text}\n")
                continue

            data = response.json()

            answer = data.get("answer", "")
            end = data.get("end", False)

            print(f"\nAssistente: {answer}\n")

            # 🔥 ENCERRAMENTO AUTOMÁTICO
            if end or should_end(answer):
                print("Chat encerrado automaticamente.\n")
                break

        except Exception as e:
            print(f"\nErro de conexão: {e}\n")


if __name__ == "__main__":
    main()