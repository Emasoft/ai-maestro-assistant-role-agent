#!/usr/bin/env python3
"""Unified publish pipeline: bypass-guard -> lint -> validate (remote CPV) -> test -> bump -> badge -> changelog -> commit -> push -> release -> verify-ci -> install-smoke.

Modes:
  --gate                  Pre-push gate: orchestrator check + lint (ruff/jscpd/
                          actionlint/mypy) + validate + tests only (no bump/push).
                          Called by git-hooks/pre-push automatically.
  --install-hook          Install git-hooks/pre-push into .git/hooks/ and set core.hooksPath.
  --install-branch-rules  Apply the cpv-branch-rules GitHub ruleset to the origin
                          (server-side CI enforcement — run once after first push).
  (no flag)               Full release pipeline (17 steps — 0-14 fail-fast,
                          15-16 post-release reporters). The bump type
                          is AUTO-DETECTED via `git-cliff --bumped-version` from the
                          conventional commits on HEAD.
  --patch/--minor/--major Force a specific bump type (overrides auto-detection).

Pipeline stages (all fail-fast — any non-zero exit aborts):
   0. Bypass guard — reject CPV_SKIP_*, SKIP_*, NO_VERIFY env vars
   1. Check working tree is clean
   2. Lint + type-check (ruff + mypy)
   3. Run tests (pytest)
   4. Validate plugin (uvx cpv-remote-validate plugin . --strict — fetches
      the canonical CPV validator from GitHub so this plugin never vendors
      a local copy and never drifts from upstream rules)
   5. CI-parity preflight (uvx cpv-remote-validate ci-preflight . — the
      jscpd / actionlint / mypy / uv-sync-dev / Mega-Linter / static-CIP gates
      that CI's Lint job runs but `validate_plugin --strict` does NOT). Runs
      BEFORE the bump/commit/tag/push, so a pipeline defect can never leave a
      half-published state. A MISSING local tool degrades to a WARNING and never
      blocks the publish.
   6. Marketplace-registration check (Layout A: notify workflow + PAT secret +
      remote marketplace.json registration + remote receiver workflow;
      Layout B: must run from marketplace root + nested plugin must be listed)
   7. Secret scan (trufflehog — a committed credential BLOCKS the publish;
      canon CPV#217: a leaked auth key sat on main 85 days while every local
      gate passed. Auto-installs trufflehog as a stage dependency; a missing
      scanner blocks, because "cannot check" is not clean)
   8. Linux fork-parity probe (re-runs the suite with multiprocessing forced
      to fork, the way Linux CI runs it — the v3.23.0 deadlock class no
      macOS local run can see)
   9. Check version consistency across all sources
  10. Bump version in plugin.json, pyproject.toml, and __version__ vars
  11. Update README version badge
  12. Generate changelog (git-cliff)
  13. Commit, tag, push
  14. Create GitHub release (gh CLI)
Post-release reporters (the release is already public; they never abort the run):
  15. Verify CI is green on the released commit (advisory)
  16. Install smoke test (clean-dir `claude plugin install`; fails the run
      only with CPV_PUBLISH_REQUIRE_INSTALL_SMOKE=1)

Gate stages (--gate mode, called by pre-push hook):
   G0. Orchestrator check — direct `git push` is blocked; only publish.py
       may initiate a push (verified via process ancestry, NOT env vars).
   G1. Version bump check (local vs remote, auto-detects origin/HEAD)
   G2. Lint (ruff)
   G2b. Copy-paste check (jscpd, parity with ci.yml Mega-Linter COPYPASTE_JSCPD;
        WARNs+skips if jscpd/npx unavailable so a push is never false-blocked)
   G2c. Workflow lint (actionlint, parity with ci.yml Lint job; WARNs+skips if
        actionlint unavailable so a push is never false-blocked)
   G2d. Type-check (mypy scripts/ --ignore-missing-imports, parity with ci.yml
        Lint job; WARNs+skips if mypy unavailable so a push is never false-blocked)
   G3. Validate (uvx cpv-remote-validate plugin . --strict)
   G4. Tests (pytest)

Usage:
    uv run python scripts/publish.py                      # auto-bump from git-cliff
    uv run python scripts/publish.py --gate
    uv run python scripts/publish.py --install-hook
    uv run python scripts/publish.py --install-branch-rules
    uv run python scripts/publish.py --patch              # force patch
    uv run python scripts/publish.py --minor              # force minor
    uv run python scripts/publish.py --major              # force major
    uv run python scripts/publish.py --dry-run            # preview (auto-bump)

Cornerstone rule: a plugin CANNOT be pushed unless validation passes with
0 issues (WARNING allowed). There are no exceptions and no bypass flags.
Every push is blocked unless scripts/publish.py orchestrates it end-to-end
AND stage_validate / stage_tests / stage_lint all succeed.
"""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Load gh / git retry wrappers from the sibling module so every push +
# `gh release create` survives transient github.com hiccups (the retry
# pattern from ~/.claude/rules/github-timeouts.md). Shipped verbatim
# from the canonical CPV install via gen_cpv_network_resilience_py().
# cpv_fork_parity rides the same import-fallback pattern: the fork-parity
# stage (canon Gate 3c) degrades to a WARNING-without-probe when an older
# scaffold has not shipped the module yet.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    # `pyright: ignore[reportAssignmentType]` (on the import line itself):
    # the typed real import and the ImportError fallback shims below are
    # conditional variants of the same names; Pyright flags the typed import as
    # not assignable to the fallback's loose declared type (its mypy counterpart
    # is the [no-redef, misc] on the shims). Suppress exactly that — the
    # standard import-fallback idiom. issue #151.
    from cpv_network_resilience import gh_with_retry, git_with_retry  # pyright: ignore[reportAssignmentType]
except ImportError:
    # Fallback: scripts/cpv_network_resilience.py was not shipped with this
    # plugin (older scaffold). Define no-op shims so publish.py still works,
    # but warn so the user knows to refresh via `cpv standardize --force-templates`.
    print(
        "[publish.py] WARNING: scripts/cpv_network_resilience.py missing — "
        "network calls will not auto-retry on transient errors. "
        "Run `cpv standardize --force-templates` to refresh.",
        file=sys.stderr,
    )

    # `misc` is needed alongside `no-redef`: under `mypy --strict` the typed
    # real import (cpv_network_resilience) and these minimal fallback shims are
    # conditional variants of the same name with NON-IDENTICAL signatures, which
    # `--strict` reports as [misc] ("All conditional function variants must have
    # identical signatures"); the combined code suppresses exactly that, the
    # standard import-fallback idiom (cf. the tomli fallback at
    # cpv_lint_engine.py with [no-redef,import-not-found]).
    def gh_with_retry(cmd, **kwargs):  # type: ignore[no-redef, misc]
        kwargs.pop("max_attempts", None)
        kwargs.pop("backoff", None)
        kwargs.setdefault("check", True)
        kwargs.setdefault("capture_output", False)
        return subprocess.run(cmd, **kwargs)

    def git_with_retry(cmd, **kwargs):  # type: ignore[no-redef, misc]
        kwargs.pop("max_attempts", None)
        kwargs.pop("backoff", None)
        kwargs.setdefault("check", True)
        kwargs.setdefault("capture_output", False)
        return subprocess.run(cmd, **kwargs)

    def fork_parity_supported():  # type: ignore[no-untyped-def]
        return False, "scripts/cpv_fork_parity.py missing — run `cpv standardize --force-templates`"

    def run_under_linux_fork_default(cmd, cwd, timeout=1800.0, env=None):  # type: ignore[no-untyped-def]
        raise ImportError("cpv_fork_parity not shipped")


# -- ANSI colors ---------------------------------------------------------------


def _colors_ok() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_C = _colors_ok()
RED = "\033[0;31m" if _C else ""
GREEN = "\033[0;32m" if _C else ""
YELLOW = "\033[1;33m" if _C else ""
BLUE = "\033[0;34m" if _C else ""
BOLD = "\033[1m" if _C else ""
DIM = "\033[2m" if _C else ""
NC = "\033[0m" if _C else ""

# Fork-parity probe (canon Gate 3c). Import with fallback so an older scaffold
# without scripts/cpv_fork_parity.py degrades to "cannot run the probe" instead
# of a NameError mid-publish — the same ImportError idiom as the retry shims.
try:
    # The ignore mirrors the retry-shim idiom: the typed import and the None
    # fallback are conditional variants of the same names with NON-identical
    # types, which mypy reports as [assignment] on this import line itself.
    from cpv_fork_parity import fork_parity_supported, run_under_linux_fork_default  # type: ignore[assignment]
except ImportError:
    fork_parity_supported = None  # type: ignore[assignment, misc]
    run_under_linux_fork_default = None  # type: ignore[assignment, misc]

# -- Push budget (canon issue #224) --------------------------------------------
#
# The pre-push hook runs INSIDE the `git push` call's wall clock, so the push
# timeout must cover the whole downstream gate, not just the wire transfer:
# the CPV remote-validate call plus the full pytest suite (both re-run inside
# the hook) plus slack. Three attempts survives a flaky-link retry cycle
# without turning a permanently red gate into a threefold wait.
_CPV_TIMEOUT_SEC = 600.0
_TEST_SUITE_TIMEOUT_SEC = 1800.0
_PUSH_TIMEOUT_SEC = _CPV_TIMEOUT_SEC + 2 * _TEST_SUITE_TIMEOUT_SEC + 1800.0
_PUSH_MAX_ATTEMPTS = 3

# -- CI-verify + install-smoke budgets ------------------------------------------

# Post-release CI verification budget. The release is already public when this
# runs, so the timeout exists to bound the REPORT, never to gate the publish.
_CI_VERIFY_DEFAULT_TIMEOUT_S = 900


# -- Helpers -------------------------------------------------------------------


def cprint(msg: str) -> None:
    print(msg, flush=True)


def run(
    cmd: list[str],
    cwd: Path | None = None,
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command, stream output, fail-fast on error."""
    cprint(f"  {BLUE}$ {' '.join(cmd)}{NC}")
    # A subprocess exceeding `timeout` raises TimeoutExpired; without this it
    # would die with a raw traceback instead of the styled fail-fast message
    # every other failure path uses. Catch it and exit 1.
    try:
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=capture, timeout=300)
    except subprocess.TimeoutExpired:
        cprint(f"  {RED}Command timed out after 300s: {' '.join(cmd)}{NC}")
        sys.exit(1)
    if check and result.returncode != 0:
        cprint(f"  {RED}Command failed (exit {result.returncode}){NC}")
        sys.exit(result.returncode)
    return result


def get_repo_root() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return Path(r.stdout.strip())


# -- gh-auth precheck (TRDD-bbff5bc5) ---------------------------------------


def _parse_owner_repo_from_remote(remote_url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from `git@host:owner/repo.git` or
    `https://host/owner/repo[.git]`. Returns None on unparseable input.
    """
    if not remote_url:
        return None
    url = remote_url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    match = re.search(r"[:/]([^:/\s]+)/([^/\s]+)$", url)
    if not match:
        return None
    return match.group(1), match.group(2)


def _resolve_owner_repo(plugin_root: Path) -> tuple[str, str]:
    """Read remote.origin.url, parse (owner, repo). Exit 1 on failure."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=str(plugin_root),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        cprint(f"  {RED}Could not read remote.origin.url. Run: git remote add origin <url>{NC}")
        sys.exit(1)
    parsed = _parse_owner_repo_from_remote(result.stdout.strip())
    if parsed is None:
        cprint(f"  {RED}Could not parse owner/repo from remote URL: {result.stdout.strip()!r}{NC}")
        sys.exit(1)
    return parsed


def _ensure_gh_auth(owner: str, repo: str) -> None:
    """Verify gh CLI installed + authenticated + push perm on owner/repo.

    Called BEFORE every push gate. Exits 1 on any of: gh missing, not
    authed, no push permission. Per TRDD-bbff5bc5 §4.1: never invokes
    `gh auth token`; uses only `gh auth status` and `gh api` so PAT-shaped
    strings cannot leak to stdout/stderr.
    """
    if os.environ.get("CPV_SKIP_GH_AUTH_CHECK") == "1":
        return
    gh_bin = shutil.which("gh")
    if gh_bin is None:
        cprint(f"  {RED}gh CLI not installed. Install: brew install gh{NC}")
        sys.exit(1)
    # 60s timeout (was 15s) — slow-link tolerance; downstream push gates
    # still enforce real auth on failure.
    try:
        status = subprocess.run(
            [gh_bin, "auth", "status"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        cprint(
            f"  {RED}gh auth status timed out after 60 s — flaky network. Retry, or set CPV_SKIP_GH_AUTH_CHECK=1.{NC}"
        )
        sys.exit(1)
    if status.returncode != 0:
        cprint(f"  {RED}gh CLI not authenticated.{NC}")
        cprint(f"  {YELLOW}Run: gh auth login --hostname github.com --git-protocol https{NC}")
        sys.exit(1)
    try:
        perms = subprocess.run(
            [gh_bin, "api", f"repos/{owner}/{repo}", "--jq", ".permissions.push"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        cprint(
            f"  {RED}gh permission check timed out after 60 s — set CPV_SKIP_GH_AUTH_CHECK=1 to bypass this gate.{NC}"
        )
        sys.exit(1)
    if perms.returncode != 0 or perms.stdout.strip() != "true":
        active_login = ""
        for line in (status.stdout + status.stderr).splitlines():
            line = line.strip()
            if "account " in line and ("Logged in" in line or "Active" in line):
                m = re.search(r"account\s+(\S+)", line)
                if m:
                    active_login = m.group(1)
                    break
        login_str = f" '{active_login}'" if active_login else ""
        cprint(f"  {RED}gh user{login_str} has no push permission on {owner}/{repo}.{NC}")
        cprint(f"  {YELLOW}Diagnose:{NC}")
        cprint(f"  {YELLOW}  1. Ask the repo owner to add you as a collaborator with write access.{NC}")
        cprint(f"  {YELLOW}  2. If you have multiple gh accounts: gh auth status; gh auth switch{NC}")
        cprint(f"  {YELLOW}  3. If using a fine-grained token: ensure 'Contents: write' on this repo.{NC}")
        sys.exit(1)


# -- Semver --------------------------------------------------------------------


def parse_semver(version: str) -> tuple[int, int, int] | None:
    """Parse 'X.Y.Z' into (major, minor, patch)."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_semver(current: str, bump_type: str) -> str | None:
    """Bump version by major/minor/patch. Returns new version string or None."""
    parsed = parse_semver(current)
    if not parsed:
        return None
    major, minor, patch = parsed
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return None


# -- Version readers/writers ---------------------------------------------------


def get_current_version(plugin_root: Path) -> str | None:
    """Read version from .claude-plugin/plugin.json."""
    pj = plugin_root / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return None
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
        ver = data.get("version")
        return str(ver) if ver is not None else None
    except (json.JSONDecodeError, OSError):
        return None


def update_plugin_json(root: Path, new_ver: str) -> tuple[bool, str]:
    """Write version to .claude-plugin/plugin.json."""
    pj = root / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return False, "plugin.json not found"
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
        data["version"] = new_ver
        pj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return True, f"plugin.json -> {new_ver}"
    except (json.JSONDecodeError, OSError) as e:
        return False, f"plugin.json update failed: {e}"


def update_self_marketplace_json(root: Path, new_ver: str) -> tuple[bool, str]:
    """Write version to .claude-plugin/marketplace.json (Layout C — both metadata and self-entry)."""
    mp = root / ".claude-plugin" / "marketplace.json"
    if not mp.is_file():
        return False, "no marketplace.json (not Layout C)"
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, f"marketplace.json read failed: {e}"
    # Bump metadata.version if present
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        metadata["version"] = new_ver
    # Bump the self-entry's version (the entry whose name matches plugin.json's name AND source is "./")
    plugin_json_path = root / ".claude-plugin" / "plugin.json"
    plugin_name: str | None = None
    if plugin_json_path.is_file():
        try:
            pdata = json.loads(plugin_json_path.read_text(encoding="utf-8"))
            plugin_name = pdata.get("name")
        except (json.JSONDecodeError, OSError):
            plugin_name = None
    plugins = data.get("plugins")
    bumped_entry = False
    if isinstance(plugins, list):
        for entry in plugins:
            if not isinstance(entry, dict):
                continue
            entry_name = entry.get("name")
            entry_source = entry.get("source")
            is_self = (entry_name == plugin_name or plugin_name is None) and entry_source in (
                "./",
                {"source": "directory", "path": "./"},
            )
            if is_self:
                entry["version"] = new_ver
                bumped_entry = True
                break
    try:
        mp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        return False, f"marketplace.json write failed: {e}"
    if bumped_entry:
        return True, f"marketplace.json (metadata + self-entry) -> {new_ver}"
    return True, f"marketplace.json (metadata only — no self-entry matched) -> {new_ver}"


def _project_block(content: str) -> tuple[int, int] | None:
    """Char span of the [project] table body, or None if absent.

    The project version lives in the [project] table. A whole-file first-match
    for `version = "..."` writes the WRONG version when a [tool.X] table with
    its own top-level `version` (e.g. [tool.commitizen]) precedes [project].
    When there is no [project] table (poetry keeps it under [tool.poetry]),
    return None so the caller falls back to the legacy whole-file first-match.
    """
    m = re.search(r"^\[project\]\s*$", content, re.MULTILINE)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"^\[", content[start:], re.MULTILINE)
    return start, (start + nxt.start() if nxt else len(content))


