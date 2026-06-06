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
- `characters.json` — playable character stats, mana, and shield values
- `abilities.json` — attack/skill definitions with mana costs
- `cards.json` — buff cards for between-round selection

## Game Mechanics

### Execution Order
Battle execution order is determined by team speed totals: the sum of speed for all living characters on a team. The faster team executes all planned actions first; ties favor the player.

### Mana System
Each character has a mana pool (`max_mana`). Abilities have a `mana_cost` field:
- **Normal Attack**: Always free (0 mana) — player always has a fallback.
- **Special Attack**: Costs 3-5 mana depending on the ability.
- **Ultimate**: Free (0 mana) — gated by charge mechanic instead.

Mana regenerates by `MANA_REGEN_PER_TURN` (2) at the start of each new round, before the planning phase. If a character cannot afford a Special, the button is greyed out and the action is rejected.

### Shield System
Each character has a numeric shield (`max_shield`). Damage hits shield first, then HP:
- Shield absorbs ALL ability damage types (normal, special, ultimate).
- Status effect damage (burn) bypasses shield and hits HP directly.
- Shield does NOT regenerate naturally.
- When shield reaches 0, a "SHIELD BROKEN!" event fires.
- The existing `StatusEffect.SHIELD` (one-shot block from Shield Bash) remains separate — it blocks all damage from one hit before numeric shield is checked.

### Ultimate Charge
Characters accumulate charges by using Special abilities (2 charges unlock Ultimate). Using Ultimate resets the counter.

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `BURN_DAMAGE_PER_STACK` | 5 | Burn damage per stack per turn |
| `TEAM_SIZE` | 3 | Characters per team |
| `CARD_CHOICES_PER_ROUND` | 3 | Base card options per round |
| `ATTACK_SCALING_DIVISOR` | 5 | Attack stat scaling for damage |
| `ULTIMATE_CHARGE_REQUIRED` | 2 | Special uses to unlock Ultimate |
| `MANA_REGEN_PER_TURN` | 2 | Mana restored at start of each round |
| `NORMAL_ATTACK_MANA_COST` | 0 | Normal attacks are always free |

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install package in dev mode |
| `make run` | Launch the game |
| `make test` | Run tests with coverage |
| `make lint` | Run ruff + mypy |
| `make fmt` | Auto-format with ruff |
