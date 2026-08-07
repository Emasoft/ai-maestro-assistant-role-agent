---
trdd-id: F54QWQEV
title: Which R39 binds this plugin, and R39.2 asserts a publication state that is false
column: complete
created: 2026-08-07T12:01:26+0200
updated: 2026-08-08T00:35:31+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: user
blocked-by: []
external-refs: [ai-maestro#67, ai-maestro#86, ai-maestro#118, ai-maestro#120, ai-maestro#127]
relevant-rules: []
release-via: none
---

# Which R39 binds this plugin, and R39.2 asserts a publication state that is false

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-07

- **The question moved.** It began as *"which of two `GOVERNANCE-RULES.md` versions binds me"*.
  Per ai-maestro#67 (surfaced via #120 on 2026-08-07), the answer may be **neither**: the operative
  layer is the **DEP overlay** `rules/aimaestro/*.md`, seeded read-only per workdir as
  `.claude/rules/aimaestro-*.md`; `docs/GOVERNANCE-RULES.md` is *the design target, not operative*.
- **Verified first-hand, 2026-08-07** — do not re-derive:

  | measurement | result |
  |---|---|
  | `rules/aimaestro/` on `main` | **404** |
  | `rules/aimaestro/` on `governance-rules` | 5 files present |
  | `design/specs/3-pillars-spec.md` on `main` | **404** |
  | same on `governance-rules` | 25,637 b |
  | `ASSISTANT` across all 5 overlay files | **0 occurrences** |
  | `R39` across all 5 overlay files | **0 occurrences** |
  | `.claude/rules/` in THIS workdir | **absent** — overlay never seeded here |
  | `.claude/rules/aimaestro-*.md` elsewhere on host | **40 files / 8 workdirs** under `~/agents/` |

- **So: the operative layer contains no rule for this role at all**, and is branch-only besides.
  The persona is the sole artifact defining the ASSISTANT, and it cites the branch-only
  `GOVERNANCE-RULES.md` that #67 calls non-operative.
- **Not a self-heal failure.** The overlay IS seeded on this host, just not into a plugin dev repo
  — read as "this repo is not a registered agent workdir", not as a broken `dep-rules` invariant.
- **ASK 2 IS ANSWERED — and it was already decided before I asked (ai-maestro#86, closed
  2026-07-29). I missed it because I searched OPEN issues.** Measured 2026-08-07, same branch,
  two different documents:

  | file | R39.2 says |
  |---|---|
  | `design/specs/governance-spec.md:1571` (the SPEC) | *"**PUBLISHED** — public since 2026-07-22, listed in the marketplace manifest … remains absent from `PREDEFINED_ROLE_PLUGIN_NAMES`, which is now an **OPEN QUESTION** rather than a settled consequence of being local"* |
  | `docs/GOVERNANCE-RULES.md` (the CATALOG) | *"a **LOCAL/D4 source** … intentionally **NOT a published GitHub repo**"* |

  So this was never a spec defect — it was a **PROPAGATION GAP**. The correction landed in the
  SPEC on 2026-07-22 under the spec-first authority inversion; the CATALOG step lagged it.

- **THE GAP IS NOW CLOSED — measured 2026-08-07T20:58, superseding the row above.** The CATALOG
  on `governance-rules` now reads *"**PUBLISHED** — `Emasoft/ai-maestro-assistant-role-agent`,
  public since 2026-07-22 and listed in the `ai-maestro-plugins` marketplace manifest"*, with the
  `PREDEFINED_ROLE_PLUGIN_NAMES` omission restated as an **open question** rather than a
  consequence of being local. Landed by commit `95052d6e` in `ai-maestro@governance-rules`
  (*"docs(governance): R39.2 + RP-ASSISTANT-01 publication fact re-aligned"*). **Ask 2 is fully
  resolved in both documents; do not re-report the mirror as stale.**
- **The `PREDEFINED_ROLE_PLUGIN_NAMES` half is SETTLED: the ASSISTANT stays OUT, and the tuple
  must NOT be "fixed" to 9.** Ruled on #86 F2 by the MANAGER as the most-affected consumer
  (zero references to the tuple; title→plugin resolution uses separate maps). The *omission* was
  always right; only its stated reason ("local ⇒ not predefined") was dead. Correct grounds:
  **user-bound, not fleet-bound.** Do not re-open this.
- **ASK 1 IS RULED — `column: complete`.** ai-maestro#127 comment `5222763179`
  (2026-08-07T22:23:48Z, verified first-hand): **the `governance-rules` branch binds**, now
  v5.3.2. This persona's R39.8/.9/.10 citations implement current law and were correct all
  along. Three qualifications shipped into the persona's new *Which copy of the rules binds
  you* section: the 4.8.0 authority inversion (spec over catalog); `main`'s copy asserts
  completeness falsely, so a compliance check against the default branch is the document being
  wrong, not this plugin; and the interim fairness rule shields an agent that read `main` — not
  this one, which read the branch.
- **Measurement correction for the table above:** the tip is no longer `af7f5ed8`/v5.2.0. As of
  2026-08-08 the local branch tip is `afba54bb` and the file reads `version: "5.3.2"`. The
  ruling cites `0329558c`, which is real and an ancestor — it had simply moved again by the
  time I checked. Re-measure rather than trusting any of these three.
- **NEW, and it explains the whole shape of this card — CORRECTED 2026-08-08, read the corrected
  form and not the first one.** I first wrote that `governance-rules` is "not on the remote at
  all". That came from `git ls-remote --heads origin`, and **`origin` in `~/ai-maestro` is
  UPSTREAM (`23blocks-OS/ai-maestro`), not the fork** — a remote-availability claim that does not
  name its remote, which is the same defect as a sha citation that does not name its repo. The
  measured per-remote facts:

  | remote | url | `governance-rules` |
  |---|---|---|
  | `origin` | `23blocks-OS/ai-maestro` | **absent** |
  | `fork` | `Emasoft/ai-maestro` | present at `2ca29e43` — v5.2.0, **exactly 245 behind** local, 0 ahead |

  So the branch IS fetchable, from the fork, frozen before 2026-08-05. Publication is therefore
  not one decision but **two staleness gaps** — upstream absent, fork 245 behind. The conclusion
  survives: the *current* law (v5.3.2) is on no remote, so a plugin told "the branch binds you"
  still cannot fetch what binds it, and this plugin vendors the canonical bytes
  (see `TRDD-4983GIZW`) rather than read them across repos.
- **NEXT ACTION: none by me.** `main`'s fate rides the USER's publication decision, which is the
  hub's to carry. Do NOT touch R39.2 — spec and catalog now agree.

## Ask 1 — which R39

`docs/GOVERNANCE-RULES.md` differs by ref: `main` carries `version: 4.0.2` with R39.1–R39.7;
`governance-rules` carries `version: 5.2.0` with R39.1–R39.**10**. `compare/main...governance-rules`
→ `ahead_by=2906, behind_by=0`.

The delta is load-bearing, not cosmetic. `main`'s R39.5: *"obeys **only its user and the
MAESTRO** … may message only its user and the MAESTRO."* The branch: *"obeys **no one else — not
the MAESTRO user**, no other agent … may message only its own user and the MANAGER."* R39.8/.9/.10
are absent from `main` entirely — no self-approval clause, no MANAGER channel, no scoped
collaboration expansion.

**This persona implements the branch version** — 10 citations of R39.9, 7 of R39.10, 6 of R39.8. An
operator checking compliance against the default branch would read a superseded document and
conclude this plugin is non-compliant on obedience, its single most load-bearing rule.

## Ask 2 — R39.2 says this plugin is not published; it is

Verbatim from the branch, R39.2: *"a **LOCAL/D4 source** — already built at
`~/agents/role-plugins/roles-marketplace/`, **intentionally NOT a published GitHub repo** and
**absent from `PREDEFINED_ROLE_PLUGIN_NAMES`**"*.

Measured: the repo is **PUBLIC**, latest release **v0.3.2** (2026-07-23), and listed in
`Emasoft/ai-maestro-plugins` `.claude-plugin/marketplace.json` (line 59, with the `.git` URL at line
62). The README's install path is the published marketplace route the rule says does not exist.

The `PREDEFINED_ROLE_PLUGIN_NAMES` half is **unverified** — a code search over the hub repo returned
0 results, which reads as "not indexed", not as "absent". No claim is made about the constant.

**One of the two must move, and the choice is not this plugin's to make.** Either the rule is stale
and should describe a published, marketplace-listed role-plugin, or the publication was unintended —
in which case de-listing has consequences for anyone who already installed from the marketplace.
Nothing has been changed pending the ruling.

## Acceptance criteria

- [x] Ruling recorded: which layer is operative for R39. **`docs/GOVERNANCE-RULES.md` on the
      `governance-rules` branch**, with `design/specs/governance-spec.md` authoritative over it
      where they differ (4.8.0 authority inversion).
- [x] The overlay question is answered by that: the DEP overlay is not the operative layer for
      R39, so its zero ASSISTANT content is not the gap it looked like.
- [x] R39.2 either amended to match reality, or a de-publication decision taken by the USER.
      **Amended** — `95052d6e` in `ai-maestro@governance-rules`; catalog and spec now agree.
- [x] Persona citations updated to name the operative layer — new *Which copy of the rules
      binds you* section, carrying the ruling and its three qualifications so a future session
      does not re-derive them.

## Approval log

- 2026-08-08T00:37:41+0200 — TERMINAL-EDIT sanctioned by ai-maestro (the server session),
  manager tier. This card is `column: complete` and therefore frozen to body edits (IND base
  step 12), yet it was edited on 2026-08-08 to retract a false measurement ("the branch is not
  on the remote at all", made against `origin` without naming that `origin` is upstream). Ruled:
  **accept the retraction in place, do not move it to a separate card** — the freeze exists to
  stop a terminal card silently changing what it ASSERTED, and a dated retraction that keeps the
  old claim visible inside it strengthens the audit trail rather than eroding it; a separate
  card would orphan the retraction from the claim it corrects, and a false fact in a card marked
  DONE propagates precisely because nobody re-reads DONE cards.
  **Two constraints, so this does not become a loophole:** (1) the old claim stays VISIBLE
  inside the retraction and is never deleted; (2) it licenses retracting false **facts** only —
  never re-litigating a decision, a scope, or an acceptance criterion.
  Flagged by the approver as a manager-tier gloss on the freeze rule, recorded in its report for
  the USER, who owns the rule and may narrow it.
