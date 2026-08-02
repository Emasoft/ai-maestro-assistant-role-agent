"""Guard: no shipped markdown may carry a bare `@name` in GitHub-rendered prose.

WHY THIS IS EXECUTABLE AND NOT A NOTE. The persona used to recommend a
self-identification byline reading `(via the shared @owner identity)`. Agents
copied it verbatim into issue and comment bodies, where GitHub linkifies
`@owner` — a REAL organization — so every compliant agent notified a stranger
on every post. The same shape paged the real `@manager` and `@janitor` accounts
elsewhere in the fleet (ai-maestro#109 confirmed all six role words resolve to
live accounts via `gh api users/<h>`).

The generalizable defect: a template is only safe if its LITERAL form is
harmless, because literal pasting is the expected behaviour. `<placeholder>`
is never pasted verbatim; `@owner` is, because it looks like finished text.
Prose alone could not hold this — ai-maestro#109 reports its own author typing
a bare mention minutes after writing the warning. Hence a test.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# A GitHub mention fires only when `@` opens a word: at the start of a line or
# after whitespace/an opening delimiter. Anything glued to a preceding
# alphanumeric, dot, slash, dash, underscore or plus is an email local part or
# a ref pin (`actions/checkout@v5`, `pkg@1.2.3`, `user@host.com`).
#
# Those two exemptions are deliberate and load-bearing: a guard that flags
# every email address gets ignored, and an ignored guard protects nothing.
# Raw emails are covered by a separate rule ("never paste a raw address"),
# not by widening this pattern until it cries wolf.
_BARE_MENTION_RE = re.compile(r"(?:(?<=^)|(?<=[\s(\[{<]))@[A-Za-z][A-Za-z0-9-]*")

_FENCED_RE = re.compile(r"```.*?```", re.DOTALL)
_CODE_SPAN_RE = re.compile(r"`[^`]*`")


def _prose_only(markdown: str) -> str:
    """Strip fenced blocks and code spans — GitHub does not linkify inside them.

    Stripping rather than flagging is the whole point: backticks ARE the
    prescribed fix, so a guard that also reported them would redden on
    correct writing and get deleted.
    """
    return _CODE_SPAN_RE.sub("", _FENCED_RE.sub("", markdown))


def _tracked_markdown(repo_root: Path) -> list[Path]:
    """Every git-tracked .md file — untracked scratch never reaches GitHub."""
    out = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [repo_root / p for p in out]


def test_the_guard_detects_a_bare_mention_and_spares_the_exempt_forms() -> None:
    """The pattern itself is correct: it catches prose mentions, not emails or pins.

    Asserted before the corpus scan so a regex that silently matches nothing
    cannot make the real test below pass vacuously.
    """
    caught = _BARE_MENTION_RE.findall("ping @manager now\n@janitor at line start\n(@owner in parens)")
    assert caught == ["@manager", "@janitor", "@owner"]

    for exempt in ("user@host.com", "actions/checkout@v5", "pkg@1.2.3", "a@b"):
        assert not _BARE_MENTION_RE.findall(exempt), f"must not fire on {exempt}"


def test_code_spans_and_fences_are_stripped_before_scanning() -> None:
    """Backticked mentions are inert on GitHub, so the guard must not report them."""
    assert not _BARE_MENTION_RE.findall(_prose_only("use `@janitor` safely"))
    assert not _BARE_MENTION_RE.findall(_prose_only("```\n@manager\n```"))
    assert _BARE_MENTION_RE.findall(_prose_only("bare @manager here"))


def test_no_tracked_markdown_carries_a_bare_mention_in_prose(repo_root: Path) -> None:
    """No shipped .md pages a real GitHub account when quoted into an issue."""
    offenders: list[str] = []
    for path in _tracked_markdown(repo_root):
        prose = _prose_only(path.read_text(encoding="utf-8"))
        for hit in _BARE_MENTION_RE.findall(prose):
            offenders.append(f"{path.relative_to(repo_root)}: {hit}")

    assert not offenders, (
        "bare @mention in GitHub-rendered prose — each pages a real account:\n  "
        + "\n  ".join(offenders)
        + "\nFix: write the name plain, or wrap it in backticks."
    )


def test_the_scan_actually_reads_files(repo_root: Path) -> None:
    """Coverage check — a clean result is only meaningful if files were scanned."""
    files = _tracked_markdown(repo_root)
    assert len(files) >= 2, f"expected tracked markdown, found {files}"
    assert any(p.name == "README.md" for p in files)
