"""Tests that the canonical CPV release pipeline is present and coherent.

These guard the pipeline itself: publish.py, the three workflows, the pre-push
hook, and the changelog config. A silently-missing workflow is invisible until
a release day, which is exactly when it costs the most.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

WORKFLOWS = ("ci.yml", "release.yml", "notify-marketplace.yml")

# Every place the pipeline pins the CPV validator. The three MUST agree: CI,
# the release gate and the local publish gate all fetch the validator from this
# ref, so a partial bump makes local and CI enforce different rule sets.
CPV_REF_SITES = (
    ("scripts", "publish.py"),
    (".github", "workflows", "ci.yml"),
    (".github", "workflows", "release.yml"),
)
# Match only ref-legal characters, so a trailing ")" / quote / backslash from the
# surrounding prose or shell continuation is never captured as part of the ref.
CPV_REF_RE = re.compile(r"claude-plugins-validation@([A-Za-z0-9][A-Za-z0-9._/-]*)")


def test_publish_script_present_and_executable(repo_root: Path) -> None:
    """scripts/publish.py ships and is executable — the release entry point."""
    publish = repo_root / "scripts" / "publish.py"
    assert publish.is_file(), "scripts/publish.py is missing"
    assert publish.stat().st_mode & 0o111, "scripts/publish.py is not executable"


def test_pre_push_hook_present_and_executable(repo_root: Path) -> None:
    """git-hooks/pre-push ships and is executable — the local quality gate."""
    hook = repo_root / "git-hooks" / "pre-push"
    assert hook.is_file(), "git-hooks/pre-push is missing"
    assert hook.stat().st_mode & 0o111, "git-hooks/pre-push is not executable"


def test_pre_push_hook_invokes_the_publish_gate(repo_root: Path) -> None:
    """The hook actually runs publish.py --gate rather than being a stub."""
    text = (repo_root / "git-hooks" / "pre-push").read_text(encoding="utf-8")
    assert "publish.py" in text and "--gate" in text


def test_pre_push_hook_is_posix_sh(repo_root: Path) -> None:
    """The hook is POSIX sh, not bash.

    The canonical hook deliberately targets /usr/bin/env sh so it runs on a
    machine with no bash (a stock Debian/Alpine contributor box). A bash-only
    shebang makes the gate silently impossible to run exactly where it matters.
    """
    text = (repo_root / "git-hooks" / "pre-push").read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env sh"), "pre-push must be POSIX sh"


def test_pre_push_hook_secret_scans_feature_branches(repo_root: Path) -> None:
    """A feature-branch push is secret-scanned, and FAILS CLOSED without the scanner.

    The release gate only covers the default branch and tags, so without this
    a contributor could push secrets on a feature branch untouched by any gate.
    'trufflehog missing' must therefore BLOCK, never silently allow — a push
    that skipped the scan but still looks like a pass is the worst outcome.
    """
    text = (repo_root / "git-hooks" / "pre-push").read_text(encoding="utf-8")
    assert "trufflehog" in text, "pre-push does not secret-scan feature branches"
    assert "BLOCKED" in text, "pre-push does not fail closed when the scanner is absent"


def test_cpv_ref_is_pinned_and_consistent(repo_root: Path) -> None:
    """publish.py, ci.yml and release.yml pin ONE identical CPV version tag.

    Guards the drift class this pipeline was migrated to fix: a bump that
    updates the workflow but not publish.py leaves CI and the local gate
    enforcing different rules, so a push passes locally and fails in CI. A
    floating ref (@main) is equally rejected — it makes any upstream release
    able to break this plugin's gate with no change here.
    """
    refs: set[str] = set()
    for parts in CPV_REF_SITES:
        text = repo_root.joinpath(*parts).read_text(encoding="utf-8")
        found = set(CPV_REF_RE.findall(text))
        assert found, f"{'/'.join(parts)} pins no CPV validator ref"
        refs |= found
    assert len(refs) == 1, f"CPV ref disagrees across the pipeline: {sorted(refs)}"
    ref = refs.pop()
    assert re.fullmatch(r"v\d+\.\d+\.\d+", ref), f"CPV ref is not a pinned version tag: {ref}"


def test_all_canonical_workflows_present(repo_root: Path) -> None:
    """ci.yml, release.yml and notify-marketplace.yml all ship."""
    for name in WORKFLOWS:
        assert (repo_root / ".github" / "workflows" / name).is_file(), f"missing workflow {name}"


def test_no_legacy_validate_workflow(repo_root: Path) -> None:
    """No leftover validate.yml.

    It was merged into ci.yml; keeping both makes the two runs cancel each
    other through the shared concurrency group, and a cancelled required run
    is not a pass.
    """
    assert not (repo_root / ".github" / "workflows" / "validate.yml").exists()


def test_workflows_declare_least_privilege_permissions(repo_root: Path) -> None:
    """Every workflow pins an explicit top-level permissions block."""
    for name in WORKFLOWS:
        text = (repo_root / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "permissions:" in text, f"{name} has no permissions block"
        assert "write-all" not in text, f"{name} grants write-all"


def test_workflows_set_a_job_timeout(repo_root: Path) -> None:
    """Every workflow bounds its jobs with timeout-minutes."""
    for name in WORKFLOWS:
        text = (repo_root / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "timeout-minutes:" in text, f"{name} has no timeout-minutes"


def test_notify_marketplace_targets_the_real_marketplace(repo_root: Path) -> None:
    """notify-marketplace.yml points at the AI Maestro marketplace repo.

    An unreplaced owner/repo placeholder makes the notification dispatch 404
    at release time, leaving the marketplace stuck on the previous version.
    """
    text = (repo_root / ".github" / "workflows" / "notify-marketplace.yml").read_text(encoding="utf-8")
    assert "ai-maestro-plugins" in text
    assert "OWNER/REPO" not in text and "<owner>" not in text


def test_changelog_config_present(repo_root: Path) -> None:
    """cliff.toml ships so publish.py can auto-detect the bump level."""
    assert (repo_root / "cliff.toml").is_file()


def test_lint_and_gate_configs_present(repo_root: Path) -> None:
    """The configs CI's linters read all ship, so local and CI agree."""
    for name in (".mega-linter.yml", ".jscpd.json", ".cspell.json", ".commitlintrc.json"):
        assert (repo_root / name).is_file(), f"missing {name}"


