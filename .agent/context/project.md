# Project Context

> Detailed project structure, architecture, and domain knowledge.

---

## Repository Structure

```
JanusAgent/
├── main.py                        # Framework entry point
├── pyproject.toml                 # UV workspace root config
├── ruff.toml                      # Linter/formatter rules
├── .pre-commit-config.yaml        # Git pre-commit hooks
├── uv.lock                        # Locked dependency versions
│
├── packages/
│   ├── agent-core/                # Core abstractions and base classes
│   ├── agentpool/                 # AgentPool orchestration hub (multi-protocol)
│   ├── quant-agent/               # Quantitative analysis agent
│   └── companion-agent/           # Conversational companion agent
│
├── docs/
│   └── survey/                    # Technical surveys and background research
│
├── openspec/                      # Spec-driven change management
│   ├── config.yaml
│   ├── specs/
│   └── changes/
│       ├── active/
│       └── archive/
│
├── .omo/                          # Task orchestration (OpenCode/Sisyphus)
│   ├── plans/
│   ├── evidence/
│   ├── notepads/
│   └── boulder.json
│
├── .agent/                        # ← AI agent configuration (this directory)
│   ├── AGENT.md
│   ├── context/
│   ├── rules/
│   ├── memory/
│   └── skills/
│
└── .github/
    └── copilot-instructions.md    # GitHub Copilot rules
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                    JanusAgent                     │
│  (main.py - framework orchestrator)               │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────┐      ┌──────────────────┐       │
│  │  Quant Agent  │      │ Companion Agent  │       │
│  │  (quantitative)│     │  (conversational) │       │
│  └──────┬───────┘      └────────┬─────────┘       │
│         │                       │                  │
│         └───────────┬───────────┘                  │
│                     │                              │
│            ┌────────▼────────┐                     │
│            │   AgentPool     │                     │
│            │  (orchestration)│                     │
│            │  ACP / AG-UI    │                     │
│            │  MCP / OpenCode │                     │
│            └─────────────────┘                     │
│                                                   │
└──────────────────────────────────────────────────┘
```

### AgentPool (packages/agentpool/)

AgentPool is the core orchestration layer. It enables YAML-based configuration of heterogeneous AI agents and bridges multiple protocols:

- **ACP** — Agent Communication Protocol (for IDE integration like Zed, Toad)
- **AG-UI** — Agent UI protocol
- **MCP** — Model Context Protocol
- **OpenCode** — OpenCode TUI/Desktop integration

Key features:
- Multi-agent coordination (teams, chains, parallel execution)
- Rich YAML configuration (models, tools, triggers, storage)
- Structured output with schema validation
- Skill Commands (SKILL.md as slash commands)
- Streaming TTS support

---

## Development Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | `uv` (workspace mode) |
| Linter | `ruff` |
| Formatter | `ruff format` |
| Pre-commit | `pre-commit` (config: `.pre-commit-config.yaml`) |
| Testing | `pytest` (no test classes, plain functions) |
| Docstrings | Google style |
| VCS | Git |

---

## Development Commands

```bash
# Install all dependencies
uv sync --all-extras

# Run linter
ruff check .

# Run formatter
ruff format .

# Run tests
pytest

# Run the framework
python main.py
```

---

## Key Design Decisions

- **Workspace-first**: UV workspace with 4 packages for clean separation of concerns
- **Spec-driven development**: All significant changes go through OpenSpec flow
- **Protocol-agnostic**: AgentPool abstracts over ACP/AG-UI/MCP so agents can be exposed through any protocol
- **YAML-first configuration**: Agents defined in YAML, not code
