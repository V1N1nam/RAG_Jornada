import requests

API_URL = "https://rag-jornada.onrender.com/ask"


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

            print(f"\nAssistente: {data.get('answer')}\n")

        except Exception as e:
            print(f"\nErro de conexão: {e}\n")


if __name__ == "__main__":
    main()