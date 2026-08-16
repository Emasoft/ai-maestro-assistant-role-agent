---
name: cpv-release-gate-blocks-on-demoted-nit
description: "CPV release gate exits non-zero on a demoted NIT even at CRITICAL=0 MAJOR=0 MINOR=0; the canonical R22 rule row trips A2A_AGENT_IMPERSONATION and made the plugin unreleasable. Fix is .cpv-audit-consent.json (CPV v5.5.0+), never editing the rule text."
ocd: 2026-08-16
lmd: 2026-08-16
metadata:
  node_type: memory
  type: project
  tier: component
publish-globally: false
---

# cpv-release-gate-blocks-on-demoted-nit


^ATOM-PA08-TP4R [desc: "A demoted NIT still exits 4 and blocks the canonical release gate; consent the reviewed false positive, never edit the rule text", keywords: demoted_NIT_blocks_release validator_exit_4_with_zero_critical A2A_AGENT_IMPERSONATION_on_a_rule_table_row cpv-audit-consent.json canonical_rule_text_trips_the_impersonation_detector release_gate_fails_at_CRITICAL=0, type: project, ocd: 2026-08-16, lmd: 2026-08-16]

CPV's canonical release gate fails on ANY validator exit 1-4, so a single DEMOTED NIT blocks a
tree at `CRITICAL=0 MAJOR=0 MINOR=0`. This repo hits it because the vendored canonical R22 rule
row DESCRIBES the impersonation it forbids, and `skillaudit`'s `A2A_AGENT_IMPERSONATION`
detector cannot tell a rule about spoofing from an attempt at it.

The supported fix (CPV **v5.5.0+**, issues #194/#201) is a consent registry at the plugin root,
`.cpv-audit-consent.json`:

    {"version": 1, "consents": [
      {"file": "<plugin-relative posix path>", "ruleId": "A2A_AGENT_IMPERSONATION",
       "lineSha256": "<sha256 of the FULL flagged line, stripped, read from disk>",
       "reason": "<why this is a reviewed false positive>"}]}

Measured 2026-08-16 on this repo: v5.5.0 exits **4** without it, **0** with it, and the finding
stays visible as `(demoted, consented)`. It is informed review, not suppression — only an
ALREADY-DEMOTED finding is consentable, the "prose IS the attack" family (prompt-inject, exfil,
secrets, decode-threats) can never be consented, and the sha256 is over the full line re-read
from disk, so any edit to that line invalidates the consent and the finding blocks again.

Two things that cost time and are easy to get wrong:
- The pinned CPV version is what matters, not the issue's CLOSED state. #201 was closed while
  this repo still pinned v3.1.0, which does not know what a consent registry is. Bump EVERY pin
  site together (here: `scripts/publish.py` x5, `.github/workflows/ci.yml`, `release.yml`) or CI
  disagrees with the local gate for a reason nobody finds.
- Verify WHICH line is flagged. The card asserted R22.2 for eight days; the detector actually
  fires on R22.4.

## Notes and lessons learned
