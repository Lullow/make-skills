#!/usr/bin/env python3
"""Lint the skills in .claude/skills/ for defects that only surface at run time.

Usage (from the repo root):
    python3 scripts/lint_skills.py

Every rule here comes from a defect this repo actually shipped, which is the whole
selection principle: a linter built from invented rules produces noise, and noise
trains people to stop reading the output.

    R1  a skill directory with no SKILL.md
    R2  frontmatter name that disagrees with the directory name
    R3  a description with no "Use ..." clause, so the skill under-triggers
    R4  a runnable command naming a .py path that does not resolve from the repo root
    R5  a runnable command invoking bare `python`, which is absent on some machines

R4 and R5 inspect one thing only: lines inside a fenced code block that invoke an
interpreter. Two narrower scopes than the obvious ones, both because the obvious one
misfired on the first live run. Scanning all prose flagged every SKILL.md that names
its own script in a sentence — four hits, all legitimate. Scanning whole code blocks
flagged a filename inside an illustrative example. Neither is a command an agent will
copy and run, which is the actual defect class.

Every failure is reported in one pass — an author who can fix only one problem per
run will stop running it.

Exit code 0 = all skills clean, 1 = at least one failure. Standard library only.
"""

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(".claude/skills")
PY_PATH = re.compile(r"[A-Za-z0-9_./-]+\.py")
INVOCATION = re.compile(r"\bpython3?\b")
BARE_PYTHON = re.compile(r"\bpython(?!3)\b")
USE_CLAUSE = re.compile(r"(?:^|[.;!?]\s+)Use\b")


def parse_frontmatter(text: str) -> dict:
    """Flat key: value pairs only — the same minimal reader the skills' own scripts use."""
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


def code_lines(text: str):
    """Lines inside fenced code blocks, as (line_number, text) pairs.

    Numbers come straight from the source rather than from measuring the
    frontmatter's length: that arithmetic reported every line one too high,
    because the measured prefix ends part-way through the closing delimiter.
    """
    lines, in_fence, in_frontmatter = [], False, False
    for number, line in enumerate(text.splitlines(), start=1):
        if number == 1 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            in_frontmatter = line.strip() != "---"
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append((number, line))
    return lines


def lint_skill(directory: Path):
    """Return (failures, summary) for one skill directory."""
    failures = []
    skill_file = directory / "SKILL.md"

    if not skill_file.is_file():
        return [f"{directory}: no SKILL.md — not a skill, or a broken one"], None

    text = skill_file.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)

    name = meta.get("name", "")
    if not name:
        failures.append(f"{skill_file}: no name: in frontmatter")
    elif name != directory.name:
        failures.append(
            f"{skill_file}: frontmatter name is {name!r} but the directory is "
            f"{directory.name!r} — they must match or the skill will not resolve"
        )

    description = meta.get("description", "")
    if not description:
        failures.append(f"{skill_file}: no description: in frontmatter")
    elif not USE_CLAUSE.search(description):
        failures.append(
            f"{skill_file}: description has no 'Use ...' clause saying when to trigger — "
            f"a skill that never fires is worse than no skill"
        )

    for number, line in code_lines(text):
        if BARE_PYTHON.search(line):
            failures.append(
                f"{skill_file}:{number}: invokes bare 'python' — use 'python3', which exists "
                f"on machines where 'python' does not"
            )
        if not INVOCATION.search(line):
            continue
        for path in PY_PATH.findall(line):
            if not Path(path).exists():
                failures.append(
                    f"{skill_file}:{number}: runnable command names {path!r}, which does not "
                    f"resolve from the repo root"
                )

    scripts = sorted(p.name for p in (directory / "scripts").glob("*.py")) \
        if (directory / "scripts").is_dir() else []
    summary = f"{directory.name:<18} {len(text.splitlines()):>4} lines" \
              f"{'  + ' + ', '.join(scripts) if scripts else ''}"
    return failures, summary


def main() -> int:
    if not SKILL_ROOT.is_dir():
        print(f"ERROR: no {SKILL_ROOT}/ directory — run this from the repo root")
        return 1

    directories = sorted(p for p in SKILL_ROOT.iterdir() if p.is_dir())
    if not directories:
        print(f"ERROR: no skills found in {SKILL_ROOT}/")
        return 1

    all_failures = []
    for directory in directories:
        failures, summary = lint_skill(directory)
        all_failures.extend(failures)
        mark = "FAIL" if failures else "ok  "
        print(f"{mark}  {summary if summary else directory.name}")

    if all_failures:
        print(f"\nFAIL ({len(all_failures)}):")
        for item in all_failures:
            print(f"  - {item}")
        return 1

    print(f"\nPASS — {len(directories)} skill(s) clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
