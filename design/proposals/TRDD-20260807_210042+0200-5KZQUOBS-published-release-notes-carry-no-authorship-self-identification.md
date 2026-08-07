---
trdd-id: 5KZQUOBS
title: Published release notes carry no authorship self-identification line
column: proposal
created: 2026-08-07T21:00:42+0200
updated: 2026-08-07T21:00:42+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: infra
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: manager
mandate: false
routed-via: manager
parent-trdd: 92LA26H1
severity: low
blocked-by: []
relevant-rules: []
external-refs: []
release-via: publish
---

# Published release notes carry no authorship self-identification line

## The gap

A GitHub **release note** is a GitHub-writing surface, and G1.1 covers it explicitly
(*"issue, issue comment, PR, PR comment, PR review, discussion, release note"*). This repo's
release body carries no self-identification line.

Verified in `.github/workflows/release.yml`: the `Generate changelog` step writes
`changelog.txt` from one of four sources — the matching `## [X.Y.Z] — DATE` section of
`CHANGELOG.md`, the whole `CHANGELOG.md` when no section matches, or a generated `git log` when
there is no changelog at all — and the publish step passes exactly that file through as the
body:

```
gh release edit   "$TAG" --notes-file changelog.txt --verify-tag
gh release create "$TAG" ... --notes-file changelog.txt --verify-tag
```

`CHANGELOG.md` is git-cliff output. It opens with the version heading and closes with the
git-cliff footer. No branch of the chain contributes an authorship line, so every release this
repo has ever cut is unattributed.

This is finding **F4** of `TRDD-92LA26H1`.

## Why this is a proposal and not a task I just do

Two independent §D3 signals put the floor at `manager`: the change is inside `.github/`, and it
is in the **release pipeline**. Either alone is sufficient. `complete → publish` and
`publish → published` are also NON-EXEMPT in `aimaestro-manager-approval-defaults` §Y.

I route it to the MANAGER, which under the USER's governance-readiness delegation may approve
it without a USER round-trip.

## The proposed change

One step in `.github/workflows/release.yml`, inserted after the fallback chain resolves and
before `changelog_file` is written to `$GITHUB_OUTPUT`. Prepending **after** the chain rather
than inside it means all four sources are covered by one edit, and a future fifth fallback
inherits it automatically instead of silently opting out:

```yaml
          # G1.1 — every GitHub-writing surface leads with who authored it.
          # A release note is such a surface. Prepended AFTER the fallback
          # chain so all four body sources are covered by one edit.
          # NO '@': this line is a template, it gets copied out of wherever
          # it sits, and any @word in prose linkifies and pages a live
          # account (TRDD-3972YVFH is that harm, still live in v0.3.2).
          {
            printf '_Released by the ASSISTANT role-plugin (via the shared repo-owner identity)._\n\n'
            cat changelog.txt
          } > changelog.body && mv changelog.body changelog.txt
```

Placement matters and is the whole design: the fallback chain has four exits, and prepending
inside it would need four edits, three of which a reviewer would have to notice were missing.

## What this proposal deliberately does NOT do

- **It does not cut a release.** `3972YVFH` — the live bare-mention harm — is escalated to the
  USER and is not mine to green-light. This card changes the pipeline only; whether and when
  the next release runs stays the USER's decision.
- **It does not touch `CHANGELOG.md` or `cliff.toml`.** The byline belongs to the release
  surface, not to the changelog, which is also read in-repo where no notification can occur.
- **It adds no `@`.** Naming the role in plain words identifies the author exactly as well.

## Acceptance criteria

- [ ] MANAGER rules on the change.
- [ ] If approved: the step lands in `.github/workflows/release.yml` after the fallback chain.
- [ ] The line contains no `@` — asserted by the existing bare-mention guard, extended to cover
      workflow files, since today that guard scans tracked **markdown** only and would not have
      caught this line at all.
- [ ] A dry run confirms the body carries the line ahead of the changelog section, for a tag
      whose section exists **and** for one whose section does not (the fallback path).

## Approval log

- 2026-08-07T21:00:42+0200 — FILED as a proposal by the ASSISTANT
  (min-approval-requirement: manager). Routed to the MANAGER. Floor is manager on two
  independent §D3 signals: `.github/` and the release pipeline.
