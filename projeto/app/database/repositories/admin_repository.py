from app.database.connection import get_connection


def clear_rag_data():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM document_chunks;")
            cur.execute("DELETE FROM documents;")
        conn.commit()