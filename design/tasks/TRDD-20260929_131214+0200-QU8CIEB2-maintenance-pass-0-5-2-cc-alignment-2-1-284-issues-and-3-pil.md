---
trdd-id: QU8CIEB2
title: Maintenance pass 0.5.2 - CC alignment 2.1.284 issues and 3-pillars adoption
column: todo
status: tasked
created: 2026-09-29T13:12:14+0200
updated: 2026-09-29T13:19:38+0200
current-owner: user
created-by: user
task-type: docs
min-approval-requirement: none
scope: project
project-id: ai-maestro-assistant-role-agent
assignee: user
mandate: true
mandated-by: none
approved: true
approval-judge: user
approval-datetime: 2026-09-29T13:12:14+0200
---

# Maintenance pass 0.5.2 - CC alignment 2.1.284 issues and 3-pillars adoption

Goal-driven maintenance pass (user directive 2026-09-29): (1) solve GitHub issues #1 #2; (2) align persona to Claude Code 2.1.249-2.1.284; (3) adopt 3-pillars tool references (trddgrep/prrdgrep/specgrep/memgrep) per governance-trdd-kanban rule; (4) CPV-verify publish pipeline; (5) test+docs+publish. Facts verified in-session: board was empty (20 TRDDs all terminal), persona last aligned to 2.1.241-2.1.248 (TRDD-8GZ3TZD0), kanban CLI absent (board IS trddgrep), changelog captured to /tmp/cc-changelog.md (Update-tag format). R22/R23 canonical blocks are sha-pinned vendored canon - byte-identical or publish gate fails (consent recorded 2026-08-29).

## Approval log

- 2026-09-29T13:12:14+0200 — MANDATE issued by user (min-approval-requirement: none). Pre-approved: issuer authority >= required approver. No approval request was sent.

## Advisor verdict

ADVISOR VERDICT (Fable, 2026-09-29): make exactly ONE persona edit - A(ii) delivery-is-not-read sentence in the Messaging section (2.1.271 queue-notice is a SUCCESS result the failure-framing does not cover), with auto-mode-default as one clause riding along; B nowhere; C (R22/R23 canonical blocks) untouched; for 3-pillars adoption: keep the persona tool-AGNOSTIC (governance-trdd-kanban is a user-scope rule loading exactly where trddgrep is installed; restating it in a vendored fleet file recreates the R22 duplication defect the persona itself retired), and the team-kanban skill pointer was VERIFIED live and current (ai-maestro-plugin 3.2.5 routes to the TRDD-as-board model). Task 3 resolves as: no persona edit for tool naming; decision recorded here.
ADVERSARIAL-REVIEW (fork, 2026-09-29) - accepted findings: (1) the persona edit must ADD 1-2 new _CURRENT_REACH rows (2.1.271 delivery-not-read, 2.1.284 auto-default) or the pinning stops advancing - the suite would stay green while the persona drifts; (2) fence .git/hooks off from cpv-agent edits (pre-push hook is the only-push-via-publish.py invariant) - instructed cpv-agent accordingly; (3) cpv-agent must never commit; (4) the 23-Update-label count vs 22 enumerated is arithmetic on my side - the range 2.1.276-2.1.248 contains 22 version labels among 23 lines because one label can share a line region; claim re-phrased as all-existing-entries. Rejected: none - all four findings accepted or adopted.
