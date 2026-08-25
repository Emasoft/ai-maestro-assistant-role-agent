---
trdd-id: 4E1P2A1T
title: design_human_review visual-artifact duty for the ASSISTANT role (PRRD G7.1)
column: design
created: 2026-08-25T13:58:21+0200
updated: 2026-08-25T14:20:00+0200
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

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-25

Provenance is now VERIFIED, not hearsay: `governance-rules` head `c8b0e9cb`
(2026-08-23T15:10:43Z) read first-hand via `gh api`, and the G7.1 text fetched from
that blob (`design/requirements/PRRD.md` line 108) matches the peer's summary — the
artifact-creation procedure is "usually delegated to the MANAGER agent … or to the
ASSISTANT for ordinary non-MAESTRO USERS", and the column is skipped when the approval
level is `none`. The card was authored 2026-08-25 (after the 3P-KAN-21 grandfather
line), so 3.0.0 semantics apply: approved (Tier-0 intake, `min-approval-requirement:
none`) + undesigned ⇒ `column: design`, not `backburner`.

**NEXT ACTION (one step):** run the design pass — decide what the shipped ASSISTANT
persona must state about generating a visual artifact the human can annotate (Artifact tool +
comment threads are a plausible substrate) when a UI-design card reaches
`design_human_review`, under the hard constraint that the persona is ~20 words below
its 5000-word ceiling (`test_agent_body_stays_within_its_word_budget`), so every
addition must be paid for by a deletion. Deliberately NOT done in the 2026-08-25
session: a persona edit made without review at the budget ceiling was judged out of scope for
"complete pending tasks" (a persona edit at the budget ceiling without review risks the
product) — the card is filed, verified, and correctly columned instead.

## Approval log

- 2026-08-25T13:58:21+0200 — Authored directly as Tier-0 in-scope intake (feature ask
  for this repo's own persona), parked at `backburner`, under the USER delegation of
  2026-08-25. No approval needed to queue; implementation will need its own design pass.

## Notes and lessons learned
