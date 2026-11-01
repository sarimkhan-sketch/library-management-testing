"""Start the API on this computer only (http://127.0.0.1:5000).

The admin password is generated on first run and saved in instance/admin_password.txt.
"""
import secrets
from pathlib import Path

from library import create_app

INSTANCE = Path(__file__).resolve().parent / "instance"


def main():
    INSTANCE.mkdir(exist_ok=True)
    password_file = INSTANCE / "admin_password.txt"
    if not password_file.exists():
        password_file.write_text(secrets.token_urlsafe(9))
    password = password_file.read_text().strip()

    app = create_app({"DATABASE": str(INSTANCE / "library.db"), "ADMIN_PASSWORD": password})
    print("Library Management API")
    print("  Open  http://127.0.0.1:5000/books  in a browser to see the catalogue")
    print(f"  Admin login:  username = admin   password = {password}")
    print("  Press CTRL+C to stop\n")
    # 127.0.0.1 keeps the server private to this laptop.
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
