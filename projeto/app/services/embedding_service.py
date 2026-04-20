from langchain_openai import OpenAIEmbeddings

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding_model():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def embed_text(text: str) -> list[float]:
    embeddings = get_embedding_model()
    return embeddings.embed_query(text)