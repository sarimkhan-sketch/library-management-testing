"""Builds docs/Software_Testing_Report.docx from the test files and pytest results.

Run after the test cycles and make_figures.py:  python scripts/build_report.py
"""
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from report_data import (COURSE, FIGURES, GUIDE, PHASES, PROGRAMME, PROJECT, REG_NO, REPO_URL,
                         ROOT, STUDENT, UNIVERSITY, DEFECTS, load)

OUT = ROOT / "docs" / "Software_Testing_Report.docx"
NAVY = RGBColor(0x14, 0x2B, 0x4C)

D = load()
CASES, CYCLES, COV, COV_TOTAL = D["cases"], D["cycles"], D["coverage"], D["cov_total"]
TOTAL_RUNS = sum(c["run"] for c in CYCLES)
TOTAL_PASS = sum(c["passed"] for c in CYCLES)
TOTAL_FAIL = sum(c["failed"] for c in CYCLES)

doc = Document()
styles = doc.styles
styles["Normal"].font.name = "Calibri"
styles["Normal"].font.size = Pt(11)
styles["Normal"].paragraph_format.space_after = Pt(6)
for name, size in (("Heading 1", 16), ("Heading 2", 13)):
    styles[name].font.name = "Calibri"
    styles[name].font.size = Pt(size)
    styles[name].font.color.rgb = NAVY
for section in doc.sections:
    section.left_margin = section.right_margin = Cm(2.2)
    section.top_margin = section.bottom_margin = Cm(2)


def shade(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def table(rows, widths, size=9.5, status_col=None):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = t.cell(i, j)
            cell.width = Cm(widths[j])
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(value))
            run.font.size = Pt(size)
            cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            if i == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shade(cell, "142B4C")
            elif status_col is not None and j == status_col:
                run.bold = True
                run.font.color.rgb = RGBColor(0x0A, 0x6E, 0x0A) if value == "PASS" else RGBColor(0xB0, 0x2A, 0x2A)
            elif i % 2 == 0:
                shade(cell, "F2F5FA")
    repeat_header(t.rows[0])
    doc.add_paragraph()
    return t


def para(text, bold_prefix=None, italic=False):
    p = doc.add_paragraph()
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    r = p.add_run(text)
    r.italic = italic
    return p


def bullets(items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        if isinstance(item, tuple):
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)


def figure(path, caption, width=15):
    doc.add_picture(str(path), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(caption)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9.5)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ------------------------------------------------------------------ Cover page
for _ in range(4):
    doc.add_paragraph()
for text, size, bold in [
        (UNIVERSITY.upper(), 16, True),
        ("Department of Computer Science and Engineering", 12, False),
        ("", 12, False),
        ("SOFTWARE TESTING REPORT", 24, True),
        (PROJECT, 20, True),
        ("A Flask + SQLite REST API tested with pytest", 13, False),
        ("", 12, False), ("", 12, False),
        (f"Submitted by: {STUDENT}", 13, True),
        (f"Registration No.: {REG_NO}", 12, False),
        (PROGRAMME, 12, False),
        (f"Course: {COURSE}", 12, False),
        (f"Submitted to: {GUIDE}", 12, False),
        ("", 12, False),
        (f"Repository: {REPO_URL}", 11, False)]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    if size >= 20:
        r.font.color.rgb = NAVY
page_break()

# ------------------------------------------------------------------ 1. Overview
doc.add_heading("1. Project Overview", 1)
para("Small libraries often track books and loans in registers or spreadsheets. This makes it easy "
     "to lend a copy that is not on the shelf, to forget who has a book, and to calculate late fines "
     "inconsistently.", "Problem statement. ")
para("Build a small, well-tested back-end service that (1) lets members register and log in, "
     "(2) lets the librarian (admin) manage the catalogue, (3) enforces the lending rules automatically, "
     "and (4) is verified by an automated test suite that can be re-run after every change.",
     "Objectives. ")
para("A REST API written in Python with Flask, storing data in a single SQLite file. All business rules "
     "are implemented on the server, and 45 automated pytest test cases check them.",
     "Proposed solution. ")

doc.add_heading("1.1 Technology stack", 2)
table([["Layer", "Technology", "Use in the project"],
       ["Language", "Python 3.12", "All application and test code"],
       ["Web framework", "Flask 3", "Routing, JSON requests and responses, blueprints per module"],
       ["Database", "SQLite (Python sqlite3)", "Tables users, tokens, books, loans; parameterised SQL"],
       ["Security", "Werkzeug password hashing, secrets.token_hex", "Hashed passwords, random 64-character login tokens"],
       ["Testing", "pytest, Flask test client, pytest-cov", "Unit, integration and system tests; coverage"]],
      [3, 5.2, 8.4])

