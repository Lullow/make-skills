---
id: ML-002
title: Flag bundled scripts no command invokes
status: done
spec: docs/specs/skill-lint.md
---

# ML-002 — Flag bundled scripts no command invokes

Spec: [docs/specs/skill-lint.md](docs/specs/skill-lint.md)

## Acceptance criteria

- [x] Exits 1 and names the path when a skill bundles a scripts/*.py that no fenced command in its own SKILL.md invokes
- [x] A script named by its full repo-root path in a fenced command counts as invoked
- [x] A bundled script whose filename starts with an underscore is exempt, as a helper meant to be imported rather than run
- [x] Exits 0 against the four skills currently in .claude/skills/, which each invoke their bundled script

## Constraints

- Standard library only, like the other scripts in this repo

## Notes

