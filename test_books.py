import pytest


class TestBooks:

    CURRENT_STUDENT = "Zelyuk Andriy"

    def test_get_books_empty(self, client):
        res = client.get("/api/books")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_create_book(self, client):
        res = client.post(
            "/api/books",
            json={"title": "Test Masterpiece", "created_by": self.CURRENT_STUDENT},
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["title"] == "Test Masterpiece"
        assert data["created_by"] == self.CURRENT_STUDENT

    def test_create_book_without_title(self, client):
        res = client.post("/api/books", json={"created_by": self.CURRENT_STUDENT})
        assert res.status_code == 400

    def test_create_book_without_created_by(self, client):
        res = client.post("/api/books", json={"title": "Orphan Book"})
        assert res.status_code == 400

    def test_create_book_with_author(self, client):
        author = client.post(
            "/api/authors", json={"name": "Ivan Franko"}
        ).get_json()
        res = client.post(
            "/api/books",
            json={
                "title": "Zakhar Berkut",
                "author_id": author["id"],
                "created_by": self.CURRENT_STUDENT,
            },
        )
        assert res.status_code == 201
        assert res.get_json()["author_id"] == author["id"]

    def test_create_book_with_nonexistent_author(self, client):
        res = client.post(
            "/api/books",
            json={
                "title": "Ghost Book",
                "author_id": 9999,
                "created_by": self.CURRENT_STUDENT,
            },
        )
        assert res.status_code == 400

    def test_get_book_by_id(self, client):
        book = client.post(
            "/api/books",
            json={"title": "Unique Title", "created_by": self.CURRENT_STUDENT},
        )
        res = client.get(f"/api/books/{book.get_json()['id']}")
        assert res.status_code == 200
        assert res.get_json()["title"] == "Unique Title"


class TestBooksFilter:
    CURRENT_STUDENT = "Dzhus Andriy"

    def test_filter_by_genre(self, client):
        client.post(
            "/api/books",
            json={
                "title": "Poetry Book",
                "genre": "poetry",
                "created_by": self.CURRENT_STUDENT,
            },
        )
        client.post(
            "/api/books",
            json={
                "title": "Prose Book",
                "genre": "prose",
                "created_by": self.CURRENT_STUDENT,
            },
        )

        res = client.get("/api/books?genre=poetry")
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Poetry Book"

    def test_search_by_title(self, client):
        client.post(
            "/api/books",
            json={"title": "Kobzar Volume 1", "created_by": self.CURRENT_STUDENT},
        )
        res = client.get("/api/books?q=kobzar")
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Kobzar Volume 1"


class TestCascadeBehavior:
    CURRENT_STUDENT = "Dzhus Andriy"

    def test_delete_author_keeps_books(self, client):
        # Перевірка правила каскадності ON DELETE SET NULL
        author = client.post(
            "/api/authors", json={"name": "Temporary Author"}
        ).get_json()
        book = client.post(
            "/api/books",
            json={
                "title": "Persistent Book",
                "author_id": author["id"],
                "created_by": self.CURRENT_STUDENT,
            },
        ).get_json()

        # Видаляємо автора
        client.delete(f"/api/authors/{author['id']}")

        # Книга повинна залишитися в системі, але її author_id стає null
        res = client.get(f"/api/books/{book['id']}")
        assert res.status_code == 200
        assert res.get_json()["author_id"] is None