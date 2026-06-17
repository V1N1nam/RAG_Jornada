from app.database.connection import get_connection


def create_message(conversation_id: int, sender: str, message_text: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (conversation_id, sender, message_text)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (conversation_id, sender, message_text),
            )
            message_id = cur.fetchone()[0]
        conn.commit()
        return message_id


def get_recent_messages(conversation_id: int, limit: int = 8) -> list[dict]:
    """Retorna as últimas `limit` mensagens em ordem cronológica (mais antigas primeiro)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender, message_text
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (conversation_id, limit),
            )
            rows = cur.fetchall()
    return [{"sender": row[0], "message_text": row[1]} for row in reversed(rows)]


def list_messages_by_conversation(conversation_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, conversation_id, sender, message_text, created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (conversation_id,),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "conversation_id": row[1],
            "sender": row[2],
            "message_text": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]