from pathlib import Path
from app.database.connection import get_connection


def init_db():
    schema_path = Path(__file__).with_name("schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()

    print("Banco inicializado com sucesso.")


if __name__ == "__main__":
    init_db()