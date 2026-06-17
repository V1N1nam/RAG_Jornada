from app.services.embedding_service import embed_text
from app.services.llm_service import ask_llm
from app.database.repositories.chunk_repository import similarity_search


def retrieve_context(question: str, k: int = 3):
    query_embedding = embed_text(question)
    results = similarity_search(query_embedding=query_embedding, limit=k)
    return results


def ask_question(
    question: str,
    k: int = 3,
    extra_context: str = "",
    mode: str = "support",
    history: str = "",
) -> dict:
    search_query = (question + " " + extra_context[:400]).strip() if extra_context else question
    results = retrieve_context(search_query, k=k)

    rag_context = "\n\n".join([item["content"] for item in results])
    context = (extra_context + "\n\n" + rag_context).strip() if extra_context else rag_context

    llm_question = question
    if mode == "alarmes" and extra_context:
        llm_question = (
            question
            + "\n\nCom base nos dados acima: apresente os alarmes listados em ALARMES ATIVOS NUMERADOS "
            "mantendo exatamente a mesma numeração e ordem. Para cada alarme explique brevemente o que significa. "
            "Ao final, informe ao usuário que pode digitar o número do alarme para obter mais detalhes."
        )
    elif mode == "alarme_detalhe" and extra_context:
        llm_question = (
            question
            + "\n\nCom base nos dados acima: explique em detalhes o que esse alarme significa, "
            "qual é a causa técnica mais provável, há quanto tempo está ativo, e quais "
            "verificações simples e seguras o usuário pode fazer antes de acionar um técnico."
        )

    answer = ask_llm(context, llm_question, history)

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