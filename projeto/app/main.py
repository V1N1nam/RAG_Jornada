from dotenv import load_dotenv
from app.services.rag_service import ask_question

load_dotenv()


def main():
    question = input("Pergunta: ").strip()
    result = ask_question(question)

    print("\n=== FONTES ENCONTRADAS ===")
    for i, source in enumerate(result["sources"], start=1):
        print(f"\n[{i}] Arquivo: {source['source']}")
        print(f"Categoria: {source['category']}")
        print(f"Chunk: {source['chunk_id']}")
        print(f"Conteúdo: {source['content']}")

    print("\n=== RESPOSTA ===")
    print(result["answer"])


if __name__ == "__main__":
    main()