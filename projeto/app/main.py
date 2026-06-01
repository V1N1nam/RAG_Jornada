from dotenv import load_dotenv
from app.services.rag_service import ask_question
from app.services.eletrofio_service import buscar_contexto_loja

load_dotenv()


def main():
    loja_id_input = input("ID da loja (deixe em branco para ignorar): ").strip()
    loja_id = int(loja_id_input) if loja_id_input.isdigit() else None

    print("\nChat iniciado (digite 'sair' para encerrar)\n")

    while True:
        question = input("Pergunta: ").strip()

        if question.lower() == "sair":
            print("Encerrando.")
            break

        extra_context = buscar_contexto_loja(loja_id) if loja_id else ""
        result = ask_question(question, extra_context=extra_context)

        print("\n=== FONTES ENCONTRADAS ===")
        for i, source in enumerate(result["sources"], start=1):
            print(f"\n[{i}] Arquivo: {source['source']}")
            print(f"Categoria: {source['category']}")
            print(f"Distância: {source['distance']}")
            print(f"Conteúdo: {source['content']}")

        print("\n=== RESPOSTA ===")
        print(result["answer"])
        print()


if __name__ == "__main__":
    main()