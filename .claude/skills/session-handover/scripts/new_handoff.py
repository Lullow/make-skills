#!/usr/bin/env python3
"""Scaffold a handoff with the machine-checkable facts already filled in.

Usage (from the repo root):
    python3 .claude/skills/session-handover/scripts/new_handoff.py \
        --title "Ticket workflow skills"

Gathers only what a script gathers more reliably than a reader: branch and
tracking state, uncommitted and untracked files, the commits that are yours,
every ticket's status, and which specs are still drafts. Those are the facts a
model reconstructs from memory with quiet errors, and a quiet error in a handoff
is worse than an omission.

Everything requiring judgement is left as a <placeholder> for you to replace.

The frontmatter parser is deliberately the same minimal one used by
check_ticket.py and check_spec.py, so each skill stays installable on its own.

Exit code 0 = handoff written. Standard library only.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TICKET_DIR = Path("docs/tickets")
SPEC_DIR = Path("docs/specs")
STATUS_ORDER = ["in-progress", "open", "done"]


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else ""


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
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


def state_lines() -> list:
    if not git("rev-parse", "--git-dir"):
        return ["- not a git repository"]

    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "(detached)"
    lines = [f"- branch: `{branch}`"]

    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        counts = git("rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        behind, ahead = (counts + ["0", "0"])[:2]
        lines.append(f"- upstream: `{upstream}` — {ahead} ahead, {behind} behind")
        commits = git("log", "--oneline", f"{upstream}..HEAD")
        label = "unpushed commits"
    else:
        lines.append("- upstream: none — nothing has been pushed anywhere")
        commits = git("log", "--oneline", "-10")
        label = "last 10 commits"

    dirty = [line for line in git("status", "--porcelain").splitlines() if line]
    untracked = [line for line in dirty if line.startswith("??")]
    if dirty:
        lines.append(f"- working tree: {len(dirty) - len(untracked)} changed, "
                     f"{len(untracked)} untracked")
        for line in dirty[:10]:
            lines.append(f"  - `{line.strip()}`")
        if len(dirty) > 10:
            lines.append(f"  - ...and {len(dirty) - 10} more")
    else:
        lines.append("- working tree: clean")

    lines.append(f"- {label}:")
    if commits:
        lines.extend(f"  - `{line}`" for line in commits.splitlines())
    else:
        lines.append("  - none")
    return lines


def ticket_lines() -> list:
    if not TICKET_DIR.is_dir():
        return [f"- no `{TICKET_DIR}/` directory"]
    by_status = {}
    for path in sorted(TICKET_DIR.glob("*.md")):
        meta = frontmatter(path)
        status = meta.get("status", "unknown")
        entry = f"{meta.get('id', path.stem)} — {meta.get('title', path.stem)}"
        by_status.setdefault(status, []).append(f"`{path}` · {entry}")
    if not by_status:
        return [f"- no tickets in `{TICKET_DIR}/`"]
    lines = []
    for status in STATUS_ORDER + sorted(set(by_status) - set(STATUS_ORDER)):
        for entry in by_status.get(status, []):
            lines.append(f"- **{status}** — {entry}")
    return lines


def spec_lines() -> list:
    if not SPEC_DIR.is_dir():
        return []
    drafts = [path for path in sorted(SPEC_DIR.glob("*.md"))
              if frontmatter(path).get("status") not in ("agreed", "superseded")]
    if not drafts:
        return []
    return ["", "Specs not yet agreed — these block ticket creation:"] + \
           [f"- `{path}`" for path in drafts]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="<what this session was doing>")
    parser.add_argument("--out", default="", help="output path (default /tmp/handoff-<repo>-<stamp>.md)")
    args = parser.parse_args()

    top = git("rev-parse", "--show-toplevel")
    repo = Path(top).name if top else Path.cwd().name
    now = datetime.now()
    out = Path(args.out) if args.out else Path(f"/tmp/handoff-{repo}-{now:%Y-%m-%d-%H%M}.md")

    body = [
        "---", f"repo: {repo}", f"date: {now:%Y-%m-%d %H:%M}", "---", "",
        f"# Handoff — {args.title}", "",
        "## State", *state_lines(), *spec_lines(), "",
        "## Tickets", *ticket_lines(), "",
        "## Next step",
        "<one action, concrete enough to start without asking a question>", "",
        "## Failed approaches",
        "<what was tried, what happened, and why you stopped — or: none this session>", "",
        "## Traps",
        "<what surprised you about this environment — or: none this session>", "",
        "## Filed elsewhere",
        "<what you wrote into the repo this session, and where — or: nothing>", "",
        "## Session index",
        "<two-level tree; every leaf carries a literal string that appears in the transcript>",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")

    remaining = sum(1 for line in body if line.startswith("<"))
    print(f"created:      {out}")
    print(f"placeholders: {remaining} — replace every one before this counts as a handoff")
    return 0


if __name__ == "__main__":
    sys.exit(main())
