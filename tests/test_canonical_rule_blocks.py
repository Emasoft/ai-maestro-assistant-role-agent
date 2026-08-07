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
repo. Measured 2026-08-08: `git ls-remote --heads origin` on ai-maestro lists
no `governance-rules` ref — the branch carrying these rules is LOCAL-ONLY. A
test that read across repos would therefore pass on exactly one machine and
fail in CI and in every clone, which is worse than no test: it would report the
rule as enforced everywhere while enforcing it nowhere. The fixtures under
tests/fixtures/canonical/ are the captured bytes; PROVENANCE.json records the
source commit, path, line range and sha256 so a future sync is a diff, not an
archaeology exercise.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

CANONICAL_NAMES = ("R22", "R23")


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
    'this sha does not resolve' finding on 2026-08-07; the fields below are the
    fix, applied to our own records.
    """
    prov = json.loads((_fixture_dir(repo_root) / "PROVENANCE.json").read_text(encoding="utf-8"))

    assert prov["source_repo"] == "Emasoft/ai-maestro"
    assert prov["source_branch"] == "governance-rules"
    assert re.fullmatch(r"[0-9a-f]{40}", prov["source_commit"]), "commit must be a full 40-hex sha"
    assert prov["source_branch_is_remote"] is False, (
        "if governance-rules has since been pushed, this test SHOULD fail — reading the "
        "canonical text across repos becomes possible and the vendoring rationale changes"
    )

    for name in CANONICAL_NAMES:
        assert re.fullmatch(r"\d+-\d+", prov["blocks"][name]["source_lines"])


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_the_comparison_would_actually_catch_a_drift(name: str, agent_text: str) -> None:
    """Falsification: a one-character edit inside the block must fail the compare.

    A byte-for-byte assertion that both sides normalize into oblivion passes
    vacuously. This proves the extractor returns real content and the compare
    is sensitive to it.
    """
    block = _extract_block(agent_text, name)
    assert len(block) > 500, f"{name} block is suspiciously small ({len(block)} chars)"

    tampered = block.replace("MUST", "SHOULD", 1)
    assert tampered != block, f"{name} block contains no 'MUST' — the tamper was a no-op"
