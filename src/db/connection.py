import psycopg
import os


def get_db_connection():
    conn = psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="db",  # important: service name from docker-compose
        port=5432
    )
    return conn
