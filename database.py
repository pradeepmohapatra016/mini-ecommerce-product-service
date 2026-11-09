import os
import sqlite3

DATABASE_NAME = os.getenv("DATABASE_PATH", "/app/data/products.db")


def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_NAME), exist_ok=True)
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    connection.commit()
    connection.close()