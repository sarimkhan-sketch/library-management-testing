"""Phase 3 - Book catalogue: admin CRUD, role checks and search."""
from conftest import ISBNS


def test_tc20_admin_adds_book(api):
    """Scenario: Admin adds a new book with valid details
    Steps: 1. Log in as admin; 2. POST /books with isbn, title, author, total_copies = 2
    Expected: 201 Created; available_copies equals total_copies (2)
    Priority: High"""
    res = api.add_book(api.admin())
    assert res.status_code == 201
    assert res.get_json()["available_copies"] == 2


def test_tc21_member_cannot_add_book(api):
    """Scenario: Member (non-admin) tries to add a book
    Steps: 1. Log in as member; 2. POST /books
    Expected: 403 Forbidden; book is not created
    Priority: High"""
    assert api.add_book(api.member()).status_code == 403
    assert api.client.get("/books").get_json() == []


def test_tc22_add_book_invalid_isbn(api):
    """Scenario: Admin adds a book with an ISBN whose checksum is wrong
    Steps: 1. Log in as admin; 2. POST /books with isbn "9780306406158"
    Expected: 400 Bad Request "isbn checksum is invalid"
    Priority: Medium"""
    res = api.add_book(api.admin(), isbn="9780306406158")
    assert res.status_code == 400
    assert res.get_json()["error"] == "isbn checksum is invalid"


def test_tc23_add_book_empty_title(api):
    """Scenario: Admin adds a book whose title is only spaces
    Steps: 1. Log in as admin; 2. POST /books with title "   "
    Expected: 400 Bad Request
    Priority: Medium"""
    assert api.add_book(api.admin(), title="   ").status_code == 400


def test_tc24_add_book_duplicate_isbn(api):
    """Scenario: Admin adds two books with the same ISBN
    Steps: 1. Add a book; 2. Add another book with the same ISBN
    Expected: Second request returns 409 Conflict
    Priority: Medium"""
    admin = api.admin()
    api.add_book(admin)
    assert api.add_book(admin, title="Another title").status_code == 409


def test_tc25_search_by_title_and_author(api):
    """Scenario: Public search matches part of the title or author, ignoring case
    Steps: 1. Add "Software Testing" (Ron Patton) and "Clean Code" (Robert Martin); 2. GET /books?q=testing; 3. GET /books?q=MARTIN; 4. GET /books?q=zzz
    Expected: Step 2 returns only Software Testing; step 3 only Clean Code; step 4 an empty list
    Priority: High"""
    admin = api.admin()
    api.add_book(admin, isbn=ISBNS[0], title="Software Testing", author="Ron Patton")
    api.add_book(admin, isbn=ISBNS[1], title="Clean Code", author="Robert Martin")
    assert [b["title"] for b in api.client.get("/books?q=testing").get_json()] == ["Software Testing"]
    assert [b["title"] for b in api.client.get("/books?q=MARTIN").get_json()] == ["Clean Code"]
    assert api.client.get("/books?q=zzz").get_json() == []


def test_tc26_get_unknown_book(api):
    """Scenario: Requesting a book id that does not exist
    Steps: 1. GET /books/999
    Expected: 404 Not Found with an error message
    Priority: Low"""
    res = api.client.get("/books/999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "book not found"


def test_tc27_admin_updates_title(api):
    """Scenario: Admin corrects the title of an existing book
    Steps: 1. Add a book; 2. PUT /books/1 {"title": "Software Testing, 2nd Ed."}; 3. GET /books/1
    Expected: 200 OK; new title is saved, other fields unchanged
    Priority: Medium"""
    admin = api.admin()
    api.add_book(admin)
    res = api.call("PUT", "/books/1", admin, {"title": "Software Testing, 2nd Ed."})
    assert res.status_code == 200
    book = api.client.get("/books/1").get_json()
    assert book["title"] == "Software Testing, 2nd Ed."
    assert book["author"] == "Ron Patton"


def test_tc28_update_copies_below_borrowed(api):
    """Scenario: Admin reduces total copies below the number currently borrowed
    Steps: 1. Add a book with 2 copies; 2. Two members borrow it; 3. PUT /books/1 {"total_copies": 1}
    Expected: 400 Bad Request; available_copies never becomes negative
    Priority: High"""
    admin = api.admin()
    api.add_book(admin, copies=2)
    api.borrow(api.member("user1"), 1)
    api.borrow(api.member("user2"), 1)
    res = api.call("PUT", "/books/1", admin, {"total_copies": 1})
    assert res.status_code == 400
    assert api.client.get("/books/1").get_json()["available_copies"] == 0


def test_tc29_update_copies_invalid_value(api):
    """Scenario: Admin updates total_copies with text and with 0
    Steps: 1. Add a book; 2. PUT /books/1 {"total_copies": "abc"}; 3. PUT /books/1 {"total_copies": 0}
    Expected: 400 Bad Request both times (no server error)
    Priority: Medium"""
    admin = api.admin()
    api.add_book(admin)
    assert api.call("PUT", "/books/1", admin, {"total_copies": "abc"}).status_code == 400
    assert api.call("PUT", "/books/1", admin, {"total_copies": 0}).status_code == 400


def test_tc30_delete_book_with_active_loan(api):
    """Scenario: Admin tries to delete a book that a member has not returned
    Steps: 1. Add a book; 2. Member borrows it; 3. DELETE /books/1; 4. Member checks /loans/me
    Expected: 409 Conflict; book and the member's loan record still exist
    Priority: High"""
    admin = api.admin()
    api.add_book(admin)
    member = api.member()
    api.borrow(member, 1)
    assert api.call("DELETE", "/books/1", admin).status_code == 409
    assert len(api.call("GET", "/loans/me", member).get_json()) == 1


def test_tc31_delete_book(api):
    """Scenario: Admin deletes a book with no loans
    Steps: 1. Add a book; 2. DELETE /books/1; 3. GET /books/1
    Expected: Delete returns 200; later GET returns 404
    Priority: Medium"""
    admin = api.admin()
    api.add_book(admin)
    assert api.call("DELETE", "/books/1", admin).status_code == 200
    assert api.client.get("/books/1").status_code == 404
