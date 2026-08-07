---
trdd-id: 3NQKQSQG
title: Adopt a PRRD for this plugin with G1.1 as its first golden rule
column: proposal
created: 2026-08-07T21:00:42+0200
updated: 2026-08-07T21:00:42+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: docs
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: user
mandate: false
routed-via: manager
parent-trdd: 92LA26H1
severity: medium
blocked-by: []
relevant-rules: []
external-refs: []
release-via: none
---

# Adopt a PRRD for this plugin with G1.1 as its first golden rule

## The gap

This repo has no `design/requirements/PRRD.md`. Verified by `find` over the whole tree
(excluding `.git/` and `.venv/`): zero matches for `PRRD*.md`. The project therefore has no
constitution, and the one golden rule the ai-maestro overlay says every project PRRD SHOULD
carry — **G1.1, GitHub authorship self-identification** — has nowhere to live.

This is finding **F3** of `TRDD-92LA26H1`.

## Why this is a proposal and not a task I just do

`aimaestro-prrd-governance` gives GOLDEN authorship to the **USER alone**: not the MANAGER, not
me. `prrd-edit.py` enforces it — a MANAGER golden edit is refused `403 — golden rules are
user-only`. The §D3 objective floor puts a golden-rule change at `user`, so this card is a
proposal by construction, never a mandate. Nothing in it is applied until the USER rules.

I route it to the MANAGER because R39.9 makes the MANAGER my only agent channel — I have no
team and therefore no CHIEF-OF-STAFF to funnel through. The MANAGER carries it to the USER;
it cannot approve this itself and has said so.

## What I am asking to be created

`design/requirements/PRRD.md`, git-tracked, never gitignored, with this content:

```markdown
# PRRD — ai-maestro-assistant-role-agent

project-id: ai-maestro-assistant-role-agent

## Golden rules (USER-set; immutable to every agent, MANAGER included)

- **G1.1** — Every agent that writes to GitHub from this plugin (issue, issue comment, PR, PR
  comment, PR review, discussion, release note) MUST begin the body with a one-line
  self-identification naming which agent/role/plugin authored it, because every AI Maestro
  agent on a host shares the single human-owner GitHub identity. The line carries NO `@`: a
  byline is a TEMPLATE, it is copied out of whatever code span protects it, and in prose any
  `@word` linkifies and pages a live account. Naming the author in plain words identifies them
  exactly as well; the `@` only adds a notification. Commit messages MUST carry an
  `Agent: ai-maestro-assistant-role-agent` trailer.

## Silver rules (MANAGER-mutable)

- **S2.1** — Every TRDD in this repo carries `min-approval-requirement:`. The deprecated
  `approval-tier:` is decode-only on legacy cards and is never written on a new one.
- **S3.1** — Every TRDD carries `assignee:`, because it is the only field the multi-agent
  board reads for assignment; `current-owner:` does not substitute for it.
```

Rule numbering follows the IND base: the number is globally unique across both tiers and is
never reused, the letter flips on promote/demote, the version bumps on a text edit.

## Why G1.1 specifically, and why golden

It is an anti-impersonation convention. Every agent on this host posts to GitHub as the same
human owner, so a reader cannot tell which agent wrote a comment unless the comment says so.
Golden — rather than silver — because the MANAGER must not be able to weaken it: an agent that
could relax its own attribution requirement is an agent that can post unattributably.

The no-`@` clause is not decoration. This exact byline previously shipped with a live handle
in it and paged a real organization from every agent that copied it verbatim; that is
`TRDD-3972YVFH`, still live in the published artifact today. G1.1 written **with** an `@`
would re-introduce the harm it exists to prevent, which is why the rule text names the
template-copying mechanism rather than merely saying "be careful".

## The two silver rules ride along for a reason

They are the durable form of `TRDD-92LA26H1` findings F1 and F2, which I have already
remediated in-tree (`0fdf4c6`). Without a written rule, the next card authored here reaches
for `approval-tier:` again and the fix decays. Silver, so the MANAGER can revise them as the
overlay evolves without a USER round-trip.

## Acceptance criteria

- [ ] USER rules on adopting a PRRD for this project.
- [ ] If adopted: `design/requirements/PRRD.md` created via `prrd-edit.py --user`, not by hand.
- [ ] G1.1 present as the first golden rule, its text carrying no `@` anywhere.
- [ ] S2.1 and S3.1 present as silver.
- [ ] `design/requirements/` confirmed NOT gitignored.

## Approval log

- 2026-08-07T21:00:42+0200 — FILED as a proposal by the ASSISTANT
  (min-approval-requirement: user). Routed to the MANAGER, which carries it to the USER;
  golden authorship is USER-only, so no agent may approve this card.
