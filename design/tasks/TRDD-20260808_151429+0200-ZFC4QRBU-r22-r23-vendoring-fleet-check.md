---
trdd-id: ZFC4QRBU
title: Fleet check — which role-plugins vendored R22 and R23 without declaring the spec normative
column: complete
created: 2026-08-08T15:14:29+0200
updated: 2026-08-08T15:25:09+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: audit
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: none
mandate: true
mandated-by: ai-maestro hub
severity: medium
blocked-by: []
relevant-rules: []
external-refs: [ai-maestro#127, ai-maestro TRDD-9SEQ4QI9]
release-via: none
---

# Fleet check — which role-plugins vendored R22 and R23 without declaring the spec normative

## Why this exists

`ai-maestro#127` Ask 1 ruled `design/specs/governance-spec.md` authoritative over
`docs/GOVERNANCE-RULES.md`. `TRDD-9SEQ4QI9` refined it: the spec's granular renderings
(`R22.1`…`R22.5` / `R23.1`…`R23.8`) are **NORMATIVE**; the doc's verbatim blocks are **PROVENANCE**.
Coexistence is allowed **only if the normative declaration is stated where the clauses live**.

I discovered this by finding it in my own repo — I had vendored the doc, i.e. the source that loses
a conflict, with no such declaration. That is unlikely to be unique to me: any plugin that copied
canonical rule text almost certainly copied the doc, because the doc is the human-readable one.

**Work order from the ai-maestro hub** (accepted 2026-08-08): run the measurement across the
role-plugin repos and report results TO THE HUB. **Do NOT file per-repo issues** — which repos get
told, and how, is the hub's relay decision, made on my data. This is a read-only audit of other
projects, which is what keeps it inside the cross-project rule: I measure and report, I never edit.

## Method (so the numbers are reproducible, not asserted)

1. Fetch `docs/GOVERNANCE-RULES.md` and `design/specs/governance-spec.md` from
   `Emasoft/ai-maestro@governance-rules`, recording the tip sha at measurement time.
2. Derive **needles** — distinctive verbatim runs of the canonical R22/R23 doc prose. Several per
   rule, so a repo that vendored a *different extent* is still detected instead of silently
   reading as clean.
3. For each repo, download the **default-branch tarball** and scan every text file. A tarball is
   one call and gives COMPLETE coverage; per-path fetching samples, and a sampled audit that
   reports "clean" is worse than no audit.
4. Per repo record: HEAD sha, matched files, which needles matched, and whether a
   normative-declaration signal is present.

## Verdicts

- `vendored-without-declaration` — canonical prose present, no normative declaration beside it
- `declares-spec-normative` — canonical prose present AND declared as provenance/spec-normative
- `no-vendoring` — no canonical prose found

## Result — the question came back NULL, and the sweep found something else

**Nobody vendored the canonical prose except me. My hypothesis was WRONG** — and stating that
plainly is the point: an audit that quietly drops its own falsified premise is how a null becomes
invisible. All 9 reachable repos CITE R22/R23 (validated by a separate false-negative sweep); none
copy the text.

Two findings the vendoring question would have missed:

1. **5 of 9 name only `docs/GOVERNANCE-RULES.md` and never the spec** — under `TRDD-9SEQ4QI9` that
   is the same exposure one layer out: not stale bytes, but readers directed to the copy that loses
   a conflict.
2. **9 live defects: 6 repos ship a PRRD `G1.1` byline template carrying a literal `@owner`** — a
   real GitHub Organization — plus `integrator`'s persona AMP template and two of its skill
   reference files. These are STALE copies of the PRE-FIX canonical text; current canon (doc AND
   spec, tip `0be8cf32`) reads `<owner>` and says "carries NO `@`, deliberately".

**Classification mattered more than counting here:** 31 raw `@owner` occurrences reduce to 9
defects, because 19 are TESTS asserting the string must never ship. A `grep -c` would have reported
31 problems where there are 9, and would have named four repos' guards as faults.

Report: `reports/r22-r23-fleet-check/20260808_152001+0200-r22-r23-vendoring-and-byline-fleet-check.md`

## Acceptance criteria

- [x] Population stated explicitly. **10/10 measured — no unreachable rows.** My first pass called
      `ai-maestro-webdesign-agent` unreachable (404); the hub supplied the real name
      (`ai-maestro-webdesign`, no `-agent` suffix) and it measured clean (`c43af898c530`,
      1,321 files, `no-vendoring`). The lesson is that **"unreachable" and "I guessed the repo
      name wrong" look identical from outside**, and only one of them is a real gap — so a 404 in
      an audit population is a prompt to check the name, not a row to write off.
- [x] Every repo measured, all-clean rows listed (a clean row omitted is a row nobody can audit).
- [x] Method validated: 6/6 needles positive-controlled against the canonical doc, plus a
      false-negative citation sweep — a null across 8 repos is otherwise indistinguishable from
      broken instrumentation.
- [x] Results reported to the hub with per-repo verdict, HEAD shas, and measurement timestamps.
- [x] No per-repo issues filed by me; no edits to any audited repo.

## Approval log

- 2026-08-08T15:14:29+0200 — MANDATE from the ai-maestro hub, Tier-0 (`min-approval-requirement:
  none`): a read-only cross-repo measurement reported to the mandating party. No approval rung is
  needed to READ public repos and report what is there; the relay decision that follows is the
  hub's, which is exactly why the mandate withholds issue-filing from me.
