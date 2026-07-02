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
└── skills/               # Reusable capability definitions (50+ skills installed)
    │                       # Grouped by source for maintainability
    │
    ├── # Obra Workflow (14)
    ├── brainstorming/    # Guided brainstorming workflows
    ├── dispatching-parallel-agents/  # Parallel agent orchestration
    ├── executing-plans/  # Plan execution patterns
    ├── finishing-a-development-branch/  # Branch completion workflows
    ├── receiving-code-review/  # Handling code reviews
    ├── requesting-code-review/  # Requesting code reviews
    ├── subagent-driven-development/  # Subagent-driven development
    ├── systematic-debugging/  # Structured debugging
    ├── test-driven-development/  # TDD workflows
    ├── using-git-worktrees/  # Git worktree usage
    ├── using-superpowers/  # Superpowers usage guide
    ├── verification-before-completion/  # Pre-completion verification
    ├── writing-plans/    # Plan writing
    └── writing-skills/   # Skill authoring
    │
    ├── # Anthropic Suite (17)
    ├── algorithmic-art/  # Generative art creation
    ├── brand-guidelines/ # Brand consistency enforcement
    ├── canvas-design/    # HTML Canvas design
    ├── claude-api/       # Claude API integration
    ├── doc-coauthoring/  # Document co-authoring
    ├── docx/             # DOCX generation
    ├── frontend-design/  # Frontend UI/UX design
    ├── internal-comms/   # Internal communications
    ├── mcp-builder/      # MCP server building
    ├── pdf/              # PDF generation
    ├── pptx/             # PPTX generation
    ├── security-review/  # Security vulnerability audit
    ├── skill-creator/    # Skill creation framework
    ├── slack-gif-creator/ # Slack GIF creation
    ├── theme-factory/    # Theme generation
    ├── web-artifacts-builder/ # Web artifact building
    ├── webapp-testing/   # Web app testing
    └── xlsx/             # Excel/Spreadsheet generation
    │
    └── # Custom / User-installed (16)
        ├── code-submit/              # Code submission workflows
        ├── create-agent-skills/      # Agent skill creation
        ├── create-skill-file/        # Skill file scaffolding (zh)
        ├── create-skill-file-EN/     # Skill file scaffolding (en)
        ├── daily-ai-news/            # Daily AI news digest
        ├── darwin-skill/             # Darwin-themed interaction
        ├── deep-reading-analyst/     # Deep reading & analysis
        ├── dry-refactoring/          # DRY-principled refactoring
        ├── fastgpt-workflow-generator/ # FastGPT workflow generation
        ├── heal-skill/               # Skill healing & repair
        ├── local-diff-review/        # Local diff code review
        ├── metaskill/                # Meta-skill framework
        ├── planning-with-files/      # File-based planning
        ├── prompt-master/            # Prompt engineering
        ├── prompt-optimize/          # Prompt optimization
        └── software-copyright-writer/ # Software copyright docs
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
