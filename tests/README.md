# Tests

The test suite for `ai-maestro-assistant-role-agent`. Every test asserts on a
**real shipped artifact** from the working tree — the manifest, the agent
markdown, the AI Maestro profile, and the release pipeline files. Nothing is
mocked, because a mocked manifest cannot tell you whether the plugin a user
installs is loadable.

## Run locally

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

Match what CI does (two duration-balanced shards via `pytest-split`):

```bash
uv run pytest tests/ --splits 2 --group 1 -v
uv run pytest tests/ --splits 2 --group 2 -v
```

Match what the pre-push gate does (`publish.py --gate` G4):

```bash
uv run pytest tests/ -x -q --tb=short
```

## Files

| File | Covers |
|---|---|
| `conftest.py` | Session fixtures that load the real manifest, agent markdown, profile, and `pyproject.toml`. |
| `test_plugin_manifest.py` | `.claude-plugin/plugin.json` — required fields, semver, version parity with `pyproject.toml`, declared dependency and license. |
| `test_agent_definition.py` | `agents/*-main-agent.md` — YAML frontmatter parses with a real parser, name matches the filename stem, examples are well formed, R39 prohibitions survive, no absolute path leaks. |
| `test_agent_profile_toml.py` | `*.agent.toml` — the quad-match invariant, ASSISTANT-only title binding, no bundled skills, required external skills, `team-governance` stays excluded. |
| `test_transport_claims.py` | **Every shipped prose file** — a 403 / server-enforced promise never travels without naming the cross-session channel that cannot return one, plus the channel's current reach (other machines, `@name`, `crossSessionInbound`). Corpus-scoped on purpose: the persona-scoped predecessor reported clean while `README.md` was wrong. |
| `test_canonical_rule_blocks.py` | The vendored canonical R22/R23 governance blocks — marker integrity and byte-for-byte fidelity when present, self-disarming while they are withheld. |
| `test_no_bare_github_mentions.py` | Postable text — no bare `@handle` outside a code span, because one pages a real account. |
| `test_cpv_network_resilience.py` | `scripts/cpv_network_resilience.py` — transient-vs-fatal classification of publish-time network and HTTP failures. |
| `test_pipeline_files.py` | The canonical CPV pipeline — `publish.py`, pre-push hook, the three workflows, least-privilege permissions, timeouts, changelog and lint configs. |

## Adding a test

Add it to the file that owns the artifact. Give every test function a one-line
docstring stating what it proves — the docstring is what the result table
shows, and a test whose purpose is not stated in one line is usually testing
more than one thing.

Tests open no browsers, no sockets, and no subprocesses, so there is no
teardown to write; if you add a test that does, close what it opens in a
`try/finally` so the suite leaves a clean process table.
