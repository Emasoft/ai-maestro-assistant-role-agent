"""Shared fixtures for the ai-maestro-assistant-role-agent test suite.

Every fixture resolves a REAL shipped artifact from the repository working
tree. Nothing here is mocked: the whole point of this suite is that it fails
when the artifact a user would actually install is broken, so a mocked
manifest or a synthetic agent body would test nothing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

# Imported hard, never via importorskip: this parser IS the regression guard for
# the v0.2.2 defect that made the agent unloadable. A skip-on-missing would have
# let that CRITICAL bug ship green, and pyyaml is a declared dev dependency, so
# its absence is a broken environment — which must fail, not silently pass.
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - the project pins requires-python >= 3.12
    raise RuntimeError("Python 3.11+ required for tomllib")

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "ai-maestro-assistant-role-agent"

# The frontmatter delimiter must be the FIRST thing in the file and the closing
# fence must sit on its own line, which is exactly what Claude Code's own
# loader requires. Anchored with re.DOTALL so a multi-line block scalar in the
# description is captured whole.
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the plugin repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def plugin_manifest() -> dict[str, Any]:
    """Parsed .claude-plugin/plugin.json."""
    path = REPO_ROOT / ".claude-plugin" / "plugin.json"
    # Annotate explicitly: json.loads is typed as returning Any, and returning
    # Any from a dict-declared function trips mypy's warn_return_any.
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


@pytest.fixture(scope="session")
def agent_toml() -> dict[str, Any]:
    """Parsed <plugin-name>.agent.toml (the AI Maestro agent profile)."""
    path = REPO_ROOT / f"{PLUGIN_NAME}.agent.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def pyproject() -> dict[str, Any]:
    """Parsed pyproject.toml."""
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def agent_path() -> Path:
    """Path to the single main agent definition shipped by this role-plugin."""
    return REPO_ROOT / "agents" / f"{PLUGIN_NAME}-main-agent.md"


@pytest.fixture(scope="session")
def agent_text(agent_path: Path) -> str:
    """Raw UTF-8 text of the main agent definition."""
    return agent_path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def _agent_frontmatter_match(agent_text: str) -> re.Match[str]:
    """The single frontmatter match both the raw block and the body derive from."""
    match = _FRONTMATTER_RE.match(agent_text)
    assert match is not None, "agent file has no leading '---' YAML frontmatter block"
    return match


@pytest.fixture(scope="session")
def agent_frontmatter_raw(_agent_frontmatter_match: re.Match[str]) -> str:
    """The raw YAML frontmatter block of the main agent, fences stripped."""
    return _agent_frontmatter_match.group(1)


@pytest.fixture(scope="session")
def agent_frontmatter(agent_frontmatter_raw: str) -> dict[str, Any]:
    """The main agent's frontmatter parsed by a real YAML parser.

    Uses PyYAML deliberately: Claude Code parses agent frontmatter with a
    real YAML parser, so a construct PyYAML rejects (for example a bare
    ': ' inside a multi-line plain scalar) makes the agent unloadable in
    production even though the file "looks fine" to the eye.
    """
    data = yaml.safe_load(agent_frontmatter_raw)
    assert isinstance(data, dict), "agent frontmatter must parse to a mapping"
    return data


@pytest.fixture(scope="session")
def agent_body(agent_text: str, _agent_frontmatter_match: re.Match[str]) -> str:
    """The main agent's markdown body (everything after the frontmatter)."""
    return agent_text[_agent_frontmatter_match.end():]
