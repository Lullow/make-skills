#!/usr/bin/env python3
"""Round-trip test across two skills.

write-ticket's generator and ticket-done's checker have to agree on one ticket
format. Nothing enforces that at runtime, so it is enforced here: a ticket is
generated, checked while unfinished, finished, and checked again.

If this fails, the two skills have diverged and a ticket produced by one will be
rejected by the other for the wrong reason.

Run:  python3 tests/test_roundtrip.py
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW = ROOT / ".claude/skills/write-ticket/scripts/new_ticket.py"
CHECK = ROOT / ".claude/skills/ticket-done/scripts/check_ticket.py"

failures = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run(["git", "init", "-q"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "test"], repo)

        (repo / "docs/specs").mkdir(parents=True)
        (repo / "docs/specs/example.md").write_text("# Example spec\n", encoding="utf-8")

        print("1. generator refuses a ticket whose spec does not exist")
        result = run([sys.executable, str(NEW), "--prefix", "PA", "--spec", "docs/specs/missing.md",
                      "--title", "No spec", "--criterion", "x"], repo)
        check("exits non-zero", result.returncode != 0, result.stdout)
        check("no ticket directory created", not (repo / "docs/tickets").exists())

        print("2. generator creates a ticket")
        result = run([sys.executable, str(NEW), "--prefix", "PA", "--spec", "docs/specs/example.md",
                      "--title", "Add token budget estimator",
                      "--criterion", "estimate_tokens('') returns 0 rather than raising",
                      "--criterion", "budget_for(model) returns the documented window",
                      "--constraint", "must use the stdlib only"], repo)
        check("exits zero", result.returncode == 0, result.stdout + result.stderr)
        ticket = repo / "docs/tickets/PA-001-add-token-budget-estimator.md"
        check("filename is <ID>-<slug>.md", ticket.is_file(), str(list((repo / 'docs/tickets').glob('*'))))
        if not ticket.is_file():
            return report()
        body = ticket.read_text(encoding="utf-8")
        check("constraints are not checkboxes",
              len(re.findall(r"^\s*[-*]\s*\[[ xX]\]", body, re.MULTILINE)) == 2, body)

        print("3. checker rejects the fresh ticket, for the right reasons")
        result = run([sys.executable, str(CHECK), "PA-001"], repo)
        check("exits non-zero", result.returncode != 0)
        check("reports both unticked criteria", result.stdout.count("unticked criterion") == 2, result.stdout)
        check("reports missing commit", "no commit message references PA-001" in result.stdout, result.stdout)
        check("frontmatter and spec path accepted",
              "id is" not in result.stdout and "spec path does not exist" not in result.stdout, result.stdout)

        print("4. checker accepts the finished ticket")
        ticket.write_text(body.replace("- [ ]", "- [x]").replace("status: open", "status: done"),
                          encoding="utf-8")
        run(["git", "add", "-A"], repo)
        run(["git", "commit", "-qm", "PA-001 add token budget estimator"], repo)
        result = run([sys.executable, str(CHECK), "PA-001"], repo)
        check("exits zero", result.returncode == 0, result.stdout)
        check("reports PASS", "PASS" in result.stdout, result.stdout)
        check("counts 2 ticked criteria", "2 ticked, 0 unticked" in result.stdout, result.stdout)

        print("5. next ticket takes the next ID")
        run([sys.executable, str(NEW), "--spec", "docs/specs/example.md",
             "--title", "Second thing", "--criterion", "y"], repo)
        check("prefix inferred and ID incremented",
              (repo / "docs/tickets/PA-002-second-thing.md").is_file())

    return report()


def report() -> int:
    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("PASS — generator and checker agree on the ticket format")
    return 0


if __name__ == "__main__":
    sys.exit(main())
