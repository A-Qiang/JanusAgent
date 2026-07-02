# Git Workflow

> Git conventions and workflow rules for AI agents.

---

## Branch Strategy

- **main**: Stable, production-ready
- Feature branches: `feat/<short-description>`
- Fix branches: `fix/<short-description>`
- Keep branches short-lived and focused

## Commit Messages

Follow conventional commits format:

```
<type>: <brief description>

[optional body with details]
```

**Types**:
- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code restructuring (no behavior change)
- `test:` — Adding/updating tests
- `docs:` — Documentation changes
- `chore:` — Maintenance, dependencies, CI
- `style:` — Formatting, linting (no logic change)

**Rules**:
- First line ≤ 72 characters
- Use imperative mood ("Add feature" not "Added feature")
- Body explains WHY, not WHAT (the diff shows what)
- Reference issues/PRs when applicable

## Before Committing

1. Run `ruff check .` — must pass
2. Run `ruff format .` — must be clean
3. Run `pytest` — must pass
4. Check `git status` — staged changes only (no unintended files)

## Pre-commit Hooks

This project uses `.pre-commit-config.yaml`. Hooks run automatically on `git commit`.

## What NOT to Do

- ❌ Do NOT commit without explicit user request
- ❌ Do NOT force-push to main/master without explicit approval
- ❌ Do NOT modify `.gitignore` without clear reason
- ❌ Do NOT commit secrets, credentials, or `.env` files
- ❌ Do NOT use `--no-verify` to skip hooks unless explicitly asked
