from app.database.connection import get_connection


def create_document(source_name: str, source_type: str, category: str | None = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (source_name, source_type, category)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_name)
                DO UPDATE SET source_type = EXCLUDED.source_type,
                              category = EXCLUDED.category
                RETURNING id
                """,
                (source_name, source_type, category),
            )
            document_id = cur.fetchone()[0]
        conn.commit()
        return document_id