#!/usr/bin/env python3
"""Tests for scripts/lint_skills.py, one per acceptance criterion in ML-001 and ML-002.

The last two cases are regression guards, not criteria: the first live run of the
linter flagged a filename inside an illustrative example and every SKILL.md that
names its own script in a sentence. Both are legitimate text, and a linter that
cries wolf stops being read.

Run:  python3 tests/test_lint.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINT = ROOT / "scripts/lint_skills.py"

SKILL = """---
name: {name}
description: {description}
---

# Demo

{prose}

```
{command}
```
"""

GOOD_DESCRIPTION = "Does a thing. Use when the thing needs doing."

failures = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(f"{label}{': ' + detail.strip() if detail else ''}")


def make_skill(root: Path, directory: str, *, name=None, description=GOOD_DESCRIPTION,
               command="python3 .claude/skills/demo/scripts/tool.py", prose="Prose.",
               bundle=True, skill_file=True, extra_scripts=()):
    path = root / ".claude/skills" / directory
    (path / "scripts").mkdir(parents=True)
    if bundle:
        (path / "scripts/tool.py").write_text("print('hi')\n", encoding="utf-8")
    for script_name in extra_scripts:
        (path / "scripts" / script_name).write_text("print('hi')\n", encoding="utf-8")
    if skill_file:
        (path / "SKILL.md").write_text(
            SKILL.format(name=name if name is not None else directory,
                         description=description, command=command, prose=prose),
            encoding="utf-8")
    return path


def lint(root: Path):
    return subprocess.run([sys.executable, str(LINT)], cwd=root,
                          capture_output=True, text=True, encoding="utf-8")


def case(label: str, **kwargs):
    """Lint a fresh repo holding one skill built from kwargs."""
    tmp = tempfile.TemporaryDirectory()
    make_skill(Path(tmp.name), "demo", **kwargs)
    result = lint(Path(tmp.name))
    tmp.cleanup()
    return result


def main() -> int:
    print("0. a clean skill passes")
    result = case("clean")
    check("exits zero", result.returncode == 0, result.stdout)
    check("prints a summary line for it", "demo" in result.stdout, result.stdout)

    print("1. unresolvable script path in a runnable command")
    result = case("bad path", command="python3 .claude/skills/demo/scripts/missing.py")
    check("exits one", result.returncode == 1, result.stdout)
    check("names the path", "missing.py" in result.stdout, result.stdout)
    check("says it does not resolve", "does not resolve" in result.stdout, result.stdout)

    print("1b. the reported line number is the real one")
    tmp = tempfile.TemporaryDirectory()
    path = make_skill(Path(tmp.name), "demo",
                      command="python3 .claude/skills/demo/scripts/missing.py")
    source = (path / "SKILL.md").read_text(encoding="utf-8").splitlines()
    expected = next(i for i, line in enumerate(source, 1) if "missing.py" in line)
    result = lint(Path(tmp.name))
    tmp.cleanup()
    check(f"points at line {expected}", f"SKILL.md:{expected}:" in result.stdout, result.stdout)

    print("2. frontmatter name disagreeing with the directory")
    result = case("name mismatch", name="something-else")
    check("exits one", result.returncode == 1, result.stdout)
    check("names both", "'something-else'" in result.stdout and "'demo'" in result.stdout,
          result.stdout)

    print("3. bare python invocation")
    result = case("bare python", command="python .claude/skills/demo/scripts/tool.py")
    check("exits one", result.returncode == 1, result.stdout)
    check("names the line and the fix", "bare 'python'" in result.stdout, result.stdout)

    print("4. description with no 'Use ...' clause")
    result = case("no trigger", description="Does a thing to some files.")
    check("exits one", result.returncode == 1, result.stdout)
    check("explains the consequence", "never fires" in result.stdout, result.stdout)

    print("5. a directory with no SKILL.md")
    result = case("no skill file", skill_file=False)
    check("exits one", result.returncode == 1, result.stdout)
    check("says why", "no SKILL.md" in result.stdout, result.stdout)

    print("6. regression: a .py filename in an example, not a command")
    result = case("example block", bundle=False,
                  command="- failed: per-model caching in src/budget.py — grep: \"TooMany\"")
    check("exits zero", result.returncode == 0, result.stdout)

    print("7. regression: a .py filename named in prose")
    result = case("prose mention",
                  prose="The bundled check_ticket.py counts every checkbox in the body.")
    check("exits zero", result.returncode == 0, result.stdout)

    print("8. a bundled script no command invokes")
    result = case("orphan", extra_scripts=("orphan.py",))
    check("exits one", result.returncode == 1, result.stdout)
    check("names the orphan", "scripts/orphan.py" in result.stdout, result.stdout)
    check("says why it matters", "dead weight" in result.stdout, result.stdout)
    check("does not flag the invoked script",
          "tool.py: bundled" not in result.stdout, result.stdout)

    print("9. an underscore-prefixed helper is exempt from the orphan rule")
    result = case("helper", extra_scripts=("_shared.py",))
    check("exits zero", result.returncode == 0, result.stdout)

    print("10. the four skills in this repo are clean")
    result = lint(ROOT)
    check("exits zero", result.returncode == 0, result.stdout)
    summaries = [line for line in result.stdout.splitlines() if line.startswith("ok  ")]
    check("one summary line per skill", len(summaries) == 4, result.stdout)

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("PASS — lint_skills.py meets every criterion in ML-001 and ML-002")
    return 0


if __name__ == "__main__":
    sys.exit(main())
