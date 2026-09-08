#!/usr/bin/env python3
"""Scaffold a ticket file that the ticket-done checker will accept.

Usage (from the repo root):
    python3 .claude/skills/write-ticket/scripts/new_ticket.py \
        --spec docs/specs/context-budget.md \
        --title "Add token budget estimator" \
        --criterion "estimate_tokens('') returns 0 rather than raising" \
        --criterion "budget_for(model) returns the documented window"

Handles only what a script does more reliably than a reader: allocating the
next ID in sequence, slugging the filename, and emitting frontmatter in the
shape check_ticket.py parses. What the criteria say is not automatable.

Refuses to create a ticket that check_ticket.py would reject.

Exit code 0 = ticket written, 1 = refused. Standard library only.
"""

import argparse
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path("docs/tickets")
ID_WIDTH = 3


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:50].rstrip("-") or "untitled"


def infer_prefix(ticket_dir: Path) -> str:
    prefixes = set()
    for path in ticket_dir.glob("*.md"):
        match = re.match(r"([A-Za-z]+)-\d+-", path.name)
        if match:
            prefixes.add(match.group(1).upper())
    if len(prefixes) == 1:
        return prefixes.pop()
    if not prefixes:
        fail("no existing tickets to infer a prefix from — pass --prefix (e.g. --prefix PA)")
    fail(f"several prefixes in use ({sorted(prefixes)}) — pass --prefix to choose one")
    raise AssertionError("unreachable")


def next_id(ticket_dir: Path, prefix: str) -> str:
    numbers = []
    for path in ticket_dir.glob(f"{prefix}-*.md"):
        match = re.match(rf"{re.escape(prefix)}-(\d+)-", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"{prefix}-{max(numbers, default=0) + 1:0{ID_WIDTH}d}"


def build(ticket_id, title, spec, criteria, constraints, depends_on):
    lines = ["---", f"id: {ticket_id}", f"title: {title}", "status: open", f"spec: {spec}"]
    if depends_on:
        lines.append(f"depends_on: {depends_on}")
    lines += ["---", "", f"# {ticket_id} — {title}", "", f"Spec: [{spec}]({spec})", ""]
    lines += ["## Acceptance criteria", ""]
    lines += [f"- [ ] {item}" for item in criteria]
    if constraints:
        # Plain bullets on purpose: check_ticket.py counts any checkbox in the
        # body as an acceptance criterion.
        lines += ["", "## Constraints", ""]
        lines += [f"- {item}" for item in constraints]
    lines += ["", "## Notes", ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="path to the agreed spec, relative to the repo root")
    parser.add_argument("--title", required=True)
    parser.add_argument("--criterion", action="append", required=True,
                        help="one acceptance criterion; repeat for each")
    parser.add_argument("--constraint", action="append", default=[],
                        help="a mandated implementation detail; repeat for each")
    parser.add_argument("--depends", default="", help="ticket ID this one cannot start before")
    parser.add_argument("--prefix", default="", help="ticket ID prefix, e.g. PA (inferred when omitted)")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="ticket directory")
    args = parser.parse_args()

    # The generator must not produce anything the checker would reject, so the
    # spec has to exist before the ticket does.
    spec = args.spec.strip()
    if not Path(spec).is_file():
        fail(f"spec does not exist: {spec} — write the spec before the ticket")

    title = args.title.strip()
    if "#" in title:
        fail("title must not contain '#' — the frontmatter parser treats it as a comment")
    if not title:
        fail("title is empty")

    criteria = [c.strip() for c in args.criterion if c.strip()]
    if not criteria:
        fail("at least one acceptance criterion is required")
    for item in criteria:
        if item.startswith(("- ", "* ", "[ ]", "[x]")):
            fail(f"pass the criterion text only, without list or checkbox markup: {item!r}")
    if len(criteria) > 5:
        print(f"note: {len(criteria)} criteria — more than five usually means this is two tickets")

    ticket_dir = Path(args.dir)
    ticket_dir.mkdir(parents=True, exist_ok=True)

    prefix = args.prefix.strip().upper() or infer_prefix(ticket_dir)
    if not prefix.isalpha():
        fail(f"prefix must be letters only, got {prefix!r}")

    ticket_id = next_id(ticket_dir, prefix)
    path = ticket_dir / f"{ticket_id}-{slugify(title)}.md"
    if path.exists():
        fail(f"refusing to overwrite existing file: {path}")

    constraints = [c.strip() for c in args.constraint if c.strip()]
    path.write_text(build(ticket_id, title, spec, criteria, constraints, args.depends.strip()),
                    encoding="utf-8")

    print(f"created:  {path}")
    print(f"id:       {ticket_id}")
    print(f"criteria: {len(criteria)}")
    print("\nConfirm the criteria with the user before writing code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
