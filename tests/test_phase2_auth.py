"""Phase 2 - Registration, login, logout and token checks."""
import sqlite3


def test_tc10_register_member(api):
    """Scenario: New user registers with a valid username and password
    Steps: 1. POST /auth/register {"username": "sarim", "password": "secret123"}
    Expected: 201 Created; response role is "member"
    Priority: High"""
    res = api.register("sarim")
    assert res.status_code == 201
    assert res.get_json()["role"] == "member"


def test_tc11_register_missing_fields(api):
    """Scenario: Registration with empty body, missing password and missing username
    Steps: 1. POST /auth/register {}; 2. POST with only username; 3. POST with only password
    Expected: 400 Bad Request with an error message each time
    Priority: High"""
    for body in [{}, {"username": "sarim"}, {"password": "secret123"}]:
        res = api.client.post("/auth/register", json=body)
        assert res.status_code == 400
        assert "error" in res.get_json()


def test_tc12_register_duplicate_username(api):
    """Scenario: Registering a username that already exists
    Steps: 1. Register "sarim"; 2. Register "sarim" again
    Expected: Second request returns 409 Conflict
    Priority: High"""
    api.register("sarim")
    assert api.register("sarim").status_code == 409


def test_tc13_register_duplicate_username_different_case(api):
    """Scenario: Registering "Sarim" when "sarim" already exists
    Steps: 1. Register "sarim"; 2. Register "Sarim"
    Expected: 409 Conflict, usernames are unique regardless of letter case
    Priority: Medium"""
    api.register("sarim")
    assert api.register("Sarim").status_code == 409


def test_tc14_password_is_hashed(api, app):
    """Scenario: Password is not stored in plain text in the database
    Steps: 1. Register "sarim" with "secret123"; 2. Read users table directly with sqlite3
    Expected: Stored value is a hash, not "secret123"
    Priority: High"""
    api.register("sarim")
    con = sqlite3.connect(app.config["DATABASE"])
    stored = con.execute("SELECT password_hash FROM users WHERE username = 'sarim'").fetchone()[0]
    con.close()
    assert stored != "secret123"
    assert stored.startswith(("scrypt:", "pbkdf2:"))


def test_tc15_register_cannot_choose_admin_role(api):
    """Scenario: User tries to register as admin by sending "role": "admin"
    Steps: 1. POST /auth/register with role "admin"; 2. Log in; 3. Check the role returned
    Expected: Account is created as "member"; extra role field is ignored
    Priority: High"""
    res = api.register("mallory", role="admin")
    assert res.get_json()["role"] == "member"
    assert api.login("mallory").get_json()["role"] == "member"


def test_tc16_login_valid(api):
    """Scenario: Registered user logs in with correct credentials
    Steps: 1. Register "sarim"; 2. POST /auth/login with the same credentials
    Expected: 200 OK with a 64-character token and role "member"
    Priority: High"""
    api.register("sarim")
    res = api.login("sarim")
    assert res.status_code == 200
    assert len(res.get_json()["token"]) == 64


def test_tc17_login_invalid_credentials(api):
    """Scenario: Login with a wrong password, an unknown username and an empty body
    Steps: 1. Register "sarim"; 2. Login with wrong password; 3. Login as "ghost"; 4. POST {}
    Expected: 401 Unauthorized each time with the same generic message
    Priority: High"""
    api.register("sarim")
    responses = [api.login("sarim", "wrongpass"), api.login("ghost"),
                 api.client.post("/auth/login", json={})]
    for res in responses:
        assert res.status_code == 401
        assert res.get_json()["error"] == "invalid username or password"


def test_tc18_protected_endpoint_requires_valid_token(api):
    """Scenario: Accessing /loans/me with no token, a malformed header and a made-up token
    Steps: 1. GET /loans/me without header; 2. With "Authorization: Token abc"; 3. With "Bearer fake"
    Expected: 401 Unauthorized each time
    Priority: High"""
    assert api.call("GET", "/loans/me").status_code == 401
    res = api.client.get("/loans/me", headers={"Authorization": "Token abc"})
    assert res.status_code == 401
    assert api.call("GET", "/loans/me", token="fake").status_code == 401


def test_tc19_logout_invalidates_token(api):
    """Scenario: Token cannot be used after logout
    Steps: 1. Log in as member; 2. POST /auth/logout; 3. GET /loans/me with the old token
    Expected: Logout returns 200; later request returns 401
    Priority: High"""
    token = api.member()
    assert api.call("POST", "/auth/logout", token).status_code == 200
    assert api.call("GET", "/loans/me", token).status_code == 401