doc.add_heading("1.2 Architecture and modules", 2)
para("The application follows a layered design. A request reaches a Flask blueprint, passes the "
     "access-control decorators (login_required, admin_required), is checked by the validators, and "
     "then reads or writes the SQLite database through db.py.")
table([["Module (file)", "Responsibility", "Endpoints"],
       ["validators.py", "Input rules: username, password, ISBN-13 checksum, copies, text fields", "(used by all modules)"],
       ["auth.py", "Registration, login, logout, token check, admin check", "POST /auth/register, /auth/login, /auth/logout"],
       ["books.py", "Catalogue: search (public); add, update, delete (admin)", "GET/POST /books, GET/PUT/DELETE /books/<id>"],
       ["loans.py", "Borrow, return, due date (14 days), fine (Rs 5/day), limit of 3 books", "POST /loans, POST /loans/<id>/return, GET /loans/me, GET /loans"],
       ["db.py", "SQLite connection, schema, admin account creation", "-"]],
      [3, 7.3, 6.3])

doc.add_heading("1.3 User roles and main workflows", 2)
bullets([("Admin (librarian): ", "adds, updates and deletes books; views all loans and the overdue list. "
          "The admin account is created at start-up; it cannot be obtained through registration."),
         ("Member: ", "registers, logs in, searches books, borrows up to 3 books, returns them and sees "
          "their own loan history."),
         ("Guest (not logged in): ", "can only search and view the catalogue.")])
para("Main workflow: member registers → logs in and receives a token → searches the catalogue → "
     "borrows a book (available copies decrease, due date = today + 14 days) → returns it (copies "
     "increase, fine = days late × Rs 5) → logs out (token is deleted).")

# ------------------------------------------------------------------ 2. Strategy
doc.add_heading("2. Testing Strategy", 1)
para("All testing is automated with pytest. Each test gets a fresh temporary SQLite database, and the "
     "application's clock is replaced by a fixed date (1 September 2026) so that due dates and fines are "
     "predictable. The Flask test client sends real HTTP requests to the application without starting a server.")
table([["Technique", "How it is applied in this project", "Test cases"],
       ["Unit testing", "validators.py and calculate_fine() tested directly as functions", "TC-01 to TC-09"],
       ["Integration testing", "Requests pass through auth, validation, business logic and database together", "TC-28, TC-30, TC-32 to TC-42"],
       ["System / end-to-end testing", "One test walks the complete member journey across all modules", "TC-43"],
       ["Functional testing", "Each endpoint checked against its specified behaviour", "TC-10 to TC-42"],
       ["Boundary value analysis", "Username 2/3/20/21, password 5/6/64/65, copies 0/1/100/101, fine on due date, 3-book limit", "TC-02, 04, 07, 09, 35, 37"],
       ["Equivalence class partitioning", "Valid and invalid classes for username, ISBN, copies, book_id", "TC-01, 03, 05, 06, 08, 36"],
       ["Negative testing", "Missing fields, wrong passwords, unknown ids, bad JSON, wrong methods", "TC-11, 17, 26, 36, 45"],
       ["Security testing", "Password hashing, token checks, role escalation, SQL injection", "TC-14, 15, 18, 19, 44"],
       ["Role-based access testing", "Member blocked from admin actions; members cannot touch others' loans", "TC-21, 39, 42"],
       ["Regression testing", "Full suite re-run after every fix (3 cycles)", "All 45"]],
      [3.8, 9.3, 3.5])

# ------------------------------------------------------------------ 3. Allocation
doc.add_heading("3. Testing Responsibility Allocation", 1)
para("This is an individual project, so development and testing of every module were carried out by "
     f"{STUDENT}. To keep the testing independent of the code, each test was written from the "
     "requirement first (scenario and expected result in the test docstring) and then run against the code.")
table([["Team member", "Developed module", "Testing responsibility"],
       [STUDENT, "validators.py, fine calculation", "Phase 1: unit tests, BVA and ECP"],
       [STUDENT, "auth.py", "Phase 2: authentication and security tests"],
       [STUDENT, "books.py, db.py", "Phase 3: catalogue, role and database tests"],
       [STUDENT, "loans.py", "Phase 4: lending rules and integration tests"],
       [STUDENT, "Complete application", "Phase 5: end-to-end, security and regression runs"]],
      [3.5, 5.5, 7.6])

