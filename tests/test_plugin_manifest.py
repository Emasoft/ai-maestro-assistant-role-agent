"""Manifest contract tests for the ai-maestro-assistant-role-agent plugin.

These assert on the real shipped .claude-plugin/plugin.json. A broken manifest
is the single failure mode that makes the plugin uninstallable, so every field
Claude Code and the marketplace read is checked here rather than assumed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PLUGIN_NAME = "ai-maestro-assistant-role-agent"


def test_plugin_manifest_is_valid_json(repo_root: Path) -> None:
    """plugin.json parses as JSON — a syntax error makes the plugin uninstallable."""
    raw = (repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert isinstance(json.loads(raw), dict)


def test_plugin_manifest_has_required_fields(plugin_manifest: dict[str, Any]) -> None:
    """plugin.json carries every field Claude Code requires to load a plugin."""
    for field in ("name", "version", "description", "author"):
        assert field in plugin_manifest, f"plugin.json is missing required field '{field}'"


def test_plugin_name_matches_repository_directory(plugin_manifest: dict[str, Any], repo_root: Path) -> None:
    """plugin.json 'name' matches the repo directory — marketplace installs key on it."""
    assert plugin_manifest["name"] == PLUGIN_NAME
    assert repo_root.name == PLUGIN_NAME


def test_plugin_version_is_semver(plugin_manifest: dict[str, Any]) -> None:
    """plugin.json 'version' is a bare MAJOR.MINOR.PATCH string (no 'v' prefix)."""
    version = plugin_manifest["version"]
    parts = version.split(".")
    assert len(parts) == 3, f"version '{version}' is not MAJOR.MINOR.PATCH"
    assert all(p.isdigit() for p in parts), f"version '{version}' has a non-numeric component"


def test_plugin_version_matches_pyproject(plugin_manifest: dict[str, Any], pyproject: dict[str, Any]) -> None:
    """plugin.json and pyproject.toml agree on the version.

    publish.py bumps both slots atomically; a drift here means a release tag
    would describe a version the manifest never claimed.
    """
    assert plugin_manifest["version"] == pyproject["project"]["version"]


def test_plugin_author_is_a_structured_object(plugin_manifest: dict[str, Any]) -> None:
    """'author' is an object with a name, not a bare string."""
    author = plugin_manifest["author"]
    assert isinstance(author, dict), "author must be an object, not a string"
    assert author.get("name")


def test_plugin_declares_ai_maestro_dependency(plugin_manifest: dict[str, Any]) -> None:
    """The role-plugin declares its hard dependency on ai-maestro-plugin.

    It ships no skills of its own and calls AI Maestro's messaging/identity
    skills by name, so without this dependency an install silently lacks them.
    """
    names = {d.get("name") for d in plugin_manifest.get("dependencies", [])}
    assert "ai-maestro-plugin" in names


def test_plugin_license_declared_and_file_present(plugin_manifest: dict[str, Any], repo_root: Path) -> None:
    """A declared license has a matching LICENSE file at the repo root."""
    assert plugin_manifest.get("license") == "MIT"
    license_file = repo_root / "LICENSE"
    assert license_file.is_file(), "plugin.json declares MIT but no LICENSE file ships"
    assert "MIT License" in license_file.read_text(encoding="utf-8")


def test_plugin_repository_url_matches_plugin_name(plugin_manifest: dict[str, Any]) -> None:
    """The repository URL ends in the plugin name so marketplace source URLs resolve."""
    repo = plugin_manifest.get("repository", "")
    assert repo.rstrip("/").endswith(PLUGIN_NAME), f"repository '{repo}' does not end in '{PLUGIN_NAME}'"
