# Changelog

_Released by the ASSISTANT role-plugin (via the shared owner gh auth)._

All notable changes to this project will be documented in this file.

## [0.4.0] — 2026-08-18

### Bug Fixes

- **publish:** Render release notes from explicit tag range — --current is blind when HEAD carries the dependency tag (a302857)
- **gate:** Consent the memory note that documents the false positive (TRDD-NRQK4W2P) (cc0b52e)
- **publish:** Restore atomic-push retry, real newlines, drop dead helper (TRDD-E0NETVRP, TRDD-ULD03IAG, TRDD-F8D1BH24) (7b4e8ba)

### Documentation

- Unblock TRDD-NRQK4W2P — CPV#201 closed 2026-08-15, blocked → dev (77ba992)
- Record 6be9eaf on TRDD-NRQK4W2P (7660aed)
- Add TRDD-E0NETVRP, TRDD-ULD03IAG, TRDD-I42GB55M, TRDD-F8D1BH24 — Phase-2 cards from the hub-ledgered Phase-1 audit (e96e1ec)
- **ci:** De-version the stale CPV-pin comments (TRDD-I42GB55M) (dba029c)
- Archive TRDD-E0NETVRP, TRDD-ULD03IAG, TRDD-I42GB55M, TRDD-F8D1BH24 → completed (f84e8d0)
- Record the completed state on the four archived Phase-2 cards (dffd3a9)

### Features

- **persona:** Restore the canonical R22/R23 blocks (TRDD-NRQK4W2P) (6be9eaf)

### Miscellaneous Tasks

- Track PROJECT-scope memory, and record how the CPV gate was cleared (40e15a6)
## [0.3.7] — 2026-08-15

### Bug Fixes

