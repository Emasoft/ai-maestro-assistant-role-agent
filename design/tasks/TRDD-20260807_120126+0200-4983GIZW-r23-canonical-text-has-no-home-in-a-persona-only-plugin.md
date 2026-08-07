---
trdd-id: 4983GIZW
title: R23 canonical prohibition has no decision-time surface in a persona-only plugin
column: blocked
pre-block-column: todo
created: 2026-08-07T12:01:26+0200
updated: 2026-08-07T12:01:26+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: manager
blocked-by: [ai-maestro#127]
external-refs: [ai-maestro#107, ai-maestro#127, ai-maestro-assistant-role-agent#1]
relevant-rules: []
release-via: publish
---

# R23 canonical prohibition has no decision-time surface in a persona-only plugin

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-07

- **Measured, first-hand, 2026-08-06:** `grep -inE "frozen CLI|aimaestro-[a-z]+\.sh|never call|R23"`
  over `agents/*.md` returns **zero hits**. The plugin instructs the R23 transport prohibition
  **nowhere**.
- **Clause 1 is clean:** `grep -rnE "/api/|localhost:[0-9]+|127\.0\.0\.1:[0-9]+"` over
  `agents scripts tests README.md` → no hits. No `curl`, no `wget`. Zero direct server calls.
- **Why the prescribed fix does not apply:** ai-maestro#107's ruling is *canonical text copied
  verbatim into each `SKILL.md`, never a pointer*. This plugin ships **no `skills/`, no
  `commands/`, no `hooks/`** — `.agent.toml` declares `[skills] primary/secondary/specialized = []`
  deliberately and reaches four AI Maestro skills by name via `[dependencies].external_skills`.
  There is nothing to copy into.
- **BLOCKED ON:** the hub's ruling on ai-maestro#127 Ask 3. Two candidate answers with opposite
  consequences (below); picking one unilaterally is the failure this card exists to avoid.
- **NEXT ACTION (once the ruling lands):** apply the chosen option, then add a conformance test
  asserting the canonical block byte-for-byte, falsified against tampered text before commit.
- **SUPERSEDED — do NOT carry forward:** nothing yet.

## The question

Where does canonical rule text live for a role-plugin whose only shipped prompt surface is a
persona?

## The two candidate answers

1. **The persona is the decision-time surface** when there is no skills layer, so the canonical
   block goes there plus a conformance test. Cheap, and honest about what actually loads — but it
   re-creates the exact defect ai-maestro#107 named, since a persona is precisely what an agent
   does *not* re-read at the moment it decides.
2. **A persona-only plugin must grow a skills layer** to have a decision-time surface at all.
   Correct by #107's logic, but it contradicts the deliberate zero-skills design in `.agent.toml`
   and the plugin-abstraction principle that design cites.

A third possibility would make both moot: if the four inherited skills already carry the rule, a
plugin that ships none may be covered by construction. Unverified from here — those skills' text is
not in this repo — and #107's ruling was explicitly *"duplication, verified. Not indirection"*,
which reads as forbidding that inheritance.

## Why this is not cosmetic

The same property recurred within 24h on a second instruction: the hub's 2026-08-06 server digest
(`ai-maestro-assistant-role-agent#1`) reported that `read-prompt` is not sufficient (AskUserQuestion
captured 0/419) and asked every role-plugin to fix any doc that contradicts it. This plugin
contradicts nothing — `grep` for `read-prompt|block-state|chat-state|capturePane` returns zero — and
equally has nowhere to carry the correction. **The property that makes a persona-only plugin immune
to a stale instruction makes it unable to absorb a fresh one.** That is the general finding; R23 is
the instance.

## Acceptance criteria

- [ ] Hub ruling recorded on ai-maestro#127 Ask 3.
- [ ] Canonical R23 text present in whichever surface the ruling names, byte-for-byte.
- [ ] Conformance test asserting the copy matches canonical, verified to FAIL before the fix.
- [ ] No pointer/indirection substituted for the text (per #107's ruling).
