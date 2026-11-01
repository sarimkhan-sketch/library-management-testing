"""Book catalogue: public search, admin-only add/update/delete."""
import sqlite3

from flask import Blueprint, jsonify, request

from .auth import admin_required, error
from .db import get_db
from .validators import check_copies, check_isbn, check_text

bp = Blueprint("books", __name__, url_prefix="/books")


def book_json(row):
    return {key: row[key] for key in row.keys()}


@bp.get("")
def list_books():
    q = request.args.get("q", "").strip()
    rows = get_db().execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title",
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    return jsonify([book_json(r) for r in rows])


@bp.get("/<int:book_id>")
def get_book(book_id):
    row = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        return error("book not found", 404)
    return jsonify(book_json(row))


@bp.post("")
@admin_required
def add_book():
    data = request.get_json(silent=True) or {}
    problem = (check_isbn(data.get("isbn")) or check_text(data.get("title"), "title")
               or check_text(data.get("author"), "author") or check_copies(data.get("total_copies")))
    if problem:
        return error(problem, 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO books (isbn, title, author, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (data["isbn"], data["title"].strip(), data["author"].strip(),
             data["total_copies"], data["total_copies"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("a book with this isbn already exists", 409)
    return get_book(cur.lastrowid), 201


@bp.put("/<int:book_id>")
@admin_required
def update_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        return error("book not found", 404)
    data = request.get_json(silent=True) or {}
    title = data.get("title", book["title"])
    author = data.get("author", book["author"])
    total = data.get("total_copies", book["total_copies"])
    problem = check_text(title, "title") or check_text(author, "author") or check_copies(total)
    if problem:
        return error(problem, 400)
    on_loan = book["total_copies"] - book["available_copies"]
    if total < on_loan:
        return error(f"{on_loan} copies are on loan; total_copies cannot be lower", 400)
    available = book["available_copies"] + (total - book["total_copies"])
    db.execute(
        "UPDATE books SET title = ?, author = ?, total_copies = ?, available_copies = ? WHERE id = ?",
        (title.strip(), author.strip(), total, available, book_id),
    )
    db.commit()
    return get_book(book_id)


@bp.delete("/<int:book_id>")
@admin_required
def delete_book(book_id):
    db = get_db()
    if db.execute("SELECT 1 FROM books WHERE id = ?", (book_id,)).fetchone() is None:
        return error("book not found", 404)
    if db.execute("SELECT 1 FROM loans WHERE book_id = ?", (book_id,)).fetchone():
        return error("book has loan records and cannot be deleted", 409)
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return jsonify({"message": "book deleted"})
