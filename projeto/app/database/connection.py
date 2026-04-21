import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url, autocommit=False)

    # fallback Docker correto
    return psycopg.connect(
        host="db",   # 🔥 AQUI ESTAVA O ERRO
        port=5432,
        dbname="ragdb",
        user="raguser",
        password="ragpass",
        autocommit=False,
    )