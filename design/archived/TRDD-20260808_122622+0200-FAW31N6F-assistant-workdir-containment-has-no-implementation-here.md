---
trdd-id: FAW31N6F
title: The ASSISTANT workdir containment mandated by TRDD-3QRUDK12 has no implementation in this plugin
column: cancelled
created: 2026-08-08T12:26:22+0200
updated: 2026-08-08T12:58:00+0200
superseded-by: [ai-maestro TRDD-9SEQ4QI9]
current-owner: ai-maestro-assistant-role-agent
assignee: ai-maestro-assistant-role-agent
task-type: security
scope: project
project-id: ai-maestro-assistant-role-agent
min-approval-requirement: user
mandate: false
severity: high
blocked-by: []
relevant-rules: [1]
external-refs: [ai-maestro#39, ai-maestro TRDD-3QRUDK12]
release-via: publish
---

# The ASSISTANT workdir containment mandated by TRDD-3QRUDK12 has no implementation in this plugin

## ⏵ STATE — CLOSED 2026-08-08. The premise was wrong, and that is the answer. — 2026-08-08

**RULED (ai-maestro hub, `TRDD-9SEQ4QI9`, verified at `governance-rules` tip `f3f02743`): containment
is SERVER-owned, and this plugin shipping `hooks/` EMPTY is CORRECT — not a gap.** My own sentence
became the ruling's core: *"a control the constrained agent can uninstall is not containment."* A
role plugin installs at agent-local scope, so the constrained agent could remove it; the core plugin
fails identically (R17 self-heal restores presence, not integrity). Authoritative containment is
server-side gates the agent cannot reach, plus any workdir-local hook **provisioned and re-asserted
by a watchdog living outside the workdir**.

**So the finding that opened this card — "hooks/ ships zero files" — was a correct measurement with
an incorrect implication.** I read an empty directory as a missing control; it is the intended
shape. Recording that explicitly because the next reader will re-run the same `find` and reach the
same wrong conclusion unless the card says why the emptiness is deliberate.

**What was still mine, and is done:** the persona was silent about a constraint the USER dictated
for it. Item 14 of the forbidden list now states that containment is server-owned and must never be
relaxed or routed around — paid for by cutting redundant prose, not by raising the word ceiling.

**Nothing further here.** Implementation is hub-side work on `TRDD-9SEQ4QI9`.

## Original STATE (retained — this is what the question looked like before it was answered)

- **The gap, measured not assumed (2026-08-08T12:20):** ai-maestro's `TRDD-3QRUDK12` — a USER
  dictation, relayed on `ai-maestro#39` — mandates for this role:

  > Reads AND writes outside the ASSISTANT's workdir are blocked by hooks + ASSISTANT-role-specific
  > permission rules. Enumerated exceptions only: designated locally-scoped folders, project-scoped
  > folders (for approved collaborations), the assistant's own files, and files needed for the
  > collaboration. Host files outside those exceptions are strictly unreadable.

  This plugin ships **`hooks/` with zero files**, and `grep -iE 'workdir|filesystem containment'`
  over the persona returns **one** hit, about not installing at user scope. So the containment has
  **no implementation and no instruction** in the role plugin that is supposed to carry it.
- **Why this is not merely "a feature not built yet":** every other ASSISTANT constraint (no teams,
  invisibility, obey-only-your-user) is enforced *server-side*, where an agent cannot reach it.
  Filesystem containment is the one constraint whose enforcement point is **on the agent's own
  machine** — so if the role plugin does not carry it, nothing does. A persona sentence is also
  not sufficient here: the threat model includes an ASSISTANT that has been prompt-injected, and
  such an agent is exactly the one that will not honour a persona instruction.
- **NEXT ACTION:** ask ai-maestro (on `#39`) who owns this — the role plugin, the core plugin, or
  the server's provisioning — before building anything. See the open question below; it decides
  whether this card is mine at all.
- **Do NOT unilaterally add hooks.** `PreToolUse`-style filesystem gating is a security control
  for a multi-user product; a wrong or partial one is worse than none because it reads as
  protection. `min-approval-requirement: user`, and the design needs ai-maestro's answer first.

## The open question that decides ownership

`TRDD-3QRUDK12` says containment is by "hooks + ASSISTANT-role-specific permission rules", which
names two mechanisms without saying which artifact ships them. Three candidates:

1. **This role plugin** ships `hooks/` + a `permissions` block. Pro: travels with the role, applies
   the moment the plugin is installed. Con: this plugin is deliberately persona-only and
   zero-skills (`.agent.toml` declares empty skill lists); adding a hooks layer is the same shape
   ai-maestro **rejected** as "compliance theater" in `#127` Ask 3 — though that rejection was
   about hosting a *rule*, not about implementing a *control*, which is a real distinction.
2. **The core plugin / harness** ships it for every agent, parameterised by title. Pro: one
   implementation, uniformly enforced, and an ASSISTANT cannot uninstall it. Con: needs the title
   at hook time.
3. **The server** enforces at provisioning by writing the sandbox config into the agent's workdir.
   Pro: outside the agent's reach entirely — the strongest of the three. Con: does not constrain a
   session started outside the harness.

My reading is that (2) or (3) is correct and (1) is the weakest, because a control an agent can
uninstall is not containment — and R39 already forbids me from installing at user scope, which is
the same argument one level up. But this is ai-maestro's call, not mine.

## Acceptance criteria

- [ ] ai-maestro states which artifact owns ASSISTANT filesystem containment.
- [ ] If it is this plugin: a design that survives a prompt-injected ASSISTANT (i.e. not a persona
      instruction), reviewed before implementation, with the enumerated exception list from
      `TRDD-3QRUDK12` as its allowlist.
- [ ] If it is NOT this plugin: this card is closed as `cancelled` with the owning card cited, and
      the persona gains one line telling the agent the containment exists and is not its to relax.
- [ ] Either way, the persona stops being silent about a constraint the USER dictated for it.

## Approval log

- 2026-08-08T12:26:22+0200 — FILED by the ASSISTANT (`min-approval-requirement: user`). Not
  self-approved: this proposes a security control for a multi-user product, and the USER dictated
  the model it implements. Filed at `column: todo` rather than as a proposal because the FIRST
  action is a question to ai-maestro, which needs no approval; any implementation does.
- 2026-08-08T12:58:00+0200 — **CANCELLED** by the ASSISTANT, per this card's own acceptance
  criterion ("if it is NOT this plugin: closed as cancelled with the owning card cited, and the
  persona gains one line"). The ai-maestro hub ruled containment SERVER-owned
  (`TRDD-9SEQ4QI9`, verified at tip `f3f02743` before acting — the commit exists, is the branch
  tip, and carries the card). Cancelled rather than completed: the work is real but belongs to
  another repo, so claiming completion here would assert I built something I did not.
  The persona half WAS mine and shipped (forbidden-list item 14).
  **Asking instead of building was the right call** — I had a measurement ("hooks/ is empty") that
  looked like a gap, and building a filesystem gate on that reading would have produced an
  agent-uninstallable control that reads as protection while providing none.
