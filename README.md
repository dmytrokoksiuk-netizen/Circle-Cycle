# Circle Cycle

Circle Cycle is a turn-based strategy game built with Python 3.12+ and Tkinter, following Clean Architecture.

## Features

- 7 playable characters with distinct roles (DPS, Healer, Buffer, Debuffer, Shield Breaker)
- Planning phase → execution phase battle flow with speed-based turn order
- Mana resource system and shield damage absorption
- Buff/debuff system with timed durations
- Ultimate abilities charged by using Specials
- JSON-driven characters, abilities, and cards
- Weighted card selection between rounds
- Bot AI with role-aware targeting
- Clean Architecture (domain → application → infrastructure)
- Fully typed with mypy strict mode

## Prerequisites

- **Python 3.12+** (3.13 recommended)
- **Tkinter** — included with standard Python on Windows/macOS; on Linux install `python3-tk`

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dmytrokoksiuk-netizen/Circle-Cycle.git
cd Circle-Cycle

# Create a virtual environment (pick one)
python -m venv .venv          # standard
# OR
uv venv                       # if using uv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
# OR with uv:
uv pip install -e ".[dev]"

# Run the game
python -m circle_cycle

# Run tests
python -m pytest --cov=src --cov-report=term-missing

# Lint and type-check
ruff check . && mypy src

# Format code
ruff format .
```

## Build & Run (short version)

```bash
pip install -e ".[dev]"       # install
python -m circle_cycle        # run
python -m pytest              # test
```

## Project Layout

```
src/circle_cycle/
├── domain/           # Pure business rules (entities, enums, interfaces)
├── application/      # Services (BattleEngine, BotAI, resolvers)
├── infrastructure/   # Adapters (JSON repo, Tkinter UI, config)
└── shared/           # Cross-cutting utilities
data/                 # Runtime JSON definitions (characters, abilities, cards)
tests/                # Unit and integration tests
```

## Characters

| Name | Role | Description |
|------|------|-------------|
| Nova | DPS | Balanced damage dealer with burn |
| Stone | DPS | Tanky bruiser with high HP/shield |
| Ace | DPS | Fast glass cannon |
| Sage | Healer | Restores ally HP and shields |
| Drum | Buffer | Boosts team ATK/SPD/DEF |
| Hex | Debuffer | Reduces enemy stats, fragile but fast |
| Spike | Breaker | Pierces and destroys enemy shields |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and layer responsibilities
- [CLAUDE.md](CLAUDE.md) — Game mechanics, constants, and agent instructions
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines
