from app.database.init_db import init_db
from app.database.repositories.admin_repository import clear_rag_data
from app.services.indexing_service import index_mock_documents


def main():
    print("Inicializando banco...")
    init_db()

    print("Limpando documentos e chunks...")
    clear_rag_data()

    print("Reindexando documentos mock...")
    index_mock_documents()

    print("Concluído com sucesso.")


if __name__ == "__main__":
    main()