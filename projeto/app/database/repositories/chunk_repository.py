from app.database.connection import get_connection


def create_chunk(
    document_id: int,
    chunk_index: int,
    content: str,
    category: str | None,
    equipment: str | None,
    embedding: list[float],
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_chunks (
                    document_id, chunk_index, content, category, equipment, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (document_id, chunk_index, content, category, equipment, embedding),
            )
            chunk_id = cur.fetchone()[0]
        conn.commit()
        return chunk_id


def similarity_search(query_embedding: list[float], limit: int = 3):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    dc.id,
                    dc.content,
                    dc.category,
                    dc.equipment,
                    d.source_name,
                    dc.embedding <=> %s::vector AS distance
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, query_embedding, limit),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "content": row[1],
            "category": row[2],
            "equipment": row[3],
            "source_name": row[4],
            "distance": row[5],
        }
        for row in rows
    ]