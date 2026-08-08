---
prrd-version: 1.0
updated: "2026-08-08T05:01:29+0200"
project: ai-maestro-assistant-role-agent
project-id: ai-maestro-assistant-role-agent
canonical-source: design/requirements/PRRD.md
mirrors: []
---

# Project Requirements & Rules

`ai-maestro-assistant-role-agent` is a Claude Code **role-plugin**: its entire shipped payload
is one agent persona (`agents/ai-maestro-assistant-role-agent-main-agent.md`) plus the release
tooling. It ships no skills, no commands, no hooks. These rules govern THIS project and override
general conventions where they conflict.

**Relationship to the ai-maestro project PRRD.** This plugin belongs to the ai-maestro project,
so ai-maestro's PRRD is intended to cover it. That PRRD **does not exist yet** — it is still an
open proposal (`ai-maestro` `design/proposals/…-61KLQT7N-bootstrap-the-ai-maestro-prrd.md`,
filed 2026-07-26). This document therefore stands in for it. **When the ai-maestro PRRD lands,
any rule here that duplicates one there MUST be deleted and cited instead, not kept in parallel**
— two copies of one rule drift, and the drift is invisible until one of them is wrong. That is
the same failure this project already hit with its own phrasing of R22 (`TRDD-4983GIZW`).

## §I. How to read this document

Rule citation form: `PRRD G<n>.<v>` or `PRRD S<n>.<v>`. Numbers are unique across BOTH tiers and
are never reused; the letter flips on promote/demote; the version bumps on a text edit. Full
spec: `~/.claude/rules/prrd-design-rules.md`.

Governance profile: the USER is the approver. Golden rules are USER-only. Silver rules are
MANAGER-mutable; with no MANAGER session for this repo, the USER acts as one.

## 🥇 GOLDEN — set by the USER (immutable to every agent, MANAGER included)

- **G1.1** — Every agent that writes to GitHub from this plugin — issue, issue comment, PR, PR
  comment, PR review, discussion, release note — MUST begin the body with a one-line
  self-identification of which agent / role / plugin authored it, because every AI Maestro agent
  on a host shares the single human-owner GitHub identity. The line carries **no `@`**: a byline
  is a TEMPLATE, it is copied out of whatever code span protects it, and in prose any `@word`
  linkifies and pages a live account. Naming the author in plain words identifies them exactly
  as well; the `@` only adds a notification. Commit messages MUST carry an
  `Agent: ai-maestro-assistant-role-agent` trailer. This mirrors ecosystem rule R22, whose
  canonical text is reproduced verbatim in the persona.

## 🥈 SILVER — MANAGER-mutable

- **S2.1** — Every TRDD in this repo carries `min-approval-requirement:`. The deprecated
  `approval-tier:` is decode-only on legacy cards and is never written on a new one; legacy
  cards migrate on next touch, never in a mass rewrite, and a purely mechanical migration must
  not bump `updated:` (the board sorts on it).

- **S3.1** — Every TRDD carries `assignee:`. It is the only field the multi-agent board reads
  for assignment; `current-owner:` does not substitute for it.

- **S4.1** — Canonical governance text reproduced in this plugin is **vendored**, never fetched
  across repos at test time, and lives between `CANONICAL-BEGIN/END` markers with a
  byte-for-byte conformance test plus a sha256-pinned fixture. The deciding question is not
  whether an upstream copy is reachable but **which copy you would reach**: measured 2026-08-08,
  the only fetchable copy of R22 still carried the `@<owner>` byline that pages a live account.
  A fixture pin is mandatory because the obvious way to green a drift failure is to edit the
  fixture to match a corrupted persona.

- **S5.1** — The persona word budget measures **authored** prose only; canonical blocks are
  excluded. Counting them would make every upstream rule edit a spurious budget failure whose
  only available remedy is deleting authored guidance, and would put a standing incentive on
  trimming the canonical copy — the exact drift S4.1 exists to prevent.

- **S6.1** — A guard that scans for shipped defects scans the **tracked** tree, so a new file is
  invisible to it until staged. Stage before trusting a green run. Guards must also strip the
  forms where the pattern is inert (markdown code spans and fences; whole-line YAML comments) —
  a guard that reddens on correct writing gets deleted, and an ignored guard protects nothing.

- **S7.1** — The release pipeline is CPV's canonical pipeline, kept current rather than forked.
  Pipeline defects are filed on the CPV repo; this repo does not carry local divergence except
  what `.claude-plugin/plugin.json` declares under `cpv.pipeline.intentional_divergence`.
