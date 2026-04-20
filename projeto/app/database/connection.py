import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL não está definida")

    return psycopg.connect(
        database_url,
        autocommit=False
    )