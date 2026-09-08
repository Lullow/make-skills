---
id: ML-001
title: Lint skills for path and interpreter defects
status: done
spec: docs/specs/skill-lint.md
---

# ML-001 — Lint skills for path and interpreter defects

Spec: [docs/specs/skill-lint.md](docs/specs/skill-lint.md)

## Acceptance criteria

- [x] Exits 1 and names the skill and path when a SKILL.md references a bundled script path that does not resolve from the repo root
- [x] Exits 1 and names the skill when frontmatter name differs from the skill's directory name
- [x] Exits 1 and names the line when a SKILL.md invokes a bare 'python ' rather than 'python3 '
- [x] Exits 1 and names the skill when the description frontmatter contains no sentence beginning with 'Use'
- [x] Exits 0 with one summary line per skill against the four skills currently in .claude/skills/

## Constraints

- Standard library only, like the other scripts in this repo

## Notes

