from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app.config import MOCK_DIR, VECTORSTORE_PATH
from app.utils.text_loader import load_mock_documents


EMBEDDING_MODEL = "text-embedding-3-small"


def get_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def build_vectorstore():
    docs = load_mock_documents(MOCK_DIR)
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore


def save_vectorstore(vectorstore):
    VECTORSTORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_PATH))


def load_vectorstore():
    embeddings = get_embeddings()
    return FAISS.load_local(
        str(VECTORSTORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )


def vectorstore_exists() -> bool:
    index_file = Path(str(VECTORSTORE_PATH)) / "index.faiss"
    pkl_file = Path(str(VECTORSTORE_PATH)) / "index.pkl"
    return index_file.exists() and pkl_file.exists()