# ------------------------------------------------------------------ 4. Phase plan
doc.add_heading("4. Phase-wise Testing Plan", 1)
rows = [["Phase", "Module tested", "Testing activity", "Testing type", "Tool", "Expected outcome", "Status (cycle 3)"]]
for stem, n, module, activity, kind, tool in PHASES:
    phase_cases = [c for c in CASES if c["phase"] == n]
    passed = sum(c["status"] == "PASS" for c in phase_cases)
    rows.append([n, module, activity, kind, tool,
                 f"All {len(phase_cases)} test cases ({phase_cases[0]['id']} to {phase_cases[-1]['id']}) pass",
                 f"PASS ({passed}/{len(phase_cases)})"])
table(rows, [1.2, 3.2, 3.4, 2.5, 2.4, 2.6, 1.8], size=8.5)

# ------------------------------------------------------------------ 5. Test cases (landscape)
section = doc.add_section()
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width, section.page_height = section.page_height, section.page_width
section.left_margin = section.right_margin = Cm(1.5)
doc.add_heading("5. Detailed Test Cases", 1)
para(f"{len(CASES)} test cases. Each one is an automated pytest function in the tests/ folder "
     "(for example TC-35 is test_tc35_borrow_limit in tests/test_phase4_loans.py). The scenario, steps, "
     "expected result and priority below are taken from the test's docstring; the actual result and status "
     "come from the pytest JUnit output of the three test cycles (C1, C2, C3).")
rows = [["Test ID", "Module", "Test scenario", "Test steps", "Expected result", "Priority", "Actual result", "Status"]]
for c in CASES:
    rows.append([c["id"], c["module"], c["scenario"], c["steps"], c["expected"], c["priority"],
                 c["actual"], c["status"]])
table(rows, [1.4, 2.4, 4.6, 6.0, 4.8, 1.5, 3.9, 1.4], size=7.5, status_col=7)

# ------------------------------------------------------------------ 6. Evidence (portrait)
section = doc.add_section()
section.orientation = WD_ORIENT.PORTRAIT
section.page_width, section.page_height = section.page_height, section.page_width
section.left_margin = section.right_margin = Cm(2.2)
doc.add_heading("6. Testing Evidence", 1)
para("All evidence files are committed in the repository under reports/: junit.xml and console.txt "
     "for each cycle, and coverage.json for cycle 3. Every result in this report can be reproduced with "
     "python -m pytest.")
table([["Area", "Evidence", "Result"],
       ["Requirements verification", "Each rule (3-book limit, 14-day loan, Rs 5/day fine, unique ISBN, admin-only catalogue changes) has at least one test case", "All rules covered; see Section 5"],
       ["UI and navigation", "Demo web page (library/static) checked in a real browser by scripts/ui_check.py (Playwright): 14/14 checks pass, see Section 6.1. API routing: unknown URL → 404 JSON, wrong method → 405 JSON (TC-45)", "PASS"],
       ["Authentication", "TC-10 to TC-19: register, duplicate names, hashing, login, invalid tokens, logout", "10/10 PASS"],
       ["Functional", "TC-20 to TC-42: catalogue and loan operations", "23/23 PASS"],
       ["Database", "TC-14 reads the users table directly; TC-28, TC-30, TC-37, TC-40 check stored stock and loan rows", "PASS"],
       ["Integration", "Phase 4 tests exercise auth + books + loans + database in one request chain", "PASS"],
       ["End-to-end", "TC-43 runs the full member journey; demo.py shows the same flow for a live demonstration", "PASS"],
       ["Code coverage", f"pytest-cov, cycle 3: {COV_TOTAL['covered_lines']} of {COV_TOTAL['num_statements']} statements executed", f"{COV_TOTAL['percent_covered']:.1f}%"]],
      [3.4, 10, 3.2])
figure(FIGURES / "fig2_coverage.png", "Figure 1: Statement coverage per module after cycle 3.", 14)
doc.add_heading("6.1 Web front end check", 2)
para("A demo web page (library/static: index.html, app.js, style.css) was added after the three test cycles. "
     "It only calls the JSON API, so every rule is still enforced and tested on the server. It is not part of "
     "the 45 test cases above; instead scripts/ui_check.py uses Playwright to drive Microsoft Edge or Chrome "
     "through the main flows on a fresh database. Its output is saved in reports/ui_check.txt.")
