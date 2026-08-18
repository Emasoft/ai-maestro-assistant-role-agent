---
trdd-id: ULD03IAG
title: Fix two cprint calls printing a literal backslash-n instead of a newline
column: completed
created: 2026-08-18T19:59:09+0200
updated: 2026-08-18T20:05:50+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: bugfix
scope: project
project-id: ai-maestro-assistant-role-agent
approval-tier: 0
severity: low
blocked-by: []
external-refs: [reports/plugin-self-audit/20260816_171109+0200-axis4-bugs.md C2]
implementation-commits: [7b4e8ba]
---

# Fix two cprint calls printing a literal backslash-n instead of a newline

Phase-1 audit axis-4 C2. Verified first-hand: `scripts/publish.py:578` and `:641` use
`cprint(f"\\n{BOLD}...")` — a doubled backslash, i.e. the two characters `\` `n` — while every
sibling header uses the real escape `f"\n{BOLD}..."`. Cosmetic only: `--install-hook` and
`--install-branch-rules` print `\nInstalling ...` on one line.

## Acceptance criteria

- [x] Both calls use `\n`; `grep -n 'cprint(f"\\\\n' scripts/publish.py` returns nothing.
- [x] Full suite green.

## Approval log

- 2026-08-18T19:59:09+0200 — Tier-0 self-mandate (in-scope cosmetic bugfix); PHASE-2 GO.
- 2026-08-18T20:05:50+0200 — COMPLETED by ai-maestro-assistant-role-agent. Fixed, verified (112 tests pass, ruff+mypy clean), landed on main.
