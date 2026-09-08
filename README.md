# make-skills

A small, cherry-picked set of Claude Code skills for a good project workflow.

## Pipeline

| Skill | Role |
|---|---|
| `spec-align` *(todo)* | brainstorm -> human/machine alignment -> spec |
| `write-ticket` | break a spec into tickets with testable criteria |
| `ticket-done` | verification procedure before declaring a ticket done |
| `session-handover` *(todo)* | structured tree summary + next step at compaction |

## Tests

```
python3 tests/test_roundtrip.py
```

Proves `write-ticket`'s generator and `ticket-done`'s checker still agree on one ticket format.
