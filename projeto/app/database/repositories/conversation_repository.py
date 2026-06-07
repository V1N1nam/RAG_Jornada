from app.database.connection import get_connection


def get_conversation_by_phone(phone: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, phone, current_state, last_intent, is_active, created_at, updated_at, loja_id
                FROM conversations
                WHERE phone = %s
                """,
                (phone,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "phone": row[1],
                "current_state": row[2],
                "last_intent": row[3],
                "is_active": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "loja_id": row[7],
            }


def create_conversation(phone: str, current_state: str = "new"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (phone, current_state)
                VALUES (%s, %s)
                RETURNING id
                """,
                (phone, current_state),
            )
            conversation_id = cur.fetchone()[0]
        conn.commit()
        return conversation_id


def get_or_create_conversation(phone: str):
    conversation = get_conversation_by_phone(phone)
    if conversation:
        return conversation

    conversation_id = create_conversation(phone)
    return get_conversation_by_id(conversation_id)


def get_conversation_by_id(conversation_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, phone, current_state, last_intent, is_active, created_at, updated_at, loja_id
                FROM conversations
                WHERE id = %s
                """,
                (conversation_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "phone": row[1],
                "current_state": row[2],
                "last_intent": row[3],
                "is_active": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "loja_id": row[7],
            }


def update_conversation_loja(phone: str, loja_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE conversations SET loja_id = %s, updated_at = NOW() WHERE phone = %s",
                (loja_id, phone),
            )
        conn.commit()


def update_conversation_state(phone: str, current_state: str, last_intent: str | None = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE conversations
                SET current_state = %s,
                    last_intent = %s,
                    updated_at = NOW()
                WHERE phone = %s
                """,
                (current_state, last_intent, phone),
            )
        conn.commit()