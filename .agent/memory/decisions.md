# Architecture Decision Log

> Persistent record of key architectural decisions made in this project.
> New entries appended to the top.

---

## ADR-001: Adopt `.agent/` Directory for AI Agent Configuration

**Date**: 2026-07-02

**Context**: AI coding tools (Claude Code, Cursor, GitHub Copilot, OpenCode, etc.) each use different configuration files (`CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, etc.). This fragmentation means project context must be duplicated across vendor-specific formats.

**Decision**: Adopt the `.agent/` directory structure as the canonical source of truth for AI agent instructions. This follows the community proposal ([Issue #71](https://github.com/agentsmd/agents.md/issues/71)) and aligns with the broader ecosystem trend toward standardized agent configuration. The root-level `AGENT.md` serves as the entry point, with progressive disclosure via subdirectories (`context/`, `rules/`, `memory/`, `skills/`).

**Consequences**:
- Positive: Single source of truth for agent instructions, tool-agnostic
- Positive: Progressive disclosure avoids context bloat
- Negative: Not all tools natively read `.agent/` yet (may need symlinks or generation for specific tools)
- Risk: The `.agent/` standard is still evolving; structure may need updates

**Status**: Accepted

---

*Add new decisions above this line. Format:*

*```*
*## ADR-{NNN}: {Title}*

***Date**: YYYY-MM-DD*

***Context**: {What prompted the decision}*

***Decision**: {What was decided and why}*

***Consequences**: {Positive and negative effects}*

***Status**: {Proposed | Accepted | Deprecated | Superseded}*
*```*
