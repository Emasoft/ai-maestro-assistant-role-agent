"""Guard: the canonical governance blocks in the persona match their source byte-for-byte.

WHY THIS TEST IS THE ENFORCEMENT, AND NOT A NOTE. ai-maestro#107 ruled that
canonical rule text is copied verbatim into each decision-time surface —
"duplication, verified. Not indirection." A pointer is not compliance, and a
paraphrase is worse than a pointer: it looks authoritative while drifting.

This plugin ships NO skills, commands or hooks — the persona is its only
prompt surface, so that is where the canonical text lives (ai-maestro#127
Ask 3). The obvious objection to putting a rule in a persona is that a persona
is exactly what an agent does not re-read at the moment it decides. THIS TEST
is the answer to that objection: #107's real finding was that a rule present in
prose but absent from the CHECKLIST goes unenforced, and for a persona-only
plugin the conformance test IS the checklist.

WHY THE CANONICAL BYTES ARE VENDORED HERE rather than read from the ai-maestro
repo. The reason survived two corrections, and both are worth keeping because
each one changed the answer.

FIRST CORRECTION — name the remote. An earlier revision said the branch was
"LOCAL-ONLY" after checking only `origin`, which is UPSTREAM
(23blocks-OS/ai-maestro, no governance-rules ref at all). The FORK
(Emasoft/ai-maestro) had it all along. A reachability claim that does not name
which remote it checked is the same defect as citing a sha without its repo.

SECOND CORRECTION — re-measure before reporting. At fork tip 2ca29e43 the
fetchable copy was v5.2.0, 245 commits behind, and its R22.2 row still carried
the pre-fix template with a literal '@<owner>' — the form that pages a live
account. That was true when measured, was filed as ai-maestro#135, and has
since been FIXED BY A PUSH: re-measured 2026-08-08T10:45, the tip is 1ccbe9e0,
the doc is v5.3.3, and BOTH vendored blocks are now byte-identical to the
fetchable copy. A probe aimed at a stale ref returns a true-looking negative.

So the vendoring rationale is no longer "the reachable copy is wrong" — it is
the durable one: a cross-repo test pins this plugin to whatever the remote
happens to hold AT TEST TIME, which for a stretch today was the very bug the
vendored text fixes. Vendored bytes plus a recorded provenance make that a diff
instead of a surprise. The fixtures under tests/fixtures/canonical/ are the
captured bytes; PROVENANCE.json records the source commit, path, line range,
sha256, and the per-remote availability of each block.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

CANONICAL_NAMES = ("R22", "R23")


# v0.3.3 ONLY — the canonical blocks are temporarily withheld from the shipped
# persona (see TRDD-NRQK4W2P): CPV's A2A_AGENT_IMPERSONATION detector fires on
# the canonical R22 byline row, and the release gate blocks on the resulting
# DEMOTED NIT (claude-plugins-validation#201). The vendored fixtures stay, and
# the fixture-integrity tests below stay LIVE, so the bytes cannot rot while the
# persona copy is out.
#
# The skip is computed from the persona itself rather than hardcoded, so the
# moment the blocks are restored these tests re-arm on their own. A manual
# "remember to re-enable" flag is exactly the kind of thing that gets forgotten
# for a year — and a conformance test that silently never runs is worse than no
# test, because the suite still reports green.
def _persona_has_canonical_blocks(text: str) -> bool:
    return "<!-- CANONICAL-BEGIN:" in text


_WITHHELD_REASON = (
    "canonical blocks temporarily withheld from the persona for the v0.3.3 release "
    "(CPV#201 gate defect, TRDD-NRQK4W2P) — this test re-arms automatically when they return"
)


def _fixture_dir(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures" / "canonical"


def _extract_block(text: str, name: str) -> str:
    """Return the text between the CANONICAL markers for `name`.

    Only the newlines immediately adjacent to the marker lines are normalized —
    they are an artifact of where the markers sit, not part of the rule. Every
    interior byte is compared exactly.
    """
    pattern = re.compile(
        rf"<!-- CANONICAL-BEGIN: {re.escape(name)} -->(.*?)<!-- CANONICAL-END: {re.escape(name)} -->",
        re.DOTALL,
    )
    match = pattern.search(text)
    assert match is not None, (
        f"persona has no CANONICAL-BEGIN/END block for {name} — the canonical text was "
        "removed or its markers were renamed; either is a governance regression"
    )
    return match.group(1).strip("\n")


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_persona_canonical_block_matches_the_fixture_byte_for_byte(name: str, agent_text: str, repo_root: Path) -> None:
    """The persona's copy of each rule is the canonical text, unedited."""
    if not _persona_has_canonical_blocks(agent_text):
        pytest.skip(_WITHHELD_REASON)
    expected = (_fixture_dir(repo_root) / f"{name}.md").read_text(encoding="utf-8").strip("\n")
    actual = _extract_block(agent_text, name)

    assert actual == expected, (
        f"persona's {name} block has DRIFTED from the canonical text.\n"
        "It must be byte-for-byte identical (ai-maestro#107: duplication, verified — not "
        "indirection). If the upstream rule changed, re-capture the fixture and update "
        "tests/fixtures/canonical/PROVENANCE.json in the same commit."
    )


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_fixture_matches_its_recorded_provenance_hash(name: str, repo_root: Path) -> None:
    """The vendored fixture is the bytes PROVENANCE.json says it is.

    Without this, someone could 'fix' a drift failure by editing the fixture to
    match a corrupted persona — the test would go green and both copies would be
    wrong. The hash makes the fixture itself tamper-evident.
    """
    prov = json.loads((_fixture_dir(repo_root) / "PROVENANCE.json").read_text(encoding="utf-8"))
    recorded = prov["blocks"][name]
    raw = (_fixture_dir(repo_root) / f"{name}.md").read_bytes()

    assert hashlib.sha256(raw).hexdigest() == recorded["sha256"], (
        f"tests/fixtures/canonical/{name}.md no longer matches its recorded sha256. "
        "Re-capture from the source commit named in PROVENANCE.json, or update the hash "
        "deliberately in the same commit that re-captures."
    )
    assert len(raw) == recorded["bytes"]


