---
trdd-id: 4E1P2A1T
title: design_human_review visual-artifact duty for the ASSISTANT role (PRRD G7.1)
column: design_ai_review
created: 2026-08-25T13:58:21+0200
updated: 2026-08-25T17:05:00+0200
current-owner: main-claude
task-type: feature
release-via: publish
min-approval-requirement: none
---

# design_human_review visual-artifact duty for the ASSISTANT role (PRRD G7.1)

## The ask

Per ai-maestro 3-pillars spec 3.0.0 (kanban 17 → 22 columns), the new
`design_human_review` column is where a human reviews a card's DESIGN. When the card
includes a UI design (web, TUI or native), a VISUAL ARTIFACT must be generated so the
human can evaluate the mockup, annotate elements, and have those annotations recorded.
ai-maestro PRRD **G7.1** delegates that artifact duty to the MANAGER for MAESTRO users
and **to the ASSISTANT for ordinary non-MAESTRO users** — i.e. to the persona this repo
ships. The capability does not exist yet anywhere: it is a ratified requirement with no
implementation (a feature ask, not a process to follow today). The column is skipped
entirely when min-approval-requirement is `none`.

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-25 17:05

DESIGN PASS DONE (USER directive via HUB 2026-08-25: "a card that can move must
move"). The design is the `## Design` section below; column advanced
`design → design_ai_review`. **NEXT ACTION:** AI-review the Design section (a fork
reviewer); on pass → `todo` (design_human_review SKIPPED — min-approval-requirement
is none), then verify_assumptions → plan → dev per the 22-column flow.

Provenance (verified 2026-08-25, first-hand): `governance-rules` head `c8b0e9cb`,
G7.1 at `design/requirements/PRRD.md` line 108 — artifact duty delegated "to the
ASSISTANT for ordinary non-MAESTRO USERS"; the column is skipped when the approval
level is `none`.

## Design (2026-08-25 design pass — the spec `dev` must implement)

**Change:** one new bullet in the shipped persona
(`agents/ai-maestro-assistant-role-agent-main-agent.md`), placed under
`### Planning capability`, directly after the kanban bullet ("Be aware of, and
inherit, your user's kanban tasks…"). Text (≈75 words, final wording may be
tightened at dev time but must keep the bolded lead, the G7.1 cite, the
annotate-and-record duty, and the skip-on-none clause):

> - **Generate the visual artifact for `design_human_review` (PRRD G7.1).** When a
>   card whose design includes a UI (web, TUI, or native) reaches
>   `design_human_review`, render the mockup as a visual artifact your user can
>   open, inspect, and annotate (the Artifact tool with comment threads is the
>   default substrate), then record every annotation back onto the card before the
>   review concludes. This duty does not arise when the card's
>   `min-approval-requirement:` is `none` — that column is skipped entirely.

**Budget (hard constraint):** authored words are 4981/5000
(`test_agent_body_stays_within_its_word_budget`; canonical blocks excluded). The
addition is PAID FOR by deleting example 3 in `## Examples` (the
MANAGER-pings-without-permission example, ≈110 words incl. tags): its refusal shape
duplicates example 2 and its R39.9 content is fully covered by the "MANAGER
channel" section. Constraints verified against `tests/test_agent_definition.py`:
≥3 examples must remain (4 → 3 ✓); every remaining example keeps its `user:` turn,
`assistant:` turn and `<commentary>` (untouched ✓); net word delta ≈ −35 keeps the
count inside [3000, 5000] ✓. Do NOT delete commentary blocks (test-mandated) and do
NOT move the ceiling.

**Acceptance criteria:**
- [ ] Persona carries the new G7.1 bullet under Planning capability.
- [ ] Example 3 removed; exactly 3 well-formed examples remain.
- [ ] Full test suite green (incl. word budget, example well-formedness, keyword guards).
- [ ] Released via `publish.py` (release-via: publish); CI green on the pushed commit.

**Derived tasks (depth-1, per TRDD rules):**
- EHT: add a keyword-guard test asserting the persona states the G7.1
  visual-artifact duty (mirrors the existing prohibition-keyword tests), so a later
  trim can't silently drop it.
- EHT: sweep repo docs/README for example-count references ("four examples" etc.)
  after the deletion (check-all-files-after-breaking-change).

## Approval log

- 2026-08-25T13:58:21+0200 — Authored directly as Tier-0 in-scope intake (feature ask
  for this repo's own persona), parked at `backburner`, under the USER delegation of
  2026-08-25. No approval needed to queue; implementation will need its own design pass.

## Notes and lessons learned
