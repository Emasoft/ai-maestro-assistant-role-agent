---
trdd-id: HSJ1D0A6
title: retroactive record — persona alignment with Claude Code 2.1.233 to 2.1.240
column: complete
created: 2026-08-25T13:58:21+0200
updated: 2026-08-25T13:58:21+0200
current-owner: main-claude
task-type: docs
release-via: none
approved: true
implementation-commits: [8516cc2, f13bb59, 7e0321b]
---

# retroactive record — persona alignment with Claude Code 2.1.233 to 2.1.240

Retroactive TRDD, filed at `column: complete` after the work shipped. It exists so the
board carries a card for work that was performed without one (2026-08-23 session); it is
a record, not a plan, and says so.

## What was done (all verified green before commit)

- `8516cc2` — pinned `testpaths` in `pyproject.toml`: a bare `pytest` collected ZERO
  tests because rootdir collection walked into a superseded snapshot under
  `docs_dev/pending-20260814_143612+0200-cc-changelog-alignment/tests/` and aborted on
  "import file mismatch". Nothing deleted (RULE 0); the stale `__pycache__` is still on
  disk, and collection survives it ONLY because of this pin.
- `f13bb59` — persona aligned with CC 2.1.233–2.1.240: the unpoliced channel became
  FALLIBLE (delivery verdicts, never comm-graph ones); `notify_when_idle` zero-message
  subscription carved out of FORBIDDEN #5; roster converse (an absent row is not an
  absent session). Each fact pinned in `_CURRENT_REACH` in
  `tests/test_transport_claims.py`.
- `7e0321b` — README gap closed (it carried only 2 of the 3 facts), one brittle pin
  loosened, `unaddressable` reworded out (the only NEW cspell unknown).

Verified first-hand at the time: 112 passed, ruff, ruff-format, mypy, markdownlint,
zero new cspell unknowns, and all three new pins proven to bite against the pre-edit
persona. The persona ended roughly 20 words under its 5000-word ceiling — any future
addition must be paid for by a deletion.

## Approval log

- 2026-08-25T13:58:21+0200 — Filed retroactively at `complete` and archived in the same
  commit, under the USER delegation of 2026-08-25 ("complete all pending tasks and
  TRDDs … decide yourself … verify first"). The alternative — pretending the card
  predated the work — was rejected on 2026-08-23 when the retro-filing was first offered.

## Notes and lessons learned
