"""Input validation rules shared by the API modules.

Each function returns None when the value is valid, otherwise an error message.
"""
import re

USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,20}")
MAX_COPIES = 100


def check_username(value):
    if not isinstance(value, str) or not USERNAME_RE.fullmatch(value):
        return "username must be 3-20 letters, digits or underscores"
    return None


def check_password(value):
    if not isinstance(value, str) or not 6 <= len(value) <= 64:
        return "password must be 6-64 characters"
    return None


def check_isbn(value):
    """ISBN-13: 13 digits whose weighted sum (weights 1,3,1,3,...) is divisible by 10."""
    if not isinstance(value, str) or not value.isdigit() or len(value) != 13:
        return "isbn must be 13 digits"
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(value))
    if total % 10 != 0:
        return "isbn checksum is invalid"
    return None


def check_copies(value):
    # bool is a subclass of int, so True would otherwise pass as 1
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_COPIES:
        return f"total_copies must be an integer from 1 to {MAX_COPIES}"
    return None


def check_text(value, field, max_len=200):
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        return f"{field} is required (max {max_len} characters)"
    return None
