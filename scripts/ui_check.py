"""Browser check of the demo web page with Playwright (optional, not part of the 45-case suite).

Starts its own copy of the site on http://127.0.0.1:5001 with a temporary database and the
same sample data as run.py, clicks through the main member and admin flows in a real browser,
and saves screenshots to reports/figures/ui_*.png.

    python -m pip install -r requirements-ui.txt
    python scripts/ui_check.py            (uses Microsoft Edge on Windows, Chrome elsewhere)
"""
import logging
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from library import create_app  # noqa: E402
from run import seed  # noqa: E402

FIGURES = ROOT / "reports" / "figures"
URL = "http://127.0.0.1:5001/"
ADMIN_PASSWORD = "ui-check-admin"
results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}")


def login(page, username, password):
    page.fill("#auth-form input[name=username]", username)
    page.fill("#auth-form input[name=password]", password)
    page.click("#auth-submit")


def run_checks(page):
    page.goto(URL)
    page.wait_for_selector(".book")
    check("Guest sees the 6 sample books", page.locator(".book").count() == 6)
    check("Guest sees no Borrow buttons", page.locator("button", has_text="Borrow").count() == 0)
    page.fill("#search", "clean")
    page.wait_for_timeout(600)
    check("Search 'clean' shows only Clean Code", page.locator(".book .title").all_inner_texts() == ["Clean Code"])
    page.fill("#search", "")
    page.wait_for_timeout(600)
    page.screenshot(path=str(FIGURES / "ui_guest.png"))

    login(page, "sarim", "wrong-pass")
    page.wait_for_timeout(400)
    check("Wrong password shows 401 message", "401" in page.inner_text("#toast"))
    login(page, "sarim", "secret123")
    page.wait_for_selector("#my-loans-body tr td")
    check("Seeded loan shows as overdue with Rs 30 fine",
          "Overdue 6 days · Rs 30" in page.inner_text("#my-loans-body"))
    for title in ["Software Testing", "Clean Code"]:
        page.locator(".book", has_text=title).locator("button", has_text="Borrow").click()
        page.wait_for_timeout(400)
    check("Borrowing reduces available copies", "1 of 2 available" in
          page.locator(".book", has_text="Clean Code").inner_text())
    page.locator(".book", has_text="Effective Java").locator("button", has_text="Borrow").click()
    page.wait_for_timeout(400)
    check("4th book refused: 409 borrowing limit", "409 · borrowing limit of 3 books reached" in page.inner_text("#toast"))
    page.screenshot(path=str(FIGURES / "ui_member.png"), full_page=True)
    page.locator("#my-loans-body tr", has_text="Design Patterns").locator("button", has_text="Return").click()
    page.wait_for_timeout(400)
    check("Late return charges Rs 30", "fine Rs 30" in page.inner_text("#toast"))
    page.click("header button:has-text('Log out')")
    page.wait_for_selector("#auth:not(.hidden)")
    check("Logout returns to guest view", page.locator("#my-loans.hidden").count() == 1)

    login(page, "admin", ADMIN_PASSWORD)
    page.wait_for_selector("#admin:not(.hidden)")
    check("Admin panel visible to admin", page.locator("#admin:not(.hidden)").count() == 1)
    page.fill("#book-form input[name=isbn]", "9780306406158")
    page.fill("#book-form input[name=title]", "Bad ISBN")
    page.fill("#book-form input[name=author]", "Nobody")
    page.click("#book-form button")
    page.wait_for_timeout(400)
    check("Bad ISBN rejected: 400 checksum", "400 · isbn checksum is invalid" in page.inner_text("#toast"))
    page.check("#overdue-only")
    page.wait_for_timeout(400)
    check("Overdue filter: no overdue loans after return", "No loans." in page.inner_text("#all-loans-body"))
    page.uncheck("#overdue-only")
    page.wait_for_timeout(400)
    page.screenshot(path=str(FIGURES / "ui_admin.png"), full_page=True)

    page.fill("#book-form input[name=isbn]", "9781617294136")
    page.fill("#book-form input[name=title]", "<img src=x onerror=alert(1)>")
    page.fill("#book-form input[name=author]", "Tester")
    page.click("#book-form button")
    page.wait_for_timeout(500)
    check("HTML in a title is shown as text, not run (XSS)",
          page.locator(".books img").count() == 0
          and page.locator(".book .title", has_text="<img").count() == 1)


def main():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    FIGURES.mkdir(parents=True, exist_ok=True)
    channel = "msedge" if sys.platform == "win32" else "chrome"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        app = create_app({"DATABASE": str(Path(tmp) / "ui.db"), "ADMIN_PASSWORD": ADMIN_PASSWORD})
        seed(app)
        server = make_server("127.0.0.1", 5001, app)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel=channel, headless="--show" not in sys.argv)
                page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1.5)
                page.on("pageerror", lambda e: errors.append(str(e)))
                print(f"UI check in {channel} at {URL}")
                run_checks(page)
                browser.close()
        finally:
            server.shutdown()
    check("No JavaScript errors on the page", not errors)
    passed = sum(ok for _, ok in results)
    print(f"\n{passed}/{len(results)} UI checks passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
