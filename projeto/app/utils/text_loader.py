from pathlib import Path
from langchain_core.documents import Document


def split_text_into_chunks(text: str) -> list[str]:
    chunks = []
    for part in text.split("\n\n"):
        cleaned = part.strip()
        if cleaned:
            chunks.append(cleaned)
    return chunks


def load_mock_documents(mock_dir: Path) -> list[Document]:
    documents = []

    for file_path in mock_dir.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        chunks = split_text_into_chunks(text)

        for i, chunk in enumerate(chunks, start=1):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": file_path.name,
                        "chunk_id": i,
                        "category": file_path.stem,
                        "equipment": "compressor",
                        "type": "manual_mock",
                    },
                )
            )

    return documents