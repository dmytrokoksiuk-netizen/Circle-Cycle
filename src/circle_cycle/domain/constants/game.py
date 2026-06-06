"""Game-wide constants for the Circle Cycle domain."""

from __future__ import annotations

BURN_DAMAGE_PER_STACK: int = 5
TEAM_SIZE: int = 3
CARD_CHOICES_PER_ROUND: int = 3
ATTACK_SCALING_DIVISOR: int = 5

# Number of Special uses required to unlock an Ultimate
ULTIMATE_CHARGE_REQUIRED: int = 2

# Shared team mana system constants
TEAM_MAX_MANA: int = 15
TEAM_MANA_REGEN_PER_TURN: int = 3
NORMAL_ATTACK_MANA_COST: int = 0
