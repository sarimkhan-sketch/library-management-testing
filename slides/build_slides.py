"""Builds slides/Library_Management_Testing.pptx from the same data as the report.

Run:  python slides/build_slides.py
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from report_data import (COURSE, DEFECTS, FIGURES, GUIDE, PHASES, PROGRAMME, PROJECT, REG_NO,  # noqa: E402
                         REPO_URL, ROOT, STUDENT, UNIVERSITY, load)

OUT = ROOT / "slides" / "Library_Management_Testing.pptx"

NAVY = RGBColor(0x14, 0x2B, 0x4C)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)
LIGHT = RGBColor(0xF2, 0xF5, 0xFA)
GREEN = RGBColor(0x0A, 0x6E, 0x0A)
RED = RGBColor(0xB0, 0x2A, 0x2A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PALE = RGBColor(0xBF, 0xD3, 0xF0)

D = load()
CASES, CYCLES, COV_TOTAL = D["cases"], D["cycles"], D["cov_total"]
TOTAL_RUNS = sum(c["run"] for c in CYCLES)
TOTAL_PASS = sum(c["passed"] for c in CYCLES)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = prs.slide_width, prs.slide_height


def text(slide, x, y, w, h, content, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font="Calibri"):
    """Add a text box. `content` is a string or a list of (text, options) paragraphs."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [(content, {})]
    for i, (line, opt) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opt.get("align", align)
        p.space_after = Pt(opt.get("space", 6))
        run = p.add_run()
        run.text = line
        run.font.name = opt.get("font", font)
        run.font.size = Pt(opt.get("size", size))
        run.font.bold = opt.get("bold", bold)
        run.font.color.rgb = opt.get("color", color)
    return box


def bullets(slide, x, y, w, h, items, size=18):
    paras = []
    for item in items:
        if isinstance(item, tuple):
            paras.append(("▸ " + item[0], {"bold": True, "size": size, "space": 2}))
            paras.append(("   " + item[1], {"size": size - 3, "color": INK_2, "space": 10}))
        else:
            paras.append(("▸ " + item, {"size": size, "space": 10}))
    return text(slide, x, y, w, h, paras)


def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def new_slide(title, kicker=None):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, Inches(1.05), NAVY)
    text(s, Inches(0.5), Inches(0.12), Inches(12), Inches(0.85), title, size=30, color=WHITE,
         bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if kicker:
        text(s, Inches(0.5), Inches(1.15), Inches(12.3), Inches(0.6), kicker, size=17, color=BLUE, bold=True)
    text(s, Inches(11.8), Inches(7.0), Inches(1.3), Inches(0.4), str(len(prs.slides)), size=11,
         color=INK_2, align=PP_ALIGN.RIGHT)
    text(s, Inches(0.5), Inches(7.0), Inches(9), Inches(0.4),
         f"{PROJECT} Testing  ·  {STUDENT}  ·  {COURSE}", size=11, color=INK_2)
    return s


def table(slide, x, y, w, rows, col_widths, size=13, row_h=0.4, status_col=None):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w, Inches(row_h * len(rows)))
    tbl = shape.table
    for j, cw in enumerate(col_widths):
        tbl.columns[j].width = Emu(int(w * cw / sum(col_widths)))
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            run = cell.text_frame.paragraphs[0].runs[0]
            run.font.size = Pt(size)
            run.font.name = "Calibri"
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = NAVY
                run.font.color.rgb = WHITE
                run.font.bold = True
            else:
                cell.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
                run.font.color.rgb = INK
                if status_col is not None and j == status_col:
                    run.font.bold = True
                    run.font.color.rgb = GREEN if val in ("Fixed", "PASS") else RED
    return tbl


def callout(slide, x, y, w, h, big, small, color=BLUE):
    rect(slide, x, y, w, h, LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
    rect(slide, x, y, Inches(0.09), h, color)
    text(slide, x + Inches(0.25), y + Inches(0.1), w - Inches(0.35), Inches(0.75), big, size=30,
         color=color, bold=True)
    text(slide, x + Inches(0.25), y + Inches(0.8), w - Inches(0.35), h - Inches(0.85), small,
         size=14, color=INK_2)


# 1. Title
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, NAVY)
rect(s, Inches(0.8), Inches(2.0), Inches(0.12), Inches(2.3), BLUE)
text(s, Inches(1.15), Inches(1.9), Inches(11), Inches(1.2), f"Testing a {PROJECT}", size=44,
     color=WHITE, bold=True)
