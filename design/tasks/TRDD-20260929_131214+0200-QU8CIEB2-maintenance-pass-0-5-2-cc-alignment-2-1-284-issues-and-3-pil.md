---
trdd-id: QU8CIEB2
title: Maintenance pass 0.5.2 - CC alignment 2.1.284 issues and 3-pillars adoption
column: todo
status: tasked
created: 2026-09-29T13:12:14+0200
updated: 2026-09-29T13:31:59+0200
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
GOVERNANCE SYNC (polled governance-rules head 2026-09-29, replacing the unreachable ai-maestro-d7 peer per issue #1's poll-dont-wait doctrine): spec 2.6.1 / GOVERNANCE-RULES 5.5.1 / 3-pillars 4.0.0 (was 3.0.0 at last check - but the persona-relevant rules did not change shape). Findings: (1) R42.9 (NEW 2026-08-20, corrected same day) - in HARNESS workdirs the server enforces crossSessionInbound refuse via the amp-only-messaging invariant; permissions.deny SendMessage is now FORBIDDEN (breaks own-subagent handling). The persona's crossSessionInbound line (line 391) stays TRUE - it describes the general control and its owner, not the harness value; a harness ASSISTANT has inbound refuse imposed server-side, which only tightens what the persona already requires. No conflict. (2) R42.9 carve-out: own sub-agents untouched - matches persona's subagent section. (3) R39.2 now says this plugin is PUBLISHED (corrected 5.3.2) and REMAINS absent from PREDEFINED_ROLE_PLUGIN_NAMES as open question #86 F2 - consistent with our memory note. (4) 3-pillars spec 4.0.0 is a teaching-prose reform (3P-VER-01 semver; the 22-column vocabulary unchanged) - no persona impact. VERDICT: persona needs no further edit beyond the 2.1.284 alignment already committed.
