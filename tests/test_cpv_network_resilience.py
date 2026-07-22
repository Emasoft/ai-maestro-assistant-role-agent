"""Tests for scripts/cpv_network_resilience.py, publish.py's retry layer.

This module decides whether a failed `git push` / `gh release create` is a
transient hiccup worth retrying or a permanent error that must fail fast. Both
misclassifications are expensive: retrying an auth failure burns 30 attempts
and hides the real cause, while failing fast on a 503 aborts a release that
would have succeeded a second later.

Nothing here is mocked. The classifiers are pure functions fed real error
strings and real exception objects, and the retry wrapper drives real
subprocesses.
"""

from __future__ import annotations

import socket
import ssl
import subprocess
import sys
import urllib.error
from http.client import RemoteDisconnected
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cpv_network_resilience import (  # noqa: E402
    GH_MAX_ATTEMPTS,
    is_transient_http_error,
    is_transient_subprocess_error,
    run_with_retry,
)

# ── Subprocess classification ────────────────────────────────────────────────

TRANSIENT_STDERR = [
    "fatal: unable to access 'https://github.com/x.git/': Failed to connect to github.com port 443",
    "error: RPC failed; HTTP 502 curl 22 The requested URL returned error: 502",
    "fatal: the remote end hung up unexpectedly",
    "Get \"https://api.github.com/repos\": context deadline exceeded",
    "dial tcp 140.82.121.6:443: i/o timeout",
    "gh: Service Unavailable (HTTP 503)",
    "API rate limit exceeded for user",
    "fatal: unable to access 'https://github.com/x.git/': Could not resolve host: no such host",
]

PERMANENT_STDERR = [
    "! [rejected] main -> main (non-fast-forward)",
    "git@github.com: Permission denied (publickey).",
    "remote: Invalid username or password. fatal: Authentication failed for 'https://github.com/x.git/'",
    "gh: Not Found (HTTP 404)",
    "gh: 403 Forbidden",
    "release create failed: name already exists on this account",
]


@pytest.mark.parametrize("stderr", TRANSIENT_STDERR)
def test_transient_stderr_is_retryable(stderr: str) -> None:
    """Known transient network failures are classified as retryable."""
    assert is_transient_subprocess_error(stderr, returncode=1) is True


@pytest.mark.parametrize("stderr", PERMANENT_STDERR)
def test_permanent_stderr_is_not_retryable(stderr: str) -> None:
    """Auth, 4xx and non-fast-forward failures are never retried."""
    assert is_transient_subprocess_error(stderr, returncode=1) is False


def test_permanent_signature_wins_over_transient() -> None:
    """When both signatures appear, permanent wins.

    A chained report like "401 Unauthorized ... rate limit exceeded" contains a
    transient phrase, but the auth half is the real cause; retrying it 30 times
    would just spam the API and bury the actionable error.
    """
    mixed = "gh: 401 Unauthorized - API rate limit exceeded for user"
    assert is_transient_subprocess_error(mixed, returncode=1) is False


def test_success_is_never_retryable() -> None:
    """returncode 0 is a success, no matter what landed on stderr."""
    assert is_transient_subprocess_error("HTTP 503 Service Unavailable", returncode=0) is False


def test_empty_stderr_is_not_retryable() -> None:
    """A failure with no stderr is unclassifiable, so it is not retried blindly."""
    assert is_transient_subprocess_error("", returncode=1) is False


def test_unrecognized_stderr_is_not_retryable() -> None:
    """An unknown failure fails fast rather than being retried on a guess."""
    assert is_transient_subprocess_error("error: pathspec 'nope' did not match", returncode=1) is False


# ── HTTP / urllib classification ─────────────────────────────────────────────


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_transient_http_status_codes(code: int) -> None:
    """408/429/5xx are transient — the server may recover."""
    exc = urllib.error.HTTPError("https://example.invalid", code, "boom", {}, None)  # type: ignore[arg-type]
    assert is_transient_http_error(exc) is True


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_permanent_http_status_codes(code: int) -> None:
    """4xx client errors are permanent — retrying cannot change the answer."""
    exc = urllib.error.HTTPError("https://example.invalid", code, "boom", {}, None)  # type: ignore[arg-type]
    assert is_transient_http_error(exc) is False


@pytest.mark.parametrize(
    "exc",
    [
        socket.timeout("timed out"),
        TimeoutError("timed out"),
        ssl.SSLError("handshake failure"),
        RemoteDisconnected("closed"),
        ConnectionResetError("reset by peer"),
    ],
)
def test_transient_socket_level_errors(exc: BaseException) -> None:
    """Socket, TLS and connection-reset failures are transient."""
    assert is_transient_http_error(exc) is True


def test_urlerror_unwraps_its_reason() -> None:
    """A URLError is classified by the exception it wraps, not by its own type."""
    assert is_transient_http_error(urllib.error.URLError(TimeoutError("slow"))) is True
    assert is_transient_http_error(urllib.error.URLError(ValueError("bad url"))) is False


def test_none_is_not_a_transient_error() -> None:
    """A missing exception is not a network error."""
    assert is_transient_http_error(None) is False


# ── Retry wrapper (real subprocesses) ────────────────────────────────────────


def test_run_with_retry_returns_success_without_retrying() -> None:
    """A command that succeeds runs once and returns its output."""
    result = run_with_retry([sys.executable, "-c", "print('ok')"], max_attempts=3, backoff=0.0)
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


def test_run_with_retry_fails_fast_on_permanent_error() -> None:
    """A permanent failure raises immediately instead of burning the attempt budget."""
    attempts: list[int] = []

    def record(attempt: int, _proc: subprocess.CompletedProcess[str]) -> None:
        attempts.append(attempt)

    script = "import sys; sys.stderr.write('fatal: Authentication failed'); sys.exit(1)"
    with pytest.raises(subprocess.CalledProcessError):
        run_with_retry(
            [sys.executable, "-c", script],
            max_attempts=5,
            backoff=0.0,
            on_retry=record,
        )
    assert attempts == [], "a permanent failure must not schedule any retry"


def test_run_with_retry_retries_a_transient_error_then_gives_up() -> None:
    """A transient failure is retried up to max_attempts, then reported."""
    attempts: list[int] = []

    def record(attempt: int, _proc: subprocess.CompletedProcess[str]) -> None:
        attempts.append(attempt)

    script = "import sys; sys.stderr.write('error: RPC failed; HTTP 503'); sys.exit(1)"
    result = run_with_retry(
        [sys.executable, "-c", script],
        max_attempts=3,
        backoff=0.0,
        check=False,
        on_retry=record,
    )
    assert result.returncode == 1
    assert len(attempts) == 2, "3 attempts means 2 retries were scheduled"


def test_run_with_retry_check_false_returns_instead_of_raising() -> None:
    """check=False surfaces the failed CompletedProcess rather than raising."""
    script = "import sys; sys.stderr.write('nope'); sys.exit(3)"
    result = run_with_retry([sys.executable, "-c", script], max_attempts=1, backoff=0.0, check=False)
    assert result.returncode == 3


def test_attempt_budget_is_generous_enough_for_a_real_outage() -> None:
    """The default attempt budget tolerates a multi-minute github.com wobble."""
    assert GH_MAX_ATTEMPTS >= 10
