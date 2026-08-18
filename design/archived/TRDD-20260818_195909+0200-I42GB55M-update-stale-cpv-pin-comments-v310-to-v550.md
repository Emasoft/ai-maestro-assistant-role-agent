---
trdd-id: I42GB55M
title: Update the two workflow comments still claiming the CPV pin is v3.1.0
column: completed
created: 2026-08-18T19:59:09+0200
updated: 2026-08-18T20:05:50+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
approval-tier: 0
severity: low
blocked-by: []
external-refs: [reports/plugin-self-audit/20260816_171109+0200-axis4-bugs.md C3, reports/plugin-self-audit/20260816_190000+0200-axis2-governance.md C1]
implementation-commits: [dba029c]
---

# Update the two workflow comments still claiming the CPV pin is v3.1.0

Phase-1 audit axis-4 C3 ≡ axis-2 C1 (same defect, found from two axes). Verified first-hand:
`.github/workflows/ci.yml:170` and `.github/workflows/release.yml:57` carry comments saying
"CPV is PINNED to `@v3.1.0`" while the `uvx --from` lines below (ci.yml:196, release.yml:85) pin
`@v5.5.0` — the TRDD-NRQK4W2P bump touched the code lines, not the prose. State the invariant
without hardcoding the version number, so the comment cannot rot again on the next bump.

## Acceptance criteria

- [x] `grep -rn "v3.1.0" .github/workflows/` returns nothing.
- [x] Comments no longer embed a version literal that the code line already carries.

## Approval log

- 2026-08-18T19:59:09+0200 — Tier-0 self-mandate (comment/doc drift fix); PHASE-2 GO.
- 2026-08-18T20:05:50+0200 — COMPLETED by ai-maestro-assistant-role-agent. Fixed, verified (112 tests pass, ruff+mypy clean), landed on main.