ui_lines = [l.strip() for l in (ROOT / "reports" / "ui_check.txt").read_text().splitlines() if l.strip().startswith("[")]
table([["Browser check", "Result"]] + [[l[7:], l[1:5]] for l in ui_lines], [13, 3], size=9, status_col=1)
figure(FIGURES / "ui_member.png", "Figure 2: Member view during the browser check: the 4th borrow is refused (409) and the overdue fine is shown.", 14)
para("Automation. All 45 test cases are automated and run in about 7 seconds. The same suite can run on "
     "every push using GitHub Actions; a workflow file (.github/workflows/tests.yml) that runs it on "
     "Windows and Ubuntu is included in the repository. Possible additions: Postman/Newman collections for "
     "manual API checks, Locust for load testing, and Selenium only if a web front end is added later.",
     italic=False)

# ------------------------------------------------------------------ 7. Summary
doc.add_heading("7. Test Execution Summary", 1)
rows = [["Cycle", "Code version", "Purpose", "Executed", "Passed", "Failed", "Pass %"]]
for c in CYCLES:
    rows.append([c["cycle"], c["version"], c["purpose"], c["run"], c["passed"], c["failed"],
                 f"{100 * c['passed'] / c['run']:.1f}%"])
rows.append(["Total", "", "", TOTAL_RUNS, TOTAL_PASS, TOTAL_FAIL, f"{100 * TOTAL_PASS / TOTAL_RUNS:.1f}%"])
table(rows, [1.6, 3.8, 5.2, 1.6, 1.4, 1.4, 1.6], size=9)
table([["Measure", "Value"],
       ["Total test cases", len(CASES)],
       ["Total automated executions (3 cycles × 45)", TOTAL_RUNS],
       ["Passed executions", TOTAL_PASS],
       ["Failed executions", TOTAL_FAIL],
       ["Overall pass percentage (all executions)", f"{100 * TOTAL_PASS / TOTAL_RUNS:.1f}%"],
       ["Pass percentage in final regression cycle", f"{100 * CYCLES[-1]['passed'] / CYCLES[-1]['run']:.1f}%"]],
      [10, 4])
figure(FIGURES / "fig1_cycles.png", "Figure 3: Passed and failed test cases in each cycle.", 14)
para("Cycle 1 had 22 failures, but 21 of them were caused by one crash (DEF-01): adding a book returned "
     "HTTP 500, so every test that needed a book failed at setup. Fixing that single line exposed five "
     "real logic defects in cycle 2. After fixing those, the full suite passed in cycle 3.")

# ------------------------------------------------------------------ 8. Defects
doc.add_heading("8. Defect Log", 1)
para("DEF-01 to DEF-06 were reproduced by failing automated tests (evidence in reports/cycle1 and "
     "reports/cycle2) and fixed in commits 2d7cd48 and 72837f4. DEF-07 to DEF-09 were found by reading "
     "the code; they are not caught by any failing test and remain open or deferred.")
rows = [["Defect ID", "Severity", "Description", "Test case", "Found in", "Type", "Status"]]
for d in DEFECTS:
    rows.append([d["id"], d["severity"], d["desc"], d["tc"], d["found"], d["kind"], d["status"]])
table(rows, [1.6, 1.6, 7.4, 1.4, 1.7, 1.7, 1.4], size=8.5)

# ------------------------------------------------------------------ 9. Conclusion
doc.add_heading("9. Conclusion", 1)
para(f"The Library Management System API was tested with {len(CASES)} automated test cases over five "
     f"phases and three execution cycles ({TOTAL_RUNS} executions). Testing found six real defects, "
     "including one crash and two business-rule errors (the off-by-one borrowing limit and negative stock) "
     "that would have caused wrong behaviour for librarians and members. All six were fixed and confirmed "
     f"by a full regression run in which all 45 test cases passed with {COV_TOTAL['percent_covered']:.1f}% "
     "statement coverage.")
para("The exercise showed the value of boundary value analysis (it found DEF-03 at exactly the limit of "
     "3 books) and of re-running the whole suite after each fix: the cycle 1 crash hid five other defects "
     "that only appeared once it was fixed. Remaining work: add token expiry (DEF-07), limit repeated "
     "failed logins (DEF-08), make the borrow check and stock update a single atomic statement (DEF-09), "
     "and add a concurrency test for it.")

OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print("saved", OUT)
