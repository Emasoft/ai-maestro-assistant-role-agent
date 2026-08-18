---
trdd-id: NRQK4W2P
title: Restore the vendored canonical R22 and R23 blocks to the persona once CPV 201 is fixed
column: human_review
created: 2026-08-08T10:46:16+0200
updated: 2026-08-18T16:28:32+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: none
mandate: true
mandated-by: self
derived: true
derived-kind: eht
parent-trdd: 4983GIZW
severity: medium
blocked-by: []
relevant-rules: []
external-refs: [ai-maestro#127, claude-plugins-validation#198, claude-plugins-validation#201]
release-via: publish
implementation-commits: [6be9eaf]
---

# Restore the vendored canonical R22 and R23 blocks to the persona once CPV 201 is fixed

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-16

- **UNBLOCKED 2026-08-16.** CPV#201 is CLOSED (`closedAt` 2026-08-15T14:41:20Z, verified
  first-hand via `gh issue view 201 --repo Emasoft/claude-plugins-validation`). CPV#198/#204/#205
  also closed. `blocked-by` cleared, column `blocked` → `dev`.
- **A CLOSED ISSUE IS NOT A PASSING GATE.** #201 closed says the maintainer considers it fixed;
  it does not say the CPV version this repo pins ships that fix. So the FIRST step of the restore
  is empirical: restore the blocks, run the real validator, and read its exit code. If it still
  exits non-zero on the byline NIT, STOP and re-block — do not weaken the canonical text to pass
  (that is Option 3, rejected 2026-08-08 and still rejected).

- **The canonical blocks were REMOVED FROM THE PERSONA for the v0.3.3 release only, and this
  card is the promise to put them back.** They are mandated by ai-maestro#127 Ask 3/4; nothing
  about that ruling was reversed.
- **Why they came out:** CPV's `A2A_AGENT_IMPERSONATION` detector fires on the canonical R22.2
  byline row — a rule *about* attribution reads to a regex like an attempt to spoof one. It is
  DEMOTED to a NIT ("needs review"), but the canonical release gate fails on **any** validator
  exit 1–4, so one demoted NIT made the plugin unreleasable at `CRITICAL=0 MAJOR=0 MINOR=0`.
- **Both pins were blocked, for different reasons** — that is why removal was the only path:
  v5.3.0 exits 2 on canon's own `publish.py` (CPV#198), v3.1.0 exits 4 on this NIT (CPV#201).
- **What is NOT gone:** the fixtures, `PROVENANCE.json`, and the fixture-integrity tests all
  stay live, so the vendored bytes cannot rot while the persona copy is out. The rules
  themselves remain stated in the persona in this repo's own words — only the byte-for-byte
  canonical reproduction is withheld.
- **The tests re-arm BY THEMSELVES.** The skips are computed from the persona (`"<!-- CANONICAL-BEGIN:" in text`),
  not hardcoded — restore the blocks and the conformance tests start enforcing again with no
  flag to remember. A manual re-enable is the kind of thing that stays forgotten for a year, and
  a conformance test that silently never runs is worse than no test, because the suite still
  reports green.
- **⚠️ SUPERSEDED — DO NOT RE-VENDOR FROM THE SPEC. Ruled by the hub 2026-08-08T13:00.** The bullet
  below was my reading of Ask 1 before the hub ruled, and it is kept because it is the measurement
  that produced the question, not because it is the instruction. **The ruling:** the spec's granular
  renderings (`R22.1`…`R22.5` / `R23.1`…`R23.8`) are the **NORMATIVE** form; the doc's verbatim
  blocks — what is vendored here — are **PROVENANCE**, the source being rendered. Coexistence is
  fine, so the fixtures stay as captured. **The one condition:** the normative declaration must be
  stated WHERE THE CLAUSES LIVE — so the restored persona blocks must carry, adjacent to them, an
  explicit line saying the spec's granular form is normative and this is the provenance copy.
  Without that line a reader takes the vendored prose as the rule. Verified against
  `Emasoft/ai-maestro@governance-rules` tip `f3f02743`, card `TRDD-9SEQ4QI9`.
