# Circle Cycle

Circle Cycle is a turn-based strategy game built with Python 3.12+ and Tkinter, following Clean Architecture.

## Features

- Tkinter Canvas-based character rendering
- JSON-driven characters, abilities, and cards
- Clean Architecture (domain → application → infrastructure)
- Selection screen, battle screen, and card screen flow
- Fully typed with mypy strict mode

## Quick Start

```bash
# Install dependencies (dev mode)
python -m pip install -e ".[dev]"

# Run the game
python -m circle_cycle

# Run tests
pytest --cov=src --cov-report=term-missing

# Lint and type-check
ruff check . && mypy src
```

## Project Layout

```
src/circle_cycle/
├── domain/           # Pure business rules (entities, enums, interfaces)
├── application/      # Services (BattleEngine, BotAI, resolvers)
├── infrastructure/   # Adapters (JSON repo, Tkinter UI, config)
└── shared/           # Cross-cutting utilities
data/                 # Runtime JSON definitions
tests/                # Unit and integration tests
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.
