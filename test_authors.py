import pytest


class TestAuthors:

    def test_get_authors_empty(self, client):
        # Перевірка порожнього списку авторів на старті
        res = client.get("/api/authors")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_create_author(self, client):
        # Тест створення нового автора (Перевірка імені варіантів)
        res = client.post(
            "/api/authors", json={"name": "Ivan Franko", "birth_year": 1856}
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["name"] == "Ivan Franko"
        assert data["birth_year"] == 1856
        assert "id" in data

    def test_create_author_without_name(self, client):
        # Валідація відхилення порожнього запису
        res = client.post("/api/authors", json={"birth_year": 1900})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_get_author_by_id(self, client):
        # Отримання існуючого запису за ID
        author = client.post(
            "/api/authors", json={"name": "Lesya Ukrainka"}
        ).get_json()
        res = client.get(f"/api/authors/{author['id']}")
        assert res.status_code == 200
        assert res.get_json()["name"] == "Lesya Ukrainka"

    def test_get_author_not_found(self, client):
        res = client.get("/api/authors/9999")
        assert res.status_code == 404

    def test_delete_author(self, client):
        author = client.post(
            "/api/authors", json={"name": "To Be Deleted"}
        ).get_json()
        res = client.delete(f"/api/authors/{author['id']}")
        assert res.status_code == 204

        # Перевірка, що автора більше немає
        assert client.get(f"/api/authors/{author['id']}").status_code == 404

    def test_delete_author_not_found(self, client):
        res = client.delete("/api/authors/9999")
        assert res.status_code == 404


class TestAuthorBooks:

    def test_get_author_books_empty(self, client):
        author = client.post(
            "/api/authors", json={"name": "Author Without Books"}
        ).get_json()
        res = client.get(f"/api/authors/{author['id']}/books")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_get_author_books_not_found(self, client):
        res = client.get("/api/authors/9999/books")
        assert res.status_code == 404