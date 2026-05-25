"""Domain entity representing a game ability."""

from __future__ import annotations

from dataclasses import dataclass

from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.status_effect import StatusEffect


@dataclass(frozen=True)
class Ability:
    """Represents a single game ability loaded from data."""

    id: str
    name: str
    type: AbilityType
    damage: int
    effect: StatusEffect | None
    cooldown: int
