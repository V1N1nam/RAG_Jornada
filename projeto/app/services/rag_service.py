from app.services.embedding_service import embed_text
from app.services.llm_service import ask_llm
from app.database.repositories.chunk_repository import similarity_search


def retrieve_context(question: str, k: int = 3):
    query_embedding = embed_text(question)
    results = similarity_search(query_embedding=query_embedding, limit=k)
    return results


def ask_question(question: str, k: int = 3) -> dict:
    results = retrieve_context(question, k=k)

    context = "\n\n".join([item["content"] for item in results])

    answer = ask_llm(context, question)

    sources = [
        {
            "source": item["source_name"],
            "category": item["category"],
            "distance": item["distance"],
            "content": item["content"],
        }
        for item in results
    ]

    return {
        "question": question,
        "context": context,
        "sources": sources,
        "answer": answer,
    }