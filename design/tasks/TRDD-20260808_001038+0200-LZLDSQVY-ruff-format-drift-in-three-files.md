---
trdd-id: LZLDSQVY
title: Ruff-format drift in three files, with the bulk of it in the release-pipeline script
column: dev
created: 2026-08-08T00:10:38+0200
updated: 2026-08-08T05:04:00+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: refactor
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: none
mandate: true
mandated-by: self
derived: true
derived-kind: eht
parent-trdd: 5KZQUOBS
severity: low
blocked-by: []
relevant-rules: []
external-refs: []
release-via: none
---

# Ruff-format drift in three files, with the bulk of it in the release-pipeline script

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-08

- **Two of the three files are FIXED** (one hunk each, both unambiguous).
- **`scripts/publish.py` is NOT, and that is a deliberate open decision, not an oversight.**
  67 hunks, and applying them **destroys deliberate column alignment** in the release-pipeline
  script. See *The publish.py question*.
- **ANSWERED 2026-08-08 by the USER, and the answer dissolves the question I asked.** I framed
  it as a three-way style preference (apply / exempt / accept). The USER's ruling:
  *"just ask the cpv agent to update the plugin to the last publish canon. unless your problem
  is more complex, then you need to open an issue on the cpv plugin repo."*
- **Why that is the better answer:** `scripts/publish.py` is not this repo's code to style — it
  is CPV's **canonical pipeline**, vendored here. Formatting it locally would create exactly the
  local divergence the canon exists to prevent, and the drift would return on the next canon
  sync. Measured: this repo pins CPV **v3.1.0** while the latest release is **v5.3.0** — two
  majors behind, which is the real defect the format drift was a symptom of.
- **NEXT ACTION:** CPV agent brings the pipeline to canon; the formatting resolves as a
  consequence, not as a decision. If the migration turns out to need a CPV-side change, file it
  as an issue on the CPV repo rather than patching locally (PRRD S7.1).

## Why this card exists separately

It came out of `TRDD-5KZQUOBS`: `ruff format --check` was already failing when I went to verify
that change. Folding a 893-line reformat into a governance-approved one-step release-pipeline
edit would have buried the reviewed change under noise, so it was deliberately left out and
filed here instead — the ai-maestro session confirmed that call and asked for exactly this card.

Tier 0: own tree, formatting only, reversible, no governance surface, no `.github/`.

## Measured, first-hand — do not re-derive

| fact | value |
|---|---|
| `ruff format --check tests/ scripts/` | 3 files would reformat, 6 already formatted |
| total diff | 893 lines |
| `scripts/publish.py` | **67 hunks** |
| `tests/conftest.py` | 1 hunk |
| `tests/test_cpv_network_resilience.py` | 1 hunk |
| drift predates my work? | **yes** — identical 3 files with my changes stashed |
| does CI gate on it? | **NO** |

**CI does not enforce formatting**, which is the fact that turns this from a latent build
failure into a preference. Mega-Linter runs `PYTHON_RUFF` as a *linter* with
`--select=E,F,W,I --ignore=E501`, and `APPLY_FIXES: none`. `ruff check` passes today. Nothing
red is being hidden by leaving this open.

## What was fixed

Both are single hunks with no judgement in them:

- `tests/conftest.py` — `[...end():]` → `[...end() :]` (ruff's slice-spacing rule when the bound
  is an expression).
- `tests/test_cpv_network_resilience.py` — a string literal full of escaped `\"` rewritten to
  single quotes, removing the escapes. Strictly more readable, and the string's VALUE is
  unchanged — it is a network-error fixture whose content is load-bearing, so that was checked
  rather than assumed.

## The publish.py question

`ruff format` would rewrite an aligned constant block:

```python
RED    = "\033[0;31m" if _C else ""
GREEN  = "\033[0;32m" if _C else ""
YELLOW = "\033[1;33m" if _C else ""
```

into a ragged one (`RED = `, `GREEN = `, …). That alignment is not accidental — someone lined it
up by hand — and 67 hunks of similar re-wrapping would also churn `git blame` across the script
that cuts every release.

Three defensible answers, and the choice is a human's:

1. **Apply it.** The repo's own README documents `ruff format scripts/ tests/` as the standard,
   so the aligned block is drift *from* the declared standard. One-time churn, then
   `--check` is green forever.
2. **Exempt the file.** Add `scripts/publish.py` to `[tool.ruff.format] exclude` so `--check`
   goes green without touching the code — honest only if the alignment is genuinely wanted.
3. **Accept the drift.** Change nothing. Costs nothing today (CI does not gate), but
   `--check` stays red, and a red check that everyone knows to ignore trains people to ignore
   checks.

**Recommendation: (1).** A formatter the project declares but does not follow is the worst of
the three — it makes every future diff a coin-flip between the two styles, and the alignment is
recoverable from history if anyone misses it. But this is a readability call on someone else's
codebase, so it is asked, not assumed.

## Acceptance criteria

- [x] `tests/conftest.py` formatted; the fixture's behaviour unchanged.
- [x] `tests/test_cpv_network_resilience.py` formatted; the error-string VALUES verified
      identical, since they are matched against real network failures.
- [x] Full suite green after the change.
- [ ] Decision recorded on `scripts/publish.py` (apply / exempt / accept).
- [ ] Whichever is chosen, applied — and if apply: `ruff format --check` green repo-wide.

## Approval log

- 2026-08-08T00:10:38+0200 — MANDATE issued by self (min-approval-requirement: none).
  Pre-approved: a Tier-0 self-mandate's issuer and receiver are the same agent. No approval
  request was sent.
