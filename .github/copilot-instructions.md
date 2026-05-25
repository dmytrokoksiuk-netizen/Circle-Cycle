# Copilot Instructions for Circle Cycle

## Architecture
- Follow Clean Architecture: domain → application → infrastructure (deps point inward).
- `domain/` has ZERO imports from Tkinter, file I/O, or third-party packages.
- `application/services/` orchestrates game logic using domain interfaces only.
- `infrastructure/` implements interfaces and contains all framework code.

## Code Style
- Use type hints on every public method. No `Any`.
- Add docstrings to every class and public method.
- Keep all game logic in `application/services/` and `domain/entities/`.
- Keep `infrastructure/ui/` focused on rendering and event forwarding.
- Load all characters, abilities, and cards from `data/*.json` via `DataRepository`.
- Prefer small, composable objects over large shared state.
- Use domain enums (`AbilityType`, `StatusEffect`, etc.) instead of raw strings.
- Domain exceptions in `domain/exceptions/`, handle in infrastructure layer.

## Commands
- Run: `python -m circle_cycle`
- Test: `pytest --cov=src --cov-report=term-missing`
- Lint: `ruff check . && mypy src`
- Format: `ruff format .`
