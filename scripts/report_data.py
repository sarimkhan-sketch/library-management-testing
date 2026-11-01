"""Collects everything the report and slides need from the repository itself.

Test case details come from the docstrings in tests/, results from the JUnit XML files
written by pytest in reports/cycle*/, and coverage from reports/cycle3/coverage.json.
"""
import ast
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

STUDENT = "Sarim Khan"
REG_NO = "23F10CSE00486"
PROGRAMME = "B.Tech CSE, Semester VII, 2026-27"
UNIVERSITY = "Manipal University Jaipur"
COURSE = "Software Testing"
GUIDE = "[Faculty name]"          # fill in before submission
REPO_URL = "github.com/sarimkhan-sketch/library-management-testing"
PROJECT = "Library Management System"

PHASES = [
    # file stem, phase number, module, activity, testing type, tool
    ("test_phase1_validation", 1, "Validation & fine rules (validators.py, calculate_fine)",
     "Check every input rule and the fine formula in isolation",
     "Unit, BVA, ECP", "pytest"),
    ("test_phase2_auth", 2, "Authentication (auth.py)",
     "Register, log in, log out, token and role checks",
     "Functional, Negative, Security", "pytest + Flask test client"),
    ("test_phase3_books", 3, "Book catalogue (books.py)",
     "Admin add/update/delete, member access denied, search",
     "Functional, Role-based access, Database", "pytest + Flask test client + sqlite3"),
    ("test_phase4_loans", 4, "Loans (loans.py)",
     "Borrow and return, 3-book limit, stock, due dates, fines",
     "Functional, BVA, Integration", "pytest + Flask test client"),
    ("test_phase5_integration", 5, "Whole system",
     "End-to-end member journey, SQL injection, error handling",
     "System, Integration, Security", "pytest + Flask test client"),
]

CYCLES = [
    ("Cycle 1", "v1.0 (commit eb8772f)", "First run of the suite on the initial code"),
    ("Cycle 2", "v1.0 + DEF-01 fix (commit 2d7cd48)", "Re-test after fixing the crash that blocked 21 tests"),
    ("Cycle 3", "v1.1 (commit 72837f4)", "Regression run after fixing DEF-02 to DEF-06"),
]

# Reproduced defects are the ones the suite actually caught (see reports/cycle1 and cycle2).
DEFECTS = [
    {"id": "DEF-01", "severity": "Critical", "tc": "TC-20",
     "desc": "POST /books saved the book but returned HTTP 500 (TypeError: add_book indexed the Response object). Blocked every test that needs a book.",
     "found": "Cycle 1", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-02", "severity": "Medium", "tc": "TC-13",
     "desc": "Usernames differing only in case ('sarim' / 'Sarim') could both be registered; UNIQUE column was case-sensitive.",
     "found": "Cycle 1", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-03", "severity": "High", "tc": "TC-35",
     "desc": "Borrowing limit off by one: check used '> 3' so a member could hold 4 books.",
     "found": "Cycle 2", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-04", "severity": "High", "tc": "TC-28",
     "desc": "Reducing total_copies below the number on loan was accepted and made available_copies negative.",
     "found": "Cycle 2", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-05", "severity": "Medium", "tc": "TC-29",
     "desc": "PUT /books did not validate total_copies: text caused HTTP 500, 0 was accepted.",
     "found": "Cycle 2", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-06", "severity": "High", "tc": "TC-30",
     "desc": "Deleting a book that was on loan was allowed and silently deleted the members' loan records.",
     "found": "Cycle 2", "status": "Fixed", "kind": "Reproduced"},
    {"id": "DEF-07", "severity": "Medium", "tc": "TC-19",
     "desc": "Login tokens never expire; a token is only removed by logout (no expiry column in tokens table).",
     "found": "Code review", "status": "Deferred", "kind": "Static review"},
    {"id": "DEF-08", "severity": "Medium", "tc": "TC-17",
     "desc": "No limit on failed login attempts, so passwords can be guessed by brute force.",
     "found": "Code review", "status": "Open", "kind": "Static review"},
    {"id": "DEF-09", "severity": "Low", "tc": "TC-33",
     "desc": "Suspected race: the copies check and the decrement in borrow() are separate statements, so two simultaneous requests could both take the last copy. Not reproduced (tests run sequentially).",
     "found": "Code review", "status": "Open", "kind": "Static review"},
]


def _fields(doc):
    out = {}
    for key in ("Scenario", "Steps", "Expected", "Priority"):
        m = re.search(rf"{key}:\s*(.+?)(?=\n\s*(?:Scenario|Steps|Expected|Priority):|\Z)", doc, re.S)
        out[key.lower()] = " ".join(m.group(1).split()) if m else ""
    return out


def load_junit(path):
    """Map test function name -> (outcome, short message)."""
    results = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        if failure is None:
            results[case.get("name")] = ("PASS", "")
        else:
            msg = (failure.get("message") or "").splitlines()[0]
            results[case.get("name")] = ("FAIL", msg[:120])
    return results


def load():
    cycles = [load_junit(REPORTS / f"cycle{i}" / "junit.xml") for i in (1, 2, 3)]
    defects_by_tc = {d["tc"]: d for d in DEFECTS if d["kind"] == "Reproduced"}
    cases = []
    for stem, phase, module, *_ in PHASES:
        tree = ast.parse((ROOT / "tests" / f"{stem}.py").read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_tc"):
                tc = "TC-" + node.name.split("_")[1][2:]
                outcomes = [c[node.name][0] for c in cycles]
                final = outcomes[-1]
                if final == "PASS" and "FAIL" in outcomes:
                    notes = []
                    for i, outcome in enumerate(outcomes[:-1], start=1):
                        if outcome != "FAIL":
                            continue
                        own = defects_by_tc.get(tc)
                        cause = own["id"] if own and i >= int(own["found"][-1]) else "blocked by DEF-01"
                        notes.append(f"C{i} FAIL ({cause})")
                    actual = ", ".join(notes) + "; C3 PASS after fix"
                elif final == "PASS":
                    actual = "Matches expected result"
                else:
                    actual = "Failed: " + cycles[-1][node.name][1]
                cases.append({"id": tc, "func": node.name, "phase": phase,
                              "module": module.split(" (")[0], **_fields(ast.get_docstring(node)),
                              "outcomes": outcomes, "actual": actual, "status": final})
    cov = json.loads((REPORTS / "cycle3" / "coverage.json").read_text())
    coverage = {Path(f).name: v["summary"] for f, v in cov["files"].items()}
    totals = cov["totals"]
    summary = []
    for (name, version, purpose), res in zip(CYCLES, cycles):
        passed = sum(1 for o, _ in res.values() if o == "PASS")
        summary.append({"cycle": name, "version": version, "purpose": purpose,
                        "run": len(res), "passed": passed, "failed": len(res) - passed})
    return {"cases": cases, "cycles": summary, "coverage": coverage, "cov_total": totals}


if __name__ == "__main__":
    data = load()
    print(len(data["cases"]), "test cases")
    for c in data["cycles"]:
        print(c)
    print("coverage", round(data["cov_total"]["percent_covered"], 1))
