---
name: spec-align
description: Take a rough idea from brainstorming to a written specification both the user and you actually agree on, rather than one you each read differently. Use at the start of any new feature, project or piece of work; when the user describes something they want built and no spec exists; when requirements are vague, contested or half-decided; when you are about to start planning or implementing from a conversation alone; and when the user asks to brainstorm, scope, align on, or spec out an idea.
---

# Reaching a spec both sides actually agree on

Agreement is the cheapest thing to fake and the most expensive thing to get wrong. A
misread spec is copied into every ticket, test and line of code beneath it, and is usually
discovered only once the work is finished and wrong.

The default failure is not disagreement. It is a conversation where both sides believe they
agree because neither said anything specific enough to conflict.

**Your own default behaviour causes this.** Restating the user's idea in more confident
vocabulary reads to them as understanding, and commits you to nothing. Everything below
exists to force statements specific enough to be wrong.

---

## 1. Diverge before you converge

The user arrives with one shape in mind. Before narrowing, put at least three genuinely
different shapes on the table, and include the boring one — do nothing, do it by hand, use
something that already exists.

They must be options you would actually defend. A straw man you raise in order to dismiss it
is worse than not diverging at all: it produces the *feeling* that alternatives were
considered, which is the thing that stops anyone looking again.

Do not write anything down yet. Writing narrows, and the moment prose exists you will both
start defending it.

## 2. State what you would build, not what you heard

Do not paraphrase. Paraphrase is where false agreement lives — it reuses the user's own
words, so of course they recognise it.

Instead describe the thing concretely enough to be contradicted: the interface, the inputs,
what happens when it fails, where the data lives, what the user sees. Name specifics the
user never gave you, so that the wrong ones can be corrected.

**If the user could not possibly disagree with your restatement, it said nothing.** This is
the same falsifiability test `write-ticket` applies to acceptance criteria, one stage
earlier and applied to your own understanding.

## 3. Write down the decisions the user never made

The user thought about the part they cared about. Everything else you are about to decide
silently, on your own, and they will not find out until they see it.

List those explicitly: *"unless you say otherwise, I will assume X."*

The assumption list is the real product of this phase. Prose gets skimmed; a numbered list
of assumptions gets read, because each line is visibly a thing that could be wrong. Anything
you would otherwise resolve quietly belongs on it.

## 4. Adversarial pass — argue against building it

Now attack the decision itself, not the wording:

- What is the cheapest thing that gets most of the value? If it is much cheaper, say so.
- What does this make hard to change later? What would make us regret it in three months?
- Who else has to change something for this to work?
- What happens if it is used ten times more than expected — or twice, and then abandoned?

Make the strongest version of the case against, even when the user has already decided. If
it survives, the spec is stronger for it. If it does not, you have saved the entire pipeline
below. Then defer: if the user hears the objection and reaffirms, that is their call — record
it as a Decision with the rationale and move on.

If a dedicated interrogation or grilling skill is available in this session, this is the step
to use it in.

**This is the first of three adversarial passes in this workflow, and they attack different
things**: here the *decision*, in `write-ticket` the *contract*, in `ticket-done` the *work*.
Running one at the wrong altitude is a common waste — arguing about whether a feature should
exist during code review is far too late to be useful.

## 5. Converge — write the spec

One file, at `docs/specs/<slug>.md`:

```markdown
---
name: context-budget
status: draft
date: 2026-09-08
---

# Context budget estimator

## Problem
What currently goes wrong, in terms someone outside the conversation would recognise.

## Goals
What must be true when this is finished. Prose, not checkboxes.

## Non-goals
What this deliberately does not do, especially the things a reader would otherwise
assume it covers.

## Decisions
- **Estimate from character count, not a tokeniser** — a tokeniser dependency costs more
  than the accuracy is worth here; revisit if estimates drift over 15%.

## Assumptions
- Only Anthropic models need supporting for now.

## Open questions
- Should the budget include the system prompt?
```

Three rules about that file:

**Decisions carry their rationale and the rejected alternative.** A decision recorded alone
gets re-litigated in six months by someone who cannot see why the obvious option was not
taken. The rationale is the part with a shelf life.

**Non-goals are not optional.** They are the only thing that keeps scope from growing during
implementation, and the section people skip.

**Goals stay prose.** Turning them into testable criteria is `write-ticket`'s job. Doing it
here as well produces two definitions of done that drift apart.

## 6. Gate — check, then get real agreement

Run the checker bundled with this skill. It lives *next to this SKILL.md file*, not in the
repo's own `scripts/` directory:

```
python3 .claude/skills/spec-align/scripts/check_spec.py docs/specs/context-budget.md
```

It verifies the sections exist and are filled in, and — the check that matters — refuses
`status: agreed` while open questions remain.

Then ask for agreement in a form that can fail. "Does this look right?" invites yes. Instead:

- ask the user to react to the **assumption list**, line by line
- ask whether anything in **Non-goals** is something they expected to see in Goals

Set `status: agreed` only once they have actually answered. `new_ticket.py` refuses to create
tickets against a spec that is not agreed, so this gate is enforced rather than advisory.

---

## What not to do

**Never close an open question by picking the more convenient answer.** An open question
resolved silently is the same bug as an ambiguous acceptance criterion, one stage earlier and
harder to see.

**Never write the spec during brainstorming.** Diverge in conversation, converge on the page.

**Never let the spec describe implementation.** If the *how* really is constrained, that is a
Decision with a rationale, not a design section.

**Never mark a spec agreed on silence.** No response is not agreement, and it is the cheapest
of all these failures to avoid.
