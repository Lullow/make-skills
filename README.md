# make-skills

A small, cherry-picked set of Claude Code skills for a good project workflow.

## Pipeline

| Skill | Role |
|---|---|
| `spec-align` | brainstorm -> human/machine alignment -> spec |
| `write-ticket` | break a spec into tickets with testable criteria |
| `ticket-done` | verification procedure before declaring a ticket done |
| `session-handover` *(todo)* | structured tree summary + next step at compaction |

## Tests

```
python3 tests/test_roundtrip.py
```

Proves the three skills still agree on both file formats: a spec is checked, a ticket
is generated from it, checked while unfinished, finished, and checked again.
