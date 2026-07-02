# Coding Conventions

> Invariant behavioral guidelines for AI agents writing code in this project.

---

## Language & Syntax

- **Python 3.12+**: Use newest language features when appropriate
  - Pattern matching (`match`/`case`)
  - Walrus operator (`:=`)
  - Type union syntax (`X | Y` instead of `Optional[X]`, `Union[X, Y]`)
  - Exception groups (`except*`)
- Prefer modern, idiomatic Python over verbose patterns

## Code Style

- Follow PEP 8
- Use `ruff` for linting (`ruff check .`)
- Use `ruff format` for formatting
- 4-space indentation, no tabs

## Type Annotations

- All public functions MUST have type annotations
- Use `X | None` instead of `Optional[X]`
- Use `list[X]` instead of `List[X]` (built-in generics)
- Use `dict[K, V]` instead of `Dict[K, V]`

## Docstrings

- **Style**: Google-style docstrings
- **Args section**: Omit types (they're in the signature)
- **Returns section**: Only include if the return value's meaning isn't obvious from the name
- **Format**: Use plain Markdown in docstrings

Example:
```python
def calculate_risk(positions: list[Position], market_data: MarketData) -> float:
    \"\"\"Calculate portfolio risk from current positions.

    Args:
        positions: Current portfolio positions
        market_data: Current market conditions

    Returns:
        Risk score as a float between 0 and 1
    \"\"\"
    ...
```

## Markdown in Code

You MAY use:
- Markdown admonitions: `!!! info`, `!!! note`, `!!! warning`
- Markdown tables
- Markdown lists
- In docstrings and documentation files

## Error Handling

- Use specific exception types (avoid bare `except:`)
- Use `try`/`except`/`else`/`finally` appropriately
- Prefer early returns over deep nesting
- Use `raise` from to chain exceptions

## Testing

- **Framework**: `pytest`
- **Structure**: Plain functions (NOT test classes)
- **Naming**: `test_<function>_<scenario>` pattern
- **Coverage**: Tests for public APIs, edge cases, and error paths

## Imports

- Standard library → Third-party → Local (grouped, alphabetical within groups)
- Use absolute imports over relative imports

## What NOT to Do

- ❌ No `as any` / `@ts-ignore` / `@ts-expect-error` (TypeScript only, but same principle: no type suppression)
- ❌ No empty `except` blocks
- ❌ No shotgun debugging (random changes hoping something sticks)
- ❌ No deleting failing tests to "pass"