text(s, Inches(1.15), Inches(3.05), Inches(11), Inches(1.2),
     "A Flask + SQLite REST API verified with 45 automated pytest test cases", size=22, color=PALE)
text(s, Inches(1.15), Inches(4.8), Inches(11), Inches(1.8), [
    (f"{STUDENT}  ({REG_NO})", {"size": 20, "bold": True, "color": WHITE}),
    (f"{COURSE}  ·  {PROGRAMME}", {"size": 16, "color": PALE}),
    (f"Guide: {GUIDE}  ·  {UNIVERSITY}", {"size": 16, "color": PALE}),
])

# 2. Problem and solution
s = new_slide("Problem and solution")
bullets(s, Inches(0.5), Inches(1.4), Inches(6.4), Inches(5.3), [
    ("Problem", "Small libraries track loans on paper: copies get double-lent, fines are worked out by hand."),
    ("Solution", "A REST API that enforces the lending rules on the server."),
    ("Testing goal", "Prove every rule works, including edge cases and misuse, with tests that re-run in seconds."),
], size=19)
rect(s, Inches(7.3), Inches(1.5), Inches(5.5), Inches(5.2), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.05
text(s, Inches(7.6), Inches(1.65), Inches(5), Inches(5), [
    ("Business rules under test", {"bold": True, "size": 18, "color": BLUE}),
    ("Loan period: 14 days", {"size": 17}),
    ("Late fine: Rs 5 per day", {"size": 17}),
    ("Max 3 books per member at a time", {"size": 17}),
    ("Cannot borrow the same book twice", {"size": 17}),
    ("Only admin can add / edit / delete books", {"size": 17}),
    ("ISBN-13 with valid checksum, unique", {"size": 17}),
    ("Username 3-20 chars, unique (any case)", {"size": 17}),
    ("Password 6-64 chars, stored hashed", {"size": 17}),
])

# 3. Architecture
s = new_slide("System design", "Python 3.12 · Flask 3 · SQLite · pytest")
boxes = [("Client", "HTTP + JSON\n(test client / demo.py)"), ("auth.py", "login_required\nadmin_required"),
         ("validators.py", "input rules"), ("books.py / loans.py", "business logic"), ("db.py", "SQLite\nusers · tokens\nbooks · loans")]
x = Inches(0.5)
for i, (name, desc) in enumerate(boxes):
    rect(s, x, Inches(2.2), Inches(2.2), Inches(1.9), LIGHT if i else NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, x, Inches(2.3), Inches(2.2), Inches(1.8), [
        (name, {"bold": True, "size": 17, "color": WHITE if i == 0 else BLUE, "align": PP_ALIGN.CENTER}),
        (desc, {"size": 13, "color": PALE if i == 0 else INK_2, "align": PP_ALIGN.CENTER})])
    if i < len(boxes) - 1:
        text(s, x + Inches(2.2), Inches(2.75), Inches(0.4), Inches(0.6), "→", size=28, color=INK_2,
             align=PP_ALIGN.CENTER)
    x += Inches(2.6)
table(s, Inches(0.5), Inches(4.6), Inches(12.3), [
    ["Role", "Can do"],
    ["Guest", "Search and view the catalogue"],
    ["Member", "Register, log in, borrow up to 3 books, return, see own loans"],
    ["Admin", "Everything above + add / update / delete books, see all and overdue loans"]],
    [1.5, 8], size=15)

# 4. Strategy
s = new_slide("Testing strategy", "Every test: fresh temporary database + a fixed clock (1 Sep 2026)")
table(s, Inches(0.5), Inches(1.9), Inches(12.3), [
    ["Technique", "Example from this project"],
    ["Unit", "check_isbn(\"9780306406158\") → \"isbn checksum is invalid\""],
    ["Boundary value analysis", "Username length 2 / 3 / 20 / 21; borrowing the 3rd and the 4th book"],
    ["Equivalence partitioning", "Copies: valid 1-100 vs text, decimal, boolean, negative"],
    ["Negative", "Wrong password, unknown book id, plain-text body instead of JSON"],
    ["Security", "Password hashed in DB, fake tokens rejected, \"role\": \"admin\" ignored, SQL injection"],
    ["Role-based access", "Member adding a book → 403; returning another member's loan → 403"],
    ["Integration / system", "Full journey: register → borrow → return late → fine Rs 10 → logout"],
    ["Regression", "Whole suite re-run after every fix (3 cycles)"]],
    [3, 9], size=15, row_h=0.5)

# 5. Phases
s = new_slide("Five testing phases", f"{len(CASES)} test cases, one pytest function each")
rows = [["Phase", "Module", "Testing type", "Test cases", "Result"]]
for stem, n, module, activity, kind, tool in PHASES:
    pc = [c for c in CASES if c["phase"] == n]
    rows.append([n, module.split(" (")[0], kind, f"{pc[0]['id']} – {pc[-1]['id']}  ({len(pc)})",
                 f"{sum(c['status'] == 'PASS' for c in pc)}/{len(pc)} PASS"])
table(s, Inches(0.5), Inches(1.9), Inches(12.3), rows, [0.8, 3.6, 3.8, 2.4, 1.6], size=16, row_h=0.62)
text(s, Inches(0.5), Inches(6.0), Inches(12.3), Inches(0.8),
     "Test ID = function name: TC-35 is test_tc35_borrow_limit() in tests/test_phase4_loans.py",
     size=15, color=INK_2, font="Menlo")

# 6. Example test case
s = new_slide("Example: boundary test on the borrowing limit")
tc = next(c for c in CASES if c["id"] == "TC-35")
text(s, Inches(0.5), Inches(1.3), Inches(6.2), Inches(5.5), [
    (f"{tc['id']}  ·  {tc['module']}  ·  Priority {tc['priority']}", {"bold": True, "size": 16, "color": BLUE}),
    ("Scenario", {"bold": True, "size": 15}), (tc["scenario"], {"size": 15, "color": INK_2}),
    ("Steps", {"bold": True, "size": 15}), (tc["steps"], {"size": 15, "color": INK_2}),
    ("Expected", {"bold": True, "size": 15}), (tc["expected"], {"size": 15, "color": INK_2}),
    ("Actual", {"bold": True, "size": 15}), (tc["actual"], {"size": 15, "color": INK_2}),
])
rect(s, Inches(7.0), Inches(1.4), Inches(5.85), Inches(5.3), NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.04
code = ("def test_tc35_borrow_limit(api):\n"
        "    setup_books(api, count=4)\n"
        "    member = api.member()\n"
        "    for book_id in (1, 2, 3):\n"
        "        assert api.borrow(member, book_id)\\\n"
        "                  .status_code == 201\n"
        "    res = api.borrow(member, 4)\n"
        "    assert res.status_code == 409\n\n"
        "# Bug found (DEF-03):\n"
        "#   if len(active) > 3:    <- allows a 4th\n"
        "# Fix:\n"
        "#   if len(active) >= 3:")
text(s, Inches(7.25), Inches(1.6), Inches(5.4), Inches(5), code, size=14, color=WHITE, font="Menlo")

# 7. Results
s = new_slide("Execution results", f"{TOTAL_RUNS} automated executions over 3 cycles")
s.shapes.add_picture(str(FIGURES / "fig1_cycles.png"), Inches(0.4), Inches(1.8), width=Inches(7.6))
c1, c2, c3 = CYCLES
callout(s, Inches(8.4), Inches(1.8), Inches(4.4), Inches(1.45), f"{c1['failed']} → {c2['failed']} → {c3['failed']}",
        "failures per cycle", color=RED)
callout(s, Inches(8.4), Inches(3.4), Inches(4.4), Inches(1.45), f"{100 * TOTAL_PASS / TOTAL_RUNS:.1f}%",
        f"{TOTAL_PASS} of {TOTAL_RUNS} executions passed (all cycles)", color=BLUE)
callout(s, Inches(8.4), Inches(5.0), Inches(4.4), Inches(1.45), f"{COV_TOTAL['percent_covered']:.1f}%",
        "statement coverage in the final cycle (pytest-cov)", color=GREEN)

# 8. Defects
s = new_slide("Defect log", "6 defects reproduced by tests and fixed · 3 found by code review")
rows = [["ID", "Severity", "Defect", "Found by", "Status"]]
short = {
    "DEF-01": "Adding a book returned HTTP 500 (blocked 21 tests)",
    "DEF-02": "'sarim' and 'Sarim' could both register",
    "DEF-03": "Borrow limit off by one: 4 books allowed",
    "DEF-04": "Reducing copies below loans → negative stock",
    "DEF-05": "Book update: text copies → 500, 0 accepted",
    "DEF-06": "Deleting a borrowed book erased loan records",
    "DEF-07": "Login tokens never expire",
    "DEF-08": "No limit on failed login attempts",
    "DEF-09": "Possible race on the last copy (not reproduced)",
}
for d in DEFECTS:
    rows.append([d["id"], d["severity"], short[d["id"]], f"{d['tc']} ({d['found']})" if d["kind"] == "Reproduced" else "Code review", d["status"]])
table(s, Inches(0.5), Inches(1.8), Inches(12.3), rows, [1.1, 1.2, 6.2, 2.2, 1.2], size=15, row_h=0.5, status_col=4)

# 9. Web front end
s = new_slide("Demo: City Library web page", "python run.py  →  http://127.0.0.1:5000  (plain HTML + JS, works offline)")
s.shapes.add_picture(str(FIGURES / "ui_member.png"), Inches(0.5), Inches(1.75), height=Inches(5.1))
bullets(s, Inches(6.55), Inches(1.8), Inches(6.35), Inches(5.1), [
    ("Member view", "Search, borrow, return; overdue loans show the fine before returning"),
    ("Admin view", "Add books, change copies, delete, all / overdue loans"),
    ("Errors shown as status + message", "e.g. red “409 · borrowing limit of 3 books reached”"),
    ("API log panel", "Every request and its HTTP code, so each click is a visible test case"),
    ("Browser check", "scripts/ui_check.py drives Edge/Chrome with Playwright: 14/14 checks pass, incl. XSS"),
], size=16)

# 10. Live demo commands
s = new_slide("Live demo plan", "Runs on Windows with Python only; no Postman or Node.js")
for i, (cmd, what) in enumerate([
        ("python run.py", "website with sample data; log in as sarim / secret123 and admin"),
        ("python -m pytest -v", "runs all 45 test cases (~7 s)"),
        ("python -m pytest --cov=library", "same run + coverage table"),
        ("python scripts/ui_check.py --show", "watch the browser test click through the site")]):
    y = Inches(1.9 + i * 1.2)
    rect(s, Inches(0.5), y, Inches(6.0), Inches(0.85), NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, Inches(0.5), y, Inches(6.0), Inches(0.85), cmd, size=17, color=WHITE, font="Menlo",
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(6.8), y, Inches(6.0), Inches(0.85), what, size=17, color=INK_2, anchor=MSO_ANCHOR.MIDDLE)

# 11. Conclusion
s = new_slide("Conclusion")
bullets(s, Inches(0.5), Inches(1.4), Inches(6.3), Inches(5.4), [
    ("Testing found real bugs", "6 defects, including a crash and two wrong business rules."),
    ("Boundary tests pay off", "The 3-book limit bug only shows up exactly at the boundary."),
    ("Regression matters", "Fixing the cycle 1 crash revealed 5 hidden defects in cycle 2."),
    ("Final state", f"45/45 pass, {COV_TOTAL['percent_covered']:.1f}% statement coverage."),
], size=18)
text(s, Inches(7.2), Inches(1.4), Inches(5.6), Inches(0.5), "Future work", size=22, bold=True, color=BLUE)
bullets(s, Inches(7.2), Inches(2.0), Inches(5.6), Inches(4.8), [
    "Token expiry (DEF-07)",
    "Lock account after repeated failed logins (DEF-08)",
    "Atomic borrow update + concurrency test (DEF-09)",
    "Run the suite on every push with GitHub Actions",
], size=18)

# 12. Thanks
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, NAVY)
text(s, Inches(0.8), Inches(2.5), Inches(11.7), Inches(1.2), "Thank you  ·  Questions?", size=44,
     color=WHITE, bold=True, align=PP_ALIGN.CENTER)
text(s, Inches(0.8), Inches(3.9), Inches(11.7), Inches(1), REPO_URL, size=18, color=PALE,
     align=PP_ALIGN.CENTER)

prs.save(OUT)
print(f"saved {OUT} ({len(prs.slides)} slides)")
