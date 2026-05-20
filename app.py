import psycopg2
from flask import Flask, jsonify, request

# Стандартна конфігурація для робочого середовища
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "library_db",
    "user": "postgres",
    "password": "secret",
}


def create_app(db_config=None):
    # Фабрика створення застосунку за специфікацією Кроку 2
    app = Flask(__name__)

    # Використовуємо тестову конфігурацію, якщо її передано з conftest.py
    app.config["DB_CONFIG"] = db_config if db_config else DEFAULT_DB_CONFIG

    def get_db_connection():
        return psycopg2.connect(**app.config["DB_CONFIG"])

    def init_db():
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS authors (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        birth_year INTEGER
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS books (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        genre VARCHAR(100),
                        year_published INTEGER,
                        author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL,
                        created_by VARCHAR(150) NOT NULL
                    )
                """)
                conn.commit()
        finally:
            conn.close()

    # Обов'язкова ініціалізація структури таблиць
    init_db()

    # ----------------------------------------
    # ROUTES REGISTRY
    # ----------------------------------------
    @app.route("/api/authors", methods=["POST"])
    def create_author():
        data = request.json
        if not data or not data.get("name") or not str(data["name"]).strip():
            return jsonify({"error": "field 'name' is required"}), 400

        name = str(data["name"]).strip()
        birth_year = data.get("birth_year")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO authors (name, birth_year) VALUES (%s, %s) RETURNING id, name, birth_year",
                    (name, birth_year),
                )
                row = cur.fetchone()
                conn.commit()
        finally:
            conn.close()
        return (
            jsonify({"id": row[0], "name": row[1], "birth_year": row[2]}),
            201,
        )

    @app.route("/api/authors", methods=["GET"])
    def get_authors():
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, birth_year FROM authors ORDER BY id")
                rows = cur.fetchall()
        finally:
            conn.close()
        return (
            jsonify(
                [{"id": r[0], "name": r[1], "birth_year": r[2]} for r in rows]
            ),
            200,
        )

    @app.route("/api/authors/<int:author_id>", methods=["GET"])
    def get_author_by_id(author_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, birth_year FROM authors WHERE id = %s",
                    (author_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        if row is None:
            return jsonify({"error": f"Author with id {author_id} not found"}), 404
        return jsonify({"id": row[0], "name": row[1], "birth_year": row[2]}), 200

    @app.route("/api/authors/<int:author_id>", methods=["DELETE"])
    def delete_author(author_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM authors WHERE id = %s RETURNING id",
                    (author_id,),
                )
                row = cur.fetchone()
                conn.commit()
        finally:
            conn.close()
        if row is None:
            return jsonify({"error": "Target author not found"}), 404
        return "", 204

    @app.route("/api/books", methods=["POST"])
    def create_book():
        data = request.json
        if not data or not data.get("title") or not str(data["title"]).strip():
            return jsonify({"error": "field 'title' is required"}), 400
        if not data.get("created_by") or not str(data["created_by"]).strip():
            return jsonify({"error": "field 'created_by' is required"}), 400

        title = str(data["title"]).strip()
        created_by = str(data["created_by"]).strip()
        genre = data.get("genre")
        year_published = data.get("year_published")
        author_id = data.get("author_id")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                if author_id is not None:
                    cur.execute(
                        "SELECT id FROM authors WHERE id = %s", (author_id,)
                    )
                    if cur.fetchone() is None:
                        return (
                            jsonify({
                                "error": f"Author with id {author_id} not found"
                            }),
                            400,
                        )

                cur.execute(
                    """
                    INSERT INTO books (title, genre, year_published, author_id, created_by)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, title, genre, year_published, author_id, created_by
                    """,
                    (title, genre, year_published, author_id, created_by),
                )
                row = cur.fetchone()
                conn.commit()
        finally:
            conn.close()
        return (
            jsonify({
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "year_published": row[3],
                "author_id": row[4],
                "created_by": row[5],
            }),
            201,
        )

    @app.route("/api/books", methods=["GET"])
    def get_books():
        genre_param = request.args.get("genre")
        author_param = request.args.get("author_id")
        query_param = request.args.get("q")

        sql_query = "SELECT id, title, genre, year_published, author_id, created_by FROM books WHERE 1=1"
        query_args = []

        if genre_param:
            sql_query += " AND genre = %s"
            query_args.append(genre_param)
        if author_param:
            sql_query += " AND author_id = %s"
            query_args.append(int(author_param))
        if query_param:
            sql_query += " AND title ILIKE %s"
            query_args.append(f"%{query_param}%")

        sql_query += " ORDER BY id"

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_query, tuple(query_args))
                rows = cur.fetchall()
        finally:
            conn.close()
        return (
            jsonify([
                {
                    "id": r[0],
                    "title": r[1],
                    "genre": r[2],
                    "year_published": r[3],
                    "author_id": r[4],
                    "created_by": r[5],
                }
                for r in rows
            ]),
            200,
        )

    @app.route("/api/books/<int:book_id>", methods=["GET"])
    def get_book_by_id(book_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, genre, year_published, author_id, created_by FROM books WHERE id = %s",
                    (book_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        if row is None:
            return jsonify({"error": "Book not found"}), 404
        return (
            jsonify({
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "year_published": row[3],
                "author_id": row[4],
                "created_by": row[5],
            }),
            200,
        )

    @app.route("/api/books/<int:book_id>", methods=["PUT"])
    def update_book(book_id):
        data = request.json
        if not data:
            return jsonify({"error": "Body must be JSON"}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM books WHERE id = %s", (book_id,))
                if cur.fetchone() is None:
                    return jsonify({"error": "Book not found"}), 404

                cur.execute(
                    """
                    UPDATE books
                    SET title = COALESCE(%s, title),
                        genre = COALESCE(%s, genre),
                        year_published = COALESCE(%s, year_published),
                        author_id = COALESCE(%s, author_id)
                    WHERE id = %s
                    RETURNING id, title, genre, year_published, author_id, created_by
                    """,
                    (
                        data.get("title"),
                        data.get("genre"),
                        data.get("year_published"),
                        data.get("author_id"),
                        book_id,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
        finally:
            conn.close()
        return (
            jsonify({
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "year_published": row[3],
                "author_id": row[4],
                "created_by": row[5],
            }),
            200,
        )

    @app.route("/api/books/<int:book_id>", methods=["DELETE"])
    def delete_book(book_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM books WHERE id = %s RETURNING id", (book_id,)
                )
                row = cur.fetchone()
                conn.commit()
        finally:
            conn.close()
        if row is None:
            return jsonify({"error": "Book not found"}), 404
        return "", 204

    @app.route("/api/authors/<int:author_id>/books", methods=["GET"])
    def get_books_by_author(author_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM authors WHERE id = %s", (author_id,)
                )
                if cur.fetchone() is None:
                    return (
                        jsonify({
                            "error": f"Author with id {author_id} not found"
                        }),
                        404,
                    )

                cur.execute(
                    "SELECT id, title, genre, year_published, author_id, created_by FROM books WHERE author_id = %s ORDER BY id",
                    (author_id,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        return (
            jsonify([
                {
                    "id": r[0],
                    "title": r[1],
                    "genre": r[2],
                    "year_published": r[3],
                    "author_id": r[4],
                    "created_by": r[5],
                }
                for r in rows
            ]),
            200,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)