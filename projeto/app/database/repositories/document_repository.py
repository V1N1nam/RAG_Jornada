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


def get_document_by_source_name(source_name: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source_name, source_type, category, created_at
                FROM documents
                WHERE source_name = %s
                """,
                (source_name,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "source_name": row[1],
        "source_type": row[2],
        "category": row[3],
        "created_at": row[4],
    }