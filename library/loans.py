"""Borrowing and returning books, with due dates and late fines."""
from datetime import date, timedelta

from flask import Blueprint, current_app, g, jsonify, request

from .auth import admin_required, error, login_required
from .db import get_db

bp = Blueprint("loans", __name__, url_prefix="/loans")

LOAN_DAYS = 14
MAX_ACTIVE_LOANS = 3
FINE_PER_DAY = 5  # rupees


def today():
    # Tests replace TODAY with a fixed date so due dates and fines are predictable.
    return current_app.config["TODAY"]()


def calculate_fine(due_on, returned_on, per_day=FINE_PER_DAY):
    """Fine for returning on `returned_on` a book due on `due_on` (both dates)."""
    days_late = (returned_on - due_on).days
    return max(0, days_late) * per_day


def loan_json(row):
    return {key: row[key] for key in row.keys()}


@bp.post("")
@login_required
def borrow():
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")
    if isinstance(book_id, bool) or not isinstance(book_id, int):
        return error("book_id must be an integer", 400)
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        return error("book not found", 404)
    active = db.execute(
        "SELECT book_id FROM loans WHERE user_id = ? AND returned_on IS NULL", (g.user["id"],)
    ).fetchall()
    if any(r["book_id"] == book_id for r in active):
        return error("you already have this book", 409)
    if len(active) > MAX_ACTIVE_LOANS:
        return error(f"borrowing limit of {MAX_ACTIVE_LOANS} books reached", 409)
    if book["available_copies"] < 1:
        return error("no copies available", 409)
    borrowed = today()
    due = borrowed + timedelta(days=LOAN_DAYS)
    db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
    cur = db.execute(
        "INSERT INTO loans (user_id, book_id, borrowed_on, due_on) VALUES (?, ?, ?, ?)",
        (g.user["id"], book_id, borrowed.isoformat(), due.isoformat()),
    )
    db.commit()
    row = db.execute("SELECT * FROM loans WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(loan_json(row)), 201


@bp.post("/<int:loan_id>/return")
@login_required
def return_book(loan_id):
    db = get_db()
    loan = db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    if loan is None:
        return error("loan not found", 404)
    if loan["user_id"] != g.user["id"] and g.user["role"] != "admin":
        return error("this loan belongs to another user", 403)
    if loan["returned_on"] is not None:
        return error("book already returned", 409)
    returned = today()
    fine = calculate_fine(date.fromisoformat(loan["due_on"]), returned)
    db.execute("UPDATE loans SET returned_on = ?, fine = ? WHERE id = ?",
               (returned.isoformat(), fine, loan_id))
    db.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
               (loan["book_id"],))
    db.commit()
    row = db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    return jsonify(loan_json(row))


@bp.get("/me")
@login_required
def my_loans():
    rows = get_db().execute(
        "SELECT * FROM loans WHERE user_id = ? ORDER BY id", (g.user["id"],)
    ).fetchall()
    return jsonify([loan_json(r) for r in rows])


@bp.get("")
@admin_required
def all_loans():
    """Admin view of every loan; ?overdue=1 shows only unreturned loans past their due date."""
    sql = "SELECT * FROM loans"
    params = ()
    if request.args.get("overdue") == "1":
        sql += " WHERE returned_on IS NULL AND due_on < ?"
        params = (today().isoformat(),)
    rows = get_db().execute(sql + " ORDER BY id", params).fetchall()
    return jsonify([loan_json(r) for r in rows])
