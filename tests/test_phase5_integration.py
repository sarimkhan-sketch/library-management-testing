"""Phase 5 - End-to-end workflow, security checks and error handling across modules."""
from datetime import timedelta

from conftest import START


def test_tc43_end_to_end_workflow(api, clock):
    """Scenario: Full member journey across all modules
    Steps: 1. Admin adds a book; 2. Member registers and logs in; 3. Searches "testing"; 4. Borrows the book; 5. Returns it 2 days late; 6. Checks loan history; 7. Logs out
    Expected: Every step succeeds; fine is Rs 10; copies are restored; token is invalid after logout
    Priority: High"""
    api.add_book(api.admin())
    assert api.register("sarim").status_code == 201
    token = api.token("sarim")
    book = api.client.get("/books?q=testing").get_json()[0]
    loan = api.borrow(token, book["id"]).get_json()
    clock.today = START + timedelta(days=16)
    returned = api.call("POST", f"/loans/{loan['id']}/return", token).get_json()
    assert returned["fine"] == 10
    history = api.call("GET", "/loans/me", token).get_json()
    assert history[0]["returned_on"] == clock.today.isoformat()
    assert api.client.get(f"/books/{book['id']}").get_json()["available_copies"] == 2
    api.call("POST", "/auth/logout", token)
    assert api.call("GET", "/loans/me", token).status_code == 401


def test_tc44_sql_injection_attempts(api):
    """Scenario: SQL injection text in the search box and in the login username
    Steps: 1. Add a book; 2. GET /books?q=' OR '1'='1; 3. POST /auth/login with username "admin' --"
    Expected: Search returns an empty list (no rows leaked, no error); login returns 401
    Priority: High"""
    api.add_book(api.admin())
    res = api.client.get("/books", query_string={"q": "' OR '1'='1"})
    assert res.status_code == 200
    assert res.get_json() == []
    assert api.login("admin' --", "anything").status_code == 401


def test_tc45_error_handling_unknown_route_and_bad_json(api):
    """Scenario: Unknown URL, wrong HTTP method and a non-JSON body
    Steps: 1. GET /nothing; 2. DELETE /auth/login; 3. POST /auth/register with plain text body
    Expected: JSON errors with 404, 405 and 400 respectively (no HTML error page, no crash)
    Priority: Low"""
    assert api.client.get("/nothing").status_code == 404
    res = api.client.delete("/auth/login")
    assert res.status_code == 405
    assert res.get_json()["error"] == "method not allowed"
    res = api.client.post("/auth/register", data="hello", content_type="text/plain")
    assert res.status_code == 400
