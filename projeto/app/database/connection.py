import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url, autocommit=False)

    # fallback local (Docker)
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="ragdb",
        user="raguser",
        password="ragpass",
        autocommit=False,
    )