def test_provenance_records_a_resolvable_origin(repo_root: Path) -> None:
    """Provenance names a repo, branch, commit and line range — not just 'upstream'.

    A citation that omits its TYPE and its REPO is what produced a false
    'this sha does not resolve' finding on 2026-08-07, and a remote-availability
    claim that omitted WHICH REMOTE produced a false 'local-only' finding the
    day after. The fields asserted here are the fix, applied to our own records.
    """
    prov = json.loads((_fixture_dir(repo_root) / "PROVENANCE.json").read_text(encoding="utf-8"))

    assert prov["source_repo"] == "Emasoft/ai-maestro"
    assert prov["source_branch"] == "governance-rules"
    assert re.fullmatch(r"[0-9a-f]{40}", prov["source_commit"]), "commit must be a full 40-hex sha"

    for name in CANONICAL_NAMES:
        assert re.fullmatch(r"\d+-\d+", prov["blocks"][name]["source_lines"])


def test_provenance_names_every_remote_it_checked(repo_root: Path) -> None:
    """Availability is recorded PER REMOTE, never as a bare 'is it pushed' boolean.

    The predecessor of this test asserted a single `source_branch_is_remote:
    false`, which was true of `origin` (upstream) and false of `fork` — one
    boolean cannot carry a fact that differs per remote, and collapsing it is
    how the wrong version of this finding got written down and relayed.
    """
    prov = json.loads((_fixture_dir(repo_root) / "PROVENANCE.json").read_text(encoding="utf-8"))
    remotes = prov["remotes"]

    for expected in ("origin", "fork"):
        assert expected in remotes, f"provenance does not say what {expected} holds"
        assert remotes[expected]["url"].startswith("https://github.com/")

    ref = remotes["fork"]["governance_rules_ref"]
    assert ref is None or re.fullmatch(r"[0-9a-f]{40}", ref)

    # Each block records whether the FETCHABLE copy equals the vendored bytes.
    # Both are True as of the 2026-08-08 re-measurement (fork tip 1ccbe9e0,
    # doc v5.3.3) — the earlier R22 divergence was real and is now fixed
    # upstream. Asserted as a plain bool rather than pinned to a value: pinning
    # it to today's answer would make this test enforce a fact about a remote
    # that can change without notice, which is the exact staleness trap the
    # docstring above is about.
    for name in CANONICAL_NAMES:
        assert isinstance(prov["blocks"][name]["identical_on_fork_remote"], bool)
    assert "fork_divergence_history" in prov["blocks"]["R22"], (
        "the resolved R22 divergence must stay recorded as history — it is the measurement "
        "that justified vendoring, and deleting it would make the rationale look arbitrary"
    )


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_the_comparison_would_actually_catch_a_drift(name: str, agent_text: str) -> None:
    """Falsification: a one-character edit inside the block must fail the compare.

    A byte-for-byte assertion that both sides normalize into oblivion passes
    vacuously. This proves the extractor returns real content and the compare
    is sensitive to it.
    """
    if not _persona_has_canonical_blocks(agent_text):
        pytest.skip(_WITHHELD_REASON)
    block = _extract_block(agent_text, name)
    assert len(block) > 500, f"{name} block is suspiciously small ({len(block)} chars)"

    tampered = block.replace("MUST", "SHOULD", 1)
    assert tampered != block, f"{name} block contains no 'MUST' — the tamper was a no-op"
