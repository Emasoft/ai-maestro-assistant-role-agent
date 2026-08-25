---
trdd-id: 4E1P2A1T
title: design_human_review visual-artifact duty for the ASSISTANT role (PRRD G7.1)
column: backburner
created: 2026-08-25T13:58:21+0200
updated: 2026-08-25T13:58:21+0200
current-owner: main-claude
task-type: feature
release-via: publish
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

## Why backburner, not todo

The governing spec is **unpublished**: it lives on ai-maestro branch `governance-rules`,
which was 282 commits ahead of its remote as of 2026-08-23 (peer session
`ai-maestro-b9`, self-corrected notification; published state was 2026-08-21). Nothing
here can be verified against a fetchable SSOT, so this card queues the work without
pretending the requirement is actionable. Provenance is the peer notification plus its
correction (spec repairs 3P-KAN-20/-10/-21, repair commit cited as 928c96b3 —
unverifiable from this repo, treat as hearsay until the branch is pushed).

**Activate (move to `todo`) when** the 3-pillars 3.0.0 spec and ai-maestro PRRD G7.1
are actually published and fetchable; re-verify the G7.1 text first-hand then, and only
then design what the ASSISTANT persona must state or do about visual-artifact
generation.

## Approval log

- 2026-08-25T13:58:21+0200 — Authored directly as Tier-0 in-scope intake (feature ask
  for this repo's own persona), parked at `backburner`, under the USER delegation of
  2026-08-25. No approval needed to queue; implementation will need its own design pass.

## Notes and lessons learned
