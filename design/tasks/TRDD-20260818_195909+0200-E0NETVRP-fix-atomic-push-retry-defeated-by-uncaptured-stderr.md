---
trdd-id: E0NETVRP
title: Restore retry on the atomic push — capture_output=False starves the transient classifier
column: todo
created: 2026-08-18T19:59:09+0200
updated: 2026-08-18T19:59:09+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: bugfix
scope: project
project-id: ai-maestro-assistant-role-agent
approval-tier: 0
severity: high
blocked-by: []
external-refs: [reports/plugin-self-audit/20260816_171109+0200-axis4-bugs.md C1]
implementation-commits: []
---

# Restore retry on the atomic push — capture_output=False starves the transient classifier

Phase-1 audit axis-4 C1, hub-ledgered, PHASE-2 GO 2026-08-18. Verified first-hand this session.

`scripts/publish.py:1947-1951` calls `git_with_retry([... "push", "--atomic" ...],
capture_output=False)`. With `capture_output=False`, `subprocess.run` leaves `result.stderr`
as `None`; `run_with_retry` computes `stderr = result.stderr or ""` and
`is_transient_subprocess_error` returns `False` unconditionally on empty stderr
(`cpv_network_resilience.py:116-117`) — so every non-zero exit is classified permanent and the
documented 60-attempt/240s retry budget is silently reduced to 1 attempt on the single most
consequential network call of the pipeline (the push that makes a release public), after the
commit and tag already exist locally.

## Fix

- Drop `capture_output=False` (default is `True`) so the classifier sees real stderr and
  `check=True` raises `CalledProcessError` on permanent/exhausted failure.
- On that exception, echo `e.stderr` to stderr and re-raise (fail-fast, diagnosis preserved —
  with capture on, git's own error text would otherwise be swallowed into the exception object).
- Regression test: assert `scripts/publish.py` passes no `capture_output=False` to
  `git_with_retry`/`gh_with_retry` (file-content guard, matching the repo's pipeline-file test
  style), since `tests/test_cpv_network_resilience.py` has zero coverage of that path.

## Acceptance criteria

- [ ] `capture_output=False` no longer reaches `git_with_retry`/`gh_with_retry` anywhere in
      `scripts/publish.py`.
- [ ] Final-failure path still surfaces git's stderr to the terminal.
- [ ] Regression test added and passing; full suite green.

## Approval log

- 2026-08-18T19:59:09+0200 — Tier-0 self-mandate (in-scope bugfix); PHASE-2 GO relayed by hub
  under the USER's delegation, USER re-granted in-session ("granted. follow the ai-maestro
  instructions").
