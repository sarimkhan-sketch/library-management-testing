"""Phase 1 - Unit tests for the validation rules and the fine calculation (BVA + ECP)."""
from datetime import date

from library.loans import calculate_fine
from library.validators import check_copies, check_isbn, check_password, check_username


def test_tc01_valid_username_accepted():
    """Scenario: A username made of letters, digits and underscore is accepted (valid class)
    Steps: 1. Call check_username("sarim_khan1")
    Expected: No error is returned
    Priority: High"""
    assert check_username("sarim_khan1") is None


def test_tc02_username_length_boundaries():
    """Scenario: Username length boundaries 2, 3, 20 and 21 characters (BVA)
    Steps: 1. Check a 2-character name; 2. Check 3 characters; 3. Check 20; 4. Check 21
    Expected: 3 and 20 are accepted; 2 and 21 are rejected
    Priority: High"""
    assert check_username("ab") is not None
    assert check_username("abc") is None
    assert check_username("a" * 20) is None
    assert check_username("a" * 21) is not None


def test_tc03_invalid_username_classes_rejected():
    """Scenario: Usernames with spaces, symbols, empty string or a non-string value (invalid classes)
    Steps: 1. Check "sarim khan"; 2. Check "sarim@1"; 3. Check ""; 4. Check None
    Expected: Every value is rejected with an error message
    Priority: Medium"""
    for value in ["sarim khan", "sarim@1", "", None]:
        assert check_username(value) is not None


def test_tc04_password_length_boundaries():
    """Scenario: Password length boundaries 5, 6, 64 and 65 characters (BVA)
    Steps: 1. Check 5 characters; 2. Check 6; 3. Check 64; 4. Check 65
    Expected: 6 and 64 are accepted; 5 and 65 are rejected
    Priority: High"""
    assert check_password("a" * 5) is not None
    assert check_password("a" * 6) is None
    assert check_password("a" * 64) is None
    assert check_password("a" * 65) is not None


def test_tc05_valid_isbn_accepted():
    """Scenario: A correct ISBN-13 with a valid checksum is accepted
    Steps: 1. Call check_isbn("9780306406157")
    Expected: No error is returned
    Priority: High"""
    assert check_isbn("9780306406157") is None


def test_tc06_invalid_isbn_rejected():
    """Scenario: ISBNs with a wrong checksum, 12 or 14 digits, letters or a number type
    Steps: 1. Check "9780306406158" (bad checksum); 2. Check 12 and 14 digits; 3. Check "97803064061X7"; 4. Check the integer 9780306406157
    Expected: Every value is rejected
    Priority: High"""
    assert check_isbn("9780306406158") == "isbn checksum is invalid"
    for value in ["978030640615", "97803064061570", "97803064061X7", 9780306406157]:
        assert check_isbn(value) == "isbn must be 13 digits"


def test_tc07_copies_boundaries():
    """Scenario: Number of copies boundaries 0, 1, 100 and 101 (BVA)
    Steps: 1. Check 0; 2. Check 1; 3. Check 100; 4. Check 101
    Expected: 1 and 100 are accepted; 0 and 101 are rejected
    Priority: High"""
    assert check_copies(0) is not None
    assert check_copies(1) is None
    assert check_copies(100) is None
    assert check_copies(101) is not None


def test_tc08_copies_wrong_type_rejected():
    """Scenario: Copies given as text, decimal, boolean or negative number (invalid classes)
    Steps: 1. Check "5"; 2. Check 2.5; 3. Check True; 4. Check -3
    Expected: Every value is rejected
    Priority: Medium"""
    for value in ["5", 2.5, True, -3]:
        assert check_copies(value) is not None


def test_tc09_fine_calculation():
    """Scenario: Late fine of Rs 5 per day for early, on-time, 1-day-late and 10-days-late returns
    Steps: 1. Due date 15-Sep-2026; 2. Return on 10-Sep, 15-Sep, 16-Sep and 25-Sep
    Expected: Fines are 0, 0, 5 and 50
    Priority: High"""
    due = date(2026, 9, 15)
    assert calculate_fine(due, date(2026, 9, 10)) == 0
    assert calculate_fine(due, date(2026, 9, 15)) == 0
    assert calculate_fine(due, date(2026, 9, 16)) == 5
    assert calculate_fine(due, date(2026, 9, 25)) == 50
