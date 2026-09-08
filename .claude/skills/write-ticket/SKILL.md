---
name: write-ticket
description: Turn an agreed specification into tickets whose acceptance criteria can be verified by someone who did not write the code. Use whenever you are about to create, draft, split or rewrite a ticket, issue, task or work item; when a spec has just been agreed and needs breaking into work; when the user asks what to build first, or to plan, scope or break down work; and before starting implementation on anything that has no ticket yet.
---

# Writing a ticket

A ticket is a promise made before the work starts. Its acceptance criteria are the only
thing stopping the implementer from grading their own exam later — which is why they are
worth more care than the ticket's prose, and why criteria written after the code are
worthless.

**The output of this skill is a file the `ticket-done` checker will accept.** Placement
and format are handled by the bundled script. What the criteria actually say is your job
and cannot be automated.

---

## 1. Find the spec

Every ticket points at an agreed spec under `docs/specs/`. Its path goes in `spec:`.

If there is no spec, stop. A ticket without one is either work nobody agreed to, or a
decision made in conversation and never written down. Both are worth interrupting for:
write the spec first, or have the user confirm that the ticket itself is the whole of the
agreement.

## 2. Decide the split

One ticket is one reviewable diff.

- If you cannot state the criteria in five bullets or fewer, it is two tickets.
- If the title needs an "and", it is two tickets.
- If half the work could ship on its own and be useful, it should.

Splitting is cheap now and expensive later. A ticket that outgrows one diff cannot be
reviewed properly, cannot be reverted cleanly, and cannot be honestly marked done in
parts.

## 3. Write the criteria

A criterion is testable when you can name the observation that would prove it **false**.
If no observation would, it is a wish, not a criterion.

| Wish | Why it fails | Criterion |
|---|---|---|
| Error handling is robust | Nothing could disprove it | `load(path)` raises `ConfigError` naming the path when the file is absent |
| Fast enough | No threshold, no measurement | p95 under 200 ms for a 10k-row export |
| Uses a connection pool | Names the implementation, not the behaviour | 100 concurrent requests complete without `TooManyConnections` |
| Works on mobile | No width, no definition of "works" | No horizontal scroll at 375 px viewport width |

Write criteria as observable behaviour, not as instructions to the implementer. The
implementer's judgement about *how* is the thing you are paying for; criteria fence the
outcome, not the route.

**When the implementation genuinely is the requirement** — a compliance rule, a mandated
library or interface — write it under `## Constraints` instead. Keep constraints as plain
bullets, never checkboxes: `check_ticket.py` counts every checkbox in the body as an
acceptance criterion, so a constraint written as one silently becomes something the ticket
claims to have verified.

## 4. Adversarial pass — satisfy your own criteria in bad faith

Re-read the list as an implementer who wants to tick every box with the least possible
work. Ask: **what is the laziest change that satisfies all of these literally, and would
it survive review?**

This reliably finds:

- criteria that describe only the happy path — the lazy implementation hardcodes it
- "returns a list of X" — satisfied by returning an empty list
- criteria that name no test — satisfied by untested code
- criteria about a function that never say anything calls it

If the lazy implementation would be rejected, a criterion is missing or too loose. Fix the
list, not the review.

This is the same move `ticket-done` makes in its adversarial pass, applied at the other end
of the pipeline: there you read the diff looking for faults, here you read the criteria
looking for loopholes.

## 5. Resolve ambiguity now

Anything you would have to interpret generously later, ask about now. `ticket-done` treats
an ambiguous criterion as a ticket-writing bug and stops. This step is where that bug is
prevented, and it is far cheaper here than after the code exists.

## 6. Scaffold the file

Run the script bundled with this skill. It lives *next to this SKILL.md file*, not in the
repo's own `scripts/` directory — so use the skill's path, and run it with the repo root
as the working directory:

```
python3 .claude/skills/write-ticket/scripts/new_ticket.py \
  --spec docs/specs/context-budget.md \
  --title "Add token budget estimator" \
  --criterion "estimate_tokens('') returns 0 rather than raising" \
  --criterion "budget_for(model) returns the documented window for every model in MODELS"
```

It allocates the next ID in sequence, slugs the filename, and writes frontmatter in the
shape the checker parses. It refuses to create anything `check_ticket.py` would reject, so
a ticket that exists is a ticket that validates.

Do not hand-write ticket files. ID allocation and filename shape are exactly the details a
model gets subtly wrong — `PA-7` one day, `PA-007` the next — and every downstream
`git log --grep=PA-001` depends on them being uniform.

## 7. Confirm before starting work

Show the user the criteria and get agreement before writing any code. The ticket is where
human and machine commit to the same definition of done. If that agreement happens after
the implementation, it is not agreement, it is ratification.

---

## What not to do

**Never write criteria for code that already exists.** They will describe what you built
rather than what was wanted, and every one will pass. If work happened without a ticket,
say so plainly instead of backfilling one.

**Never put the solution in the ticket.** If the approach really is fixed, it belongs in
the spec, where it can be argued about.

**Never bundle "and while we're in there".** Adjacent work gets its own ticket. A ticket
that grows during implementation is a ticket whose criteria no longer bound anything.

**Never estimate time in a ticket.** It is not verifiable, nothing downstream reads it, and
it quietly hardens into a commitment.
