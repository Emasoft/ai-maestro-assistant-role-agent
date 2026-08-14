"""Corpus-wide guard: a 403 promise never travels without the transport that cannot return one.

AMP is validated server-side, so this plugin's prose could once say "a forbidden
send returns HTTP 403" and be complete. Claude Code 2.1.224 shipped a SECOND
transport — `SendMessage` between live sessions, with `ListAgents` to enumerate
them — that never reaches the AI Maestro server, so no 403 is possible on it and
R39.5/R39.7/R39.9 are unenforced there. Prose documenting only the policed
transport reads as though every send is checked, which is the more dangerous of
the two errors.

**Why this module is corpus-scoped and not persona-scoped.** The predecessor of
this guard lived in `test_agent_definition.py` and checked the PERSONA only. The
persona was duly fixed; `README.md` kept the bare 403 claim for three releases
and the suite stayed green the whole time, because a guard's scope is part of its
claim (ai-maestro#143). A file-by-file walk is the fix: any shipped prose that
makes the promise must also carry the exception.

Deliberate exclusions, each for a reason that is not convenience:

- `design/` — a TRDD in a terminal column is FROZEN by rule. A guard that
  reddens on one would force a governance violation to make CI green.
- `tests/`, `scripts/` — code, where `403` is a legitimate HTTP-status literal
  (see `cpv_network_resilience`), not a claim about the comm-graph.
- `CHANGELOG.md` — a record of what shipped then. Editing history to satisfy a
  present-tense guard is falsification, not a fix.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Everything this plugin ships that a human or an agent READS AS POLICY. Skills
# and commands are globbed even though the plugin currently ships none, so the
# guard covers them the day one is added rather than the day someone remembers.
_SHIPPED_PROSE_GLOBS = (
    "README.md",
    "agents/*.md",
    "skills/**/*.md",
    "commands/**/*.md",
)

# Files the guard must always find. Without this anchor a typo'd glob would
# collect an empty-or-trivial set and every assertion below would pass vacuously.
_ANCHORS = (
    "README.md",
    "agents/ai-maestro-assistant-role-agent-main-agent.md",
)

# The promise: a forbidden send is rejected by the server.
_SERVER_ENFORCEMENT_CLAIM = re.compile(r"\b403\b|enforced\s+server-side", re.IGNORECASE)

# The exception, in two halves that must BOTH hold. Naming the tool is asserted
# apart from stating the bypass on purpose: prose that merely mentioned
# `SendMessage` in passing would satisfy a keyword scan while still implying the
# server has every send covered.
_NAMES_SENDMESSAGE = re.compile(r"\bSendMessage\b", re.IGNORECASE)
_STATES_THE_BYPASS = re.compile(
    r"(?:bypass\w*|never reach\w*|(?:does|do) not reach)[^.]{0,80}server",
    re.IGNORECASE,
)


def _makes_a_server_enforcement_claim(text: str) -> bool:
    """True when the text promises server-side rejection of a forbidden send."""
    return _SERVER_ENFORCEMENT_CLAIM.search(text) is not None


def _names_the_unpoliced_transport(text: str) -> bool:
    """True when the text names the cross-session channel AND says it bypasses the server."""
    return _NAMES_SENDMESSAGE.search(text) is not None and _STATES_THE_BYPASS.search(text) is not None


@pytest.fixture(scope="module")
def shipped_prose(repo_root: Path) -> list[Path]:
    """Every shipped policy-bearing markdown file, de-duplicated and sorted."""
    found: dict[Path, None] = {}
    for pattern in _SHIPPED_PROSE_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file():
                found[path] = None
    return list(found)


def test_the_shipped_prose_corpus_is_non_empty_and_anchored(shipped_prose: list[Path], repo_root: Path) -> None:
    """The walker actually collects files, including the two that must be in scope.

    A guard that silently scans nothing reports "clean" forever. This is the
    fail-on-an-empty-set requirement: the corpus must be non-empty, and the two
    files known to carry transport claims must be inside it.
    """
    assert shipped_prose, "shipped-prose corpus is EMPTY — the globs match nothing, so every check below is vacuous"
    relative = {p.relative_to(repo_root).as_posix() for p in shipped_prose}
    for anchor in _ANCHORS:
        assert anchor in relative, f"{anchor} is not in the scanned corpus — glob drift"


def test_no_403_claim_travels_without_the_transport_that_cannot_return_one(
    shipped_prose: list[Path], repo_root: Path
) -> None:
    """Any shipped file promising server-side enforcement also names the channel that has none.

    This is the whole point of the module. A file may say nothing about
    transports at all; what it may not do is assert the 403 promise alone,
    because a reader then concludes every send is checked.
    """
    for path in shipped_prose:
        text = path.read_text(encoding="utf-8")
        if not _makes_a_server_enforcement_claim(text):
            continue
        assert _names_the_unpoliced_transport(text), (
            f"{path.relative_to(repo_root).as_posix()} promises server-side enforcement (403) but never "
            "names `SendMessage` as a channel that bypasses the AI Maestro server; as written it reads "
            "as though every send is checked"
        )


def test_the_guard_detects_a_bare_claim_and_clears_a_complete_one() -> None:
    """The two predicates actually discriminate — proven on real prose, not mocks.

    Coverage for the guard itself. A regex that matched nothing (or everything)
    would leave the walk above green regardless of what the corpus says, and the
    only symptom would be a defect shipping months later.
    """
    bare = "The comm-graph is enforced server-side (HTTP 403 on a forbidden send)."
    assert _makes_a_server_enforcement_claim(bare)
    assert not _names_the_unpoliced_transport(bare), "the bare claim must NOT read as complete"

    complete = bare + " Claude Code's SendMessage channel bypasses that server entirely."
    assert _makes_a_server_enforcement_claim(complete)
    assert _names_the_unpoliced_transport(complete), "the corrected claim must read as complete"

    silent = "The ASSISTANT approves only its own TRDDs."
    assert not _makes_a_server_enforcement_claim(silent), "prose making no claim must not be flagged"


# What the unpoliced channel can actually REACH, as of the client releases named.
# Each row is a fact the persona once got wrong by omission, so each is pinned
# with the release that established it — a future edit that narrows the channel
# back to "another live session on this host" fails here instead of shipping.
_CURRENT_REACH = {
    "other machines (2.1.225: SendMessage starts a conversation with your Remote Control sessions elsewhere)": (
        re.compile(r"other machines", re.IGNORECASE)
    ),
    "the @-mention vector (2.1.232: typing `@name` makes the client send for you)": (
        re.compile(r"@\W{0,2}(?:name|mention)", re.IGNORECASE)
    ),
    "the inbound control (2.1.224/2.1.232: crossSessionInbound is the only gate, and it is the user's)": (
        re.compile(r"crossSessionInbound", re.IGNORECASE)
    ),
}


def test_persona_documents_the_current_reach_of_the_unpoliced_channel(agent_body: str) -> None:
    """The persona describes the channel as it is now, not as it shipped in 2.1.224.

    Naming `SendMessage` is necessary but no longer sufficient. The channel has
    since grown past this host (Remote Control and cloud sessions), gained a
    no-tool-call entry point (an `@name` mention the user types), and gained the
    one real inbound control — a USER setting, not a server rule. An agent that
    reads only the 2.1.224 description under-estimates every one of those.
    """
    for fact, pattern in _CURRENT_REACH.items():
        assert pattern.search(agent_body), f"persona no longer documents {fact}"
