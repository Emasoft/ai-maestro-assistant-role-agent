---
trdd-id: F8D1BH24
title: Remove the dead _infer_bump_type helper from publish.py
column: todo
created: 2026-08-18T19:59:09+0200
updated: 2026-08-18T19:59:09+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: refactor
scope: project
project-id: ai-maestro-assistant-role-agent
approval-tier: 0
severity: low
blocked-by: []
external-refs: [reports/plugin-self-audit/20260816_171109+0200-axis4-bugs.md REFUTED-_infer_bump_type]
implementation-commits: []
---

# Remove the dead _infer_bump_type helper from publish.py

Phase-1 audit established (refuting it as a wiring bug) that `_infer_bump_type`
(`scripts/publish.py:1578`) has no caller — introduced once in the canonical-pipeline adoption
commit, never wired: bump-type determination is fully served by `detect_bump_type()` /
`args.bump`. Dead code violates the standing NO-DEAD-CODE rule; delete it.

## Acceptance criteria

- [ ] `grep -n "_infer_bump_type" scripts/publish.py` returns nothing.
- [ ] Full suite green; `ruff check` and `mypy` clean on the file.

## Approval log

- 2026-08-18T19:59:09+0200 — Tier-0 self-mandate (dead-code hygiene); PHASE-2 GO.
