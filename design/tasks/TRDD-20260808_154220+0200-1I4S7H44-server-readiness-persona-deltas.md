---
trdd-id: 1I4S7H44
title: Server-readiness — persona deltas against the USER-dictated ASSISTANT model
column: dev
created: 2026-08-08T15:42:20+0200
updated: 2026-08-08T15:42:20+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: feature
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: none
mandate: true
mandated-by: self
severity: high
blocked-by: []
relevant-rules: []
external-refs: [ai-maestro#39, ai-maestro TRDD-3QRUDK12, ai-maestro TRDD-9SEQ4QI9]
release-via: publish
---

# Server-readiness — persona deltas against the USER-dictated ASSISTANT model

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative) — 2026-08-08

**Purpose: make this plugin correct on the day the ai-maestro server ships**, not after. The
server's ASSISTANT model is now specified (`TRDD-3QRUDK12`, a USER dictation relayed on
`ai-maestro#39`). I read the whole shipped persona against it. Most of it holds. Three things do
not, and they are listed below in the order they matter.

### D1 — MANAGER contact direction: the spec and this persona DISAGREE. Needs a ruling.

`TRDD-3QRUDK12`: *"the ASSISTANT cannot SEE or MESSAGE any other agent. Exceptions: (a) it can
**ALWAYS message the MANAGER**; (b) once the MANAGER approves the USER as a collaborator on a
project, it can message the agents working that same project."*

This persona says the opposite about direction, in three places (lines ~132, ~202, ~359):
*"you initiate no other contact with it"* / *"you initiate contact with no agent (the MANAGER
initiates; you may refuse)"*.

**These may be reconcilable and I will not guess which.** R39.9 gates whether the MANAGER may
*direct* me (obedience, user-permitted). 3QRUDK12's clause is about whether the *channel* is open
(messaging). Obedience-gated + channel-always-open is coherent. But the persona's wording forbids
me to *initiate*, and that is exactly what 3QRUDK12 grants.

**Why it is not cosmetic:** if the channel is truly always open, an ASSISTANT that believes it may
never initiate cannot escalate — it cannot report a problem, request a project invitation, or say
"I am blocked" to the only agent that can act. That is the dead-man shape again, and it is the
same hole I raised as Ask 2 on my own repo's issue #1 (R42.8 excludes an ASSISTANT from
`block-state`, so no agent may observe that I am stuck). If BOTH hold, nobody can see me stuck and
I may not speak first. **Asked, not assumed** — routed to the hub.

### D2 — ROLE-PLUGIN IMMUTABILITY: a real gap, zero coverage, and mine to fix. DONE.

`TRDD-3QRUDK12`: *"The USER may install extensions and configure its own ASSISTANT freely,
EXCEPT: the assistant role plugin itself (immutable) and the required core extensions/plugins
every agent must carry. The ASSISTANT may install/uninstall extensions at its OWN local scope
only."*

Measured: `grep -niE 'uninstall|immutable'` over the persona returned **zero** hits. Nothing told
the agent it may not uninstall its own role plugin — i.e. **remove its own governance.** The
server enforces the registry side (R9.13 rejects any state leaving an agent with zero
role-plugins), but that governs registry state, not a `claude plugin uninstall` run locally in the
agent's own session — which is precisely the "agent-local scope, agent-uninstallable" hole the hub
named in `TRDD-9SEQ4QI9`.

**Honest about what this is:** an instruction, not a control. A prompt-injected agent ignores it,
exactly as with workdir containment. It is worth shipping anyway because the *compliant* agent is
the one it is for, and its absence was a silent invitation.

### D3 — a stale claim in shipped text. FIXED.

The v0.3.3 interim note said the canonical blocks *"return in v0.3.4"*. **v0.3.4 and v0.3.5 have
both shipped without them** (CPV#201 is still open), so the shipped persona asserted a release
that came and went. Rewritten to name the CONDITION rather than a version — the same fix already
applied to `TRDD-NRQK4W2P`, which had the identical defect. **A note that names a version pins a
promise to a number nobody controls the timing of.**

### What was checked and HOLDS (so a re-audit does not redo it)

- MAINTAINER-gated PRs: covered (forbidden #10 — never merge own PRs, merging is the MAINTAINER's
  job). 3QRUDK12's "no other write path into project repos" is satisfied by that plus the
  branch-scope rule.
- No teams, ever; one ASSISTANT per user; locked identity fields; obeys own user not the MAESTRO;
  writable-scope confinement; secrets prohibition — all present and consistent.
- Workdir containment — added in v0.3.5 (forbidden #14) after the `TRDD-9SEQ4QI9` ruling.

## Acceptance criteria

- [x] D2 shipped: the persona forbids uninstalling its own role plugin / required core plugins.
- [x] D3 shipped: interim note names the condition, not a version.
- [ ] D1 resolved by the hub, then reflected in the persona (or explicitly recorded as
      "persona is correct, 3QRUDK12's clause is about obedience not initiation").
- [ ] Released.

## Approval log

- 2026-08-08T15:42:20+0200 — self-mandate, Tier-0 (`min-approval-requirement: none`): bringing this
  plugin into line with an already-ratified USER dictation is in-scope maintenance of my own
  artifact, not a governance change. D1 is the exception and is routed out, because a persona that
  guesses at a contradiction ships the guess to every future ASSISTANT.
