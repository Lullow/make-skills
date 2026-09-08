---
name: skill-lint
status: agreed
date: 2026-09-08
---

# Skill lint

## Problem
A skill's defects do not show up when you read it. They show up when an agent runs it, in a
session where nobody is watching closely.

Two have already happened in this repo. `ticket-done` shipped with prose telling the agent to
run `python scripts/check_ticket.py` — a path that resolves from the repo root, where nothing
of that name exists, because the bundled script sits next to the SKILL.md. It was found only
by running it. The corrected command then used `python`, which is absent on this machine, so
it failed a second time for a second reason.

Both are mechanical, both are invisible to a reader, and each cost a live session to find.

## Goals
One command that reads every skill under `.claude/skills/` and reports the defect classes that
have actually bitten us, naming the file and the offending line so the fix is obvious. It runs
in the same suite as the round-trip test, so a broken skill cannot be committed quietly.

## Non-goals
Does not judge whether a skill's instructions are any good — that is not mechanical. Does not
execute the bundled scripts. Does not lint skills outside this repo, and does not enforce a
house style for prose, headings or length.

## Decisions
- **A rule must be provably quiet; a defect that actually occurred is the strongest evidence
  of that, but not the only admissible kind.** This decision originally required every rule to
  come from a real defect. That was a proxy for what is actually wanted — silence on correct
  input, because noise trains people to stop reading the output — and the proxy excluded rules
  that are demonstrably quiet without a scar to point at. Amended 2026-09-08 while writing
  ML-002. The two path bugs remain the seed set; porting a generic markdown linter is still
  rejected, because it fails the quietness test rather than the provenance one.
- **A bundled script whose name begins with `_` is exempt from the orphan rule** — that is the
  Python convention for a module meant to be imported rather than run, and without the carve-out
  the rule would fire on the first shared helper anyone adds. Rejected the alternative of
  parsing imports to work it out, which is far more machinery than the risk deserves.
- **Report every failure in one pass rather than exiting on the first** — an author who can fix
  only one problem per run will stop running it.
- **Lint the prose, not the behaviour** — running a skill's scripts to see what they do is a
  different tool with different risks, and every defect we have actually hit was textual.

## Assumptions
- A skill is a directory under `.claude/skills/` containing a `SKILL.md`; one without is not a skill.
- Paths written in prose are relative to the repo root, because that is where an agent runs them.
- `python3` is this repo's interpreter; a bare `python` in prose is a defect, not a preference.
- Standard library only, matching the other scripts here.
