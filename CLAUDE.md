# Circle Cycle

Circle Cycle is a turn-based strategy game built with Python 3.12+ and Tkinter, following Clean Architecture principles.

## Quick Start

```bash
# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Run the game
python -m circle_cycle

# Run tests
pytest --cov=src --cov-report=term-missing

# Lint and type-check
ruff check . && mypy src

# Format code
ruff format .
```

## Project Structure

```
src/circle_cycle/
├── domain/           # Layer 1 — Pure business rules (no external deps)
│   ├── entities/     # Character, Ability, Card dataclasses
│   ├── enums/        # AbilityType, CharacterSize, StatusEffect, CardStat
│   ├── interfaces/   # ABC ports (DataRepository)
│   ├── value_objects/ # Immutable CardEffect
│   ├── exceptions/   # Domain-specific exceptions
│   └── constants/    # Game constants
├── application/      # Layer 2 — Use cases and services
│   ├── services/     # BattleEngine, BotAI, AbilityResolver, CardApplicator
│   └── dto/          # Data transfer objects
├── infrastructure/   # Layer 3 — Adapters and frameworks
│   ├── persistence/  # JsonDataRepository (implements DataRepository)
│   ├── ui/           # Tkinter app, screens, rendering
│   └── config/       # Settings from environment
└── shared/           # Cross-cutting utilities
```

## Clean Architecture Rules

- `domain/` has ZERO imports from Tkinter, file I/O, or any third-party package.
- `application/` depends only on `domain/` interfaces and entities.
- `infrastructure/` implements domain interfaces — only layer with framework code.
- Dependency injection wires infrastructure into application at startup.

## Data

Runtime JSON definitions live in `data/`:
- `characters.json` — playable character stats and abilities
- `abilities.json` — attack/skill definitions
- `cards.json` — buff cards for between-round selection

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install package in dev mode |
| `make run` | Launch the game |
| `make test` | Run tests with coverage |
| `make lint` | Run ruff + mypy |
| `make fmt` | Auto-format with ruff |
