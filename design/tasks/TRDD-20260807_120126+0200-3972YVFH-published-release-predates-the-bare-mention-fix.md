---
trdd-id: 3972YVFH
title: The published release predates the bare-mention fix and still pages a real organization
column: complete
created: 2026-08-07T12:01:26+0200
updated: 2026-08-07T12:01:26+0200
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: bugfix
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: user
severity: high
blocked-by: []
external-refs: [ai-maestro#109, ai-maestro#127, ai-maestro-assistant-role-agent#1]
implementation-commits: [0b87998, a6e1e48]
release-via: publish
---

# The published release predates the bare-mention fix and still pages a real organization

## ⏵ STATE — READ THIS FIRST ON RESUME (authoritative; supersedes the body) — 2026-08-07

- **The code fix is DONE and committed.** `0b87998` (persona byline + explicit prohibition) and
  `a6e1e48` (`tests/test_no_bare_github_mentions.py`, guarding that no shipped markdown carries a
  bare mention in prose, fenced and inline code stripped before scanning).
- **The fix is NOT delivered.** `git rev-list --left-right --count HEAD...origin/main` → **`2 0`**.
  The published release is **v0.3.2 (2026-07-23)**, which **predates both commits**.
- **Consequence, stated plainly:** every install from the marketplace today still carries the byline
  that names the repo owner with a live handle. An ASSISTANT that copies it verbatim into an issue
  body notifies a real organization on every post. This is the harm ai-maestro#109 is about, still
  live in the published artifact.
- **BLOCKED ON: the USER's delivery decision.** `complete → publish` is a NON-EXEMPT transition and
  this is the owner's call, not the agent's. Disclosed publicly on
  `ai-maestro-assistant-role-agent#1`: mark this plugin **fixed-in-tree, NOT fixed-in-release**.
- **NEXT ACTION:** on the USER's go — `git push origin main`, bump to v0.3.3, run the publish
  pipeline, confirm the release carries `0b87998`.

## What was wrong

The persona's recommended self-identification byline read `(via the shared <handle> identity)` with
a live handle. Agents copied it verbatim into GitHub prose, where any `@word` outside a code span
renders as a user mention — and the short generic handles are all real accounts.

## What was fixed, and the part that generalizes

The byline now names the role in plain words, and a separate paragraph states the prohibition
outright **with its reason**, so the rule survives an edit that only sees the byline. The reason
matters more than the substitution: **substituting a different placeholder is not a fix**, because
any `@word` outside a code block notifies. Backticks are the escape hatch for the cases where a
literal `@` is unavoidable — action pins, URLs, emails — since GitHub does not notify inside code.

**Backticks protect prose but do NOT protect a template**, because the reader copies what is inside
them. A template is only safe if its literal form is harmless. That is why the fix removes the `@`
rather than re-wrapping it.

## Verification already done

- Zero bare mentions remain in the persona's prose (fenced and inline code stripped before scanning).
- README's two occurrences are inside fenced blocks and do not notify.
- 90 tests pass.
- `tests/test_no_bare_github_mentions.py` guards every shipped markdown file against regression.

## Acceptance criteria

- [x] Persona byline carries no `@`.
- [x] Prohibition stated with its reason, not just the substitution.
- [x] Regression guard shipped as a test.
- [ ] **Commits pushed to `origin/main`.**
- [ ] **Release cut that contains `0b87998`** — until then the published artifact is still broken.
