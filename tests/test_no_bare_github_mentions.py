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


_YAML_WHOLE_LINE_COMMENT_RE = re.compile(r"^[ \t]*#.*$", re.MULTILINE)


def _yaml_emittable(yaml_text: str) -> str:
    """Strip whole-line YAML comments — a comment is never emitted to GitHub.

    Mandatory, not cosmetic. Three tracked workflow comments legitimately
    contain a word-boundary `@` (`PINNED to @v3.1.0`, and this guard's own
    rationale in release.yml). Scanning them would redden on correct writing,
    and a guard that cries wolf gets deleted — the same reasoning that makes
    `_prose_only` strip backticks rather than flag them.

    Only WHOLE-LINE comments are stripped. A trailing `# v6.0.3` after a SHA
    pin stays in the text, which is safe: its `@` is glued to a preceding
    character and the pattern already exempts that. Stripping to end-of-line
    from any `#` would instead cut through `#` characters inside quoted shell
    strings, hiding real emitted prose from the scan.
    """
    return _YAML_WHOLE_LINE_COMMENT_RE.sub("", yaml_text)


def _tracked(repo_root: Path, *globs: str) -> list[Path]:
    """Every git-tracked file matching the globs — untracked scratch never ships.

    Tracked-only is deliberate, and it has a sharp edge worth naming: a file
    is invisible to this guard until it is `git add`ed. When adding new
    documents, stage them BEFORE trusting a green run.
    """
    out = subprocess.run(
        ["git", "ls-files", *globs],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [repo_root / p for p in out]


def _tracked_markdown(repo_root: Path) -> list[Path]:
    """Every git-tracked .md file — untracked scratch never reaches GitHub."""
    return _tracked(repo_root, "*.md")


def _tracked_workflows(repo_root: Path) -> list[Path]:
    """Every git-tracked workflow — these BUILD GitHub prose (release bodies).

    Markdown is not the only surface that reaches GitHub: `release.yml`
    composes the release-note body that `gh release create --notes-file`
    publishes, so a bare mention added there pages an account exactly as one
    in a README would (TRDD-5KZQUOBS).
    """
    return _tracked(repo_root, ".github/workflows/*.yml", ".github/workflows/*.yaml")


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


def test_yaml_whole_line_comments_are_stripped_but_emitted_strings_are_not() -> None:
    """The YAML stripper hides comments from the scan and nothing else.

    Both halves are asserted because each alone would be satisfiable by a
    broken implementation: a stripper that removed everything would pass the
    first, and one that removed nothing would pass the second.
    """
    commented = "    # PINNED to @v3.1.0\n    run: echo hi\n"
    assert not _BARE_MENTION_RE.findall(_yaml_emittable(commented))
    assert "run: echo hi" in _yaml_emittable(commented)

    # A trailing comment is NOT stripped — and must not need to be, because
    # the `@` in a SHA pin is glued to the preceding character.
    pinned = "      - uses: actions/checkout@df4cb1c0 # v6.0.3\n"
    assert "uses:" in _yaml_emittable(pinned)
    assert not _BARE_MENTION_RE.findall(_yaml_emittable(pinned))


def test_the_workflow_guard_would_catch_a_mention_in_an_emitted_string() -> None:
    """Falsification: the workflow scan FAILS on tampered text.

    Without this, a corpus scan that happens to be clean is indistinguishable
    from one whose stripper silently ate every line before the regex ran.
    """
    tampered = "      run: |\n        printf 'Released by @owner.\\n'\n"
    assert _BARE_MENTION_RE.findall(_yaml_emittable(tampered)) == ["@owner"]


def test_no_tracked_workflow_carries_a_bare_mention_in_emitted_prose(repo_root: Path) -> None:
    """No workflow builds GitHub prose that pages a real account."""
    offenders: list[str] = []
    for path in _tracked_workflows(repo_root):
        emitted = _yaml_emittable(path.read_text(encoding="utf-8"))
        for hit in _BARE_MENTION_RE.findall(emitted):
            offenders.append(f"{path.relative_to(repo_root)}: {hit}")

    assert not offenders, (
        "bare @mention in workflow-emitted prose — a release body pages a real account:\n  "
        + "\n  ".join(offenders)
        + "\nFix: write the name plain, or glue/backtick it where a literal @ is required."
    )


def test_the_scan_actually_reads_files(repo_root: Path) -> None:
    """Coverage check — a clean result is only meaningful if files were scanned."""
    files = _tracked_markdown(repo_root)
    assert len(files) >= 2, f"expected tracked markdown, found {files}"
    assert any(p.name == "README.md" for p in files)

    workflows = _tracked_workflows(repo_root)
    assert len(workflows) >= 2, f"expected tracked workflows, found {workflows}"
    assert any(p.name == "release.yml" for p in workflows), (
        "release.yml is the workflow that composes the release-note body — "
        "if it is not scanned, the surface this guard was extended for is unguarded"
    )