def update_pyproject_toml(root: Path, new_ver: str) -> tuple[bool, str]:
    """Write version to pyproject.toml."""
    pp = root / "pyproject.toml"
    if not pp.is_file():
        return False, "pyproject.toml not found"
    try:
        content = pp.read_text(encoding="utf-8")
        block = _project_block(content)
        if block is not None:
            lo, hi = block
            replaced = re.sub(
                r'^(version\s*=\s*")[^"]*(")',
                rf"\g<1>{new_ver}\2",
                content[lo:hi],
                count=1,
                flags=re.MULTILINE,
            )
            updated = content[:lo] + replaced + content[hi:]
        else:
            updated = re.sub(
                r'^(version\s*=\s*")[^"]*(")',
                rf"\g<1>{new_ver}\2",
                content,
                count=1,
                flags=re.MULTILINE,
            )
        if updated == content:
            return False, "pyproject.toml: version field not found"
        pp.write_text(updated, encoding="utf-8")
        return True, f"pyproject.toml -> {new_ver}"
    except OSError as e:
        return False, f"pyproject.toml update failed: {e}"


def update_python_versions(root: Path, new_ver: str) -> list[tuple[bool, str]]:
    """Update __version__ = '...' in all .py files under scripts/."""
    results: list[tuple[bool, str]] = []
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        return results
    pattern = re.compile(r'^(__version__\s*=\s*["\'])([^"\']*)(["\']\s*)$', re.MULTILINE)
    for py_file in scripts_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if not pattern.search(content):
            continue
        updated = pattern.sub(rf"\g<1>{new_ver}\3", content)
        if updated != content:
            py_file.write_text(updated, encoding="utf-8")
            results.append((True, f"{py_file.relative_to(root)} -> {new_ver}"))
    return results


def check_version_consistency(root: Path) -> tuple[bool, str]:
    """Verify all version sources match. Includes marketplace.json metadata
    and self-entry (Layout C) when present."""
    versions: dict[str, str | None] = {}

    # plugin.json
    pj = root / ".claude-plugin" / "plugin.json"
    if pj.is_file():
        try:
            versions["plugin.json"] = json.loads(pj.read_text(encoding="utf-8")).get("version")
        except (json.JSONDecodeError, OSError):
            versions["plugin.json"] = None

    # marketplace.json (Layout C) — both metadata.version and the self-entry's version
    mp = root / ".claude-plugin" / "marketplace.json"
    if mp.is_file():
        try:
            mp_data = json.loads(mp.read_text(encoding="utf-8"))
            md = mp_data.get("metadata")
            if isinstance(md, dict):
                versions["marketplace.json:metadata"] = md.get("version")
            plugins_arr = mp_data.get("plugins")
            if isinstance(plugins_arr, list):
                for entry in plugins_arr:
                    if not isinstance(entry, dict):
                        continue
                    src = entry.get("source")
                    if src == "./" or (
                        isinstance(src, dict) and src.get("source") == "directory" and src.get("path") == "./"
                    ):
                        versions["marketplace.json:self-entry"] = entry.get("version")
                        break
        except (json.JSONDecodeError, OSError):
            versions["marketplace.json"] = None

    # pyproject.toml — read from the [project] table body when present, else
    # fall back to the whole-file first-match (poetry-style layouts).
    pp = root / "pyproject.toml"
    if pp.is_file():
        pp_text = pp.read_text(encoding="utf-8")
        blk = _project_block(pp_text)
        hay = pp_text[blk[0] : blk[1]] if blk is not None else pp_text
        m = re.search(r'^version\s*=\s*"([^"]*)"', hay, re.MULTILINE)
        versions["pyproject.toml"] = m.group(1) if m else None

    found = {k: v for k, v in versions.items() if v is not None}
    if not found:
        return False, "No version sources found"
    unique = set(found.values())
    if len(unique) == 1:
        return True, f"All versions match: {unique.pop()}"
    details = ", ".join(f"{k}={v}" for k, v in found.items())
    return False, f"Version mismatch: {details}"


def _sync_uv_lock(root: Path) -> None:
    """Re-resolve ``uv.lock`` against the freshly-bumped ``pyproject.toml``.

    Without this, every release leaves ``uv.lock`` stale by one version
    (``pyproject.toml`` says e.g. ``2.66.2`` but ``uv.lock`` still pins the
    root package at ``2.66.1``). The NEXT publish then runs an outer
    ``uv run``/``uv lock``/``uv sync`` which re-syncs that single root-version
    line in place, DIRTYING the working tree — and Gate 1 (clean-tree check)
    aborts that publish before it does anything (issue #149). Co-locating the
    sync in do_bump (the only place pyproject.toml is written) guarantees the
    lock can never be stale after a successful bump. Idempotent; silently
    skipped when neither ``uv`` nor ``uv.lock`` is present (plugins authored
    without uv, or a host where uv isn't installed). ``check=False`` so a uv
    hiccup degrades to a no-op instead of aborting the bump.
    """
    if not (root / "uv.lock").is_file():
        return
    if shutil.which("uv") is None:
        return
    run(["uv", "lock"], root, check=False)


def do_bump(root: Path, new_ver: str, dry_run: bool = False) -> bool:
    """Orchestrate all version updates. Detects Layout C (marketplace.json at repo root)
    and bumps both manifests atomically when present."""
    cprint(f"\n{BOLD}Bumping to {new_ver}{' (dry-run)' if dry_run else ''}{NC}")

    is_layout_c = (root / ".claude-plugin" / "marketplace.json").is_file()

    if dry_run:
        cprint(f"  Would update plugin.json -> {new_ver}")
        if is_layout_c:
            cprint(f"  Would update marketplace.json (metadata + self-entry, Layout C) -> {new_ver}")
        cprint(f"  Would update pyproject.toml -> {new_ver}")
        cprint(f"  Would update __version__ vars -> {new_ver}")
        return True

    ok1, msg1 = update_plugin_json(root, new_ver)
    cprint(f"  {'OK' if ok1 else 'FAIL'}: {msg1}")

    ok_mp = True
    if is_layout_c:
        ok_mp, msg_mp = update_self_marketplace_json(root, new_ver)
        cprint(f"  {'OK' if ok_mp else 'FAIL'}: {msg_mp}")

    ok2, msg2 = update_pyproject_toml(root, new_ver)
    cprint(f"  {'OK' if ok2 else 'FAIL'}: {msg2}")

    py_results = update_python_versions(root, new_ver)
    for ok, msg in py_results:
        cprint(f"  {'OK' if ok else 'FAIL'}: {msg}")

    ok = ok1 and ok2 and ok_mp
    if ok:
        # Bump succeeded — bring uv.lock's root version along so the
        # post-publish tree is clean and the NEXT publish's outer `uv run`
        # doesn't re-sync uv.lock and trip Gate 1 (issue #149).
        _sync_uv_lock(root)
    return ok


# -- Hook installer ------------------------------------------------------------


