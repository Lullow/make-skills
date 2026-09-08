#!/usr/bin/env python3
"""Round-trip test across the three skills.

spec-align, write-ticket and ticket-done share two file formats but nothing
enforces that at runtime, so it is enforced here: a spec is checked, a ticket is
generated from it, checked while unfinished, finished, and checked again.

If this fails, the skills have diverged and an artefact produced by one will be
rejected by the next for the wrong reason.

Run:  python3 tests/test_roundtrip.py
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_TICKET = ROOT / ".claude/skills/write-ticket/scripts/new_ticket.py"
CHECK_TICKET = ROOT / ".claude/skills/ticket-done/scripts/check_ticket.py"
CHECK_SPEC = ROOT / ".claude/skills/spec-align/scripts/check_spec.py"

SPEC = """---
name: {name}
status: {status}
date: 2026-09-08
---

# Context budget estimator

## Problem
Long sessions overflow the context window without warning.

## Goals
An estimate of how much of the window a session is using.

## Non-goals
Does not compact or evict anything.

## Decisions
- **Estimate from character count** — a tokeniser dependency is not worth the accuracy.

## Assumptions
- Only Anthropic models need supporting.

## Open questions
{questions}"""

failures = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(f"{label}{': ' + detail.strip() if detail else ''}")


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def write_spec(repo, filename, status, questions=""):
    path = repo / "docs/specs" / filename
    path.write_text(SPEC.format(name=filename[:-3], status=status, questions=questions),
                    encoding="utf-8")
    return f"docs/specs/{filename}"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run(["git", "init", "-q"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "test"], repo)
        (repo / "docs/specs").mkdir(parents=True)

        agreed = write_spec(repo, "agreed.md", "agreed")
        draft = write_spec(repo, "draft.md", "draft")
        contradictory = write_spec(repo, "contradictory.md", "agreed",
                                   questions="- Should the system prompt count?")

        print("1. spec checker accepts a settled spec")
        result = run([sys.executable, str(CHECK_SPEC), agreed], repo)
        check("exits zero", result.returncode == 0, result.stdout)
        check("reports PASS", "PASS" in result.stdout, result.stdout)

        print("2. spec checker refuses 'agreed' while a question is open")
        result = run([sys.executable, str(CHECK_SPEC), contradictory], repo)
        check("exits non-zero", result.returncode != 0)
        check("names the open question", "open question remains" in result.stdout, result.stdout)

        print("3. spec checker rejects a spec with a section left as a placeholder")
        gutted = repo / "docs/specs/gutted.md"
        gutted.write_text((repo / "docs/specs/agreed.md").read_text(encoding="utf-8").replace(
            "Does not compact or evict anything.", "<what this does not do>"), encoding="utf-8")
        result = run([sys.executable, str(CHECK_SPEC), "docs/specs/gutted.md"], repo)
        check("exits non-zero", result.returncode != 0)
        check("names the placeholder section",
              "placeholder: ## Non-goals" in result.stdout, result.stdout)

        print("4. ticket generator refuses a spec that does not exist")
        result = run([sys.executable, str(NEW_TICKET), "--prefix", "PA",
                      "--spec", "docs/specs/missing.md", "--title", "No spec",
                      "--criterion", "x"], repo)
        check("exits non-zero", result.returncode != 0, result.stdout)
        check("no ticket directory created", not (repo / "docs/tickets").exists())

        print("5. ticket generator refuses a spec that is still a draft")
        result = run([sys.executable, str(NEW_TICKET), "--prefix", "PA", "--spec", draft,
                      "--title", "Too early", "--criterion", "x"], repo)
        check("exits non-zero", result.returncode != 0, result.stdout)
        check("explains why", "not 'agreed'" in result.stdout, result.stdout)

        print("6. ticket generator creates a ticket from an agreed spec")
        result = run([sys.executable, str(NEW_TICKET), "--prefix", "PA", "--spec", agreed,
                      "--title", "Add token budget estimator",
                      "--criterion", "estimate_tokens('') returns 0 rather than raising",
                      "--criterion", "budget_for(model) returns the documented window",
                      "--constraint", "must use the stdlib only"], repo)
        check("exits zero", result.returncode == 0, result.stdout + result.stderr)
        ticket = repo / "docs/tickets/PA-001-add-token-budget-estimator.md"
        check("filename is <ID>-<slug>.md", ticket.is_file(),
              str(list((repo / "docs/tickets").glob("*"))) if (repo / "docs/tickets").exists() else "no dir")
        if not ticket.is_file():
            return report()
        body = ticket.read_text(encoding="utf-8")
        check("constraints are not checkboxes",
              len(re.findall(r"^\s*[-*]\s*\[[ xX]\]", body, re.MULTILINE)) == 2, body)

        print("7. ticket checker rejects the fresh ticket, for the right reasons")
        result = run([sys.executable, str(CHECK_TICKET), "PA-001"], repo)
        check("exits non-zero", result.returncode != 0)
        check("reports both unticked criteria",
              result.stdout.count("unticked criterion") == 2, result.stdout)
        check("reports missing commit",
              "no commit message references PA-001" in result.stdout, result.stdout)
        check("frontmatter and spec path accepted",
              "frontmatter id is" not in result.stdout
              and "spec path does not exist" not in result.stdout, result.stdout)

        print("8. ticket checker accepts the finished ticket")
        ticket.write_text(body.replace("- [ ]", "- [x]").replace("status: open", "status: done"),
                          encoding="utf-8")
        run(["git", "add", "-A"], repo)
        run(["git", "commit", "-qm", "PA-001 add token budget estimator"], repo)
        result = run([sys.executable, str(CHECK_TICKET), "PA-001"], repo)
        check("exits zero", result.returncode == 0, result.stdout)
        check("reports PASS", "PASS" in result.stdout, result.stdout)
        check("counts 2 ticked criteria", "2 ticked, 0 unticked" in result.stdout, result.stdout)

        print("9. the next ticket takes the next ID")
        run([sys.executable, str(NEW_TICKET), "--spec", agreed,
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
    print("PASS — spec-align, write-ticket and ticket-done agree on both formats")
    return 0


if __name__ == "__main__":
    sys.exit(main())