- **(superseded reading, retained) RE-VENDOR FROM THE SPEC, NOT THE DOC — found 2026-08-08T12:05.**
  ai-maestro#127 Ask 1 ruled `design/specs/governance-spec.md` **authoritative over**
  `docs/GOVERNANCE-RULES.md` where they differ. The vendored blocks came from the DOC, i.e. the
  subordinate source. Measured at tip `0e8d6896`: both blocks are still byte-verbatim in the doc,
  and **neither appears in the spec at all** — the spec states the same rules in a different,
  more granular form (`R22.1 self-id-every-github-write` … `R22.5 mirrors-PRRD-G1.1`;
  `R23.1 no-element-calls-api` … `R23.8 announce-to-ship`). So this is not drift between two
  copies of one text; it is two different renderings, and I pinned the one that loses a conflict.
  Extents recorded in `tests/fixtures/canonical/PROVENANCE.json` → `authoritative_source_note`.
- **The branch tip moved three times in one day** (`1ccbe9e0` → `db6cf8f8` → `0e8d6896`), so
  locate the blocks by HEADING and re-measure; never trust a stored line number as a key.
- **RESTORED 2026-08-16 — the code work is DONE and measured; only the release remains.** What
  landed, all verified first-hand:
  - Both `CANONICAL-BEGIN/END` blocks are back in the persona, byte-for-byte against the
    fixtures. The hub's one condition is met: an adjacent note states the spec's granular
    `R22.1…R22.5` / `R23.1…R23.8` are NORMATIVE and these blocks are the PROVENANCE copy.
  - `PROVENANCE.json` re-measured against the live branch (tip `2ae3e38d`, doc still v5.3.3):
    both blocks still byte-identical upstream, only line numbers shifted by one. Hashes unchanged.
  - Suite: **111 passed, 0 failed.** The 5 conformance tests re-armed by themselves, as designed.
  - The word-budget test caught the restore prose (5020 > 5000 authored words); the note was
    tightened rather than the bound moved. The budget did its job — do not raise it reflexively.
