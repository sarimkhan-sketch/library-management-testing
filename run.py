"""Start the library website and API on this computer only: http://127.0.0.1:5000

On first run it creates sample books, a member account (sarim / secret123) with one
overdue loan, and an admin password saved in instance/admin_password.txt.
Run with --reset to delete the database and start again with fresh sample data.
"""
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

from library import create_app
from library.db import get_db

INSTANCE = Path(__file__).resolve().parent / "instance"
DATABASE = INSTANCE / "library.db"

SAMPLE_BOOKS = [
    ("9780306406157", "Software Testing", "Ron Patton", 2),
    ("9780131103627", "The C Programming Language", "Brian Kernighan", 3),
    ("9780201633610", "Design Patterns", "Erich Gamma", 1),
    ("9780132350884", "Clean Code", "Robert Martin", 2),
    ("9781491950357", "Building Microservices", "Sam Newman", 1),
    ("9780134685991", "Effective Java", "Joshua Bloch", 2),
]
MEMBER = ("sarim", "secret123")


def seed(app):
    """Add sample data to an empty database."""
    with app.app_context():
        db = get_db()
        if db.execute("SELECT COUNT(*) FROM books").fetchone()[0]:
            return
        db.executemany(
            "INSERT INTO books (isbn, title, author, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
            [(isbn, title, author, n, n) for isbn, title, author, n in SAMPLE_BOOKS],
        )
        cur = db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'member')",
                         (MEMBER[0], generate_password_hash(MEMBER[1])))
        # One loan taken 20 days ago (6 days overdue), so the late fine can be shown straight away.
        borrowed = date.today() - timedelta(days=20)
        db.execute("INSERT INTO loans (user_id, book_id, borrowed_on, due_on) VALUES (?, 3, ?, ?)",
                   (cur.lastrowid, borrowed.isoformat(), (borrowed + timedelta(days=14)).isoformat()))
        db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = 3")
        db.commit()


def main():
    INSTANCE.mkdir(exist_ok=True)
    if "--reset" in sys.argv and DATABASE.exists():
        DATABASE.unlink()
    password_file = INSTANCE / "admin_password.txt"
    if not password_file.exists():
        password_file.write_text(secrets.token_urlsafe(9))
    password = password_file.read_text().strip()

    app = create_app({"DATABASE": str(DATABASE), "ADMIN_PASSWORD": password})
    seed(app)
    print("City Library - Library Management System")
    print("  Open  http://127.0.0.1:5000  in your browser")
    print(f"  Admin login:   username = admin   password = {password}")
    print(f"  Member login:  username = {MEMBER[0]}   password = {MEMBER[1]}")
    print("  Press CTRL+C to stop\n")
    # 127.0.0.1 keeps the server private to this laptop.
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
