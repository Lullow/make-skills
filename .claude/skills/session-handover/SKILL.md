---
name: session-handover
description: Write a handoff that lets the next session continue without redoing this one's reasoning, and index the transcript so it stays searchable. Use when context is running low or compaction is approaching, when wrapping up a work session, when switching between tickets or projects, before starting a long-running task, and whenever the user asks for a handoff, handover, summary of the session, or a note for next time.
---

# Handing over

A handoff is not a summary of what happened. It is the smallest set of facts that lets the
next reader — another agent, or you after compaction — carry on without reconstructing your
reasoning.

Written as a narrative of the session it is nearly worthless: nobody needs the order you
discovered things in. Written as *what the next reader needs before they can act*, it saves
the next session an hour.

---

## 1. File everything that has a permanent home first

The handoff is written **last**, and holds only the residue — the facts with nowhere else to
live.

| The fact | Where it belongs |
|---|---|
| Why one approach was chosen over another | `## Decisions` in the spec |
| What "done" means for this work | acceptance criteria in the ticket |
| What changed, and why | the commit message |
| A durable fact about this repo or its environment | `CLAUDE.md` |
| An approach that was tried and failed | **the handoff — it has no other home** |
| Where the work stands right now | **the handoff** |

**Point, never copy.** A handoff that restates the spec's decisions will drift from the spec,
and the next reader has no way to tell which of the two is current. Link to the file and stop.

Ask of every line: *would this still be true and useful in a month?* If yes it belongs in the
repo — put it there **before** writing the handoff, and record where you filed it. If it is
only true right now, the handoff is its home.

## 2. Write the next step so it can be started, not interpreted

One action, concrete enough to begin without asking a question first.

"Continue with the API work" is a note to yourself. "Add the 429 retry path to `client.post`,
criterion 3 in PA-004" is a handoff.

If the real next step is a question for the user, say so, and say what it blocks.

## 3. Record what failed

The highest-value section, and the one always dropped.

Without it the next agent spends an hour rediscovering the approach you already ruled out —
and worse, may stop at the point where it still looks like it works and build on it.

For each: what was tried, what happened, and **why you stopped**. The last part is what makes
it reusable. "Didn't work" alone leaves the reader unable to tell whether they would hit the
same wall or a different one.

## 4. Record what surprised you about the environment

Version quirks, a command that is not what it appears to be, a test that only fails in CI.

If it is durable, put it in `CLAUDE.md` and point at it from here. If it was a one-off, the
handoff is enough.

## 5. Build the session index as a searchable tree

The transcript still exists and holds far more detail than any handoff will. The index's job
is not to replace it but to make it **findable**.

**Every leaf must carry a literal string that appears in the transcript** — a filename, a
function name, an error message, a command that was run. A node reading "discussed the design"
is unsearchable, and therefore worth nothing to the agent trying to reconstruct why something
was done.

```
## Session index

- Spec alignment on context budgeting
  - rejected a tokeniser dependency — grep: "tokeniser dependency is not worth"
  - wrote `docs/specs/context-budget.md`
- PA-001 implementation
  - `estimate_tokens` added in `src/budget.py`
  - failed: per-model caching — grep: "TooManyConnections"
```

Two levels is usually enough. Depth is not the point; the literal strings are.

## 6. Generate the file

Run the script bundled with this skill. It lives *next to this SKILL.md file*, not in the
repo's own `scripts/` directory:

```
python3 .claude/skills/session-handover/scripts/new_handoff.py --title "Ticket workflow skills"
```

It fills in the parts you would misremember: branch, ahead/behind, uncommitted and untracked
files, which commits are yours, every ticket's status, and which specs are still drafts and
therefore blocking ticket creation. Those are facts a model reconstructs from memory with
quiet errors, and a quiet error in a handoff is worse than an omission — the next agent has
no reason to doubt it.

By default it writes to `/tmp/handoff-<repo>-<timestamp>.md`, where a session-start skill will
find it. That location is deliberate: the handoff is scaffolding for the next session, not a
project document. Anything that deserves to outlive it should already have been filed under
step 1.

Then replace every `<...>` placeholder. **A handoff with placeholders left in it is a handoff
that was not written.**

## 7. Be honest about the state

Say plainly what is broken, unfinished or untested.

A handoff claiming things work while the suite is red is worse than no handoff at all: the
next agent builds on it and the time is lost twice. If you did not run the tests, write that
you did not run them. Never write "tests pass" from memory — the same rule `ticket-done`
applies, for the same reason.

---

## What not to do

**Never write the handoff as a chronology.** State, next step, traps. Not a story.

**Never copy what the repo already holds.** A pointer stays correct; a copy goes stale
silently.

**Never write it only once, at the end.** Write it while you still hold the detail — before a
long task, before switching tickets, when context starts running low. A handoff written from
an already-compacted session is a summary of a summary.

**Never leave the next step implicit** because "it's obvious". It is obvious only while you
still have the context that is about to be discarded.