- **HOW THE GATE WAS CLEARED — and what was NOT done.** The canonical text was NOT edited; that
  is still Option 3 and still rejected. CPV#201's fix (shipped in **v5.5.0**, not in the pinned
  v3.1.0) is a **consent registry**, not a detector change: the NIT still fires. Measured:
  v5.5.0 on the restored tree exits **4** (`CRITICAL=0 MAJOR=0 MINOR=0 NIT=1`), and with
  `.cpv-audit-consent.json` at the plugin root it exits **0**, the finding still visible as
  `(demoted, consented)`. Consent is informed review, not suppression — the protected
  "prose IS the attack" rule family can never be consented, and A2A/agent-manipulation is
  provably outside it (CPV#194).
  - **The flagged line is R22.4, not R22.2** (`…-main-agent.md:400`). The old STATE said R22.2;
    that was inherited, never measured. The consent pins the sha256 of that line re-read from
    disk, so ANY edit to it invalidates the consent and the finding blocks again — which is the
    property that makes this safe to commit.
  - All **7** CPV pins bumped v3.1.0 → v5.5.0 (`scripts/publish.py` ×5, `ci.yml`, `release.yml`).
    Both entrypoints re-verified at the new pin: `plugin --strict` exit 0, `ci-preflight` exit 0
    (PARITY-CLEAN, FAIL=0). CPV#198 is moot — v5.5.0 does not flag this repo's `publish.py`.
- **AI REVIEW DONE 2026-08-18 — clean, but it caught a REGRESSION the 08-16 measurement could
  not have seen.** Re-measured first-hand on the current tree, not trusted from the note above:
  `plugin --strict` at v5.5.0 exited **4** again (`CRITICAL=0 MAJOR=0 MINOR=0 NIT=1`). The
  persona consent was fine (line 400 still hashes to the pinned value, reported `(demoted,
  consented)`); the new NIT came from **`.claude/project/memory/cpv-release-gate-blocks-on-demoted-nit.md:20`**
  — the memory note WRITTEN TO RECORD THIS EXACT FALSE POSITIVE, committed one commit later in
  `40e15a6`, trips the same detector one layer up. Documenting the trap re-armed it.
  - **Fixed by a second consent entry, not by rewording the note.** Rewording our own accurate
    prose to dodge a regex is the anti-pattern the note itself records; consent keeps the finding
    VISIBLE and sha256-pins the line so any edit re-blocks. Gate now exits **0**
    (`CRITICAL=0 MAJOR=0 MINOR=0 NIT=0 WARNING=6`, both findings shown as `(demoted, consented)`).
    Tests re-run after the edit: **111 passed, 0 skipped**.
  - **The general lesson, for the next writer:** any file added under the plugin root that
    DESCRIBES an `A2A_AGENT_IMPERSONATION` pattern will fail the gate — including a memory note,
    a TRDD, or a README. Expect to consent it; do not paraphrase the description away.
- **NEXT ACTION:** USER approval to ship (`release-via: publish`, `complete → publish` is
  non-exempt). Everything else is done and measured; the tree is clean. Do not chase a version
  number: this card was written naming v0.3.4, v0.3.4 then shipped for unrelated work, and the
  restore is defined by its CONTENT, not by a version.

## Why this exists rather than "we'll remember"

An interim removal with no card is indistinguishable from a silent regression six months later:
the persona would simply lack the canonical text, the conformance tests would sit skipped and
green, and the only trace would be a commit message nobody greps. The card, the self-arming
skips, and the interim note inside the persona itself are three independent ways for a future
reader to find out this was deliberate and temporary.

## Acceptance criteria

- [x] CPV#201 fixed (a demoted NIT no longer blocks the release gate), or CPV ships a
      `--fail-on=` control the pipeline can use. — shipped in v5.5.0 as a CONSENT REGISTRY; the
      NIT still fires and is consented, not silenced.
- [x] `CANONICAL-BEGIN/END: R22` and `: R23` restored to the persona byte-for-byte, re-captured
      from `docs/GOVERNANCE-RULES.md` at the then-current upstream ref, not pasted from memory.
      — lines 392-404 and 423-438.
- [x] **A line adjacent to the restored blocks declares the spec's granular renderings
      (`R22.1`…`R22.5` / `R23.1`…`R23.8`) NORMATIVE and these blocks PROVENANCE** — the hub's
      explicit condition for letting the two coexist (`TRDD-9SEQ4QI9`). Without it the vendored
      prose reads as the rule. — line 386.
- [x] `PROVENANCE.json` re-measured against the then-current fork tip in the same commit
      (it moved twice in one day on 2026-08-08; assume it moved again). — `2ae3e38d`, captured
      2026-08-16T16:27.
- [x] The 5 skipped tests report as PASSED, not skipped — that is the proof the restore landed.
      — 111 passed, 0 skipped, re-run 2026-08-18.
- [ ] Full validation exits 0 and the restore is published (any version; see the STATE note —
      v0.3.4 was consumed by unrelated work on 2026-08-08 while this card was still blocked).
      — validation exits 0 as of 2026-08-18; PUBLISH still pending USER approval.

## Approval log

- 2026-08-08T10:46:16+0200 — MANDATE issued by self (min-approval-requirement: none).
  Pre-approved: a Tier-0 self-mandate's issuer and receiver are the same agent.
  The removal it tracks was ruled by the ai-maestro session (Option 2 of three offered):
  ship the live-harm fix now, land the canonical blocks in v0.3.4. Option 3 — editing the
  canonical text so it stops matching the detector — was explicitly REJECTED by that ruling and
  by this agent: safety documentation is indistinguishable from the pattern it forbids to a
  regex, and weakening the decision surface to pass a gate is the anti-pattern the rules name.
