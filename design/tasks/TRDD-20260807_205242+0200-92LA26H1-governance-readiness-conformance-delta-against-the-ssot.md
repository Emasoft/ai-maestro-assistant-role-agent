---
trdd-id: 92LA26H1
title: Governance-readiness conformance delta for the ASSISTANT role-plugin against the ai-maestro SSOT
column: planned
created: 2026-08-07T20:52:42+0200
updated: 2026-08-07T21:02:10+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: audit
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: none
mandate: true
mandated-by: self
severity: medium
blocked-by: []
relevant-rules: []
external-refs: [ai-maestro#86, ai-maestro#39]
release-via: none
---

# Governance-readiness conformance delta for the ASSISTANT role-plugin against the ai-maestro SSOT

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-07

- **The audit itself is DONE.** The delta table below is the deliverable and it is complete
  for the five axes the ai-maestro session named, plus the axes it did not name that the SSOT
  binds anyway.
- **Nothing has been REMEDIED yet.** This card holds findings only. Not one line of the
  persona, the workflows, the tests, or the existing three TRDDs was changed by this audit.
- **NEXT ACTION (one step):** file the F1 and F5 remediations as Tier-0 cards
  (`min-approval-requirement: none`) and work them; file F3 and F4 as `column: proposal`
  cards in `design/proposals/` and route them to the MANAGER — they are above my rung.
- **Load-bearing gotcha:** F1's fix is an ON-NEXT-TOUCH migration, never a mass rewrite, and
  a mechanical migration must NOT bump `updated:` on the card it touches (the board sorts on
  `updated:`; a repair pass that bumps it silently reorders every card).
- **SUPERSEDED — do NOT carry forward:** this card's first revision claimed the five SHAs I was
  given for the SSOT files "do not resolve". **That claim was FALSE and is retracted** — all five
  are **commits** on `ai-maestro@governance-rules`. See *Provenance*, which now records both the
  correct facts and the method error that produced the wrong one.
- **Artifacts to read first:** this card's delta table, then the SSOT paths in *Provenance*.

## Why this card exists

The ai-maestro session (the Claude developing the server, cwd `~/ai-maestro`) owns making
every ai-maestro plugin ready for the governance rules as they will be applied inside the
server harness. It directed a conformance-delta audit of this repo against the governance
SSOT, classified the audit itself as Tier 0 — an own-scope, reversible, local, read-only pass
over my own tree — and asked that the resulting table be committed here.

Tier 0 is correct under `aimaestro-trdd-approval` Part B: the work is fully inside this
agent's own assignment scope, deviates from no baseline, touches no other project's source,
and changes no governance. It is therefore a **self-mandate** (`mandate: true`,
`mandated-by: self`), born approved, authored directly in `design/tasks/`. No approval request
was sent and none was owed.

## Provenance — what was read, and a method error of my own

Read directly from `~/ai-maestro` on branch `governance-rules` (tip
`af7f5ed8f2652628beee7061848ef58ae292ad6f`, working tree clean, so branch == tree):

| SSOT path | blob (branch == tree) | SHA I was given — `git cat-file -t` in `~/ai-maestro` |
|---|---|---|
| `docs/GOVERNANCE-RULES.md` | `c873256b` | `95052d6e` — **commit**, on branch |
| `rules/aimaestro/aimaestro-trdd-approval.md` | `ed1bc353` | `b337bb19` — **commit**, on branch |
| `rules/aimaestro/aimaestro-kanban-multiagent.md` | `2fdc9bd9` | `06d9f439` — **commit**, on branch |
| `rules/aimaestro/aimaestro-manager-approval-defaults.md` | `92c3159f` | `618f7044` — **commit**, on branch |
| `rules/aimaestro/aimaestro-prrd-governance.md` | `17eca23c` | `43cf1264` — **commit**, on branch |

**All five paths are right and all five SHAs resolve.** They are `git log -1 --format=%h -- <path>`
values — the last commit that touched each file — not blob hashes. I compared them against blob
hashes, saw no match, and reported "does not resolve" **without ever running `git cat-file -t`**.
That is asserting a negative from a single wrong-type comparison, and it was wrong.

Two defects, one shared fix, recorded so neither recurs:

- **Mine:** a failed resolution must name **where it was attempted** and must actually attempt
  resolution — `git cat-file -t <sha>` in the named repo — before "does not resolve" is written
  down. A mismatch against one object type is not evidence of non-existence.
- **The citer's:** an unlabeled short SHA invites exactly this. A citation names its **type** and
  its **repo**: "commit `95052d6e` in `ai-maestro@governance-rules`".

The audit's substance is unaffected: it rests on the text, which was read directly (the R38/R39
tables, the `min-approval-requirement` section, the §D3 floor table, G1.1) — never on the
identifiers.

