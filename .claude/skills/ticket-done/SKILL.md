---
name: ticket-done
description: Verification procedure to run before declaring work finished. Use this whenever you are about to tell the user that a ticket, task, issue, feature or bugfix is "done", "complete", "finished", "working", or "ready for review", or when you are about to open a pull request — even if the user never asked you to verify anything. Also use when the user asks whether something is ready to merge, ship, or hand off.
---

# Definition of done

Work is not done because the code runs. It is done when the next person can trust it
without reading the diff.

**The steps are ordered and they loop.** If any step fails, fix the cause and restart
from step 1. This matters more than it looks: a fix made in step 5 can silently
invalidate the test run from step 3, so a checklist walked once gives a false green.
Restarting is cheap; a ticket marked done that isn't is expensive for whoever picks it
up next.

**Steps 2 and 5 are deliberately opposite modes.** Step 2 asks "does this meet the
criteria?" and looks for confirmation. Step 5 asks "where is this wrong?" and looks for
faults. Run them as separate passes. Doing both at once reliably finds only the
confirmation — you cannot look for evidence that you succeeded and evidence that you
failed with the same read.

---

## 1. Read the ticket

Locate the ticket file under `docs/tickets/`. It is named `<ID>-<slug>.md` and its
frontmatter holds `id`, `status` and a path to the originating `spec`.

If no ticket exists for this work, stop and say so. Do not invent one retroactively to
have something to check against — the point of the criteria is that they were written
before the code, so writing them now just describes what you happened to build.

If an acceptance criterion is ambiguous, stop and ask the user. Ambiguity is a
ticket-writing bug, not something to resolve with a generous interpretation in your own
favour.

## 2. Confirmational pass — map criteria to code

For every acceptance criterion, name the file and function that satisfies it, and the
test that covers it. Write this out; do not do it in your head.

A criterion you cannot point at is not met. "Handled implicitly by the existing
validation" is not a pointer.

## 3. Run the full test suite

Run the project's whole suite, not only the tests you touched. Regressions are the
entire reason the suite exists.

Determine the command from the project rather than guessing:

| Signal | Command |
|---|---|
| `pyproject.toml` / `pytest.ini` / `tests/` | `pytest` |
| `package.json` with a `test` script | `npm test` |
| `Makefile` with a `test` target | `make test` |

If you cannot determine the command, ask. Reporting "tests pass" without having run
them is the worst possible failure of this procedure — it destroys the trust that makes
every later step worth doing.

Report the actual numbers (`87 passed, 0 failed`), never the word "passing" alone.

## 4. Prove the new tests bite

A new test that passes against the *old* code tests nothing. Verify: stash or revert
your change, run the new tests, confirm they fail, restore.

For a bugfix this is non-negotiable — a regression test that never reproduced the bug
is decorative.

## 5. Adversarial pass — read your own diff as a reviewer

Run `git diff` and read it as if you were reviewing a stranger's pull request and were
expected to find at least one problem. Look specifically at:

- **Error paths.** What happens on empty input, `None`/`null`, a missing file, a failed
  network call?
- **Boundaries.** Zero, one, the maximum, one past the maximum.
- **Anything written late.** The last thing you wrote is the least examined thing you
  wrote.
- **What you left out.** Deleted code, skipped tests, `TODO`, commented-out blocks.

Say what you found. "Nothing" is a legitimate result only if you can name what you
looked for.

## 6. Commit

One commit per logical change. The message starts with the ticket ID:

```
PA-001 add token budget estimator for context window
```

The ID prefix is what makes `git log --grep=PA-001` work as traceability later, which
is what the handover and review steps rely on. A commit without it is invisible to
every tool downstream.

## 7. Mechanical check and ticket update

Run the checker bundled with this skill. It lives in `scripts/check_ticket.py`
*next to this SKILL.md file*, not in the repo's own `scripts/` directory — so use the
skill's path, and run it with the repo root as the working directory:

```
python3 .claude/skills/ticket-done/scripts/check_ticket.py PA-001
```

It verifies what a script can verify better than you can: that all criteria checkboxes
are ticked, that the frontmatter is well formed, that at least one commit references the
ID, and that the working tree is clean. Fix anything it reports and re-run.

Then tick the criteria checkboxes and set `status: done` in the ticket frontmatter.

## 8. Report, and stop

Use this exact structure:

```
## PA-001 — <ticket title>
Criteria:      4/4 verified
Tests:         87 passed, 0 failed (pytest)
Tests bite:    yes — new tests fail on pre-change code
Adversarial:   1 issue found and fixed (empty-string path in estimate_tokens)
Commit:        a3f21c9
Check script:  pass
Status:        done

Deferred:      <work not included, with its new ticket ID — or "none">
Next:          ready to push and open a PR
```

**Stop there.** Do not push, open a pull request, or comment on an external tracker
without being asked. Those are the irreversible, other-people-can-see-it actions, and
the user decides when they happen. Everything up to this point is local and undoable.

---

## What not to do

**Never mark a ticket done because the remainder is "trivial".** Remaining work becomes
a new ticket with its own criteria. That rule is the only thing keeping the board honest
— the moment "done" means "mostly done", nobody can read the board without asking you.

**Never widen the criteria to match what you built.** If the implementation diverged
from the ticket, that is information the user needs, and it belongs in the report. Edit
criteria only when the user has agreed to the change.

**Never skip step 3 because the change is small.** Small changes are exactly the ones
shipped without a test run, which is why they are overrepresented in regressions.
