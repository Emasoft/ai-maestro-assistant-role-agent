"""Tests for the shipped main agent definition (agents/*-main-agent.md).

This role-plugin's ENTIRE payload is one agent markdown file, so these tests
are the plugin's functional test suite: if the frontmatter does not parse or
the persona loses a governance invariant, the plugin is broken in production.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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


def test_agent_body_states_the_forbidden_actions(agent_body: str) -> None:
    """The persona still enumerates the R39 prohibitions.

    These are the invariants that keep an ASSISTANT from acting like a
    MANAGER; losing them during an edit would silently widen its authority.
    """
    lowered = agent_body.lower()
    for phrase in ("forbidden", "r39", "sudo", "trdd"):
        assert phrase in lowered, f"agent body no longer mentions '{phrase}'"


def test_agent_body_forbids_creating_agents_or_teams(agent_body: str) -> None:
    """The single most important prohibition survives: no agent/team creation."""
    lowered = agent_body.lower()
    assert "team" in lowered
    assert re.search(r"(must not|cannot|can't|no authority).{0,80}(create|team|agent)", lowered, re.DOTALL)


def test_agent_body_has_no_absolute_home_paths(agent_text: str) -> None:
    """No developer-machine absolute path leaks into the shipped persona."""
    for leak in ("/Users/", "/home/", "C:\\Users\\"):
        assert leak not in agent_text, f"agent file leaks an absolute path prefix '{leak}'"
