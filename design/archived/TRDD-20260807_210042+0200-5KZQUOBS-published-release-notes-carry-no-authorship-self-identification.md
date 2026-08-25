---
trdd-id: 5KZQUOBS
title: Published release notes carry no authorship self-identification line
column: complete
created: 2026-08-07T21:00:42+0200
updated: 2026-08-08T00:06:32+0200
implementation-commits: []
approved: true
approval-judge: ai-maestro (the server session)
approval-datetime: 2026-08-08T00:03:49+0200
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

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-08

- **`column: complete`. The code work is DONE and every acceptance box is ticked.** The step is
  in `release.yml`, the guard is extended to workflow files and falsified against a real
  injection, and both body paths are dry-run.
- **It has NOT shipped, and that is correct.** `release-via: publish`, so the terminal is
  `published` — but `complete → publish` is NON-EXEMPT and is gated on the USER's F5 ruling
  (`TRDD-3972YVFH`). Nothing here cuts a release; the fix rides whichever release the USER
  authorizes.
- **NEXT ACTION: none by me.** On the USER's go, this lands with v0.3.3 alongside `TRDD-3972YVFH`
  and F6. Verify afterwards that the published release body actually carries the byline — the
  pipeline is only proven by a real run.

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

- [x] MANAGER rules on the change. **APPROVED** 2026-08-08 — see the Approval log.
- [x] The step lands in `.github/workflows/release.yml` after the fallback chain.
- [x] The line contains no `@`, asserted by the guard **extended to workflow files**. The
      extension strips whole-line YAML comments first — mandatory, because three tracked
      workflow comments legitimately carry a word-boundary `@` (`PINNED to @v3.1.0` ×2 and this
      guard's own rationale), and a guard that reddens on correct writing gets deleted. Trailing
      `# v6.0.3` comments are left in place: their `@` is glued to a preceding character and the
      pattern already exempts that, whereas stripping to end-of-line from any `#` would cut
      through `#` inside quoted shell strings and hide real emitted prose.
- [x] The extension is **falsified, not merely green**: injecting `@owner` into the real
      `release.yml` byline made the corpus test FAIL with
      `.github/workflows/release.yml: @owner`, then the file was restored and re-verified. A
      clean scan whose stripper silently ate every line would otherwise be indistinguishable
      from a correct one.
- [x] Dry run over **both** body paths: section-found (`## [0.3.3] — …`) and fallback (git-log
      lines). Both emit the byline, then a blank line, then the changelog body; `changelog.body`
      is consumed by the `mv` and leaves no stray file.
- [x] Verified NOT done: no release cut, no tag, no push. `CHANGELOG.md` and `cliff.toml`
      untouched.

## Approval log

- 2026-08-07T21:00:42+0200 — FILED as a proposal by the ASSISTANT
  (min-approval-requirement: manager). Routed to the MANAGER. Floor is manager on two
  independent §D3 signals: `.github/` and the release pipeline.
- 2026-08-08T00:03:49+0200 — APPROVED by ai-maestro (the server session),
  min-approval-requirement: manager, under the USER's governance-readiness delegation.
  Two conditions attached, both already this card's stated intent: (1) the prepended line
  follows the G1.1 no-`@` discipline — plain words, no handle anywhere, including inside the
  workflow YAML; (2) the change lands in the pipeline and cuts NO release, which stays the
  USER's F5 ruling to exercise. Promoted `proposal → planned` and moved to `design/tasks/`.
