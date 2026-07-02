# JanusAgent — Agent Instructions

> Entry point for AI coding agents working on this project.
> Read this first, then load relevant context from `.agent/` subdirectories as needed.

---

## Project Overview

JanusAgent is a **dual-faced personal agent framework** — a customizable framework that runs two AI agents:

- **Quant Agent** (`packages/quant-agent/`): Quantitative analysis and data-driven tasks
- **Companion Agent** (`packages/companion-agent/`): Conversational companion and personal assistance

Both agents are built on top of **AgentPool** (`packages/agentpool/`), a unified agent orchestration hub that bridges multiple protocols (ACP, AG-UI, MCP, OpenCode).

---

## How to Use This Directory

```
.agent/
├── AGENT.md              # ← You are here. Entry point & router.
├── context/
│   └── project.md        # Project structure, architecture, stack details
├── rules/
│   ├── coding.md         # Coding conventions and style guide
│   └── git.md            # Git workflow and commit conventions
├── memory/
│   └── decisions.md      # Architecture Decision Records (ADRs)
└── skills/               # Reusable capability definitions (31+ community skills installed)
    ├── brainstorming/    # (obra) Guided brainstorming workflows
    ├── dispatching-parallel-agents/  # (obra) Parallel agent orchestration
    ├── executing-plans/  # (obra) Plan execution patterns
    ├── finishing-a-development-branch/  # (obra) Branch completion workflows
    ├── receiving-code-review/  # (obra) Handling code reviews
    ├── requesting-code-review/  # (obra) Requesting code reviews
    ├── subagent-driven-development/  # (obra) Subagent-driven development
    ├── systematic-debugging/  # (obra) Structured debugging
    ├── test-driven-development/  # (obra) TDD workflows
    ├── using-git-worktrees/  # (obra) Git worktree usage
    ├── using-superpowers/  # (obra) Superpowers usage guide
    ├── verification-before-completion/  # (obra) Pre-completion verification
    ├── writing-plans/    # (obra) Plan writing
    ├── writing-skills/   # (obra) Skill authoring
    ├── algorithmic-art/  # (anthropic) Generative art creation
    ├── brand-guidelines/ # (anthropic) Brand consistency enforcement
    ├── canvas-design/    # (anthropic) HTML Canvas design
    ├── claude-api/       # (anthropic) Claude API integration
    ├── doc-coauthoring/  # (anthropic) Document co-authoring
    ├── docx/             # (anthropic) DOCX generation
    ├── frontend-design/  # (anthropic) Frontend UI/UX design
    ├── internal-comms/   # (anthropic) Internal communications
    ├── mcp-builder/      # (anthropic) MCP server building
    ├── pdf/              # (anthropic) PDF generation
    ├── pptx/             # (anthropic) PPTX generation
    ├── skill-creator/    # (anthropic) Skill creation framework
    ├── slack-gif-creator/ # (anthropic) Slack GIF creation
    ├── theme-factory/    # (anthropic) Theme generation
    ├── web-artifacts-builder/ # (anthropic) Web artifact building
    ├── webapp-testing/   # (anthropic) Web app testing
    └── xlsx/             # (anthropic) Excel/Spreadsheet generation
```

**Progressive disclosure**: Only read the files relevant to your current task.

---

## Key Conventions

### Development Workflow

This project uses **OpenSpec** for spec-driven change management:

- `openspec/` — capability specs and archived changes
- Workflow: `explore → propose → apply → archive`
- See `packages/agentpool/AGENTS.md` for detailed workflow instructions

### Task Orchestration

The `.omo/` directory tracks structured development work:

- `plans/` — implementation plans
- `evidence/` — verification artifacts
- `notepads/` — per-work learnings and decisions

### Stack

- **Language**: Python 3.12+
- **Package manager**: `uv` (uv.lock at root)
- **Linter/Formatter**: `ruff`
- **Pre-commit**: `.pre-commit-config.yaml`
- **Workspace**: UV workspace with 4 packages under `packages/`

### Key Files to Know

| File | Purpose |
|---|---|
| `pyproject.toml` | Workspace & project config |
| `main.py` | Framework entry point |
| `ruff.toml` | Linter/formatter config |
| `.pre-commit-config.yaml` | Git hooks |

---

## What to Do When Starting a Session

1. Read this file (`.agent/AGENT.md`)
2. Read `.agent/context/project.md` for full project context
3. Read `.agent/rules/coding.md` for coding conventions
4. If working on git operations, read `.agent/rules/git.md`
5. Check `.agent/memory/decisions.md` for relevant past decisions
6. For spec-driven changes, refer to `openspec/` and `packages/agentpool/AGENTS.md`

---

*See `.agent/context/project.md` for detailed project structure and architecture.*
