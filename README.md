# ai-maestro-assistant-role-agent

<!--BADGES-START-->
[![CI](https://github.com/Emasoft/ai-maestro-assistant-role-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Emasoft/ai-maestro-assistant-role-agent/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.4.0-blue)](https://github.com/Emasoft/ai-maestro-assistant-role-agent)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
<!--BADGES-END-->

Role-plugin for ASSISTANT-titled agents in the AI Maestro ecosystem (R39). Each human user (except the MAESTRO) gets exactly one ASSISTANT: it can plan like a MANAGER and program like an AUTONOMOUS agent, but it MUST NOT create agents or teams and has NO governing powers. It serves exactly one user (label 'Assistant of <user>'), obeys ONLY that user (not even the MAESTRO), approves only its OWN TRDDs, has no team, and is invisible to every agent except the MANAGER — which may assign it a refusable task only if the user enabled MANAGER-collaboration (R39.8/R39.9). On a shared GitHub project it acts as a peer with equal authority; when the MANAGER assigns a collaborator there (and the user permits), a scoped, user-revocable channel to that collaborator opens (R39.10). It inherits its user's kanban tasks and granted permissions. Requires AI Maestro for messaging/identity skills.

## Installation

### From Marketplace

```bash
# 1. Add the marketplace (first time only)
claude plugin marketplace add Emasoft/ai-maestro-plugins

# 2. Install the plugin
claude plugin install ai-maestro-assistant-role-agent@ai-maestro-plugins

# 3. Restart Claude Code (or run /reload-plugins) to activate
```

### From GitHub

```bash
gh repo clone Emasoft/ai-maestro-assistant-role-agent
cd ai-maestro-assistant-role-agent
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

### As a Claude Code Plugin

Add to your Claude Code configuration:

```json
{
  "plugins": [
    "https://github.com/Emasoft/ai-maestro-assistant-role-agent"
  ]
}
```

## Uninstall

```bash
claude plugin uninstall ai-maestro-assistant-role-agent
```

## Update

```bash
claude plugin update ai-maestro-assistant-role-agent@ai-maestro-plugins
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Plugin not appearing after install | Restart Claude Code or run `/reload-plugins` |
| Old version still showing after update | Restart Claude Code; if still stale, run `claude plugin update ai-maestro-assistant-role-agent` again |
| Hook path not found after update | Re-run `uv run python scripts/publish.py --install-hook` |
| `marketplace not found` error | Run `claude plugin marketplace update ai-maestro-plugins` to refresh |
| Permission denied on script | Ensure scripts are executable: `chmod +x scripts/*.py` |
| Import errors after install | Re-run `uv pip install -e .` to refresh the venv |
| Session won't pick up new hooks | Restart required — `/reload-plugins` does NOT re-read project-scoped settings.json hooks |

## Usage

This is a **role-plugin**, not a runnable command — it ships a single agent
persona (`agents/ai-maestro-assistant-role-agent-main-agent.md`), no CLI. You do
not "run" it. AI Maestro binds it to a human user's **ASSISTANT** slot; from then
on that user drives it by typing in their own terminal. Install it, then assign
the ASSISTANT title to a user via the AI Maestro UI (or `aimaestro-agent` tooling).

## Capabilities & boundaries (R39)

Each human user (except the MAESTRO) is auto-assigned exactly **one** ASSISTANT.
It is a hybrid — **MANAGER-style planning + AUTONOMOUS-style programming** — minus
agent/team creation and minus all governing powers. The persona is the source of
truth; this table is the summary an installer needs.

| The ASSISTANT **CAN** | The ASSISTANT **CANNOT** |
|---|---|
| Plan its user's work; derive NPT/EHT tasks; author & self-approve its **own** TRDDs (R39.8) | Create, delete, or modify **agents** or **teams** (MAESTRO-only, via the UI) |
| Clone repos, write code, branch, commit, push its **own** branch, open PRs, comment on GitHub | Exercise governing powers — approve/gate/vote on **another** agent's TRDD or work |
| Run tests/builds/linters and install deps **inside its own workspace** | Merge its own PRs / `gh pr merge` (unless the user says so, by PR number, that turn) |
| Read anywhere; inherit its user's kanban tasks & granted permissions (R39.7) | Message anyone but **its user** and (if the user permits) the **MANAGER** — it is invisible to every other agent (R39.7) |
| Collaborate as a **peer** on a shared GitHub project | Use a **sudo password** — agents never face a sudo gate (R32) |
| Accept a **refusable** task from the MANAGER — only if its user enabled collaboration (R39.9) | Write outside its own workspace, read secrets, or run destructive git on branches it doesn't own |

**Whom it obeys:** its user **unconditionally**; the MANAGER **only** with the
user's explicit permission, and even then every task is **refusable** (R39.5 /
R39.9 / R41). Not the MAESTRO user, not any other agent.

**Two transports, and only one of them is policed.** AMP goes through the AI
Maestro server, which checks every send against the comm-graph and returns HTTP
403 on a forbidden one. Claude Code's own cross-session channel does not:
`SendMessage` to a live session, `ListAgents` to enumerate them (including
sessions on **other machines** and in the cloud), and a `@name` mention typed in
the prompt all bypass the server entirely, so **no 403 is possible there** and
the comm-graph is unenforced — the limit is the persona's alone to hold. Inbound
messages are governed only by the user's `crossSessionInbound` setting. The
persona states all of this in full; it is duplicated here deliberately, not
delegated (ai-maestro#107).

## Development

### Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing

```bash
uv run pytest tests/ -v
```

### Linting & Formatting

```bash
uv run ruff check scripts/ tests/
uv run ruff format scripts/ tests/
uv run mypy scripts/
```

## Project Structure

```text
ai-maestro-assistant-role-agent/
├── .claude-plugin/
│   └── plugin.json                              # Plugin manifest
├── .github/
│   └── workflows/                               # CI/CD workflows
├── agents/
│   └── ai-maestro-assistant-role-agent-main-agent.md   # The ASSISTANT persona
├── ai-maestro-assistant-role-agent.agent.toml   # AI Maestro agent profile
├── git-hooks/                                   # Git hooks (pre-push)
├── scripts/                                     # Release pipeline scripts
├── tests/                                       # Test suite
├── pyproject.toml                               # Project configuration
├── cliff.toml                                   # Changelog generation config
├── README.md                                    # This file
├── LICENSE                                      # License file
└── .gitignore                                   # Git ignore rules
```

## Marketplace

This plugin is available on the [ai-maestro-plugins marketplace](https://github.com/Emasoft/ai-maestro-plugins).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

**Emasoft** - [GitHub](https://github.com/Emasoft)
