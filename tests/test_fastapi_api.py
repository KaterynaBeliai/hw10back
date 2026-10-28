import unittest

from fastapi.testclient import TestClient

from main import app
from store import get_store


class FakeStore:
    def __init__(self):
        self.items = {
            1: {"id": 1, "title": "Algebra", "category": "Math", "year": 2020},
            2: {"id": 2, "title": "Biology", "category": "Science", "year": 2021},
            3: {"id": 3, "title": "Chemistry", "category": "Science", "year": 2022},
            4: {"id": 4, "title": "History", "category": "Humanities", "year": 2019},
            5: {"id": 5, "title": "Literature", "category": "Humanities", "year": 2023},
            6: {"id": 6, "title": "Physics", "category": "Math", "year": 2024},
            7: {"id": 7, "title": "<b>Science Lab</b>", "category": "Science", "year": 2025},
        }
        self.add_calls = []

    def all(self):
        return list(self.items.values())

    def get(self, item_id):
        return self.items.get(item_id)

    def add(self, title, category, year):
        next_id = max(self.items, default=0) + 1
        item = {"id": next_id, "title": title, "category": category, "year": year}
        self.items[next_id] = item
        self.add_calls.append((title, category, year))
        return next_id


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        app.dependency_overrides[get_store] = lambda: self.store
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_root_returns_catalogue_name(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"catalogue": "School Catalogue"})

    def test_items_list_sort_and_limit(self):
        response = self.client.get("/items?sort=year&limit=3")
        years = [item["year"] for item in response.json()]
        self.assertEqual(years, [2019, 2020, 2021])

    def test_sort_validation_422(self):
        response = self.client.get("/items?sort=price")
        self.assertEqual(response.status_code, 422)

    def test_limit_validation_422(self):
        response = self.client.get("/items?limit=0")
        self.assertEqual(response.status_code, 422)

    def test_get_item_by_id_404(self):
        response = self.client.get("/items/999")
        self.assertEqual(response.status_code, 404)

    def test_get_item_by_id_422(self):
        response = self.client.get("/items/abc")
        self.assertEqual(response.status_code, 422)

    def test_post_without_token_is_401(self):
        response = self.client.post("/items", data={"title": "Test", "category": "x", "year": 2020})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.store.add_calls, [])

    def test_post_with_valid_token_redirects(self):
        response = self.client.post(
            "/items",
            data={"title": "Test", "category": "x", "year": 2020},
            headers={"X-Token": "secret-john"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["location"].endswith("/items/8"))
        self.assertEqual(self.store.add_calls, [("Test", "x", 2020)])

    def test_empty_title_is_422(self):
        response = self.client.post(
            "/items",
            data={"title": "", "category": "x", "year": 2020},
            headers={"X-Token": "secret-john"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.store.add_calls, [])

    def test_catalogue_page_escapes_html(self):
        response = self.client.get("/catalogue")
        self.assertEqual(response.status_code, 200)
        self.assertIn("&lt;b&gt;Science Lab&lt;/b&gt;", response.text)
        self.assertNotIn("<b>Science Lab</b>", response.text)
