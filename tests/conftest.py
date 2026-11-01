"""Shared fixtures: a fresh database per test, a controllable clock and API helpers."""
from datetime import date

import pytest

from library import create_app

ADMIN = {"username": "admin", "password": "admin-pass"}
START = date(2026, 9, 1)


class Clock:
    def __init__(self):
        self.today = START


class Api:
    """Thin wrapper over Flask's test client so tests read like the user workflow."""

    def __init__(self, client):
        self.client = client

    def register(self, username, password="secret123", **extra):
        return self.client.post("/auth/register", json={"username": username, "password": password, **extra})

    def login(self, username, password="secret123"):
        return self.client.post("/auth/login", json={"username": username, "password": password})

    def token(self, username, password="secret123"):
        return self.login(username, password).get_json()["token"]

    def member(self, username="sarim"):
        self.register(username)
        return self.token(username)

    def admin(self):
        return self.token(ADMIN["username"], ADMIN["password"])

    def call(self, method, url, token=None, json=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.open(url, method=method, headers=headers, json=json)

    def add_book(self, admin_token, isbn="9780306406157", title="Software Testing",
                 author="Ron Patton", copies=2):
        return self.call("POST", "/books", admin_token,
                         {"isbn": isbn, "title": title, "author": author, "total_copies": copies})

    def borrow(self, token, book_id):
        return self.call("POST", "/loans", token, {"book_id": book_id})


# Valid ISBN-13 numbers used when a test needs several different books.
ISBNS = ["9780306406157", "9780131103627", "9780201633610", "9780132350884", "9781491950357"]


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def app(tmp_path, clock):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "ADMIN_PASSWORD": ADMIN["password"],
        "TODAY": lambda: clock.today,
    })


@pytest.fixture
def api(app):
    return Api(app.test_client())
