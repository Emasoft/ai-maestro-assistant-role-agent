---
trdd-id: F54QWQEV
title: Which R39 binds this plugin, and R39.2 asserts a publication state that is false
column: blocked
pre-block-column: todo
created: 2026-08-07T12:01:26+0200
updated: 2026-08-07T12:01:26+0200
current-owner: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
approval-tier: 3
blocked-by: [ai-maestro#127]
external-refs: [ai-maestro#67, ai-maestro#118, ai-maestro#120, ai-maestro#127]
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
- **BLOCKED ON:** ai-maestro#127 Asks 1 and 2.
- **NEXT ACTION (once ruled):** update the persona's rule citations to name whichever layer is
  operative, and reconcile or amend R39.2 per the ruling.

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

- [ ] Ruling recorded: which layer (DEP overlay / `GOVERNANCE-RULES.md` / other) is operative for R39.
- [ ] If the overlay is operative, a decision on its total absence of ASSISTANT content.
- [ ] R39.2 either amended to match reality, or a de-publication decision taken by the USER.
- [ ] Persona citations updated to name the operative layer.