## The delta table

Rule id → this repo's current state → required change → the floor that change carries.
Floors are computed from the `aimaestro-trdd-approval` §D3 objective table, not judged.

| # | Rule / axis | Current state in this repo | Required change | Floor |
|---|---|---|---|---|
| **F1** | `min-approval-requirement:` supersedes `approval-tier:` (trdd-approval §"supersedes", USER 2026-07-10) | **NON-CONFORMANT.** All 3 cards carry the deprecated `approval-tier:` (`3`, `2`, `3`); none carries `min-approval-requirement:`. | Migrate **on next touch only**: `3 → user`, `2 → manager`. Never write `approval-tier:` on a new card. A file carries exactly one of the two. | `none` |
| **F2** | Missing `assignee:` (kanban-multiagent — `assignee:` IS the assignment fact) | **NON-CONFORMANT.** All 3 cards carry `current-owner:` only. Nothing else records the assignee, so the board cannot render one. | Add `assignee:` on next touch. | `none` |
| **F3** | PRRD + G1.1 (prrd-governance §"Recommended baseline golden rule G1") | **NON-CONFORMANT.** No `design/requirements/PRRD.md` exists anywhere in the repo. The project has no constitution, so G1.1 has no home. | Author the PRRD with G1.1 as its first GOLDEN rule. | **`user`** — creating a golden rule is Tier 3; I may not author it, only propose it. |
| **F4** | G1.1 self-identification on every GitHub-writing surface | **NON-CONFORMANT.** `release.yml` publishes release notes via `gh release create/edit --notes-file changelog.txt`, and that body is the raw CHANGELOG section — it carries no self-id line. A release note is a GitHub-writing surface. | Prepend the self-id line to the release body. | **`manager`** — the change is in `.github/` and in the release pipeline. |
| **F5** | Pipeline drain (kanban-is-a-pipeline) | **FLAG, not a defect of mine to fix.** `3972YVFH` sits at `column: complete` with `release-via: publish`; its next move is `complete → publish`. | Do **not** self-transition. `complete → publish` is explicitly NON-EXEMPT in `aimaestro-manager-approval-defaults` §Y. | **`manager`** |
| **F6** | `Agent:` commit trailer (G1.1 second half) | **PARTIAL.** Present on the 5 most recent hand-authored commits; absent on `c19d6db chore: bump version to 0.3.2`, which the release pipeline generates. | Decide whether `publish.py` should emit the trailer on generated commits. Low stakes; listed for completeness, not urgency. | `none` |
| **F7** | R39 / R39.10 in the persona | **CONFORMANT.** R39.1–R39.10 are all cited; R39.10 has its own *Collaboration expansion* section covering mutual visibility, AMP exchange, kanban-linked assignment, refusability (R41), scoping, and the user's absolute override. | none | — |
| **F8** | R38 messaging edge | **CONFORMANT, with a scope note.** R38.1's locked-fields carve-out is cited. R38.2 constrains what a *human user* may do (whom they message, whose terminal they may use) — it binds the user, not the ASSISTANT, so its absence from an agent-facing persona is correct, not a gap. | none | — |
| **F9** | 17-column vocabulary | **CONFORMANT.** Only `blocked` (×2) and `complete` (×1) are in use; both are ratified values. `pre-block-column:` is set on both blocked cards and `blocked-by:` is non-empty on both, so neither is a stalled card wearing a busy column. | none | — |
| **F10** | Frontmatter booleans — CC 2.1.218 accepts `yes/no/on/off/1/0` | **CONFORMANT.** The shipped agent frontmatter declares no boolean field at all, and the only parser in the repo is `yaml.safe_load` (YAML 1.1), which already accepts all six spellings natively. No allowlist, regex, or hand-rolled boolean check exists anywhere in `tests/` or `scripts/` that could reject them. Verified by reading the parser and every frontmatter assertion, not by grepping for the word `bool`. | none | — |
| **F11** | Bare `@mention` guard | **CONFORMANT.** `tests/test_no_bare_github_mentions.py` scans **all tracked markdown**, strips code spans and fences before scanning, and self-tests both that it detects a bare mention and that it actually opened files. | none | — |
| **F12** | `design/` zone folders | **CONFORMANT — not a defect.** Only `design/tasks/` exists on disk; `proposals/`, `archived/`, `refused/` are absent because git cannot track an empty directory. The promotion/refusal/archival protocols create each zone with their first `git mv`. Manufacturing them now with `.gitkeep` files would add three tracked files the rules never asked for. | none | — |
| **F13** | Model allowlist staleness (observation, outside the named axes) | `test_agent_declares_a_known_model` accepts only `{opus, sonnet, haiku, inherit}`. A persona that ever declared `model: fable` would fail a test rather than a rule. Not a governance finding; recorded so it is not re-discovered. | none — decide separately | `none` |