def install_hook(root: Path) -> int:
    """Copy git-hooks/pre-push to .git/hooks/pre-push and set core.hooksPath."""
    cprint(f"\n{BOLD}Installing git hooks...{NC}")
    source = root / "git-hooks" / "pre-push"
    if not source.is_file():
        cprint(f"  {RED}git-hooks/pre-push not found{NC}")
        return 1
    git_dir = root / ".git"
    if not git_dir.is_dir():
        cprint(f"  {RED}.git/ not found — is this a git repository?{NC}")
        return 1
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    dest = hooks_dir / "pre-push"
    shutil.copy2(source, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    cprint(f"  {GREEN}Installed: git-hooks/pre-push -> .git/hooks/pre-push{NC}")
    # Also set core.hooksPath so git finds hooks in git-hooks/ directly
    subprocess.run(["git", "config", "core.hooksPath", "git-hooks"], cwd=str(root), check=False)
    cprint(f"  {GREEN}Set git config core.hooksPath = git-hooks{NC}")
    return 0


def _get_origin_slug(root: Path) -> str | None:
    """Return OWNER/REPO parsed from the current repo's origin remote, or None."""
    try:
        r = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    url = r.stdout.strip()
    # Handle git@github.com:OWNER/REPO.git and https://github.com/OWNER/REPO.git
    if url.startswith("git@"):
        _, _, path = url.partition(":")
    elif "//" in url:
        _, _, path = url.partition("//")
        # path is now "github.com/OWNER/REPO.git"
        path = path.split("/", 1)[1] if "/" in path else ""
    else:
        return None
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.strip("/").split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return f"{parts[0]}/{parts[1]}"


def install_branch_rules(root: Path) -> int:
    """Apply the cpv-branch-rules ruleset to the repo's GitHub origin.

    Auto-detects the OWNER/REPO slug from `git config remote.origin.url` and
    shells out to `uvx cpv-setup-branch-rules` so downstream plugins do not
    need to vendor setup_branch_rules.py locally. This is the server-side
    gate that enforces CI as a required status check — the local pre-push
    hook alone is bypassable with `git push --no-verify`, but a ruleset is
    enforced by GitHub itself.
    """
    cprint(f"\n{BOLD}Installing branch-protection ruleset...{NC}")
    slug = _get_origin_slug(root)
    if slug is None:
        cprint(f"  {RED}Could not read origin remote URL — skipping.{NC}")
        cprint(f"  {YELLOW}Set `git remote add origin <url>` first, then retry.{NC}")
        return 1
    cprint(f"  Target repo: {slug}")
    try:
        r = subprocess.run(
            [
                "uvx",
                "--from",
                "git+https://github.com/Emasoft/claude-plugins-validation@v5.21.1",
                "--with",
                "pyyaml",
                "cpv-setup-branch-rules",
                slug,
            ],
            cwd=str(root),
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        cprint(f"  {RED}uvx call failed: {exc}{NC}")
        return 1
    if r.returncode != 0:
        cprint(f"  {RED}cpv-setup-branch-rules exited with code {r.returncode}{NC}")
        return r.returncode
    cprint(f"  {GREEN}Branch rules applied to {slug}.{NC}")
    return 0


# -- Gate mode (pre-push quality checks) --------------------------------------


def _get_process_ancestry(max_depth: int = 30) -> list[tuple[int, str]]:
    """Walk parent processes via ps(1). Returns [(pid, cmdline), ...] closest-first.

    Used by the orchestrator check to verify that scripts/publish.py is an
    ancestor of the current pre-push gate invocation. Process ancestry is
    non-spoofable (unlike env vars, which a user could set with
    `CPV_PIPELINE=1 git push`).
    """
    ancestry: list[tuple[int, str]] = []
    pid = os.getpid()
    seen: set[int] = set()
    for _ in range(max_depth):
        if pid in seen or pid <= 0:
            break
        seen.add(pid)
        try:
            r = subprocess.run(
                ["ps", "-p", str(pid), "-o", "ppid=,args="],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if r.returncode != 0:
            break
        line = r.stdout.strip()
        if not line:
            break
        parts = line.split(None, 1)
        if not parts:
            break
        try:
            ppid = int(parts[0])
        except ValueError:
            break
        cmdline = parts[1] if len(parts) > 1 else ""
        ancestry.append((pid, cmdline))
        if ppid <= 1:
            break
        pid = ppid
    return ancestry


def _called_by_publish_orchestrator(root: Path) -> bool:
    """Verify that scripts/publish.py (in publish mode, NOT --gate) is an ancestor.

    Expected chain for an orchestrated push:
        publish.py --patch|--minor|--major   (orchestrator)
          └─ git push
              └─ git (runs pre-push hook)
                  └─ sh (hook script)
                      └─ publish.py --gate   (this process)

    Walk the parent chain. At least one ancestor must be scripts/publish.py
    WITHOUT the --gate flag (that is, a publish orchestrator — not our own
    gate-mode re-entry).
    """
    expected_abs = str((root / "scripts" / "publish.py").resolve())
    expected_rel = "scripts/publish.py"
    for _pid, cmdline in _get_process_ancestry():
        if "publish.py" not in cmdline:
            continue
        if "--gate" in cmdline:
            continue
        if expected_abs in cmdline or expected_rel in cmdline:
            return True
    return False


def run_gate(root: Path) -> int:
    """Pre-push gate: blocks on any quality issue. Returns 0 if clean."""
    cprint(f"\n{BOLD}Pre-push gate checks{NC}\n")

    # Gate 0: Orchestrator check — only publish.py may trigger a push.
    # Prevents a user from running `git push` directly and bypassing the
    # version-bump / changelog / tag / release pipeline. Uses process
    # ancestry (non-spoofable), NOT env vars.
    cprint(f"{BLUE}[G0] Checking push orchestrator...{NC}")
    if not _called_by_publish_orchestrator(root):
        cprint("")
        cprint(f"  {RED}========================================{NC}")
        cprint(f"  {RED}  BLOCKED: Direct push not allowed{NC}")
        cprint(f"  {RED}  This pre-push hook only accepts pushes{NC}")
        cprint(f"  {RED}  initiated by scripts/publish.py.{NC}")
        cprint(f"  {RED}  Run one of:{NC}")
        cprint(f"  {RED}    uv run python scripts/publish.py --patch{NC}")
        cprint(f"  {RED}    uv run python scripts/publish.py --minor{NC}")
        cprint(f"  {RED}    uv run python scripts/publish.py --major{NC}")
        cprint(f"  {RED}========================================{NC}")
        return 1
    cprint(f"  {GREEN}Orchestrated by publish.py.{NC}")

    # Gate 1: Version bump check — local vs remote
    # Resolves origin/HEAD dynamically so the gate works on both `main` and
    # `master` default branches (and any other name). If none of the
    # candidates return a remote plugin.json, it's a first push and we allow.
    cprint(f"\n{BLUE}[G1] Checking version bump...{NC}")
    local_ver = get_current_version(root)
    if local_ver:
        # Try origin/HEAD first (most reliable), then explicit main/master
        candidates: list[str] = []
        try:
            sym = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                cwd=str(root),
                timeout=10,
            )
            if sym.returncode == 0 and sym.stdout.strip():
                # Output looks like "refs/remotes/origin/main"
                branch = sym.stdout.strip().split("/")[-1]
                candidates.append(f"origin/{branch}")
        except (OSError, subprocess.SubprocessError):
            pass
        for fallback in ("origin/main", "origin/master"):
            if fallback not in candidates:
                candidates.append(fallback)
        remote_ver: str | None = None
        matched_ref: str | None = None
        for ref in candidates:
            try:
                r = subprocess.run(
                    ["git", "show", f"{ref}:.claude-plugin/plugin.json"],
                    capture_output=True,
                    text=True,
                    cwd=str(root),
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            if r.returncode == 0 and r.stdout:
                try:
                    data = json.loads(r.stdout)
                    rv = data.get("version")
                    if isinstance(rv, str):
                        remote_ver = rv
                        matched_ref = ref
                        break
                except json.JSONDecodeError:
                    continue
        if remote_ver is None:
            cprint(f"  {YELLOW}No remote plugin.json found (first push?) — skipping version-bump check.{NC}")
        elif local_ver == remote_ver:
            cprint(f"  {RED}BLOCKED: Version not bumped — local {local_ver} == {matched_ref} {remote_ver}{NC}")
            return 1
        else:
            cprint(f"  {GREEN}Version bump OK: {remote_ver} → {local_ver} (via {matched_ref}){NC}")

    # Gate 2: Lint with ruff. MANDATORY — missing scripts/ dir is a BLOCK.
    cprint(f"\n{BLUE}[G2] Linting...{NC}")
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        cprint(f"  {RED}BLOCKED: scripts/ directory missing — cannot lint.{NC}")
        return 1
    lint_result = subprocess.run(["uv", "run", "ruff", "check", "scripts/"], cwd=str(root), timeout=120)
    if lint_result.returncode != 0:
        cprint(f"  {RED}BLOCKED: Lint issues found{NC}")
        return 1
    cprint(f"  {GREEN}Lint passed.{NC}")

    # Gate 2b: Copy-paste detection (jscpd) — PARITY with ci.yml Mega-Linter COPYPASTE_JSCPD.
    # CI's Lint job fails on jscpd duplication over the .jscpd.json threshold; surface it locally
    # BEFORE the bump/tag/push. jscpd needs Node/npx; if it cannot be obtained, DEGRADE to a
    # non-blocking WARNING (CI still enforces it) — a green gate then does NOT guarantee green CI
    # for the copy-paste dimension (issue #143). NEVER false-block a push on a tool-install failure.
    cprint(f"\n{BLUE}[G2b] Copy-paste check (jscpd, parity with CI)...{NC}")
    jscpd_bin = shutil.which("jscpd")
    # Resolve npx ONCE into a variable so mypy narrows it (a second
    # shutil.which("npx") call INSIDE the list keeps the element typed
    # `str | None`, making base_cmd `list[str | None]` → subprocess.run
    # [arg-type] under --strict). issue #151.
    npx_bin = shutil.which("npx")
    base_cmd = [jscpd_bin] if jscpd_bin else ([npx_bin, "--yes", "jscpd"] if npx_bin else None)
    if base_cmd is None:
        cprint(f"  {YELLOW}WARNING: jscpd/npx not found — copy-paste check SKIPPED locally.{NC}")
        cprint(f"  {YELLOW}CI's Mega-Linter WILL enforce it (.jscpd.json threshold). A green gate does")
        cprint(f"  {YELLOW}NOT guarantee green CI for the copy-paste dimension (issue #143). Install")
        cprint(f"  {YELLOW}Node/npx for full local parity.{NC}")
    else:
        # Probe distinguishes 'jscpd unavailable/uninstallable' (WARN) from 'jscpd ran, found dupes' (BLOCK).
        probe = subprocess.run(base_cmd + ["--version"], cwd=str(root), capture_output=True, text=True, timeout=180)
        if probe.returncode != 0:
            cprint(f"  {YELLOW}WARNING: jscpd could not run (npx fetch/install failed) — SKIPPED locally.{NC}")
            cprint(
                f"  {YELLOW}CI's Mega-Linter WILL enforce it; green gate != green CI for copy-paste (issue #143).{NC}"
            )
        else:
            cp = subprocess.run(base_cmd + ["."], cwd=str(root), timeout=300).returncode
            if cp != 0:
                cprint(f"  {RED}BLOCKED: jscpd found copy-paste duplication over the .jscpd.json threshold{NC}")
                cprint(
                    f"  {RED}(parity with CI Mega-Linter). Reduce duplication or raise the threshold in .jscpd.json.{NC}"
                )
                return 1
            cprint(f"  {GREEN}Copy-paste check passed.{NC}")

    # Gate 2c: Workflow-syntax lint (actionlint) — PARITY with ci.yml Lint job.
    # CI runs actionlint on .github/workflows/*; surface a workflow-syntax error
    # locally BEFORE the bump/tag/push. actionlint is a single static binary; if it
    # is not on PATH, DEGRADE to a non-blocking WARNING (CI still enforces it) — a
    # green gate then does NOT guarantee green CI for the workflow-syntax dimension.
    # NEVER false-block a push on a missing-tool case (the issue #143 pattern).
    cprint(f"\n{BLUE}[G2c] Workflow lint (actionlint, parity with CI)...{NC}")
    wf_dir = root / ".github" / "workflows"
    has_workflows = wf_dir.is_dir() and (any(wf_dir.glob("*.yml")) or any(wf_dir.glob("*.yaml")))
    actionlint_bin = shutil.which("actionlint")
    if not has_workflows:
        cprint(f"  {GREEN}No workflows to lint — skipped.{NC}")
    elif actionlint_bin is None:
        cprint(f"  {YELLOW}WARNING: actionlint not found — workflow lint SKIPPED locally.{NC}")
        cprint(f"  {YELLOW}CI's Lint job WILL enforce it. A green gate does NOT guarantee green CI")
        cprint(f"  {YELLOW}for the workflow-syntax dimension. Install actionlint for full parity.{NC}")
    else:
        al = subprocess.run([actionlint_bin], cwd=str(root), timeout=120).returncode
        if al != 0:
            cprint(f"  {RED}BLOCKED: actionlint found workflow-syntax errors (parity with CI Lint job).{NC}")
            return 1
        cprint(f"  {GREEN}Workflow lint passed.{NC}")

    # Gate 2d: Static type-check (mypy) — PARITY with ci.yml Lint job
    # (`uv run mypy scripts/ --ignore-missing-imports`). Surface a type error
    # locally BEFORE the bump/tag/push. A `--version` probe distinguishes
    # 'mypy unavailable' (WARN + skip, never false-block) from 'mypy ran, found
    # errors' (BLOCK) — the issue #143 degrade-gracefully pattern.
    cprint(f"\n{BLUE}[G2d] Type-check (mypy, parity with CI)...{NC}")
    mypy_bin = shutil.which("mypy")
    mypy_cmd = [mypy_bin] if mypy_bin else (["uv", "run", "mypy"] if shutil.which("uv") else None)
    if mypy_cmd is None:
        cprint(f"  {YELLOW}WARNING: mypy/uv not found — type-check SKIPPED locally.{NC}")
        cprint(f"  {YELLOW}CI's Lint job WILL enforce it; a green gate does NOT guarantee green CI for types.{NC}")
    else:
        probe = subprocess.run(mypy_cmd + ["--version"], cwd=str(root), capture_output=True, text=True, timeout=120)
        if probe.returncode != 0:
            cprint(f"  {YELLOW}WARNING: mypy could not run — type-check SKIPPED locally.{NC}")
            cprint(f"  {YELLOW}CI's Lint job WILL enforce it; green gate != green CI for types.{NC}")
        else:
            mt = subprocess.run(
                mypy_cmd + ["scripts/", "--ignore-missing-imports"], cwd=str(root), timeout=300
            ).returncode
            if mt != 0:
                cprint(f"  {RED}BLOCKED: mypy found type errors in scripts/ (parity with CI Lint job).{NC}")
                return 1
            cprint(f"  {GREEN}Type-check passed.{NC}")

    # Gate 3: Validate via REMOTE CPV validator. MANDATORY — no skip, no exceptions.
    # CORNERSTONE: a plugin cannot be pushed unless validation passes with 0
    # blocking issues (WARNING allowed). The validator is ALWAYS fetched from
    # GitHub so a tampered local copy cannot weaken the rules.
    cprint(f"\n{BLUE}[G3] Validating plugin (remote CPV)...{NC}")
    if not shutil.which("uvx"):
        cprint(f"  {RED}BLOCKED: uvx not found on PATH.{NC}")
        return 1
    ve = subprocess.run(
        [
            "uvx",
            "--from",
            "git+https://github.com/Emasoft/claude-plugins-validation@v5.21.1",
            "--with",
            "pyyaml",
            "cpv-remote-validate",
            "plugin",
            ".",
            "--strict",
        ],
        cwd=str(root),
        timeout=600,
    ).returncode
    # Exit codes: 0=pass, 1=CRITICAL, 2=MAJOR, 3=MINOR, 4=NIT, 5+=WARNING
    if ve != 0 and ve < 5:
        labels = {1: "CRITICAL", 2: "MAJOR", 3: "MINOR", 4: "NIT"}
        cprint(f"  {RED}BLOCKED: {labels.get(ve, f'exit {ve}')} issues found{NC}")
        return 1
    cprint(f"  {GREEN}Validation passed (0 blocking issues).{NC}")

    # Gate 4: Tests. MANDATORY — missing tests/ dir or zero tests is a BLOCK.
    cprint(f"\n{BLUE}[G4] Running tests...{NC}")
    test_dir = root / "tests"
    if not (test_dir.is_dir() and any(test_dir.glob("test_*.py"))):
        cprint(f"  {RED}BLOCKED: tests/ directory missing or empty.{NC}")
        cprint(f"  {RED}Every CPV plugin MUST ship tests.{NC}")
        return 1
    try:
        te = subprocess.run(
            ["uv", "run", "pytest", "tests/", "-x", "-q", "--tb=short"], cwd=str(root), timeout=300
        ).returncode
    except subprocess.TimeoutExpired:
        cprint(f"  {RED}BLOCKED: Tests timed out after 300s.{NC}")
        return 1
    if te == 5:
        cprint(f"  {RED}BLOCKED: pytest collected 0 tests.{NC}")
        return 1
    if te != 0:
        cprint(f"  {RED}BLOCKED: Tests failed{NC}")
        return 1
    cprint(f"  {GREEN}Tests passed.{NC}")

    cprint(f"\n{GREEN}{BOLD}All gates passed.{NC}")
    return 0


# -- Pipeline stages -----------------------------------------------------------


def stage_bypass_guard() -> None:
    """Step 0: Reject any env var that could bypass a check. No exceptions.

    Issue #22 hardening (v2.86.0): broadened from a fixed allowlist to
    prefix-pattern matching. Any env var matching ``PLUGIN_SKIP_*``,
    ``CPV_SKIP_*``, ``SKIP_*``, or named ``NO_VERIFY`` aborts the publish.
    Closes the loophole where a fresh skip name (e.g. ``CPV_SKIP_GATE7``)
    that was not in the original explicit list would silently slip past.

    Two explicit infrastructure exemptions remain — both are read-only
    overrides used by CPV's own integrity / auth subsystems and never
    skip a gate:
        * ``CPV_SKIP_GITHUB_INTEGRITY=1`` — used to bypass GitHub-anchored
          integrity check (see cpv_integrity.py). The integrity check is
          a defence against tampering, NOT a publish gate.
        * ``CPV_SKIP_GH_AUTH_CHECK=1`` — used by `_ensure_gh_auth` to bypass
          the `gh auth status` round-trip on flaky networks. Auth still
          has to work for the actual `git push` / `gh release create`;
          this only skips the precheck.

    Both are documented exemptions, listed below and excluded from the
    pattern match.
    """
    cprint(f"\n{BOLD}[0/17] Checking for bypass attempts...{NC}")
    # Explicit infrastructure exemptions — see docstring above.
    exemptions = {"CPV_SKIP_GITHUB_INTEGRITY", "CPV_SKIP_GH_AUTH_CHECK"}
    forbidden_prefixes = ("PLUGIN_SKIP_", "CPV_SKIP_", "SKIP_")
    forbidden_exact = {"NO_VERIFY"}
    attempted = [
        v
        for v in sorted(os.environ)
        if (v.startswith(forbidden_prefixes) or v in forbidden_exact) and v not in exemptions
        if os.environ.get(v)
    ]
    if attempted:
        cprint(f"  {RED}BLOCKED: forbidden env vars set: {', '.join(attempted)}{NC}")
        cprint(f"  {RED}The publish pipeline enforces every check. Fix failures, do not skip them.{NC}")
        cprint(f"  {DIM}(infrastructure exemptions: {', '.join(sorted(exemptions))}){NC}")
        sys.exit(1)
    cprint(f"  {GREEN}No bypass vars set.{NC}")


def stage_check_clean(root: Path) -> None:
    """Step 1: Working tree must be clean."""
    cprint(f"\n{BOLD}[1/17] Checking working tree...{NC}")
    r = run(["git", "status", "--porcelain"], cwd=root, capture=True)
    if r.stdout.strip():
        cprint(f"  {RED}Working tree is dirty. Commit or stash changes first.{NC}")
        cprint(r.stdout)
        sys.exit(1)
    cprint(f"  {GREEN}Clean.{NC}")


def stage_lint(root: Path) -> None:
    """Step 2: Lint + typecheck (ruff + mypy). MANDATORY — no skip.

    Runs ruff for style/syntax and mypy for static types in the same stage.
    Both must succeed — the cornerstone rule forbids any push with lint or
    type errors. Type-checking runs BEFORE the test suite so the cheap fails
    come before the expensive ones.
    """
    cprint(f"\n{BOLD}[2/17] Linting + type-checking...{NC}")
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        cprint(f"  {RED}BLOCKED: scripts/ directory missing — cannot lint.{NC}")
        sys.exit(1)
    cprint(f"  {BLUE}ruff check scripts/{NC}")
    run(["uv", "run", "ruff", "check", "scripts/"], cwd=root)
    cprint(f"  {BLUE}mypy scripts/ --ignore-missing-imports{NC}")
    run(["uv", "run", "mypy", "scripts/", "--ignore-missing-imports"], cwd=root)
    cprint(f"  {GREEN}Lint + typecheck passed.{NC}")


# Issue #31 (v2.98.0): browser-orphan cleanup signatures.
#
# A pytest run that spawns Playwright / dev-browser pages can leave
# behind dozens of `Chrome for Testing` / `chromium` / `headless_shell`
# processes if the test code (or fixtures) forget to close pages. Over
# a long debug session those orphans pile up, exhausting file
# descriptors or RAM and eventually crashing the browser or making
# the machine unresponsive. The baseline-diff cleanup below catches
# every leak regardless of test-code quality. NEVER skips tests — the
# iron rule (no plugin with issues pushed) is preserved.
_BROWSER_ORPHAN_SIGNATURES = (
    "Chrome for Testing",
    "chrome-for-testing",
    "headless_shell",
    "Chromium.app/Contents",
    "chromium-browser",
    "/playwright/",
    "playwright-core",
)


def _snapshot_browser_pids() -> set:
    """Snapshot-then-grep — never live-grep — for browser-signature PIDs."""
    try:
        snap = subprocess.run(
            ["ps", "-eo", "pid,command"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if snap.returncode != 0 or not snap.stdout:
        return set()
    pids = set()
    for raw_line in snap.stdout.strip().split("\n")[1:]:
        line = raw_line.strip()
        if not line:
            continue
        try:
            pid_str, cmd = line.split(None, 1)
            pid = int(pid_str)
        except (ValueError, IndexError):
            continue
        if any(sig in cmd for sig in _BROWSER_ORPHAN_SIGNATURES):
            pids.add(pid)
    return pids


def _cleanup_browser_orphans(baseline_pids: set) -> int:
    """Kill browser-signature PIDs that appeared since ``baseline_pids``.

    Baseline-diff: PIDs in baseline are pre-existing (maintainer's own
    daily browser) — NEVER killed. Only PIDs that came into existence
    during the pytest run are candidates.
    """
    import signal
    import time

    current = _snapshot_browser_pids()
    new_pids = current - baseline_pids
    if not new_pids:
        return 0
    killed = 0
    for pid in new_pids:
        try:
            os.kill(pid, signal.SIGTERM)
            killed += 1
        except (ProcessLookupError, PermissionError, OSError):
            pass
    if killed:
        time.sleep(1.5)
        for pid in new_pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
    return killed


def stage_tests(root: Path) -> None:
    """Step 3: Run pytest. MANDATORY — no skip, no exceptions.

    Cornerstone rule: failing tests block the push. Missing tests/ directory
    is a scaffolding bug and must be fixed, not bypassed.

    Order: tests run BEFORE the CPV validator so behavioral regressions fail
    fast on unit tests before the structural validator inspects the manifest.

    Issue #31 (v2.98.0): wrap the pytest invocation in a baseline-diff
    browser-orphan cleanup so dev-browser / Playwright leaks do not
    pile up Chrome-for-Testing processes. Tests still run
    unconditionally — the cleanup is a safety net, not a skip
    mechanism.
    """
    cprint(f"\n{BOLD}[3/17] Running tests...{NC}")
    test_dir = root / "tests"
    if not test_dir.is_dir():
        cprint(f"  {RED}BLOCKED: tests/ directory missing.{NC}")
        cprint(f"  {RED}Every CPV plugin MUST ship a tests/ directory.{NC}")
        sys.exit(1)
    baseline_browser_pids = _snapshot_browser_pids()
    try:
        r = run(["uv", "run", "pytest", "tests/", "-x", "-q", "--tb=short"], cwd=root, check=False)
    finally:
        killed = _cleanup_browser_orphans(baseline_browser_pids)
        if killed:
            cprint(f"  {YELLOW}Cleaned up {killed} orphaned browser process(es) spawned by pytest.{NC}")
    if r.returncode == 5:
        # pytest exit 5 = no tests collected. This is ALSO a block — no exceptions.
        cprint(f"  {RED}BLOCKED: pytest collected 0 tests.{NC}")
        cprint(f"  {RED}Every CPV plugin MUST ship at least one test.{NC}")
        sys.exit(1)
    if r.returncode != 0:
        cprint(f"  {RED}BLOCKED: tests failed (exit {r.returncode}).{NC}")
        sys.exit(r.returncode)
    cprint(f"  {GREEN}Tests passed.{NC}")


def stage_validate(root: Path) -> None:
    """Step 4: Validate plugin via REMOTE CPV validator. MANDATORY — no skip.

    Cornerstone rule: a plugin cannot be pushed unless validation passes
    with 0 issues (WARNING allowed). The validator is ALWAYS fetched from
    GitHub (git+https://github.com/Emasoft/claude-plugins-validation@v5.21.1) via
    uvx so a local tampered copy cannot weaken the rules. No exceptions.

    Order: runs AFTER lint + tests so behavioral regressions fail fast
    before the structural validator even looks at the manifest.
    """
    cprint(f"\n{BOLD}[4/17] Validating plugin (remote CPV)...{NC}")
    if not shutil.which("uvx"):
        cprint(f"  {RED}BLOCKED: uvx not found on PATH.{NC}")
        cprint(f"  {RED}Install via: brew install uv  or  pip install uv{NC}")
        sys.exit(1)
    # Fetch CPV from GitHub and run validate_plugin remotely. --strict blocks
    # on CRITICAL(1), MAJOR(2), MINOR(3), NIT(4); WARNING(5+) passes.
    run(
        [
            "uvx",
            "--from",
            "git+https://github.com/Emasoft/claude-plugins-validation@v5.21.1",
            "--with",
            "pyyaml",
            "cpv-remote-validate",
            "plugin",
            ".",
            "--strict",
        ],
        cwd=root,
    )
    cprint(f"  {GREEN}Validation passed (0 blocking issues).{NC}")


def stage_ci_preflight(root: Path) -> None:
    """Step 4b→5 (renumbered): CI-parity preflight via REMOTE CPV. MANDATORY — no skip.

    WHY THIS STAGE EXISTS. `validate_plugin --strict` (stage 4) does NOT run the
    gates this plugin's own GitHub-CI Lint job runs: jscpd copy-paste, actionlint,
    mypy, the `uv sync --extra dev` resolve, the enabled Mega-Linter sub-linters,
    and CPV's static CI-parity defect detectors. Without this stage a publish
    passes every LOCAL gate, bumps the version, commits, TAGS, PUSHES, and cuts a
    GitHub release — and only THEN goes red on GitHub, with the broken pipeline
    already shipped to everyone who installs the plugin.

    PLACEMENT IS LOAD-BEARING: this runs BEFORE stage_bump / stage_commit_and_push
    / stage_gh_release, so a parity failure aborts with the working tree untouched
    instead of leaving a half-published release behind.

    A MISSING TOOL NEVER BLOCKS THE PUBLISH. `ci-preflight` exits non-zero ONLY
    when a gate actually FAILED; every tool-absent case (no npx, no actionlint,
    no checkov, ...) degrades to a non-blocking WARNING and still exits 0. So a
    lean machine publishes exactly as before — it just gets less LOCAL coverage,
    which CI still enforces. Do not "harden" this into a hard tool requirement.
    """
    cprint(f"\n{BOLD}[5/17] CI-parity preflight (remote CPV)...{NC}")
    if not shutil.which("uvx"):
        cprint(f"  {RED}BLOCKED: uvx not found on PATH.{NC}")
        cprint(f"  {RED}Install via: brew install uv  or  pip install uv{NC}")
        sys.exit(1)
    rc = subprocess.run(
        [
            "uvx",
            "--from",
            "git+https://github.com/Emasoft/claude-plugins-validation@v5.21.1",
            "--with",
            "pyyaml",
            "cpv-remote-validate",
            "ci-preflight",
            ".",
        ],
        cwd=str(root),
    ).returncode
    if rc != 0:
        cprint(f"  {RED}BLOCKED: CI-parity preflight FAILED.{NC}")
        cprint(f"  {RED}The gates listed above would fail GitHub CI — and without this{NC}")
        cprint(f"  {RED}stage they would only have failed AFTER the tag and release were{NC}")
        cprint(f"  {RED}pushed. Fix the causes, then re-run publish.py.{NC}")
        sys.exit(1)
    cprint(f"  {GREEN}CI-parity preflight passed.{NC}")


# ── Marketplace-registration helpers (mirror of CPV's own publish.py Gate 6) ─


def _find_parent_marketplace(plugin_root: Path) -> Path | None:
    """Walk up looking for a parent marketplace.json (Layout B signature)."""
    current = plugin_root.resolve().parent
    while current != current.parent:
        mp = current / ".claude-plugin" / "marketplace.json"
        if mp.is_file():
            try:
                rel = plugin_root.resolve().relative_to(current)
                parts = rel.parts
                if len(parts) >= 2 and parts[0] == "plugins":
                    return current
            except ValueError:
                pass
            return None
        current = current.parent
    return None


def _detect_layout(plugin_root: Path) -> tuple[str, dict]:
    """Detect Layout A (standalone+notify), Layout B (nested), or 'none'."""
    parent = _find_parent_marketplace(plugin_root)
    if parent is not None:
        return "B", {"marketplace_root": parent, "plugin_name": plugin_root.name}
    notify_wf = plugin_root / ".github" / "workflows" / "notify-marketplace.yml"
    if notify_wf.is_file():
        try:
            content = notify_wf.read_text(encoding="utf-8")
        except OSError:
            content = ""
        m_owner = re.search(r"^\s*MARKETPLACE_OWNER:\s*[\"']?([^\"'\s]+)[\"']?\s*$", content, re.MULTILINE)
        m_repo = re.search(r"^\s*MARKETPLACE_REPO:\s*[\"']?([^\"'\s]+)[\"']?\s*$", content, re.MULTILINE)
        return "A", {
            "notify_workflow": notify_wf,
            "mkt_owner": m_owner.group(1) if m_owner else None,
            "mkt_repo": m_repo.group(1) if m_repo else None,
        }
    return "none", {}


def _gh_secret_exists(plugin_root: Path, secret_name: str) -> bool:
    """Check whether a GitHub secret with the given name exists on this repo."""
    gh = shutil.which("gh")
    if gh is None:
        return False
    r = subprocess.run([gh, "secret", "list"], cwd=str(plugin_root), capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return False
    for line in r.stdout.splitlines():
        if line.split("\t", 1)[0].strip() == secret_name:
            return True
    return False


def _current_repo_slug(plugin_root: Path) -> str | None:
    """Return owner/repo slug for current git origin, or None."""
    r = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=str(plugin_root), capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return None
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", r.stdout.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _read_plugin_name(plugin_root: Path) -> str:
    pj = plugin_root / ".claude-plugin" / "plugin.json"
    if pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            name = data.get("name")
            if isinstance(name, str) and name:
                return name
        except (OSError, json.JSONDecodeError):
            pass
    return plugin_root.name


def _fetch_remote_marketplace_json(owner: str, repo: str) -> dict | None:
    gh = shutil.which("gh")
    if gh is None:
        return None
    r = subprocess.run(
        [
            gh,
            "api",
            f"repos/{owner}/{repo}/contents/.claude-plugin/marketplace.json",
            "-H",
            "Accept: application/vnd.github.raw+json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _remote_has_receiver_workflow(owner: str, repo: str) -> bool:
    gh = shutil.which("gh")
    if gh is None:
        return False
    r = subprocess.run(
        [gh, "api", f"repos/{owner}/{repo}/contents/.github/workflows"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        return False
    try:
        entries = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False
    if not isinstance(entries, list):
        return False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "")
        if not isinstance(name, str) or not name.endswith((".yml", ".yaml")):
            continue
        f = subprocess.run(
            [
                gh,
                "api",
                f"repos/{owner}/{repo}/contents/.github/workflows/{name}",
                "-H",
                "Accept: application/vnd.github.raw+json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if f.returncode == 0 and "repository_dispatch" in f.stdout:
            return True
    return False


def _plugin_in_remote_marketplace(mkt_json: dict, plugin_name: str, expected_repo: str | None) -> bool:
    """Accept github/url/git source forms; match URL slug for url|git (issue #25 Defect A)."""
    plugins = mkt_json.get("plugins")
    if not isinstance(plugins, list):
        return False
    for entry in plugins:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") != plugin_name:
            continue
        source = entry.get("source")
        if not isinstance(source, dict):
            continue
        stype = source.get("source") or source.get("type")
        if stype == "github":
            if expected_repo is None or source.get("repo") == expected_repo:
                return True
        elif stype in ("url", "git"):
            url = source.get("url")
            if expected_repo is None:
                return True
            if isinstance(url, str):
                norm = url.removesuffix(".git").rstrip("/")
                if norm.endswith("/" + expected_repo) or norm.endswith(":" + expected_repo):
                    return True
    return False


def stage_marketplace_registration(root: Path) -> None:
    """Step 5→6 (renumbered): Verify the plugin is wired to its marketplace for auto-updates.

    Mirror of CPV's own publish.py Gate 6. Three modes:
      - Layout A (standalone + notify-marketplace.yml): verifies workflow,
        MARKETPLACE_PAT secret, remote marketplace.json registration,
        remote receiver workflow with repository_dispatch trigger
      - Layout B (nested under <marketplace>/plugins/<name>/): refuses to
        publish from the nested folder, requires running at marketplace root
      - 'none' (no marketplace wiring): emits a WARNING and proceeds — valid
        for first releases or experimental standalone plugins
    """
    cprint(f"\n{BOLD}[6/17] Marketplace-registration check...{NC}")
    layout, details = _detect_layout(root)

    if layout == "none":
        cprint(f"  {YELLOW}WARNING: no marketplace registration found for this plugin.{NC}")
        cprint(f"  {YELLOW}If you intend to publish to a marketplace, run the{NC}")
        cprint(f"  {YELLOW}cpv-setup-marketplace-auto-notification skill to wire up auto-updates.{NC}")
        cprint(f"  {YELLOW}Allowing release to proceed (standalone/experimental mode).{NC}")
        return

    if layout == "A":
        cprint("  Layout A detected (standalone plugin repo)")
        notify_wf = details.get("notify_workflow")
        mkt_owner = details.get("mkt_owner")
        mkt_repo = details.get("mkt_repo")
        if not notify_wf or not Path(notify_wf).is_file():
            cprint(f"  {RED}BLOCKED: .github/workflows/notify-marketplace.yml missing.{NC}")
            sys.exit(1)
        if not mkt_owner or not mkt_repo:
            cprint(f"  {RED}BLOCKED: notify-marketplace.yml has no MARKETPLACE_OWNER/MARKETPLACE_REPO.{NC}")
            sys.exit(1)
        cprint(f"  target marketplace: {mkt_owner}/{mkt_repo}")
        if shutil.which("gh") is None:
            cprint(f"  {RED}BLOCKED: gh CLI not installed — cannot verify secret/marketplace.{NC}")
            sys.exit(1)
        if not _gh_secret_exists(root, "MARKETPLACE_PAT"):
            cprint(f"  {RED}BLOCKED: MARKETPLACE_PAT secret not configured on this plugin repo.{NC}")
            cprint(
                f"  {RED}  Fix: uv run python scripts/set_marketplace_pat.py {_current_repo_slug(root) or 'OWNER/REPO'}{NC}"
            )
            sys.exit(1)
        cprint(f"  {GREEN}MARKETPLACE_PAT secret configured{NC}")
        mkt_json = _fetch_remote_marketplace_json(mkt_owner, mkt_repo)
        if mkt_json is None:
            cprint(f"  {RED}BLOCKED: cannot fetch marketplace.json from {mkt_owner}/{mkt_repo}.{NC}")
            sys.exit(1)
        plugin_name = _read_plugin_name(root)
        slug = _current_repo_slug(root)
        if not _plugin_in_remote_marketplace(mkt_json, plugin_name, slug):
            cprint(
                f"  {RED}BLOCKED: plugin '{plugin_name}' not registered in {mkt_owner}/{mkt_repo} marketplace.json.{NC}"
            )
            cprint(
                f'  {RED}  Add an entry: {{"name": "{plugin_name}", "source": {{"source": "github", "repo": "{slug}"}}}}{NC}'
            )
            sys.exit(1)
        cprint(f"  {GREEN}Plugin registered in remote marketplace.json{NC}")
        if not _remote_has_receiver_workflow(mkt_owner, mkt_repo):
            cprint(
                f"  {RED}BLOCKED: remote marketplace {mkt_owner}/{mkt_repo} has no workflow with repository_dispatch trigger.{NC}"
            )
            cprint(f"  {RED}  See cpv-setup-marketplace-auto-notification skill.{NC}")
            sys.exit(1)
        cprint(f"  {GREEN}Remote marketplace has receiver workflow{NC}")
        cprint(f"  {GREEN}Layout A marketplace registration verified.{NC}")
        return

    if layout == "B":
        cprint("  Layout B detected (nested plugin under marketplace repo)")
        marketplace_root_raw = details.get("marketplace_root")
        marketplace_root: Path | None = marketplace_root_raw if isinstance(marketplace_root_raw, Path) else None
        plugin_name_raw = details.get("plugin_name")
        # Note: no type annotation here — mypy's no-redef rule complains even
        # though the Layout A branch above returns before reaching this
        # point. Plain assignment avoids the false positive in the generated
        # template output (which downstream CI runs with mypy --strict).
        plugin_name = plugin_name_raw if isinstance(plugin_name_raw, str) else root.name
        if marketplace_root is None:
            cprint(f"  {RED}BLOCKED: Layout B detected but marketplace_root unresolved.{NC}")
            sys.exit(1)
        if root.resolve() != marketplace_root.resolve():
            cprint(f"  {RED}BLOCKED: This is a Layout B nested plugin.{NC}")
            cprint(f"  {RED}  publish.py must run at the MARKETPLACE root, not the nested folder.{NC}")
            cprint(f"  {RED}  Bumping a nested plugin alone breaks the atomic marketplace tag.{NC}")
            cprint(f"  {RED}  Fix: cd {marketplace_root} && uv run python scripts/publish.py --patch{NC}")
            sys.exit(1)
        mp_path = marketplace_root / ".claude-plugin" / "marketplace.json"
        try:
            mp_data = json.loads(mp_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            cprint(f"  {RED}BLOCKED: cannot read {mp_path}: {e}{NC}")
            sys.exit(1)
        entries = mp_data.get("plugins") if isinstance(mp_data, dict) else None
        if not isinstance(entries, list):
            cprint(f"  {RED}BLOCKED: marketplace.json has no 'plugins' array.{NC}")
            sys.exit(1)
        if not any(isinstance(e, dict) and e.get("name") == plugin_name for e in entries):
            cprint(f"  {RED}BLOCKED: plugin '{plugin_name}' not registered in {mp_path}.{NC}")
            cprint(f'  {RED}  Add: {{"name": "{plugin_name}", "source": "./plugins/{plugin_name}"}}{NC}')
            sys.exit(1)
        cprint(f"  {GREEN}Plugin '{plugin_name}' registered in parent marketplace.json{NC}")
        cprint(f"  {GREEN}Layout B marketplace registration verified.{NC}")


# -- Secret scan (canon Gate 3d, issue #217) ------------------------------------
#
# The canonical pipeline documented a pre-push secret scan it never implemented;
# a `tskey-auth-…` literal consequently reached a plugin's `main`, GitHub's own
# secret scanning flagged it, and the alert sat open for 85 days while every
# local gate passed. This repo's release gate must not inherit that hole.
#
# Implementation shape differs from canon BY DESIGN and follows this repo's
# no-vendoring rule (stage_validate's docstring): canon imports
# cpv_install_scanners / validate_security / cpv_validation_common from its own
# tree. This repo fetches CPV remotely via uvx and vendors nothing, so the
# scan runs the trufflehog BINARY directly with the same flags canon's
# check_trufflehog passes (--results widening from issue #219, --concurrency),
# and uses `git ls-files` as the unshipped-paths oracle instead of CPV's
# GitignoreFilter — same verdict, one fewer dependency. Redaction is not this
# stage's job; it reports and blocks.


def _trufflehog_scan_paths(root: Path) -> list[str] | None:
    """Git-tracked files under `root`, relative — the set a release actually ships.

    Returns None when git itself is unreadable (the caller then fails closed
    rather than scanning a guessed set). Untracked scratch is excluded on the
    same reasoning as canon's gitignore filter: gitignored = not shipped, and
    dev-scratch trees legitimately quote fixture credentials.
    """
    try:
        r = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(root),
            capture_output=True,
            text=False,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return [p.decode("utf-8", "replace") for p in r.stdout.split(b"\0") if p]


def _find_trufflehog() -> str | None:
    """Locate trufflehog: PATH first, then the go-install / user-local bin dirs.

    Returns the resolved binary path, or None. Deliberately does NOT mutate
    ``os.environ["PATH"]``: CPV's skillaudit ENV_INJECTION detector (persistence
    class) flags an env write from a release script, and canon itself hit that
    exact self-block on its own generator (upstream issue #231) — locating the
    binary explicitly is the same capability without the env write.
    """
    found = shutil.which("trufflehog")
    if found:
        return found
    for candidate in (
        Path(os.environ.get("GOPATH", str(Path.home() / "go"))) / "bin" / "trufflehog",
        Path.home() / ".local" / "bin" / "trufflehog",
    ):
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


def stage_secret_scan(root: Path) -> None:
    """Step 7: BLOCK the publish on any detected credential (canon CPV#217).

    Placement is deliberate: this runs strictly BEFORE the bump/commit/tag/push,
    so a detected credential aborts with the tree untouched. A gate that fired
    after the push could not un-publish anything.

    Cannot-check is NOT clean: a missing binary that cannot be installed, or an
    unreadable file list, BLOCKS rather than passing, because "we never finished
    looking" and "we looked and found nothing" must not produce the same verdict.
    """
    cprint(f"\n{BOLD}[7/17] Secret scan (trufflehog)...{NC}")
    if os.environ.get("CPV_PUBLISH_SKIP_SECRET_SCAN") == "1":
        cprint(f"  {RED}BLOCKED: CPV_PUBLISH_SKIP_SECRET_SCAN=1 — the secret scan has no bypass.{NC}")
        cprint(f"  {RED}The pipeline enforces every check. Fix failures, do not skip them.{NC}")
        sys.exit(1)

    # trufflehog is a DEPENDENCY of this gate, not a precondition the user is
    # asked to satisfy: canon installs it like every other external scanner
    # (brew → `go install`). Only a FAILED install blocks: telling a publisher
    # to go install something is a worse answer than installing it.
    trufflehog_bin = _find_trufflehog()
    if trufflehog_bin is None:
        cprint("  trufflehog missing — installing it (the gate ships it as a dependency)...")
        installed = False
        brew = shutil.which("brew")
        if brew:
            try:
                installed = (
                    subprocess.run(
                        [brew, "install", "trufflehog"],
                        capture_output=True,
                        text=True,
                        timeout=600,
                        check=False,
                    ).returncode
                    == 0
                )
            except (OSError, subprocess.SubprocessError):
                installed = False
        if not installed and shutil.which("go"):
            try:
                subprocess.run(
                    ["go", "install", "github.com/trufflesecurity/trufflehog/v3@latest"],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                pass
        trufflehog_bin = _find_trufflehog()
    if trufflehog_bin is None:
        cprint(
            f"  {RED}BLOCKED: trufflehog could not be installed — the release was NOT secret-scanned.{NC}"
        )
        cprint(f"  {RED}This is UNKNOWN, not clean, so the publish is blocked.{NC}")
        cprint(f"  {YELLOW}Install it manually and re-run:  brew install trufflehog{NC}")
        sys.exit(1)

    scan_paths = _trufflehog_scan_paths(root)
    if scan_paths is None:
        cprint(f"  {RED}BLOCKED: could not enumerate git-tracked files — the scan cannot run honestly.{NC}")
        sys.exit(1)

    concurrency = max(1, os.cpu_count() or 4)
    # --results widening (canon issue #219): the default bucket set OMITS
    # `filtered_unverified` — where an expired, revoked, or unreachable-service
    # credential lands. A committed credential is a leak whether or not a
    # runner can reach its API, so ask for every bucket.
    cmd = [
        trufflehog_bin,
        "filesystem",
        "--json",
        "--no-update",
        "--fail",
        "--results=verified,unknown,unverified,filtered_unverified",
        f"--concurrency={concurrency}",
        *scan_paths,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # A timed-out secret scan MUST NOT read as a clean one: "we never
        # finished looking" is not "we looked and found nothing" (canon #218).
        cprint(f"  {RED}BLOCKED: trufflehog timed out after 1800s — scan INCOMPLETE, secrets UNKNOWN.{NC}")
        cprint(f"  {RED}Re-run with a narrower scan, or commit generated trees so they are scannable.{NC}")
        sys.exit(1)
    if result.returncode not in (0, 183):
        # 183 = trufflehog's "findings found" exit with --fail; anything else
        # is a scan that never reached a verdict.
        cprint(f"  {RED}BLOCKED: trufflehog exited {result.returncode} — the scan did not complete.{NC}")
        if result.stderr:
            for line in result.stderr.strip().splitlines()[-5:]:
                cprint(f"  {RED}    {line}{NC}")
        sys.exit(1)

    findings: list[dict[str, Any]] = []
    for raw_line in (result.stdout or "").splitlines():
        raw_line = raw_line.strip()
        if not raw_line.startswith("{"):
            continue
        try:
            finding = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(finding, dict) and finding.get("SourceMetadata"):
            findings.append(finding)
    if not findings:
        cprint(f"  {GREEN}No credentials detected (700+ verified-secret detectors clean).{NC}")
        return

    cprint(f"  {RED}BLOCKED: secret scan found {len(findings)} credential finding(s){NC}")
    for f in findings[:20]:
        detector = f.get("DetectorName") or f.get("detector") or "?"
        verified = bool(f.get("Verified") or f.get("verified", False))
        source_metadata = f.get("SourceMetadata", {}) or {}
        data = source_metadata.get("Data", {}) if isinstance(source_metadata, dict) else {}
        filesystem = data.get("Filesystem", {}) if isinstance(data, dict) else {}
        rel = filesystem.get("file", "?") if isinstance(filesystem, dict) else "?"
        line_no = filesystem.get("line", "?") if isinstance(filesystem, dict) else "?"
        cprint(f"  {RED}  [{'VERIFIED' if verified else 'UNVERIFIED'}] {detector}: {rel}:{line_no}{NC}")
    if len(findings) > 20:
        cprint(f"  {RED}  ... and {len(findings) - 20} more{NC}")
    cprint(
        f"  {RED}Fix before publishing. Redaction is NOT this gate's job — a verified live "
        f"credential must be ROTATED and purged from git history, not merely deleted "
        f"from the working tree.{NC}"
    )
    sys.exit(1)


# -- Fork-parity probe (canon Gate 3c, TRDD-4KQXN8ZW) ----------------------------
#
# `multiprocessing` defaults to fork on Linux and spawn on macOS, so a deadlock
# caused by forking a multithreaded process is invisible to a developer on a Mac
# and fatal in CI (the v3.23.0 class: a green 11,484-test local suite, then a
# >300s timeout on Linux that failed CI and Release). This stage re-runs the
# suite with the start method forced to fork, removing the platform asymmetry
# before anything is bumped, committed, tagged or pushed.


_FORK_PARITY_TIMEOUT_ENV = "PLUGIN_FORK_PARITY_TIMEOUT"
# ~11x the 162s canon measured on its own suite. Generous on purpose: this
# deadline exists to catch a DEADLOCK (unbounded), not to police a slow machine.
_DEFAULT_FORK_PARITY_TIMEOUT = 1800.0


def _fork_parity_timeout() -> float:
    """Resolve the fork-parity deadline.

    An empty, zero, negative, or unparseable value falls back to the default,
    so a typo can never DISABLE the guard or set a near-zero ceiling that would
    fail every publish.
    """
    raw = os.environ.get(_FORK_PARITY_TIMEOUT_ENV, "").strip()
    if not raw:
        return _DEFAULT_FORK_PARITY_TIMEOUT
    try:
        override = float(raw)
    except ValueError:
        return _DEFAULT_FORK_PARITY_TIMEOUT
    return override if override > 0 else _DEFAULT_FORK_PARITY_TIMEOUT


def stage_fork_parity(root: Path) -> None:
    """Step 8: re-run the suite the way LINUX will run it.

    PLACEMENT IS LOAD-BEARING: this runs strictly BEFORE the bump (step 10),
    commit/tag/push (step 13), so a hang aborts with the tree untouched instead
    of stranding a tag for a release that was never cut.

    NEVER FALSE-BLOCKS. On Linux the ordinary run already forks, so the probe
    reports "already-native" and skips rather than doubling CI. Where fork does
    not exist (Windows) it degrades to a WARNING. It blocks ONLY when the probe
    actually ran and the suite actually failed — but note a TIMEOUT *is* a
    failure here, because a hang is this defect's signature, not an
    inconclusive result.
    """
    cprint(f"\n{BOLD}[8/17] Linux fork-parity probe...{NC}")
    if fork_parity_supported is None or run_under_linux_fork_default is None:
        cprint(f"  {YELLOW}WARNING: scripts/cpv_fork_parity.py missing — probe SKIPPED.{NC}")
        cprint(f"  {YELLOW}CI may still catch a fork deadlock that this run cannot see.{NC}")
        return

    runnable, reason = fork_parity_supported()
    if not runnable:
        # "cannot check" is reported as exactly that — never folded into a pass.
        cprint(f"  {YELLOW}Skipped: {reason}{NC}")
        return

    cmd = ["uv", "run", "pytest", "tests/", "-q", "--tb=short"]
    timeout = _fork_parity_timeout()
    cprint(f"  {reason}; deadline {timeout:.0f}s")
    result = run_under_linux_fork_default(cmd, root, timeout=timeout)

    if result.blocked:
        cprint(f"  {RED}BLOCKED: fork-parity probe FAILED — {result.detail}{NC}")
        cprint(f"  {RED}This is what Linux CI would do to this commit. A HANG here means something{NC}")
        cprint(f"  {RED}forks a multithreaded process.{NC}")
        tail = "\n".join(result.output.splitlines()[-25:])
        if tail:
            cprint(tail)
        sys.exit(1)

    cprint(f"  {GREEN}Suite passes under the Linux fork default.{NC}")


def stage_consistency(root: Path) -> None:
    """Step 6→9 (renumbered): Check version consistency."""
    cprint(f"\n{BOLD}[9/17] Checking version consistency...{NC}")
    ok, msg = check_version_consistency(root)
    cprint(f"  {msg}")
    if not ok:
        cprint(f"  {RED}Fix version mismatch before publishing.{NC}")
        sys.exit(1)
    cprint(f"  {GREEN}Consistent.{NC}")


def _read_remote_version(plugin_root: Path) -> str | None:
    """Read .claude-plugin/plugin.json's `version` from origin/master (or main).

    Idempotency baseline: the publish pipeline reads the REMOTE version, not
    the local one, so an interrupted publish that already bumped + committed
    locally cannot double-bump on re-run. Returns None when offline / no
    remote ref / file missing — caller must fall back to local baseline.
    """
    for ref in ("origin/master", "origin/main", "origin/HEAD"):
        try:
            r = subprocess.run(
                ["git", "show", f"{ref}:.claude-plugin/plugin.json"],
                capture_output=True,
                text=True,
                cwd=str(plugin_root),
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode != 0:
            continue
        try:
            v = json.loads(r.stdout).get("version")
        except json.JSONDecodeError:
            continue
        if isinstance(v, str):
            return v
    return None


def _git_porcelain_clean(root: Path) -> bool:
    """True iff `git status --porcelain` is empty (working tree clean)."""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and not r.stdout.strip()


def _head_commit_message(root: Path) -> str:
    """Return the subject line of HEAD, or '' on failure."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def _local_tag_exists(root: Path, tag: str) -> bool:
    """True iff `tag` already exists in the local git repo."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def _remote_tag_state(root: Path, tag: str) -> bool | None:
    """Three-valued remote-tag probe (canon issue #216, TRDD-6UW0KZVY shape).

    Returns:
      True  — ls-remote SUCCEEDED and the tag exists on origin.
      False — ls-remote SUCCEEDED and the tag does not exist (a real answer:
              first-publish and the pre-push recovery both rely on it).
      None  — the remote could NOT be read (non-zero exit / timeout). This is
              NOT "no tags": collapsing it into False made the destructive
              recovery branches act on a question the remote never answered —
              re-pointing a tag that may already be published.
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _ensure_tag_at_head(root: Path, tag: str, message: str) -> bool:
    """Guarantee `tag` exists AND points at HEAD, or refuse (canon issue #216).

    After a publish that died between tagging and the push, the retry's
    recovery saw the tag already present and skipped re-tagging, then pushed
    HEAD plus the OLD tag: every commit made between the attempts — typically
    the very fix that made the retry pass — landed on the branch but OUTSIDE
    the released tag, so the release archive differed from the tree the gates
    had just validated.

    Fail-closed: the tag is moved ONLY on the remote's positive answer that it
    is unpushed. A tag already on origin is immutable here, and an unreachable
    remote is not consent.

    Returns True when the tag is correct (created, moved, or already at HEAD),
    False when the caller must abort.
    """
    if not _local_tag_exists(root, tag):
        run(["git", "tag", "-a", tag, "-m", message], cwd=root)
        cprint(f"  {GREEN}Tag {tag} created{NC}")
        return True

    tag_sha = run(["git", "rev-list", "-n", "1", tag], cwd=root, check=False, capture=True).stdout.strip()
    head_sha = run(["git", "rev-parse", "HEAD"], cwd=root, check=False, capture=True).stdout.strip()
    if not (tag_sha and head_sha) or tag_sha == head_sha:
        # Already correct, or the shas are unreadable — the latter is the
        # pre-existing behaviour and is safe: nothing is moved on a guess.
        cprint(f"  {GREEN}Tag {tag} already present at HEAD{NC}")
        return True

    remote_state = _remote_tag_state(root, tag)
    if remote_state is None:
        cprint(
            f"  {RED}Local tag {tag} points at {tag_sha[:8]} (HEAD {head_sha[:8]}) "
            f"and origin's tags cannot be read (ls-remote failed). Refusing to move "
            f"the tag: that is only safe when the remote confirms it is unpushed. "
            f"Re-run once the remote is reachable.{NC}"
        )
        return False
    if remote_state is True:
        cprint(
            f"  {RED}Local tag {tag} points at {tag_sha[:8]} but HEAD is "
            f"{head_sha[:8]}, and the tag is ALREADY ON ORIGIN. Refusing to move a "
            f"published tag. Bump to a new version instead.{NC}"
        )
        return False

    cprint(
        f"  {YELLOW}Local tag {tag} points at {tag_sha[:8]}, HEAD is at "
        f"{head_sha[:8]}. Tag is unpushed; moving it to HEAD.{NC}"
    )
    run(["git", "tag", "-d", tag], cwd=root)
    run(["git", "tag", "-a", tag, "-m", message], cwd=root)
    cprint(f"  {GREEN}Tag {tag} re-created at HEAD{NC}")
    return True


def _plugin_name(root: Path) -> str | None:
    """Read the plugin name from .claude-plugin/plugin.json."""
    pj = root / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return None
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    name = data.get("name")
    return str(name) if name else None


def _dependency_tag_name(root: Path, new_ver: str) -> str | None:
    """The `{plugin-name}--v{version}` tag Claude Code resolves dependencies against.

    Derived from the manifest, never hardcoded, so renaming the plugin cannot silently
    desync the tag from the plugin it names. Returns None when the name is unreadable,
    in which case the caller warns and skips rather than inventing a name.

    This is the exact name `claude plugin tag` produces.
    """
    name = _plugin_name(root)
    return f"{name}--v{new_ver}" if name else None


def stage_bump(root: Path, new_ver: str, dry_run: bool) -> None:
    """Step 7→10 (renumbered): Bump version. Idempotent — skips when local already matches target.

    Recovery semantics: when a previous publish was interrupted between the
    local commit+tag and the push (transient network failure during git push,
    pre-push hook reject, etc.), the local repo is at the bumped version while
    origin is one minor behind. Re-running publish.py would DOUBLE-BUMP
    (read-local-then-add-1 → next minor on top of the already-bumped local).
    The fix: read REMOTE plugin.json as baseline, infer bump type from
    local-vs-remote delta, and skip the bump entirely when local already
    matches the target.
    """
    cprint(f"\n{BOLD}[10/17] Bumping version...{NC}")
    current = get_current_version(root)
    remote = _read_remote_version(root)
    if remote and current and current == new_ver:
        cprint(
            f"  {YELLOW}Local plugin.json is already at {new_ver} (remote at {remote}) — "
            f"skipping bump (interrupted-publish recovery).{NC}"
        )
        return
    if remote and current and current != remote and current != new_ver:
        cprint(
            f"  {RED}REFUSED: local plugin.json is at {current} but remote is at "
            f"{remote} and target is {new_ver}. Refuse to guess what state this is.{NC}"
        )
        cprint(f"  {RED}Manual intervention required: align local with remote, then re-run.{NC}")
        sys.exit(1)
    if not do_bump(root, new_ver, dry_run=dry_run):
        cprint(f"  {RED}Version bump failed.{NC}")
        sys.exit(1)
    cprint(f"  {GREEN}Version bumped to {new_ver}.{NC}")


def stage_update_badges(root: Path, old_ver: str, new_ver: str, dry_run: bool) -> None:
    """Step 8→11 (renumbered): Replace version badge in README.md.

    Strategy:
      1. Try exact-string substitution `version-<old>-blue` → `version-<new>-blue`
      2. If the exact old version is not present, fall back to a regex that
         matches ANY `version-X.Y.Z-blue` pattern (handles drift from a hand-edit
         or a missed release). Prevents the "stale forever" trap that bit CPV
         itself when its README badge fell 20 releases behind.
      3. Emit a WARNING (not silent skip) when no badge is found at all so the
         author notices the README has no shields.io version badge to update.
    """
    cprint(f"\n{BOLD}[11/17] Updating README badge...{NC}")
    readme = root / "README.md"
    if not readme.exists():
        cprint(f"  {YELLOW}WARNING: no README.md — skipping badge update.{NC}")
        return
    content = readme.read_text(encoding="utf-8")
    old_badge = f"version-{old_ver}-blue"
    new_badge = f"version-{new_ver}-blue"

    if old_badge in content:
        if dry_run:
            cprint(f"  Would update badge (exact match): {old_badge} -> {new_badge}")
            return
        readme.write_text(content.replace(old_badge, new_badge, 1), encoding="utf-8")
        cprint(f"  {GREEN}Updated README badge: {old_ver} -> {new_ver}{NC}")
        return

    # Fallback: regex match on any version-X.Y.Z-blue pattern
    badge_re = re.compile(r"version-\d+\.\d+\.\d+-blue")
    match = badge_re.search(content)
    if match is None:
        cprint(f"  {YELLOW}WARNING: no version-X.Y.Z-blue badge found in README.md.{NC}")
        cprint(f"  {YELLOW}Add a shields.io badge so future releases can update it automatically.{NC}")
        return
    found = match.group(0)
    if dry_run:
        cprint(f"  Would update badge (regex match): {found} -> {new_badge}")
        return
    readme.write_text(badge_re.sub(new_badge, content, count=1), encoding="utf-8")
    cprint(f"  {GREEN}Updated README badge (was {found}, now {new_badge}){NC}")


def detect_bump_type(root: Path) -> str:
    """Auto-detect the next bump type from conventional commits via git-cliff.

    Runs `git-cliff --bumped-version` and compares the predicted version to
    the REMOTE one (origin/master) to determine major/minor/patch. Falls back
    to 'patch' on any failure (git-cliff missing, repo empty, parse error) so
    the cornerstone rule — every push is a bump — is never violated.

    Idempotency: when the local repo already has a release commit (interrupted
    publish), reading local plugin.json would over-shoot the bump (current is
    already the bumped version, git-cliff would compute current+1). Reading
    remote/origin gives the true baseline.

    Conventional commit mapping (git-cliff defaults):
      feat:                 -> minor
      fix:/perf:/refactor:  -> patch
      BREAKING CHANGE / !   -> major
    """
    cliff_bin = shutil.which("git-cliff")
    if cliff_bin is None:
        cprint(f"{YELLOW}git-cliff not installed — auto-bump falls back to 'patch'.{NC}")
        return "patch"
    current = _read_remote_version(root) or get_current_version(root)
    if not current:
        cprint(f"{YELLOW}Cannot read current version for auto-bump — falling back to 'patch'.{NC}")
        return "patch"
    try:
        r = subprocess.run(
            [cliff_bin, "--bumped-version"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return "patch"
    if r.returncode != 0:
        return "patch"
    out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    bumped = out.lstrip("v").strip()
    if not bumped or bumped == current:
        return "patch"
    try:
        cur = [int(p) for p in current.split(".")[:3]]
        nxt = [int(p) for p in bumped.split(".")[:3]]
        while len(cur) < 3:
            cur.append(0)
        while len(nxt) < 3:
            nxt.append(0)
    except ValueError:
        return "patch"
    if nxt[0] > cur[0]:
        return "major"
    if nxt[1] > cur[1]:
        return "minor"
    return "patch"


def stage_changelog(root: Path, new_ver: str, dry_run: bool) -> None:
    """Step 9→12 (renumbered): Generate CHANGELOG.md with git-cliff using the bumped tag.

        git cliff --bump --tag v<NEXT> -o CHANGELOG.md

    --bump          promote the unreleased section into a dated tag entry
    --tag v<NEXT>   label the new entry with the computed version (prefixed v)
    -o CHANGELOG.md write the regenerated changelog back to disk

    `--unreleased` was DELIBERATELY REMOVED (CPV#204, fixed in canon v5.3.0).
    With `--unreleased`, git-cliff renders ONLY the since-last-tag section and
    `-o` then OVERWRITES the whole file with it — every prior release section
    is silently deleted at exit 0. That destroyed this repo's history on
    v0.3.4, v0.3.5 AND v0.3.6 (recovered from tags each time). Without it,
    git-cliff renders EVERY tag from the commit log, which is also idempotent:
    re-running the step for the same version reproduces the file byte for
    byte, so an interrupted publish cannot duplicate a section. Do not
    "restore" the flag because git-cliff docs pair it with `--bump` — that
    documented-looking pairing is exactly how the bug survived review 3 times.
    """
    cprint(f"\n{BOLD}[12/17] Generating changelog (git-cliff)...{NC}")
    if not shutil.which("git-cliff"):
        cprint(f"  {YELLOW}git-cliff not installed — skipping changelog.{NC}")
        return
    cliff_toml = root / "cliff.toml"
    if not cliff_toml.is_file():
        cprint(f"  {YELLOW}No cliff.toml — skipping changelog.{NC}")
        return
    tag = f"v{new_ver}"
    if dry_run:
        cprint(f"  Would run: git-cliff --bump --tag {tag} -o CHANGELOG.md")
        return
    run(
        ["git-cliff", "--bump", "--tag", tag, "-o", "CHANGELOG.md"],
        cwd=root,
    )
    # Post-condition guard (CPV#204 follow-up): the full-render command above
    # makes history loss structurally impossible, but a future edit could
    # drift the command back — so fail loudly if the section count ever drops
    # below the number of existing tags (each tag owns one `## [x.y.z]` line).
    changelog = root / "CHANGELOG.md"
    if changelog.is_file():
        section_count = sum(1 for line in changelog.read_text(encoding="utf-8").splitlines() if line.startswith("## ["))
        tag_list = run(["git", "tag", "--list", "v[0-9]*"], cwd=root, capture=True)
        tag_count = len(tag_list.stdout.strip().splitlines())
        if section_count <= tag_count and tag_count > 0:
            cprint(
                f"  {RED}CHANGELOG.md has {section_count} sections for {tag_count} "
                f"existing tags + 1 new — git-cliff ate the history again "
                f"(CPV#204 shape). Aborting BEFORE commit/tag/push.{NC}"
            )
            sys.exit(1)
    cprint(f"  {GREEN}CHANGELOG.md updated with {tag}.{NC}")


def stage_release_changes(root: Path) -> None:
    """Stage the release commit WITHOUT absorbing untracked files (canon issue #186).

    `git add -A` stages untracked files too. At release time a plugin tree
    routinely holds `reports/` (which "routinely contain private data —
    absolute paths, usernames, internal hostnames, tokens caught in logs"),
    local scratch, editor artifacts, and whatever a failed earlier run left
    behind. A release commit is the WORST place for an accidental inclusion:
    it is pushed to a public repo and it is also the artifact users install.

    Staging tracked modifications only is safe HERE specifically because step 1
    already required a clean tree: everything legitimate is committed by the
    time this runs, so the only files this pipeline itself creates are the
    generated ones enumerated below. Anything else untracked at this point is,
    by construction, not part of the release.

    The failure mode is deliberately "the release did not include your new
    file, here it is by name" rather than "the release published your scratch
    directory" — the first is a loud, cheap fix; the second is permanent.
    """
    run(["git", "add", "-u"], cwd=root)

    # Files this pipeline generates. They are normally already tracked, but a
    # first-ever CHANGELOG.md (or a plugin adopting this pipeline) can be new —
    # so name them explicitly rather than reaching for `-A`. Only existing
    # paths are staged; a missing one is not an error.
    for rel in (
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "CHANGELOG.md",
        "README.md",
        "pyproject.toml",
        "uv.lock",
    ):
        if (root / rel).exists():
            run(["git", "add", "--", rel], cwd=root)

    # Surface whatever is left untracked instead of silently absorbing it.
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    stray = [ln[3:].strip() for ln in res.stdout.splitlines() if ln.startswith("??")]
    if stray:
        cprint(f"  {YELLOW}NOT staged — untracked files are never swept into a release commit (#186):{NC}")
        for path in stray[:20]:
            cprint(f"  {YELLOW}    ?? {path}{NC}")
        if len(stray) > 20:
            cprint(f"  {YELLOW}    ... and {len(stray) - 20} more{NC}")
        cprint(f"  {YELLOW}If one of these belongs in the release, `git add` it BY NAME and re-run.{NC}")


def stage_commit_and_push(root: Path, new_ver: str, dry_run: bool) -> None:
    """Step 10→13 (renumbered): Commit, tag, push. Idempotent on commit + tag.

    Idempotency: if HEAD's subject is already `chore: bump version to <new_ver>`
    AND the working tree is clean, skip the commit step (interrupted-publish
    recovery). If the tag already exists locally, `_ensure_tag_at_head` still
    verifies it points at HEAD — a tag left stale by an interrupted publish is
    re-pointed only when the remote positively confirms it was never pushed
    (canon issue #216). The push always runs — that is what brings the remote
    into sync.

    TRDD-bbff5bc5 §5: gh-auth precheck runs BEFORE the first push so the
    user gets an actionable error if their gh CLI is unauthed/lacks push
    perm — instead of an opaque git push failure mid-pipeline.
    """
    cprint(f"\n{BOLD}[13/17] Committing and pushing...{NC}")
    tag = f"v{new_ver}"
    # The DEPENDENCY-RESOLUTION tag. Since Claude Code 2.1.110 a version-constrained
    # dependency ({"name": "<plugin>", "version": ">=1.2"}) is resolved by listing this
    # repo's tags, keeping only those starting with "<plugin>--v", and fetching the
    # highest one satisfying the range. The plain vX.Y.Z tag is IGNORED by that
    # resolver, so a plugin shipping only vX.Y.Z cannot be depended upon: every
    # dependent fails to install with `no-matching-tag` and is DISABLED.
    #
    # It stays invisible until someone installs clean (an already-installed dependent
    # keeps working), which is exactly how it went unnoticed in the wild. So both tags
    # are created and pushed in the SAME atomic push -- a release can never ship with
    # one and not the other. NOTE the separator is a DOUBLE hyphen (`--v`); a single
    # `-v` does not match the resolver's prefix filter.
    dep_tag = _dependency_tag_name(root, new_ver)
    expected_subject = f"chore: bump version to {new_ver}"
    head_subject = _head_commit_message(root)
    tree_clean = _git_porcelain_clean(root)
    tag_exists = _local_tag_exists(root, tag)
    dep_tag_exists = dep_tag is not None and _local_tag_exists(root, dep_tag)
    push_refs = ["HEAD", tag] + ([dep_tag] if dep_tag else [])

    if dry_run:
        if head_subject == expected_subject and tree_clean:
            cprint(f"  Would skip commit (HEAD already '{expected_subject}', tree clean)")
        else:
            cprint(f"  Would commit: {expected_subject}")
        if tag_exists:
            cprint(f"  Would skip tag (already exists locally): {tag}")
        else:
            cprint(f"  Would tag: {tag}")
        if dep_tag is None:
            cprint(f"  {YELLOW}Would SKIP the dependency tag - plugin name unreadable.{NC}")
        elif dep_tag_exists:
            cprint(f"  Would skip dependency tag (already exists locally): {dep_tag}")
        else:
            cprint(f"  Would tag (dependency resolution): {dep_tag}")
        cprint(f"  Would push (atomic): origin {' '.join(push_refs)}")
        return

    if head_subject == expected_subject and tree_clean:
        cprint(
            f"  {YELLOW}HEAD is already '{expected_subject}' and tree is clean — "
            f"skipping commit (interrupted-publish recovery).{NC}"
        )
    else:
        # NEVER `git add -A` (canon issue #186; also the maintainer's standing
        # rule): untracked scratch and reports must never be swept into a
        # release commit that gets pushed and installed.
        stage_release_changes(root)
        run(["git", "commit", "-m", expected_subject], cwd=root)

    # `_ensure_tag_at_head` (canon issue #216): a pre-existing tag must point
    # at HEAD, not merely exist — otherwise the retry after an interrupted
    # publish pushes HEAD plus the OLD tag and the release archive differs
    # from the tree the gates just validated. The helper refuses to move a tag
    # already on origin (published tags are immutable) and refuses when the
    # remote cannot be read.
    if not _ensure_tag_at_head(root, tag, f"Release {tag}"):
        sys.exit(1)

    if dep_tag is None:
        # Warn loudly rather than silently omitting it: a silent skip is precisely how
        # this defect survived unnoticed across many releases.
        cprint(
            f"  {YELLOW}WARNING: cannot read the plugin name from "
            f".claude-plugin/plugin.json - SKIPPING the dependency tag. Dependent "
            f"plugins will fail to resolve this release with `no-matching-tag`.{NC}"
        )
    elif not _ensure_tag_at_head(root, dep_tag, f"{_plugin_name(root)} {new_ver}"):
        sys.exit(1)

    # gh-auth precheck — fail fast with actionable error if gh missing/unauthed.
    owner, repo = _resolve_owner_repo(root)
    _ensure_gh_auth(owner, repo)
    # Atomic push: commit + tag land together or not at all. Eliminates the
    # half-published-state failure mode where `git push origin HEAD --tags`
    # could push the commit, fail on the tag (rejected/network), and leave
    # the remote with an unreleased commit + no tag. `--atomic` is a single
    # transaction in the wire protocol; the server rolls back if any ref
    # update fails. git_with_retry still wraps the call so transient
    # network hiccups (4xx-class permanent errors fall through immediately).
    cprint(f"  {BLUE}$ git push --atomic origin {' '.join(push_refs)}{NC}")
    # capture_output must stay True (the default): run_with_retry classifies a
    # failure as transient by READING stderr, and with capture_output=False
    # subprocess.run leaves result.stderr as None, so every failure looked
    # permanent and the 60-attempt retry budget silently collapsed to 1 attempt
    # (TRDD-E0NETVRP). Capturing swallows git's error text into the exception,
    # so echo it before failing fast — a mute push failure is undiagnosable.
    #
    # timeout + max_attempts (canon issue #224): the pre-push hook runs INSIDE
    # this call's wall clock (it re-runs the validator and the whole test
    # suite), so the timeout must cover the hook's budget, not just the wire
    # transfer — _PUSH_TIMEOUT_SEC is computed from exactly that budget.
    try:
        git_with_retry(
            ["git", "push", "--atomic", "origin", *push_refs],
            cwd=str(root),
            timeout=_PUSH_TIMEOUT_SEC,
            max_attempts=_PUSH_MAX_ATTEMPTS,
        )
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr, end="")
        raise
    _pushed = tag if dep_tag is None else f"{tag} + {dep_tag}"
    cprint(f"  {GREEN}Pushed {_pushed} atomically.{NC}")


def stage_gh_release(root: Path, new_ver: str, dry_run: bool) -> None:
    """Step 11→14 (renumbered): Create GitHub release via gh CLI.

    TRDD-bbff5bc5 §5: re-runs the gh-auth precheck before `gh release
    create` so an auth state change between gates 10 and 11 (token
    revoked, account switched) surfaces as an actionable error.
    """
    cprint(f"\n{BOLD}[14/17] Creating GitHub release...{NC}")
    tag = f"v{new_ver}"
    if not shutil.which("gh"):
        cprint(f"  {YELLOW}gh CLI not installed — skipping release.{NC}")
        return
    if dry_run:
        cprint(f"  Would create release: {tag}")
        return
    owner, repo = _resolve_owner_repo(root)
    _ensure_gh_auth(owner, repo)
    # Release notes = THIS version's section only, never the whole
    # CHANGELOG.md (CPV#205). Passing the full file as --notes-file ships the
    # entire history as one release's body; CPV measured 110,166 chars against
    # GitHub's 125,000-char release-body limit — a few releases from
    # `gh release create` failing outright AFTER the tag is already public.
    # The section is rendered from the explicit range <prev>..<tag>, NOT
    # `git-cliff --current`: measured on the v0.3.7 publish, --current errors
    # "No tag exists for the current commit" when HEAD carries two tags (the
    # release tag plus the `<plugin>--vX.Y.Z` dependency-resolution tag, which
    # does not match cliff.toml's tag_pattern), while the explicit range
    # renders exactly one section. prev is resolved with --match 'v[0-9]*' so
    # the dep tag can never be picked as the range base. The notes file lives
    # OUTSIDE the repo root so it can never dirty the tree mid-release.
    # Empty/failed render falls back to --generate-notes — never both flags at
    # once (undefined behavior across gh versions: some concatenate, some
    # override).
    notes_file = Path(tempfile.gettempdir()) / f"release-notes-{repo}-{tag}.md"
    notes_ok = False
    prev = run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", f"{tag}^"],
        cwd=root,
        check=False,
        capture=True,
    )
    prev_tag = prev.stdout.strip() if prev.returncode == 0 else ""
    if prev_tag and shutil.which("git-cliff") and (root / "cliff.toml").is_file():
        cliff = run(
            ["git-cliff", f"{prev_tag}..{tag}", "--strip", "all", "-o", str(notes_file)],
            cwd=root,
            check=False,
            capture=True,
        )
        notes_ok = (
            cliff.returncode == 0 and notes_file.is_file() and notes_file.read_text(encoding="utf-8").strip() != ""
        )
        if not notes_ok:
            cprint(f"  {YELLOW}git-cliff {prev_tag}..{tag} produced no notes — falling back to --generate-notes.{NC}")
        else:
            # G1.1 / R22: every GitHub-writing surface leads with who authored
            # it, and a release body is one. `--strip all` removes cliff.toml's
            # changelog HEADER — which is where the byline lives — so re-prepend
            # it here, guarded for idempotency exactly like release.yml's step
            # (same grep-fixed-string collocation). Without this, a CI failure
            # after publish would leave a byline-less body live indefinitely.
            byline = "_Released by the ASSISTANT role-plugin (via the shared owner gh auth)._"
            notes_text = notes_file.read_text(encoding="utf-8")
            if "_Released by the ASSISTANT role-plugin" not in notes_text:
                notes_file.write_text(f"{byline}\n\n{notes_text}", encoding="utf-8")
    args = ["gh", "release", "create", tag, "--title", tag]
    if notes_ok:
        args.extend(["--notes-file", str(notes_file)])
    else:
        args.append("--generate-notes")
    cprint(f"  {BLUE}$ {' '.join(args)}{NC}")
    result = gh_with_retry(args, cwd=str(root), check=False, capture_output=True)
    if result.stdout and result.stdout.strip():
        cprint(result.stdout.strip())
    if result.stderr and result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode == 0:
        cprint(f"  {GREEN}Release created.{NC}")
        return
    # `gh release create` returns an "already_exists" / "already exists"
    # validation error when a release for this tag is already present. On a
    # re-run or interrupted-publish recovery that is the idempotent-success
    # outcome (the release IS there), so it must NOT abort — match either
    # spelling gh emits, case-insensitively.
    combined_err = f"{result.stdout or ''}\n{result.stderr or ''}"
    if re.search(r"already[ _]exists", combined_err, re.IGNORECASE):
        cprint(f"  {YELLOW}Release {tag} already exists — treating as success (idempotent re-run).{NC}")
        return
    # Any other non-zero exit is a genuine failure (auth revoked mid-pipeline,
    # malformed notes file, network exhausted all retries). The tag is already
    # pushed, but the documented final stage did NOT complete — abort so the
    # pipeline does not falsely report success (fail-fast invariant).
    cprint(f"  {RED}Failed to create release (exit code {result.returncode}).{NC}")
    cprint(f"  {RED}  The tag {tag} is pushed; create the release manually or re-run after fixing the cause.{NC}")
    sys.exit(1)


# -- Post-release reporters -----------------------------------------------------
#
# Both stages run AFTER the release on purpose: they verify the commit that
# actually shipped, by which point a non-zero exit could not un-ship anything —
# it would only abort the pipeline *after* the irreversible step, losing the
# report that is the whole point. Neither folds "cannot check" into a pass:
# every skip names its reason.


def _resolve_marketplace_name(root: Path) -> str | None:
    """The marketplace NAME Claude Code installs by (``<plugin>@<name>``).

    Layout A resolves the remote marketplace repo from notify-marketplace.yml
    and reads its manifest from GitHub via `gh api`; Layout B reads the parent
    marketplace directly. Anything unresolvable returns None, which makes the
    smoke test SKIP with a reason — never guess a marketplace name, because
    installing from the wrong one would prove nothing. (The fetch reuses
    `_fetch_remote_marketplace_json` rather than urllib: bandit B310 blocks a
    release gate that urlopen's a URL assembled from manifest strings, and gh
    already owns the auth/transport layer.)
    """
    layout, details = _detect_layout(root)
    if layout == "B":
        mp_root = details.get("marketplace_root")
        if isinstance(mp_root, Path):
            try:
                data = json.loads((mp_root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
            name = data.get("name") if isinstance(data, dict) else None
            return name if isinstance(name, str) and name else None
        return None
    if layout == "A":
        owner = details.get("mkt_owner")
        repo = details.get("mkt_repo")
        if not (isinstance(owner, str) and isinstance(repo, str)):
            return None
        data = _fetch_remote_marketplace_json(owner, repo)
        if not isinstance(data, dict):
            return None
        name = data.get("name")
        return name if isinstance(name, str) and name else None
    return None


_SEMVER_RE = re.compile(r"\bv?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?)\b")

# The CLI's own wording when a plugin cannot be resolved inside a marketplace.
# Matching the SHAPE rather than one exact sentence, because this only ever
# gates a DOWNGRADE that is additionally proven by _marketplace_is_registered.
_NOT_IN_MARKETPLACE_RE = re.compile(
    r"not found in marketplace|marketplace .*not found|marketplace update",
    re.IGNORECASE,
)


def _marketplace_is_registered(claude_bin: str, marketplace: str) -> bool:
    """True when `marketplace` appears in `claude plugin marketplace list`.

    READ-ONLY on purpose: running `marketplace add` to make the smoke test pass
    would mutate the user's global registry as a side effect of publishing.

    FAIL-SAFE towards the HARD FAILURE: any inability to answer (CLI error,
    timeout, unreadable output) returns True, i.e. "assume registered", so a
    genuinely uninstallable release is never downgraded to SKIPPED by a probe
    that simply could not run.
    """
    try:
        listing = subprocess.run(
            [claude_bin, "plugin", "marketplace", "list"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    if listing.returncode != 0:
        return True
    return marketplace in ((listing.stdout or "") + (listing.stderr or ""))


def _semvers_in(text: str) -> list[str]:
    """Every semver-shaped token in `text`, in order, without the leading v."""
    return _SEMVER_RE.findall(text)


def stage_install_smoke(root: Path, new_ver: str) -> None:
    """Step 16: prove the just-published release actually INSTALLS (canon Gate 15).

    ai-maestro#62 R2, filed after eleven plugins each published green and were
    all uninstallable: static validation cannot catch it (the manifest was
    valid, the tags existed, the marketplace entry was correct) — only an
    install can. This installs the plugin from its marketplace into a clean
    temp directory.

    Position and verdict mirror the CI-verify reporter: it must run after the
    release (nothing to install before it), by which point a non-zero exit
    could not un-ship anything. So the DEFAULT is a loud report, not a failed
    run. Setting ``CPV_PUBLISH_REQUIRE_INSTALL_SMOKE=1`` makes a genuine
    install FAILURE exit non-zero, for fleets that want the pipeline to go red.

    Cannot-check is never reported as clean: a missing ``claude`` CLI (the
    normal case on a CI runner), an unresolvable marketplace, or a timeout all
    report SKIPPED with the reason, and never count as a pass.
    """
    cprint(f"\n{BOLD}[16/17] Install smoke test...{NC}")
    if os.environ.get("CPV_PUBLISH_SKIP_INSTALL_SMOKE") == "1":
        cprint(f"  {YELLOW}SKIPPED — CPV_PUBLISH_SKIP_INSTALL_SMOKE=1{NC}")
        return
    strict = os.environ.get("CPV_PUBLISH_REQUIRE_INSTALL_SMOKE") == "1"
    claude_bin = shutil.which("claude")
    if claude_bin is None:
        cprint(f"  {YELLOW}SKIPPED — the `claude` CLI is not on PATH (normal on a CI runner).{NC}")
        cprint(f"  {YELLOW}This is NOT a pass: the release was not proven installable here.{NC}")
        return
    plugin_name = _plugin_name(root)
    marketplace = _resolve_marketplace_name(root)
    if not (plugin_name and marketplace):
        cprint(f"  {YELLOW}SKIPPED — could not resolve <plugin>@<marketplace> (name={plugin_name!r},{NC}")
        cprint(f"  {YELLOW}marketplace={marketplace!r}). Not a pass — nothing was installed.{NC}")
        return
    target = f"{plugin_name}@{marketplace}"
    with tempfile.TemporaryDirectory(prefix="publish-install-smoke-") as tmp:
        cprint(f"  {BLUE}$ (cd {tmp} && claude plugin install {target} --scope local){NC}")
        try:
            result = subprocess.run(
                [claude_bin, "plugin", "install", target, "--scope", "local"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            cprint(f"  {YELLOW}SKIPPED — the install could not be run ({exc}). Not a pass.{NC}")
            return
        # Put back what we took. `--scope local` scopes only the SETTINGS file
        # (written into this temp dir, which is about to vanish) — the plugin
        # payload and its marketplace registration land in shared ~/.claude
        # state, so without this every publish left another cached copy behind.
        # `--scope local` + `--keep-data` are BOTH load-bearing safety, not
        # tidiness: the author of the plugin being published almost certainly
        # has it installed at USER scope, and a wider uninstall — or one that
        # dropped ~/.claude/plugins/data/{id}/ — would destroy their real
        # installation. Cleanup runs on EVERY path where the install was
        # invoked, not only on rc == 0. Best-effort by design: a cleanup
        # failure is reported, never fatal, and never changes the verdict.
        try:
            subprocess.run(
                [claude_bin, "plugin", "uninstall", target, "--scope", "local", "--keep-data", "-y"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            cprint(f"  {YELLOW}Note: smoke-install cleanup did not run ({exc}).{NC}")
    if result.returncode == 0:
        cprint(f"  {GREEN}{target} installs cleanly (dependencies resolved).{NC}")
        # The marketplace entry is updated ASYNCHRONOUSLY (notify-marketplace
        # dispatch), so right after a release the resolved version may still be
        # the previous one. That is a lag, NOT an install failure. Claim a lag
        # only from a version we actually read in the install output — the
        # progress line does not always print the semver.
        resolved = _semvers_in(result.stdout or "")
        if resolved and new_ver not in resolved:
            cprint(
                f"  {YELLOW}Note: the marketplace resolved v{resolved[0]}, not v{new_ver} "
                f"(async notify lag) — installability is proven, the version listing lags.{NC}"
            )
        return
    combined = (result.stderr or "") + "\n" + (result.stdout or "")
    # Disambiguate "this host never registered the marketplace" (an environment
    # gap — cannot check) from "the marketplace is registered and does not carry
    # this plugin" (a REAL uninstallable release). Both produce the same
    # not-found message. FAIL-SAFE: only a marketplace we can PROVE is
    # unregistered downgrades to SKIPPED; if the probe cannot answer, the hard
    # failure stands.
    if _NOT_IN_MARKETPLACE_RE.search(combined) and not _marketplace_is_registered(claude_bin, marketplace):
        cprint(f"  {YELLOW}SKIPPED — the marketplace {marketplace!r} is not registered on this host,{NC}")
        cprint(f"  {YELLOW}so `claude plugin install` could not resolve {target} here. Not a pass:{NC}")
        cprint(f"  {YELLOW}the release was not proven installable. Register it with{NC}")
        cprint(f"  {YELLOW}`claude plugin marketplace add <source>` and re-run to get a real verdict.{NC}")
        return
    tail = combined.strip().splitlines()[-8:]
    cprint(f"  {RED}========================================{NC}")
    cprint(f"  {RED}RELEASE IS NOT INSTALLABLE: {target}{NC}")
    cprint(f"  {RED}The release is already public — fix forward with a new release.{NC}")
    for ln in tail:
        cprint(f"  {RED}    {ln}{NC}")
    cprint(f"  {RED}Reproduce: cd $(mktemp -d) && claude plugin install {target} --scope local{NC}")
    cprint(f"  {RED}========================================{NC}")
    if strict:
        cprint(f"  {RED}CPV_PUBLISH_REQUIRE_INSTALL_SMOKE=1 — failing the publish run.{NC}")
        sys.exit(1)


def classify_ci_runs(runs: list[dict[str, Any]], successors: dict[str, bool]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split completed CI runs for one commit into (failed, unknown).

    A `success`/`skipped`/`neutral` conclusion is fine and appears in neither
    list. Any OTHER conclusion is a genuine failure — EXCEPT `cancelled`,
    which GitHub's concurrency-group cancellation reports for a run that was
    merely SUPERSEDED by a newer push to the same branch (canon issue #220).
    `successors` disambiguates: it maps a cancelled run's workflow NAME to
    whether a newer run of that same workflow exists on a commit descended
    from the one being verified. Found => the cancellation was benign
    supersession, excluded from both lists. Not found => we cannot tell a
    genuine user-cancel from a lost successor, so it goes to `unknown` and the
    reporter must say UNKNOWN, never green — a "cannot check" result is never
    folded into a pass.
    """
    failed: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    for r in runs:
        conclusion = r.get("conclusion")
        if conclusion in ("success", "skipped", "neutral"):
            continue
        if conclusion == "cancelled":
            if successors.get(str(r.get("name", "?"))):
                continue
            unknown.append(r)
            continue
        failed.append(r)
    return failed, unknown


def _resolve_ci_run_successors(
    gh_bin: str,
    root: Path,
    sha: str,
    cancelled_runs: list[dict[str, Any]],
    deadline: float | None = None,
) -> dict[str, bool]:
    """For each cancelled run, look for a newer descendant-commit successor.

    A `cancelled` run counts as superseded-not-failed only when a LATER run of
    the SAME workflow exists on a commit that is a git descendant of `sha`.
    Any failure to determine that leaves that workflow's entry absent from the
    returned map, which `classify_ci_runs` treats as "no successor found" —
    fail toward UNKNOWN, never toward green.

    BOUNDED AS A PHASE: each `gh run list` carries 120s and each
    `git merge-base` 30s, but with N cancelled runs x up to 20 candidates that
    multiplies out; one shared deadline caps the whole phase, and expiry leaves
    the remaining workflows unresolved (rendered as UNKNOWN).
    """
    result: dict[str, bool] = {}
    for r in cancelled_runs:
        name = str(r.get("name", "?"))
        if name in result:
            continue
        if deadline is not None and time.monotonic() >= deadline:
            cprint(f"  {YELLOW}successor resolution: out of time — remaining cancelled run(s) stay UNKNOWN.{NC}")
            break
        branch = r.get("headBranch")
        if not branch:
            continue
        try:
            listed = subprocess.run(
                [
                    gh_bin,
                    "run",
                    "list",
                    "--workflow",
                    name,
                    "--branch",
                    str(branch),
                    "--limit",
                    "20",
                    "--json",
                    "headSha,conclusion,status,createdAt",
                ],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if listed.returncode != 0:
            continue
        try:
            candidates = json.loads(listed.stdout or "[]")
        except json.JSONDecodeError:
            continue
        for c in candidates:
            candidate_sha = c.get("headSha")
            if not candidate_sha or candidate_sha == sha:
                continue
            try:
                ancestry = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", sha, candidate_sha],
                    cwd=str(root),
                    capture_output=True,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if ancestry.returncode == 0:
                result[name] = True
                break
    return result


def stage_verify_ci_green(root: Path, timeout_s: int = _CI_VERIFY_DEFAULT_TIMEOUT_S) -> None:
    """Step 15: confirm CI went GREEN on the commit that was just released.

    WHY THIS STAGE EXISTS. The release push targets the default branch directly,
    and the branch ruleset grants the maintainer role a bypass — so GitHub lets
    the push through and the required checks never actually gate anything: the
    tag, the release and the marketplace notification are all public before CI
    has said a word. Until this stage existed, "CI must be green" lived only in
    prose — and prose is skippable.

    NON-BLOCKING BY CONSTRUCTION, and that is a deliberate asymmetry rather
    than a weak gate: by the time this runs the release is already published,
    so returning non-zero could not un-ship anything — it would only abort the
    pipeline *after* the irreversible step, losing the report that is the whole
    point. A RED result is therefore surfaced as a loud, explicit failure notice
    that names the failing runs and the exact follow-up command.

    "Cannot check" is never reported as green: no gh, no network, no runs
    found, or a timeout are each reported as UNVERIFIED with the reason, never
    folded into a pass.
    """
    cprint(f"\n{BOLD}[15/17] Verify CI is green on the released commit...{NC}")

    gh_bin = shutil.which("gh")
    if gh_bin is None:
        cprint(f"  {YELLOW}UNVERIFIED — gh CLI not installed, cannot check CI.{NC}")
        cprint(f"  {YELLOW}The release IS published; verify manually before relying on it.{NC}")
        return

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        cprint(f"  {YELLOW}UNVERIFIED — could not resolve HEAD ({exc}).{NC}")
        return
    if head.returncode != 0:
        cprint(f"  {YELLOW}UNVERIFIED — could not resolve HEAD.{NC}")
        return
    sha = head.stdout.strip()

    deadline = time.monotonic() + timeout_s
    poll_s = 15
    runs: list[dict[str, Any]] = []
    while True:
        try:
            listed = subprocess.run(
                [gh_bin, "run", "list", "--commit", sha, "--limit", "20", "--json", "name,status,conclusion,headBranch"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            cprint(f"  {YELLOW}UNVERIFIED — `gh run list` failed ({exc}).{NC}")
            return
        if listed.returncode != 0:
            cprint(f"  {YELLOW}UNVERIFIED — `gh run list` exited {listed.returncode}: {listed.stderr.strip()[:200]}{NC}")
            return
        try:
            runs = json.loads(listed.stdout or "[]")
        except json.JSONDecodeError:
            cprint(f"  {YELLOW}UNVERIFIED — unparseable `gh run list` output.{NC}")
            return
        if not runs:
            # A workflow can take a few seconds to register after the push.
            if time.monotonic() >= deadline:
                cprint(f"  {YELLOW}UNVERIFIED — no CI runs found for {sha[:8]} within {timeout_s}s.{NC}")
                return
            time.sleep(poll_s)
            continue
        pending = [r for r in runs if r.get("status") != "completed"]
        if not pending:
            break
        if time.monotonic() >= deadline:
            names = ", ".join(sorted({str(r.get("name", "?")) for r in pending}))
            # The hint carries the FULL sha: `gh run list --commit` with an
            # abbreviated sha silently matches nothing and exits 0.
            cprint(f"  {YELLOW}UNVERIFIED — still running after {timeout_s}s: {names}.{NC}")
            cprint(f"  {YELLOW}Check with: gh run list --commit {sha}{NC}")
            return
        time.sleep(poll_s)

    # A conclusion of `skipped`/`neutral` is not a failure. A `cancelled` run
    # is not automatically a failure either (canon issue #220): the concurrency
    # group cancels a run that a newer push to the same branch superseded,
    # which looks identical to a genuine user-cancel unless we go find that
    # newer run ourselves.
    cancelled_runs = [r for r in runs if r.get("conclusion") == "cancelled"]
    successors = (
        _resolve_ci_run_successors(gh_bin, root, sha, cancelled_runs, deadline=deadline) if cancelled_runs else {}
    )
    failed, unknown = classify_ci_runs(runs, successors)
    if failed:
        detail = ", ".join(f"{r.get('name', '?')}={r.get('conclusion')}" for r in failed)
        # Follow-up commands must be pasteable as written: `gh run view` has NO
        # --commit flag (that flag belongs to `gh run list`), so the hint is a
        # two-step with the FULL sha, then the run id.
        cprint(f"  {RED}[advisory] CI RED on the released commit {sha[:8]}: {detail}{NC}")
        cprint(f"  {RED}  (advisory — this reporter never changes the exit code; the release{NC}")
        cprint(f"  {RED}  is already shipped){NC}")
        cprint(f"  {RED}  The release v-tag and GitHub release are ALREADY PUBLISHED — the{NC}")
        cprint(f"  {RED}  ruleset bypass meant no required check gated them. Fix the cause and{NC}")
        cprint(f"  {RED}  publish a follow-up patch; do NOT mute the check.{NC}")
        cprint(f"  {RED}Logs: gh run list --commit {sha}{NC}")
        cprint(f"  {RED}      then: gh run view --log-failed <run-id>{NC}")
        return

    if unknown:
        names = ", ".join(sorted({str(r.get("name", "?")) for r in unknown}))
        cprint(f"  {YELLOW}CI verdict UNKNOWN on {sha[:8]}: run cancelled and no successor found ({names}).{NC}")
        cprint(f"  {YELLOW}This is either a genuine user-cancel or a superseding run we could not{NC}")
        cprint(f"  {YELLOW}resolve. Verify manually: gh run list --commit {sha}{NC}")
        return

    names = ", ".join(sorted({str(r.get("name", "?")) for r in runs}))
    cprint(f"  {GREEN}CI green on {sha[:8]} ({names}).{NC}")


# -- Main ----------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified publish pipeline for Claude Code plugins.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Mutually exclusive modes: side-modes (--gate / --install-hook /
    # --install-branch-rules) are distinct entry points; --patch/--minor/--major
    # are OPTIONAL overrides for the auto-bump default. Calling publish.py with
    # no flags runs the full publish pipeline with an auto-detected bump type.
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--gate",
        action="store_true",
        help="Pre-push gate mode: lint + copy-paste (jscpd) + validate + tests only (no bump/push)",
    )
    mode_group.add_argument(
        "--install-hook", action="store_true", help="Install pre-push hook into .git/hooks/ and set core.hooksPath"
    )
    mode_group.add_argument(
        "--install-branch-rules",
        action="store_true",
        dest="install_branch_rules",
        help="Apply the cpv-branch-rules ruleset to the GitHub origin "
        "(enforces CI as a required status check — the server-side gate)",
    )
    mode_group.add_argument(
        "--patch", action="store_const", dest="bump", const="patch", help="Force a patch bump (override auto-detection)"
    )
    mode_group.add_argument(
        "--minor", action="store_const", dest="bump", const="minor", help="Force a minor bump (override auto-detection)"
    )
    mode_group.add_argument(
        "--major", action="store_const", dest="bump", const="major", help="Force a major bump (override auto-detection)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    # NOTE: --skip-tests was intentionally removed. The cornerstone rule is that
    # every CPV plugin MUST pass validation with 0 issues (WARNING allowed) before
    # any push. Skipping tests would bypass that guarantee — there are no exceptions.
    args = parser.parse_args()

    root = get_repo_root()

    # --install-hook mode: just set up the hook and exit
    if args.install_hook:
        return install_hook(root)

    # --install-branch-rules mode: apply the server-side GitHub ruleset
    if args.install_branch_rules:
        return install_branch_rules(root)

    # --gate mode: run quality checks only (called by pre-push hook)
    if args.gate:
        return run_gate(root)

    # Full publish pipeline — auto-detect bump type unless user forced one.
    # Idempotency: read REMOTE plugin.json (origin/master) as the bump
    # baseline. When local is ahead (interrupted publish: bumped + committed
    # but not pushed), bumping from local would double-bump. From remote,
    # bumping recomputes the SAME target as the original interrupted run,
    # and stage_bump's "already-at-target" guard then skips the bump.
    local = get_current_version(root)
    if not local:
        cprint(f"{RED}Cannot read version from .claude-plugin/plugin.json{NC}")
        return 1
    remote = _read_remote_version(root)
    baseline = remote or local

    if args.bump is None:
        bump_type = detect_bump_type(root)
        cprint(f"{BLUE}Bump type: {bump_type} (auto-detected from git-cliff){NC}")
    else:
        bump_type = args.bump
        cprint(f"{BLUE}Bump type: {bump_type} (forced via --{bump_type}){NC}")

    new_ver = bump_semver(baseline, bump_type)
    if not new_ver:
        cprint(f"{RED}Cannot parse baseline version: {baseline}{NC}")
        return 1

    if remote and local != remote:
        cprint(
            f"{YELLOW}Local plugin.json is at {local} but origin is at {remote} — "
            f"using remote as bump baseline (interrupted-publish recovery).{NC}"
        )
    current = baseline

    cprint(f"\n{BOLD}Publish pipeline: {current} -> {new_ver}{NC}")
    if args.dry_run:
        cprint(f"{YELLOW}(dry-run mode — no changes will be made){NC}")

    # Gate 0: reject bypass attempts BEFORE running any other stage.
    # Pipeline order (per the cornerstone rule "every push is a bump"):
    #   lint+typecheck → tests → validate → ci-preflight → marketplace-reg →
    #   secret-scan → fork-parity → consistency → bump → badge → changelog →
    #   commit → push → github release → (post-release) verify-ci, install-smoke
    # Lint runs before tests (cheap fails first). Tests run before validate
    # so behavioral regressions fail the test suite before the structural
    # validator inspects the manifest.
    #
    # EVERY check through stage_gh_release runs BEFORE or AT the release; the
    # pre-bump block (everything before stage_bump) aborts with the tree
    # untouched, so a parity or security defect can never strand a half-pushed
    # tag. The two post-release reporters never abort by default — the release
    # is already public when they run, so their job is the loud report.
    stage_bypass_guard()
    stage_check_clean(root)
    stage_lint(root)
    stage_tests(root)  # MANDATORY — no skip flag, no exceptions
    stage_validate(root)
    stage_ci_preflight(root)  # MANDATORY — the gates validate_plugin omits
    stage_marketplace_registration(root)  # Gate 6 parity with CPV's own publish.py
    stage_secret_scan(root)  # MANDATORY — a committed credential blocks (CPV#217)
    stage_fork_parity(root)  # MANDATORY — run the suite as Linux would
    stage_consistency(root)
    stage_bump(root, new_ver, args.dry_run)
    stage_update_badges(root, current, new_ver, args.dry_run)
    stage_changelog(root, new_ver, args.dry_run)
    stage_commit_and_push(root, new_ver, args.dry_run)
    stage_gh_release(root, new_ver, args.dry_run)

    # Post-release reporters: the release is already public, so these never
    # abort the run by default — they surface what the ruleset bypass let
    # through (a red CI) and prove the artifact actually installs. Skipped on
    # a dry-run: no release exists yet, so both would report against the WRONG
    # commit/version and read as a defect rather than a preview.
    if not args.dry_run:
        stage_verify_ci_green(root)
        stage_install_smoke(root, new_ver)

    cprint(f"\n{GREEN}{BOLD}Published {new_ver} successfully!{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
