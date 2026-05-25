# Contributing to Circle Cycle

## Code Rules

- No hardcoded values — use `domain/constants/` or `infrastructure/config/settings.py`.
- No inline comments — self-documenting code only. Docstrings on public classes and functions.
- Enums → `domain/enums/`. Abstract interfaces → `domain/interfaces/`. Constants → `domain/constants/`.
- All functions fully typed. No `Any`. Narrow `dict` to typed models.
- Domain exceptions defined in `domain/exceptions/`, caught and handled in infrastructure layer.
- No mutable default arguments. No global state.
- Prefer `dataclasses.dataclass(frozen=True)` for value objects.
- No `print()` — use structured logging if logging is needed.
- Keep functions under 20 lines. Decompose otherwise.

## Clean Architecture Rules

- `domain/` must NEVER import from `application/`, `infrastructure/`, or any third-party package.
- `application/` depends only on `domain/` — never on Tkinter, file I/O, or external libs.
- `infrastructure/` implements domain interfaces and is the only layer touching frameworks.
- New features: define the interface in `domain/interfaces/`, implement in `infrastructure/`.

## Adding New Content

### New Character
Add entry to `data/characters.json` with required fields: `id`, `name`, `size`, `hp`, `attack`, `speed`, `color`, `abilities`.

### New Ability
Add entry to `data/abilities.json`. If adding a new effect type, also add it to `domain/enums/status_effect.py` and handle in `application/services/ability_resolver.py`.

### New Card
Add entry to `data/cards.json`. If adding a new stat type, also add it to `domain/enums/card_stat.py` and handle in `application/services/card_applicator.py`.

## Testing

- Unit tests go in `tests/unit/` — test use cases with mocked repositories.
- Integration tests go in `tests/integration/` — test with real JSON data.
- Run: `pytest --cov=src --cov-report=term-missing`
- All tests must pass before committing.

## Pre-commit Checklist

1. `ruff format --check .` — no unformatted files
2. `ruff check .` — must pass
3. `mypy src` — must pass
4. `pytest --cov=src` — must pass, coverage ≥ 70%

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code restructuring
- `docs:` — documentation only
- `test:` — adding or fixing tests
- `chore:` — tooling, config, maintenance
- `style:` — formatting (no logic change)
