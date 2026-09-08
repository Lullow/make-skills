#!/usr/bin/env python3
"""Mechanical checks for a ticket that is about to be marked done.

Usage (from the repo root):
    python .claude/skills/ticket-done/scripts/check_ticket.py PA-001

Checks only what a script can check more reliably than a reader:
frontmatter shape, unticked acceptance criteria, git traceability,
and a clean working tree. Judgement calls stay in the skill.

Exit code 0 = all checks passed, 1 = at least one failure.
Standard library only.
"""

import re
import subprocess
import sys
from pathlib import Path

TICKET_DIR = Path("docs/tickets")
VALID_STATUS = {"open", "in-progress", "done"}


def find_ticket(ticket_id: str) -> Path:
    if not TICKET_DIR.is_dir():
        fail_hard(f"no {TICKET_DIR}/ directory — run this from the repo root")
    matches = sorted(TICKET_DIR.glob(f"{ticket_id}-*.md"))
    if not matches:
        fail_hard(f"no ticket file matching {ticket_id}-*.md in {TICKET_DIR}/")
    if len(matches) > 1:
        fail_hard(f"{ticket_id} matches several files: {[m.name for m in matches]}")
    return matches[0]


def parse_frontmatter(text: str) -> dict:
    """Minimal frontmatter reader — flat key: value pairs, no yaml dependency."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields = {}
    for line in text[3:end].splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def fail_hard(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail_hard("usage: python .claude/skills/ticket-done/scripts/check_ticket.py <TICKET-ID>")

    ticket_id = sys.argv[1]
    path = find_ticket(ticket_id)
    text = path.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)

    failures = []
    notes = []

    # --- frontmatter -----------------------------------------------------
    if meta.get("id") != ticket_id:
        failures.append(f"frontmatter id is {meta.get('id')!r}, expected {ticket_id!r}")

    status = meta.get("status")
    if status not in VALID_STATUS:
        failures.append(f"status is {status!r}, expected one of {sorted(VALID_STATUS)}")

    spec = meta.get("spec")
    if not spec:
        notes.append("no spec: path in frontmatter — the ticket has no traceable origin")
    elif not Path(spec).exists():
        failures.append(f"spec path does not exist: {spec}")

    # --- acceptance criteria --------------------------------------------
    body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text
    unticked = re.findall(r"^\s*[-*]\s*\[ \]\s*(.+)$", body, re.MULTILINE)
    ticked = re.findall(r"^\s*[-*]\s*\[[xX]\]\s*(.+)$", body, re.MULTILINE)

    if not ticked and not unticked:
        failures.append("no acceptance criteria checkboxes found in the ticket body")
    for item in unticked:
        failures.append(f"unticked criterion: {item.strip()}")

    # --- git traceability -------------------------------------------------
    if git("rev-parse", "--git-dir"):
        commits = git("log", "--oneline", f"--grep={ticket_id}")
        if not commits:
            failures.append(f"no commit message references {ticket_id}")
        else:
            notes.append(f"{len(commits.splitlines())} commit(s) reference {ticket_id}")

        dirty = git("status", "--porcelain")
        if dirty:
            failures.append(
                f"working tree is not clean ({len(dirty.splitlines())} changed file(s))"
            )
    else:
        notes.append("not a git repository — traceability checks skipped")

    # --- report -----------------------------------------------------------
    print(f"ticket:   {path}")
    print(f"criteria: {len(ticked)} ticked, {len(unticked)} unticked")
    for note in notes:
        print(f"note:     {note}")

    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nPASS — mechanical checks clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
