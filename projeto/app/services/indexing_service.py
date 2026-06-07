from app.config import BASE_DIR
from app.utils.text_loader import load_mock_documents
from app.services.embedding_service import embed_text
from app.database.repositories.document_repository import create_document
from app.database.repositories.chunk_repository import create_or_update_chunk


MOCK_DIR = BASE_DIR / "data" / "mock"


def index_mock_documents():
    documents = load_mock_documents(MOCK_DIR)

    for doc in documents:
        source_name = doc.metadata["source"]
        category = doc.metadata.get("category")
        equipment = doc.metadata.get("equipment")
        chunk_index = doc.metadata["chunk_id"]
        content = doc.page_content

        document_id = create_document(
            source_name=source_name,
            source_type="manual_mock",
            category=category,
        )

        embedding = embed_text(content)

        chunk_id = create_or_update_chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            category=category,
            equipment=equipment,
            embedding=embedding,
        )

        print(f"Chunk indexado: doc={source_name} chunk={chunk_index} id={chunk_id}")


if __name__ == "__main__":
    index_mock_documents()