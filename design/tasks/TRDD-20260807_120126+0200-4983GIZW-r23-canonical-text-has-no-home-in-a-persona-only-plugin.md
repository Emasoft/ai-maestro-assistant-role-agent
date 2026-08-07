---
trdd-id: 4983GIZW
title: R23 canonical prohibition has no decision-time surface in a persona-only plugin
column: complete
created: 2026-08-07T12:01:26+0200
updated: 2026-08-08T00:28:58+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: manager
blocked-by: []
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
- **RULED AND DONE — `column: complete`.** ai-maestro#127 Ask 3 (comment `5222763179`,
  2026-08-07T22:23:48Z, verified first-hand) chose **Option 1**: for a persona-only plugin the
  persona IS the decision-time surface, so the canonical R23 block goes there, **plus** a
  byte-for-byte conformance test — the test IS the checklist. Option 3 rejected on #107's own
  *"duplication, verified. Not indirection."*; Option 2 rejected as compliance theater.
- **Shipped:** canonical R23 in the persona between `CANONICAL-BEGIN/END: R23` markers, plus
  canonical R22 (Ask 4) replacing this repo's independent phrasing of the same rule.
  `tests/test_canonical_rule_blocks.py` enforces both.
- **The design decision worth not re-litigating:** the canonical bytes are **vendored** into
  `tests/fixtures/canonical/` rather than read from the ai-maestro repo. Measured 2026-08-08:
  `git ls-remote --heads origin` on ai-maestro lists **no `governance-rules` ref** — the branch
  is LOCAL-ONLY. A cross-repo test would pass on one machine and fail in CI and every clone,
  reporting the rule as enforced everywhere while enforcing it nowhere.
- **A second guard exists for a reason:** the fixture is sha256-pinned in `PROVENANCE.json`, so
  the obvious way to "fix" a drift failure — editing the fixture to match a corrupted persona —
  fails too. Proven by tampering, not assumed.
- **SUPERSEDED — do NOT carry forward:** the framing that this plugin *cannot* host canonical
  rule text. It can; the missing piece was never a surface, it was the checklist.
- **NEXT ACTION: none.** If the upstream rule changes, re-capture the fixture and update
  `PROVENANCE.json` in the same commit; the test will tell you loudly.

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

- [x] Hub ruling recorded on ai-maestro#127 Ask 3 (comment `5222763179`).
- [x] Canonical R23 text present in the persona, byte-for-byte (and R22 likewise, per Ask 4).
- [x] Conformance test asserting the copy matches canonical, **falsified three ways** before
      commit: a one-word drift inside the block fails with `DRIFTED from the canonical text`;
      deleting a marker fails with `no CANONICAL-BEGIN/END block for R22`; editing the fixture
      to match a corrupted persona fails with `no longer matches its recorded sha256`.
- [x] No pointer/indirection substituted for the text (per #107's ruling).
- [x] Derived fix: the persona word budget now measures **authored** prose only. A
      byte-for-byte mandate and a shrinkable-prose budget are in direct tension — counting
      canonical text would make every upstream rule edit a spurious budget failure whose only
      available remedy is deleting authored guidance, and would put a standing incentive on
      trimming the canonical copy. Guarded by its own coverage test so the exclusion cannot
      silently stop working.
