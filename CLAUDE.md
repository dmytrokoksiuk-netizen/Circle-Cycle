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
- `characters.json` — 7 playable characters with stats, mana, shield, and role
- `abilities.json` — attack/skill definitions with mana costs, targeting, and effects
- `cards.json` — buff cards for between-round selection

## Characters

| Name | Role | HP | ATK | DEF | SPD | Mana | Shield |
|------|------|-----|-----|-----|-----|------|--------|
| Nova | DPS | 115 | 14 | 12 | 15 | 10 | 20 |
| Stone | DPS | 150 | 16 | 20 | 8 | 8 | 50 |
| Ace | DPS | 85 | 12 | 10 | 18 | 12 | 30 |
| Sage | Healer | 130 | 12 | 18 | 14 | 14 | 25 |
| Drum | Buffer | 110 | 16 | 14 | 18 | 12 | 30 |
| Hex | Debuffer | 90 | 18 | 10 | 22 | 11 | 20 |
| Spike | Breaker | 95 | 24 | 12 | 16 | 10 | 15 |

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

### Targeting Types
Abilities have a `target_type` field (TargetType enum):
- `single_enemy` — targets one enemy (default for attacks)
- `all_enemies` — hits all enemies (AoE damage/debuffs)
- `single_ally` — targets one friendly character (heals/buffs)
- `all_allies` — affects all allies (team heals/buffs)
- `self` — targets self only (future use)

### Buff/Debuff System
Abilities can apply temporary stat modifiers:
- **Buffs** increase a stat (attack, speed, defense) for N turns.
- **Debuffs** decrease a stat for N turns.
- Active effects are tracked per character and tick down each turn.
- Effective stats = base stat + sum(buffs) - sum(debuffs).
- Minimum effective stat is 0 (debuffs cannot go negative).

### Shield Pierce / Destroy
Some abilities (Spike's kit) interact specially with shields:
- `shield_pierce: true` — damage bypasses shield and goes directly to HP.
- `shield_destroy: N` — reduces target's shield by N points (can stack with damage).

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
