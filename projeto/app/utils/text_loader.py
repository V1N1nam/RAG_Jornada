import re
from pathlib import Path
from langchain_core.documents import Document

# Matches: [CHUNK-NNN]\nCATEGORIA: ...\nTÓPICO: ...\n---\n<content>
# [^\n]+ used for single-line fields so re.DOTALL doesn't bleed across lines
_CHUNK_RE = re.compile(
    r"\[CHUNK-\d+\]\s*\nCATEGORIA:\s*([^\n]+)\nTÓPICO:\s*([^\n]+)\n---\n(.*?)(?=---\n\[CHUNK-|\Z)",
    re.DOTALL,
)


def _load_structured(file_path: Path) -> list[Document]:
    text = file_path.read_text(encoding="utf-8")
    documents = []
    for i, m in enumerate(_CHUNK_RE.finditer(text), start=1):
        categoria = m.group(1).strip()
        topico = m.group(2).strip()
        content = m.group(3).strip()
        if not content:
            continue
        documents.append(
            Document(
                page_content=f"CATEGORIA: {categoria}\nTÓPICO: {topico}\n\n{content}",
                metadata={
                    "source": file_path.name,
                    "chunk_id": i,
                    "category": categoria,
                    "equipment": categoria,
                    "type": "manual_mock",
                },
            )
        )
    return documents


def _load_plain(file_path: Path) -> list[Document]:
    text = file_path.read_text(encoding="utf-8")
    documents = []
    for i, part in enumerate((p.strip() for p in text.split("\n\n")), start=1):
        if part:
            documents.append(
                Document(
                    page_content=part,
                    metadata={
                        "source": file_path.name,
                        "chunk_id": i,
                        "category": file_path.stem,
                        "equipment": file_path.stem,
                        "type": "manual_mock",
                    },
                )
            )
    return documents


def load_mock_documents(mock_dir: Path) -> list[Document]:
    documents = []
    for file_path in mock_dir.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        if "[CHUNK-" in text:
            docs = _load_structured(file_path)
        else:
            docs = _load_plain(file_path)
        documents.extend(docs)
        print(f"  {file_path.name}: {len(docs)} chunks carregados")
    return documents