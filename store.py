from typing import Any

from fastapi import Header, HTTPException
from typing_extensions import Annotated


class MemoryStore:
    def __init__(self, items):
        self.items = {item["id"]: item for item in items}

    def all(self):
        return list(self.items.values())

    def get(self, item_id):
        return self.items.get(item_id)

    def add(self, title, category, year):
        next_id = max(self.items, default=0) + 1
        item = {"id": next_id, "title": title, "category": category, "year": year}
        self.items[next_id] = item
        return next_id


STORE = MemoryStore([
    {"id": 1, "title": "Algebra", "category": "Math", "year": 2020},
    {"id": 2, "title": "Biology", "category": "Science", "year": 2021},
    {"id": 3, "title": "Chemistry", "category": "Science", "year": 2022},
    {"id": 4, "title": "History", "category": "Humanities", "year": 2019},
    {"id": 5, "title": "Literature", "category": "Humanities", "year": 2023},
    {"id": 6, "title": "Physics", "category": "Math", "year": 2024},
    {"id": 7, "title": "<b>Science Lab</b>", "category": "Science", "year": 2025},
])

TOKENS = {
    "secret-john": "john",
    "secret-anna": "anna",
}


def get_store():
    print("open")
    yield STORE
    print("close")


def get_current_user(x_token: Annotated[str | None, Header()] = None):
    if x_token is None or x_token not in TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    return TOKENS[x_token]
