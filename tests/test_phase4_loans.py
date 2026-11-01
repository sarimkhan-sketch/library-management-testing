"""Phase 4 - Borrowing and returning books, limits and fines."""
from datetime import timedelta

from conftest import ISBNS, START


def setup_books(api, count=1, copies=2):
    admin = api.admin()
    for i in range(count):
        api.add_book(admin, isbn=ISBNS[i], title=f"Book {i + 1}", copies=copies)
    return admin


def test_tc32_borrow_book(api):
    """Scenario: Member borrows an available book
    Steps: 1. Admin adds a book with 2 copies; 2. Member POST /loans {"book_id": 1}; 3. GET /books/1
    Expected: 201 Created; due date is 14 days after borrowing; available copies drop to 1
    Priority: High"""
    setup_books(api)
    res = api.borrow(api.member(), 1)
    assert res.status_code == 201
    assert res.get_json()["due_on"] == (START + timedelta(days=14)).isoformat()
    assert api.client.get("/books/1").get_json()["available_copies"] == 1


def test_tc33_borrow_unavailable_book(api):
    """Scenario: Member borrows a book whose only copy is already on loan
    Steps: 1. Add a book with 1 copy; 2. user1 borrows it; 3. user2 tries to borrow it
    Expected: 409 Conflict "no copies available"
    Priority: High"""
    setup_books(api, copies=1)
    api.borrow(api.member("user1"), 1)
    res = api.borrow(api.member("user2"), 1)
    assert res.status_code == 409
    assert res.get_json()["error"] == "no copies available"


def test_tc34_borrow_same_book_twice(api):
    """Scenario: Member tries to borrow a second copy of a book they already hold
    Steps: 1. Add a book with 2 copies; 2. Member borrows it; 3. Member borrows it again
    Expected: 409 Conflict "you already have this book"
    Priority: Medium"""
    setup_books(api)
    member = api.member()
    api.borrow(member, 1)
    assert api.borrow(member, 1).status_code == 409


def test_tc35_borrow_limit(api):
    """Scenario: Borrowing limit of 3 active books (BVA on the limit)
    Steps: 1. Add 4 books; 2. Member borrows books 1, 2 and 3; 3. Member borrows book 4
    Expected: First 3 succeed (201); 4th returns 409 "borrowing limit of 3 books reached"
    Priority: High"""
    setup_books(api, count=4)
    member = api.member()
    for book_id in (1, 2, 3):
        assert api.borrow(member, book_id).status_code == 201
    res = api.borrow(member, 4)
    assert res.status_code == 409
    assert "limit" in res.get_json()["error"]


def test_tc36_borrow_invalid_book_id(api):
    """Scenario: Borrowing with a book id that does not exist or is not an integer
    Steps: 1. POST /loans {"book_id": 999}; 2. POST /loans {"book_id": "1"}; 3. POST /loans {}
    Expected: 404 Not Found for 999; 400 Bad Request for "1" and for the empty body
    Priority: Medium"""
    setup_books(api)
    member = api.member()
    assert api.borrow(member, 999).status_code == 404
    assert api.borrow(member, "1").status_code == 400
    assert api.call("POST", "/loans", member, {}).status_code == 400


def test_tc37_return_on_time(api, clock):
    """Scenario: Member returns a book on the due date
    Steps: 1. Borrow a book on 1-Sep-2026; 2. Move clock to 15-Sep-2026 (due date); 3. POST /loans/1/return
    Expected: 200 OK; fine is 0; available copies go back to 2
    Priority: High"""
    setup_books(api)
    member = api.member()
    api.borrow(member, 1)
    clock.today = START + timedelta(days=14)
    res = api.call("POST", "/loans/1/return", member)
    assert res.status_code == 200
    assert res.get_json()["fine"] == 0
    assert api.client.get("/books/1").get_json()["available_copies"] == 2


def test_tc38_return_late_fine(api, clock):
    """Scenario: Member returns a book 3 days after the due date
    Steps: 1. Borrow on 1-Sep-2026 (due 15-Sep); 2. Move clock to 18-Sep-2026; 3. POST /loans/1/return
    Expected: 200 OK; fine is Rs 15 (3 days x Rs 5)
    Priority: High"""
    setup_books(api)
    member = api.member()
    api.borrow(member, 1)
    clock.today = START + timedelta(days=17)
    assert api.call("POST", "/loans/1/return", member).get_json()["fine"] == 15


def test_tc39_return_other_users_loan(api):
    """Scenario: A member tries to return a loan that belongs to someone else
    Steps: 1. user1 borrows a book; 2. user2 POST /loans/1/return
    Expected: 403 Forbidden; loan stays open
    Priority: High"""
    setup_books(api)
    owner = api.member("user1")
    api.borrow(owner, 1)
    assert api.call("POST", "/loans/1/return", api.member("user2")).status_code == 403
    assert api.call("GET", "/loans/me", owner).get_json()[0]["returned_on"] is None


def test_tc40_return_twice(api):
    """Scenario: Returning the same loan twice
    Steps: 1. Borrow a book; 2. Return it; 3. Return it again
    Expected: Second return gives 409 Conflict; available copies are not increased twice
    Priority: Medium"""
    setup_books(api)
    member = api.member()
    api.borrow(member, 1)
    api.call("POST", "/loans/1/return", member)
    assert api.call("POST", "/loans/1/return", member).status_code == 409
    assert api.client.get("/books/1").get_json()["available_copies"] == 2


def test_tc41_my_loans_only_own(api):
    """Scenario: GET /loans/me shows only the logged-in member's loans
    Steps: 1. user1 borrows book 1; 2. user2 borrows book 2; 3. user1 GET /loans/me
    Expected: Exactly one loan, for book 1
    Priority: Medium"""
    setup_books(api, count=2)
    user1 = api.member("user1")
    api.borrow(user1, 1)
    api.borrow(api.member("user2"), 2)
    loans = api.call("GET", "/loans/me", user1).get_json()
    assert [loan["book_id"] for loan in loans] == [1]


def test_tc42_overdue_report_admin_only(api, clock):
    """Scenario: Admin views overdue loans; member is refused
    Steps: 1. Member borrows a book; 2. Move clock 20 days ahead; 3. Admin GET /loans?overdue=1; 4. Member GET /loans
    Expected: Admin sees 1 overdue loan; member gets 403 Forbidden
    Priority: Medium"""
    admin = setup_books(api)
    member = api.member()
    api.borrow(member, 1)
    clock.today = START + timedelta(days=20)
    assert len(api.call("GET", "/loans?overdue=1", admin).get_json()) == 1
    assert api.call("GET", "/loans", member).status_code == 403
