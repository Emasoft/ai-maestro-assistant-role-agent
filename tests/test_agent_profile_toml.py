"""Tests for the AI Maestro agent profile (<plugin-name>.agent.toml).

AI Maestro reads this profile to bind the role-plugin to a governance title
and to resolve the agent markdown. The "quad-match" invariant it depends on
(repo dir == plugin.json name == [agent].name == agents/<name>-main-agent.md)
is asserted here because a mismatch makes the role silently unassignable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PLUGIN_NAME = "ai-maestro-assistant-role-agent"


def test_agent_toml_parses(agent_toml: dict[str, Any]) -> None:
    """The profile is valid TOML with an [agent] table."""
    assert "agent" in agent_toml


def test_quad_match_invariant(agent_toml: dict[str, Any], plugin_manifest: dict[str, Any], repo_root: Path) -> None:
    """repo dir == plugin.json name == [agent].name — AI Maestro's binding key."""
    agent_name = agent_toml["agent"]["name"]
    assert agent_name == plugin_manifest["name"] == repo_root.name == PLUGIN_NAME


def test_agent_toml_path_points_at_a_real_file(agent_toml: dict[str, Any], repo_root: Path) -> None:
    """[agent].path resolves to a file that actually ships in the repo."""
    rel = agent_toml["agent"]["path"]
    assert (repo_root / rel).is_file(), f"[agent].path '{rel}' does not exist"


def test_agent_toml_source_matches_plugin(agent_toml: dict[str, Any]) -> None:
    """[agent].source uses the plugin: scheme and names this plugin."""
    assert agent_toml["agent"]["source"] == f"plugin:{PLUGIN_NAME}"


def test_compatible_title_is_assistant_only(agent_toml: dict[str, Any]) -> None:
    """The role binds to the ASSISTANT title and nothing else.

    Adding another title here would let a MANAGER-titled or MAINTAINER-titled
    slot load a persona that has no governing powers — a governance break.
    """
    assert agent_toml["agent"]["compatible-titles"] == ["ASSISTANT"]


def test_ships_no_bundled_skills(agent_toml: dict[str, Any]) -> None:
    """The role-plugin declares no bundled skills.

    Per the AI Maestro plugin-abstraction principle it references globally
    installed skills by name instead, so governance changes propagate without
    editing this repo. A non-empty list here means that principle was broken.
    """
    skills = agent_toml.get("skills", {})
    for bucket in ("primary", "secondary", "specialized"):
        assert skills.get(bucket, []) == [], f"[skills].{bucket} must stay empty"


def test_declares_the_required_external_skills(agent_toml: dict[str, Any]) -> None:
    """The external skills the persona actually invokes are declared."""
    external = set(agent_toml.get("dependencies", {}).get("external_skills", []))
    for required in ("planning", "agent-messaging", "agent-identity", "team-kanban"):
        assert required in external, f"external_skills is missing '{required}'"


def test_team_governance_is_excluded(agent_toml: dict[str, Any]) -> None:
    """team-governance stays OUT of external_skills (R39.8).

    That skill is the MANAGER's team-CRUD / approvals / transfers machinery.
    An ASSISTANT has no team and approves only its own TRDDs, so pulling it in
    would hand the role governing powers the rules deny it.
    """
    external = set(agent_toml.get("dependencies", {}).get("external_skills", []))
    assert "team-governance" not in external


def test_skills_directory_is_absent_or_empty(repo_root: Path) -> None:
    """No skills ship on disk either — consistent with the empty [skills] table."""
    skills_dir = repo_root / "skills"
    if skills_dir.is_dir():
        assert not list(skills_dir.glob("*/SKILL.md")), "role-plugin must ship no bundled skills"
