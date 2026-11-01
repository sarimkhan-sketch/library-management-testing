"""Scripted demo: walks through every module of the API and prints each request and response.

Runs fully in memory on a temporary database, so no server, browser or Postman is needed:
    python demo.py
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from library import create_app

clock = {"today": date(2026, 9, 1)}


def show(step, res):
    body = res.get_json()
    print(f"\n[{step}]  ->  HTTP {res.status_code}")
    print(f"    {body}")
    return body


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        app = create_app({
            "DATABASE": str(Path(tmp) / "demo.db"),
            "ADMIN_PASSWORD": "admin-pass",
            "TODAY": lambda: clock["today"],
        })
        c = app.test_client()

        def auth(token):
            return {"Authorization": f"Bearer {token}"}

        print("=" * 70)
        print("LIBRARY MANAGEMENT API - DEMO   (today = 2026-09-01)")
        print("=" * 70)

        admin = show("1. Admin logs in", c.post("/auth/login", json={"username": "admin", "password": "admin-pass"}))["token"]
        show("2. Admin adds 'Software Testing' (2 copies)", c.post("/books", headers=auth(admin), json={
            "isbn": "9780306406157", "title": "Software Testing", "author": "Ron Patton", "total_copies": 2}))
        show("3. Admin adds a book with a wrong ISBN checksum", c.post("/books", headers=auth(admin), json={
            "isbn": "9780306406158", "title": "Bad ISBN", "author": "Nobody", "total_copies": 1}))

        show("4. Sarim registers", c.post("/auth/register", json={"username": "sarim", "password": "secret123"}))
        show("5. Someone registers 'Sarim' again (different case)", c.post("/auth/register", json={"username": "Sarim", "password": "secret123"}))
        sarim = show("6. Sarim logs in", c.post("/auth/login", json={"username": "sarim", "password": "secret123"}))["token"]
        show("7. Sarim tries to add a book (member, not admin)", c.post("/books", headers=auth(sarim), json={
            "isbn": "9780131103627", "title": "C", "author": "K&R", "total_copies": 1}))

        show("8. Search catalogue for 'testing'", c.get("/books?q=testing"))
        loan = show("9. Sarim borrows book 1 (due in 14 days)", c.post("/loans", headers=auth(sarim), json={"book_id": 1}))
        show("10. Sarim borrows the same book again", c.post("/loans", headers=auth(sarim), json={"book_id": 1}))

        clock["today"] += timedelta(days=17)
        print("\n    ... 17 days pass (book is 3 days late) ...")
        show("11. Admin checks overdue loans", c.get("/loans?overdue=1", headers=auth(admin)))
        show("12. Sarim returns the book (fine = 3 x Rs 5)", c.post(f"/loans/{loan['id']}/return", headers=auth(sarim)))
        show("13. Copies available again", c.get("/books/1"))

        show("14. Sarim logs out", c.post("/auth/logout", headers=auth(sarim)))
        show("15. Old token is rejected", c.get("/loans/me", headers=auth(sarim)))
        print("\nDemo finished.")


if __name__ == "__main__":
    main()