- Restore changelog history deleted by publish.py again (CPV#204, third occurrence) (66ef896)
- **docs:** Align transport claims with Claude Code 2.1.222-2.1.232 (bc1435e)
- **publish:** Stop changelog history loss and full-history release bodies (CPV#204, CPV#205) (0208c63)

### Documentation

- TRDD-1I4S7H44 -> complete; it shipped in v0.3.6 and sat open for three days (b65f6ef)
- Archive TRDD-3W9HE416 (GHCFG-001) — withdrawn by the janitor (352dee1)

### Miscellaneous Tasks

- Bump version to 0.3.7 (baf615c)

### Styling

- Ruff-format publish.py (mechanical, zero behavior change) (98dc59c)
## [0.3.6] — 2026-08-08

### Bug Fixes

- Restore the changelog history that publish.py deleted again (CPV#204, second occurrence) (b5d3e6f)
- **persona:** TRDD-1I4S7H44 D1 — a stuck ASSISTANT could not say so; the channel to the MANAGER is always open (1807231)

### Documentation

- TRDD-ZFC4QRBU — fleet check; my premise was wrong, and the sweep found live `@owner` templates (e37ff70)
- TRDD-ZFC4QRBU — population completed 10/10; my "unreachable" row was a wrong repo name (313a20e)

### Features

- **persona:** TRDD-1I4S7H44 — server-readiness; the role plugin was uninstallable by the agent it governs (bc253d4)

### Miscellaneous Tasks

- Bump version to 0.3.6 (1ba7391)
## [0.3.5] — 2026-08-08

### Bug Fixes

- Restore the changelog history the publish pipeline deleted, and put the byline where both release paths see it (6fab349)

### Documentation

- Hub ruled containment server-owned — FAW31N6F cancelled, and my spec-vendoring remedy was wrong (e7a4d05)

### Miscellaneous Tasks

- Bump version to 0.3.5 (b2f7cf5)
## [0.3.4] — 2026-08-08

### Bug Fixes

- Mirror the canonical byline tail, and record that I vendored from the subordinate source (d976c87)

### Documentation

- TRDD-FAW31N6F — the USER dictated a containment this plugin does not implement (1eb2f1b)
- TRDD-NRQK4W2P — define the restore by content, not by a version number (a11953e)

### Miscellaneous Tasks

- Bump version to 0.3.4 (f12bb25)
## [0.3.3] — 2026-08-08

### Bug Fixes

- Never emit @<name> in GitHub prose — the byline was paging a real org (0b87998)
- The comm-graph rules named one transport; Claude Code 2.1.224 added a second (5157ec1)
- Retract "the branch is local-only" — I never named which remote I checked (5d7ef29)
- Withhold the canonical blocks for v0.3.3 so the byline fix can finally ship (75d79b3)
- Backtick `@mentions` in generated release notes, or the fix announces itself by paging (36bf90d)

### Documentation

- Open the board — 3 TRDDs for the work that was tracked only in prose (67b4108)
- TRDD-F54QWQEV — Ask 2 was answered before I filed it; the gap is propagation, not spec (0845ce4)
- TRDD-92LA26H1 — conformance delta vs the governance SSOT, 4 non-conformant (ee08c2e)
- TRDD-92LA26H1 F1+F2 — migrate the 3 legacy cards off approval-tier (0fdf4c6)
- TRDD-92LA26H1 — retract a false claim; the cited SHAs all resolve (e200bc3)
- TRDD-92LA26H1 F3+F4 — file the two above-my-rung findings as proposals (4846e45)
- TRDD-92LA26H1 -> complete; the audit card was claiming work nobody was doing (71b48e2)
- Record the terminal-edit ruling in both cards' Approval logs (55efc6e)
- TRDD-3NQKQSQG — adopt a PRRD; G1.1 golden, seven silver (a66c428)
- TRDD-LZLDSQVY — the publish.py style question was the wrong question (d25e1bf)

### Features

- **release:** TRDD-5KZQUOBS — release notes now say which agent authored them (dfd3c62)
- **persona:** TRDD-4983GIZW + TRDD-F54QWQEV — canonical R22/R23 in the persona, enforced (afdcdd2)

### Miscellaneous Tasks

- Bump version to 0.3.3 (c61ef6a)

### Styling

- TRDD-LZLDSQVY — format the two unambiguous files; publish.py needs a human (930588c)

### Testing

- Guard that no shipped markdown carries a bare `@mention` in prose (a6e1e48)

### Build

- Migrate the pipeline to CPV canon v5.3.0 (TRDD-LZLDSQVY) (274c877)
- TRDD-LZLDSQVY — exempt vendored canon publish.py from ruff format (7386604)
## [0.3.2] — 2026-07-23

### Documentation

- Accurate README + persona-integrity guards (30ede7d)

### Miscellaneous Tasks

- Bump version to 0.3.2 (c19d6db)
## [0.3.1] — 2026-07-22

### Bug Fixes

- Make the governance guards actually able to fail (ef558b4)

### Miscellaneous Tasks

- Bump version to 0.3.1 (fa33b7a)
## [0.3.0] — 2026-07-22

### Bug Fixes

- Repair agent YAML frontmatter + gitignore coverage (109d89e)
- Clear validator findings on the new pipeline (b88fc2a)
- Make the cspell gate pass (would have failed CI red) (51168be)

### Features

- Author ai-maestro-assistant-role-agent role-plugin source (R39, quad-match, unpublished) (0b1e0d8)
- Rewrite ASSISTANT persona to R39.8/R39.9 authority model (v0.2.0) (e2fa6d4)
- Add R39.10 scoped collaboration expansion to ASSISTANT persona (v0.2.1) (2f12f94)
- Adopt the canonical CPV release pipeline (aa8e111)

### Miscellaneous Tasks

- Commit uv.lock (9ec904e)
- Gitignore .trashcan/ (migration matrix CHECK-33) (ee8657a)
- Bump version to 0.3.0 (a452bc6)

### Refactor

- 'MAESTRO agent' -> 'MANAGER' terminology (v0.2.2) (5c9d5de)

### Testing

- Guard the pipeline invariants this migration turned on (31da0e7)

### Build

- Migrate the canonical pipeline from CPV 2.162.0 to 3.1.0 (9b567ef)
---
*Generated by [git-cliff](https://git-cliff.org)*
