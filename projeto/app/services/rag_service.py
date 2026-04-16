from app.services.vectorstore_service import (
    build_vectorstore,
    save_vectorstore,
    load_vectorstore,
    vectorstore_exists,
)
from app.services.llm_service import ask_llm


def initialize_vectorstore(force_rebuild: bool = False):
    if force_rebuild or not vectorstore_exists():
        vectorstore = build_vectorstore()
        save_vectorstore(vectorstore)
        return vectorstore

    return load_vectorstore()


def retrieve_context(question: str, k: int = 3):
    vectorstore = initialize_vectorstore()
    results = vectorstore.similarity_search(question, k=k)
    return results


def ask_question(question: str, k: int = 3) -> dict:
    results = retrieve_context(question, k=k)

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    answer = ask_llm(context, question)

    sources = [
        {
            "source": doc.metadata.get("source"),
            "category": doc.metadata.get("category"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "content": doc.page_content
        }
        for doc in results
    ]

    return {
        "question": question,
        "context": context,
        "sources": sources,
        "answer": answer
    }