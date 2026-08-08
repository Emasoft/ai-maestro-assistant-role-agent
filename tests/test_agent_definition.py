"""Tests for the shipped main agent definition (agents/*-main-agent.md).

This role-plugin's ENTIRE payload is one agent markdown file, so these tests
are the plugin's functional test suite: if the frontmatter does not parse or
the persona loses a governance invariant, the plugin is broken in production.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

PLUGIN_NAME = "ai-maestro-assistant-role-agent"
AGENT_NAME = f"{PLUGIN_NAME}-main-agent"


def test_agent_file_exists_and_is_utf8(agent_path: Path) -> None:
    """The agent file named by the TOML profile exists and decodes as UTF-8."""
    assert agent_path.is_file(), f"missing agent definition: {agent_path}"
    agent_path.read_text(encoding="utf-8")


def test_the_shipped_agent_filename_is_exactly_the_expected_one(repo_root: Path) -> None:
    """agents/ holds exactly one agent, at the literal expected filename.

    Spelled out rather than composed from PLUGIN_NAME on purpose: AI Maestro's
    quad-match binds on this exact path, so a rename of BOTH the plugin
    constant and the file would otherwise slip through every other test here.
    """
    agents = sorted(p.name for p in (repo_root / "agents").glob("*.md"))
    assert agents == ["ai-maestro-assistant-role-agent-main-agent.md"]


def test_agent_frontmatter_parses_as_yaml(agent_frontmatter: dict[str, Any]) -> None:
    """Frontmatter parses with a real YAML parser.

    Regression guard for the v0.2.2 defect: 'description:' was a multi-line
    PLAIN scalar containing a bare ': ', which YAML forbids, so safe_load
    raised ScannerError and Claude Code could not load the agent at all. The
    fix was a folded block scalar ('>-'); this test fails if it is reverted.
    """
    assert isinstance(agent_frontmatter, dict)
    assert agent_frontmatter  # non-empty mapping


def test_agent_frontmatter_has_required_keys(agent_frontmatter: dict[str, Any]) -> None:
    """Frontmatter carries the keys Claude Code needs to register an agent."""
    for key in ("name", "description"):
        assert key in agent_frontmatter, f"agent frontmatter is missing '{key}'"


def test_agent_name_matches_filename_stem(agent_frontmatter: dict[str, Any], agent_path: Path) -> None:
    """Frontmatter 'name' equals the filename stem — the dispatch key."""
    assert agent_frontmatter["name"] == agent_path.stem == AGENT_NAME


def test_agent_description_is_substantive(agent_frontmatter: dict[str, Any]) -> None:
    """The description is long enough to actually trigger delegation."""
    description = agent_frontmatter["description"]
    assert isinstance(description, str)
    assert len(description.split()) >= 20, "description too short to route on"


def test_agent_declares_a_known_model(agent_frontmatter: dict[str, Any]) -> None:
    """If a model is pinned it is one Claude Code accepts."""
    model = agent_frontmatter.get("model")
    if model is not None:
        assert model in {"opus", "sonnet", "haiku", "inherit"}, f"unknown model '{model}'"


def test_every_example_block_is_well_formed(agent_body: str) -> None:
    """Each <example> has a user turn, an assistant turn, and a commentary.

    Claude Code's routing quality depends on examples showing the TRIGGERING
    user turn; an example that opens with only 'assistant:' teaches nothing
    about when to select this agent.
    """
    examples = re.findall(r"<example>(.*?)</example>", agent_body, re.DOTALL)
    assert len(examples) >= 3, "an agent this authority-sensitive needs >= 3 examples"
    for index, block in enumerate(examples, start=1):
        assert re.search(r"^user:", block, re.MULTILINE), f"example {index} has no 'user:' turn"
        assert re.search(r"^assistant:", block, re.MULTILINE), f"example {index} has no 'assistant:' turn"
        assert "<commentary>" in block, f"example {index} has no <commentary> rationale"


# A prohibition is a NEGATION applied to a VERB applied to an OBJECT. Asserting
# only that the words appear somewhere is worthless: a body rewritten to GRANT
# the power keeps every one of those words. So each pattern below pins all three
# parts in order, and `[^.]` keeps a match inside a single sentence (it spans the
# newlines of a wrapped line but never runs past the full stop into the next
# claim). Verified by deletion: removing the prohibition makes these fail.
_NEGATION = r"(?:must not|cannot|can't|may not|no authority to|never)"
# Spelled as whole words rather than a truncated stem plus `\w*`: cspell runs
# over this source in CI and rejects a stem as an unknown word, turning Lint red.
_CREATE = r"(?:create|creates|creating|creation)"

_REQUIRED_PROHIBITIONS = {
    "no agent creation": rf"{_NEGATION}[^.]{{0,80}}{_CREATE}[^.]{{0,80}}agent",
    "no team creation": rf"{_NEGATION}[^.]{{0,80}}{_CREATE}[^.]{{0,80}}team",
    "no sudo password": rf"{_NEGATION}[^.]{{0,80}}sudo",
}


def test_agent_body_states_the_forbidden_actions(agent_body: str) -> None:
    """The persona still carries a FORBIDDEN section and cites R39 and TRDDs.

    These are the invariants that keep an ASSISTANT from acting like a
    MANAGER; losing them during an edit would silently widen its authority.
    The prohibitions themselves are asserted as negations, not as keywords —
    see test_agent_body_forbids_creating_agents_or_teams.
    """
    lowered = agent_body.lower()
    assert re.search(r"^#+ +forbidden\b", lowered, re.MULTILINE), "no FORBIDDEN section heading"
    assert "r39" in lowered, "agent body no longer cites the governing rule R39"
    assert "trdd" in lowered, "agent body no longer mentions TRDDs (its approval scope)"


def test_agent_body_forbids_creating_agents_or_teams(agent_body: str) -> None:
    """The single most important prohibition survives: no agent/team creation.

    Each check requires a negation, the verb and the object in ONE sentence,
    so the test fails the moment the prohibition is softened or deleted —
    unlike a keyword scan, which a body that GRANTS the power would still pass.
    """
    lowered = agent_body.lower()
    for label, pattern in _REQUIRED_PROHIBITIONS.items():
        assert re.search(pattern, lowered), f"persona no longer states the '{label}' prohibition"


def test_agent_body_has_no_absolute_home_paths(agent_text: str) -> None:
    """No developer-machine absolute path leaks into the shipped persona."""
    for leak in ("/Users/", "/home/", "C:\\Users\\"):
        assert leak not in agent_text, f"agent file leaks an absolute path prefix '{leak}'"


# The persona is loaded IN FULL on every dispatch of this agent, so its size is a
# standing per-invocation cost — CPV emits a "body very long" advisory that no
# gate enforces. This window guards BOTH directions: the ceiling catches
# unbounded growth (each edit that piles on more prose is paid forever); the
# floor catches a mass deletion that a keyword check would miss (a body gutted to
# a stub still contains "r39", "sudo", etc.). The window is deliberately wide —
# it fails only on a change large enough to warrant a human look, not on ordinary
# wording edits. Numbers are a budget, not the current length; widen consciously.
_WORD_FLOOR = 3000
_WORD_CEILING = 5000


_CANONICAL_BLOCK_RE = re.compile(r"<!-- CANONICAL-BEGIN: \w+ -->.*?<!-- CANONICAL-END: \w+ -->", re.DOTALL)


def test_agent_body_stays_within_its_word_budget(agent_body: str) -> None:
    """The persona's AUTHORED word count sits inside the agreed [floor, ceiling] window.

    Canonical governance blocks are excluded from the count, and that exclusion
    is the point rather than a loophole. The budget exists to stop MY prose
    from sprawling — prose I can tighten. Canonical text is reproduced
    byte-for-byte under ai-maestro#107 and may not be tightened at all, so
    counting it would turn every upstream rule edit into a spurious budget
    failure whose only available "fix" is to delete authored guidance that was
    never the problem. Worse, it would put a standing incentive on trimming the
    canonical copy, which is exactly the drift the copy exists to prevent.

    tests/test_canonical_rule_blocks.py guards the excluded regions, so nothing
    escapes review by living inside the markers.
    """
    authored = _CANONICAL_BLOCK_RE.sub("", agent_body)
    words = len(authored.split())
    assert _WORD_FLOOR <= words <= _WORD_CEILING, (
        f"persona is {words} AUTHORED words (canonical blocks excluded), outside the "
        f"[{_WORD_FLOOR}, {_WORD_CEILING}] budget; "
        "if this growth/shrink is intended, move the bound in one deliberate edit"
    )


def test_the_word_budget_actually_excludes_canonical_blocks(agent_body: str) -> None:
    """Coverage: the exclusion is real and is doing measurable work.

    Asserted separately because a regex that matched nothing would leave the
    budget silently counting canonical text again, and the only symptom would
    be a confusing failure months later after an upstream rule grew.
    """
    if "<!-- CANONICAL-BEGIN:" not in agent_body:
        pytest.skip(
            "canonical blocks temporarily withheld from the persona for the v0.3.3 release "
            "(CPV#201 gate defect, TRDD-NRQK4W2P) — re-arms automatically when they return"
        )
    authored = _CANONICAL_BLOCK_RE.sub("", agent_body)
    assert len(authored) < len(agent_body), "no canonical block was excluded — marker drift?"
    assert "R23.7" not in authored, "canonical rule rows leaked into the authored count"


def test_forbidden_list_is_intact(agent_body: str) -> None:
    """The numbered FORBIDDEN prohibitions are all still present.

    The FORBIDDEN section is the authority ceiling that keeps an ASSISTANT from
    acting like a MANAGER. The per-rule negation tests above prove the THREE
    load-bearing ones survive; this one guards the LIST as a whole against a
    silent mass-deletion that trims it down to a couple of items. Counts the
    `N. **NEVER …` numbered entries, which is the persona's own list format.
    """
    prohibitions = re.findall(r"^\d+\.\s+\*\*never\b", agent_body.lower(), re.MULTILINE)
    assert len(prohibitions) >= 12, (
        f"only {len(prohibitions)} numbered FORBIDDEN prohibitions found; the authority-boundary list looks truncated"
    )


def test_agent_body_covers_the_unpoliced_cross_session_channel(agent_body: str) -> None:
    """The persona names the client's direct session-to-session channel.

    AMP is validated server-side, so the persona could once say "a forbidden
    send returns HTTP 403" and be complete. Claude Code 2.1.224 shipped a
    SECOND transport — SendMessage between live sessions, with ListAgents to
    enumerate them — that never reaches the AI Maestro server. No 403 is
    possible on it, so R39.5/R39.7/R39.9 are unenforced there and the limit is
    the persona's alone to hold. A body that documents only the policed
    transport reads as though every send is checked, which is the more
    dangerous of the two errors.

    Naming the tools is asserted separately from the not-policed claim on
    purpose: a body that merely mentioned them in passing would satisfy a
    keyword scan while still implying the server has it covered.
    """
    lowered = agent_body.lower()
    for tool in ("sendmessage", "listagents"):
        assert tool in lowered, (
            f"persona never names `{tool}` — the unpoliced cross-session transport "
            "is invisible to an agent that only reads this file"
        )
    assert re.search(r"(?:bypasses|never reaches|does not reach)[^.]{0,80}server", lowered), (
        "persona names the cross-session channel but no longer states that it "
        "bypasses the AI Maestro server; without that, the 403 promise above it "
        "reads as covering every send"
    )