def test_python_version_pinned(repo_root: Path) -> None:
    """.python-version pins the interpreter uv resolves locally and in CI."""
    pinned = (repo_root / ".python-version").read_text(encoding="utf-8").strip()
    assert pinned.startswith("3.")


def test_readme_present_and_names_the_plugin(repo_root: Path) -> None:
    """README.md ships and names the plugin — the marketplace listing reads it."""
    readme = repo_root / "README.md"
    assert readme.is_file()
    assert "ai-maestro-assistant-role-agent" in readme.read_text(encoding="utf-8")


def test_gitignore_covers_private_and_transient_paths(repo_root: Path) -> None:
    """.gitignore excludes report dirs, session state, and editor temp files.

    Reports and janitor state routinely contain absolute paths and hostnames;
    committing them is a data leak, not just clutter.
    """
    text = (repo_root / ".gitignore").read_text(encoding="utf-8")
    # reports_dev/ is listed explicitly, not left to the `*_dev/` catch-all: the
    # agent-reports rule requires BOTH report dirs ignored by name, and a later
    # edit that drops the glob would otherwise silently start tracking them.
    for entry in ("reports/", "reports_dev/", ".janitor/", ".claude/", "*.swp", "__pycache__/", ".venv/", ".env"):
        assert entry in text, f".gitignore is missing '{entry}'"


def test_dev_extra_declares_the_test_toolchain(pyproject: dict[str, Any]) -> None:
    """The dev extra declares pytest and pytest-split.

    ci.yml runs `pytest --splits N --group K`; without pytest-split installed
    every shard dies on unrecognized arguments.
    """
    dev = " ".join(pyproject["project"]["optional-dependencies"]["dev"])
    assert "pytest" in dev
    assert "pytest-split" in dev
