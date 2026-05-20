import os
import pytest
import psycopg2
from app import create_app

# Гнучке зчитування параметрів підключення для локального середовища та CI систем
TEST_DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "database": os.environ.get("POSTGRES_DB", "library_test_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "secret"),
}


@pytest.fixture(scope="session")
def app():
    # Фікстура створення інстансу додатка для тестової сесії
    app = create_app(db_config=TEST_DB_CONFIG)
    return app


@pytest.fixture(scope="session")
def client(app):
    # Надання клієнта виконання HTTP запитів
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_database():
    # Повне очищення і скидання лічильників ідентифікаторів перед кожним окремим тестом
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE books, authors RESTART IDENTITY CASCADE;")
            conn.commit()
    finally:
        conn.close()