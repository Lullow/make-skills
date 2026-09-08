#!/usr/bin/env python3
"""Mechanical checks for a spec before it is called agreed.

Usage (from the repo root):
    python3 .claude/skills/spec-align/scripts/check_spec.py docs/specs/context-budget.md

Checks only what a script checks more reliably than a reader: frontmatter
shape, required sections, template placeholders left in place, and the one
that matters — that a spec is not marked agreed while open questions remain.
Whether the content is any good is not automatable and stays in the skill.

The frontmatter parser is deliberately the same minimal one used by
check_ticket.py: each skill stays self-contained and installable on its own,
which is worth more here than removing thirty duplicated lines.

Exit code 0 = all checks passed, 1 = at least one failure. Standard library only.
"""

import re
import sys
from pathlib import Path

VALID_STATUS = {"draft", "agreed", "superseded"}
REQUIRED_SECTIONS = ["Problem", "Goals", "Non-goals", "Decisions"]
PLACEHOLDER_LINE = re.compile(r"^[-*]?\s*(<[^>]{1,80}>|[\s—,.:;-])+$")


def fail_hard(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def parse_frontmatter(text: str) -> dict:
    """Flat key: value pairs only — no yaml dependency."""
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


def split_sections(body: str) -> dict:
    """Map '## Heading' -> its lines, ignoring the level-1 title."""
    sections, current = {}, None
    for line in body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            sections[current] = []
        elif current is not None:
            sections[current] = sections[current] + [line]
    return sections


def content_lines(lines: list) -> list:
    """Real content: no blanks, no leftover template placeholders."""
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        if PLACEHOLDER_LINE.match(stripped.replace("**", "")):
            continue
        out.append(stripped)
    return out


def main() -> int:
    if len(sys.argv) != 2:
        fail_hard("usage: python3 .claude/skills/spec-align/scripts/check_spec.py <path/to/spec.md>")

    path = Path(sys.argv[1])
    if not path.is_file():
        fail_hard(f"no such file: {path} — run this from the repo root")

    text = path.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text
    sections = split_sections(body)

    failures, notes = [], []

    # --- frontmatter -----------------------------------------------------
    if not meta:
        failures.append("no frontmatter — a spec needs name, status and date")
    if not meta.get("name"):
        failures.append("no name: in frontmatter")
    status = meta.get("status")
    if status not in VALID_STATUS:
        failures.append(f"status is {status!r}, expected one of {sorted(VALID_STATUS)}")
    date = meta.get("date", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        failures.append(f"date is {date!r}, expected YYYY-MM-DD")

    # --- required sections ------------------------------------------------
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            failures.append(f"missing section: ## {name}")
        elif not content_lines(sections[name]):
            failures.append(f"section is empty or still a template placeholder: ## {name}")

    # --- the gate ---------------------------------------------------------
    open_questions = content_lines(sections.get("Open questions", []))
    if status == "agreed" and open_questions:
        for item in open_questions:
            failures.append(f"open question remains while status is agreed: {item}")
    elif open_questions:
        notes.append(f"{len(open_questions)} open question(s) — resolve before status: agreed")

    if "Assumptions" not in sections:
        notes.append("no ## Assumptions section — the decisions you made silently are invisible")

    # --- report -----------------------------------------------------------
    print(f"spec:     {path}")
    print(f"status:   {status}")
    print(f"sections: {', '.join(sections) or 'none'}")
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