## The four non-conformant findings, in one line each

- **F1** — every TRDD in this repo uses the deprecated `approval-tier:`; none uses `min-approval-requirement:`.
- **F2** — no TRDD carries `assignee:`, so the multi-agent board cannot render assignment for this project.
- **F3** — the repo has no PRRD, so the G1.1 golden self-identification rule has nowhere to live.
- **F4** — published release notes carry no self-identification line, and a release note is a GitHub-writing surface G1.1 covers.

F5 and F6 are flagged rather than counted: F5 is a transition I am forbidden to make, and F6 is a
gap in a generated commit rather than in a shipped surface.

## What I did NOT touch, and why

- `PREDEFINED_ROLE_PLUGIN_NAMES` and the 8-plugin count — deliberate per ai-maestro#86; consumers
  assume exactly 8, and the decision belongs to the server side. Not audited, not "fixed".
- Auto-provisioning — ai-maestro#39 AC4 is gated on native-user registration, which does not exist.
  Nothing here builds on it.
- Any repo other than this one. `~/ai-maestro` was opened read-only, for reading the SSOT.
- The fleet-wide `context:fork` / background-triage defect — this repo ships **zero** `SKILL.md`
  (verified: the payload is one agent definition plus python tooling), so that defect has no
  surface here and was not hunted.

## Acceptance

- [x] Delta table covering all five named axes plus every other axis the SSOT binds.
- [x] Each row carries rule → current state → required change → the floor of that change.
- [x] Findings state what was checked, not merely that things are clean.
- [x] Committed to this repo.
- [x] **F1 remediated** — all 3 legacy cards migrated `approval-tier: N` → `min-approval-requirement:`
      (`3 → user` ×2, `2 → manager` ×1). Per-card, reviewed, never a scripted sweep.
- [x] **F2 remediated** — `assignee:` added to all 3 cards.
- [x] **F3 filed** — `TRDD-3NQKQSQG` in `design/proposals/`, `min-approval-requirement: user`,
      carrying the PRRD skeleton + the G1.1 text. Routed to the MANAGER, who carries it to the
      USER; golden authorship is USER-only, so no agent may approve it.
- [x] **F4 filed** — `TRDD-5KZQUOBS` in `design/proposals/`,
      `min-approval-requirement: manager` (two independent §D3 signals: `.github/` and the
      release pipeline). Routed to the MANAGER, who may approve it.
- [ ] F5 — **not mine.** Escalated to the USER via the MANAGER; hold until the ruling returns.

## Approval log

- 2026-08-07T20:52:42+0200 — MANDATE issued by self (min-approval-requirement: none).
  Pre-approved: a Tier-0 self-mandate's issuer and receiver are the same agent. No approval
  request was sent.
