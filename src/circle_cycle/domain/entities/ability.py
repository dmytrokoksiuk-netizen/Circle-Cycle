"""Domain entity representing a game ability."""

from __future__ import annotations

from dataclasses import dataclass

from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.enums.target_type import TargetType


@dataclass(frozen=True)
class Ability:
    """Represents a single game ability loaded from data.

    Fields:
        description: Short human-readable description shown in the UI preview.
        mana_cost: Amount of mana required to use this ability.
        target_type: How this ability selects targets.
        heal_amount: HP restored to targets (for heal abilities).
        shield_restore: Shield points restored to targets.
        shield_pierce: If True, damage bypasses shield and hits HP directly.
        shield_destroy: Amount of shield points destroyed on target.
        buff_stat: Stat to buff on targets (attack/speed).
        buff_amount: Amount of the buff.
        buff_duration: Number of turns the buff lasts.
        debuff_stat: Stat to debuff on targets (attack/speed).
        debuff_amount: Amount of the debuff.
        debuff_duration: Number of turns the debuff lasts.
    """

    id: str
    name: str
    type: AbilityType
    damage: int
    effect: StatusEffect | None
    cooldown: int
    description: str = ""
    mana_cost: int = 0
    target_type: TargetType = TargetType.SINGLE_ENEMY
    heal_amount: int = 0
    shield_restore: int = 0
    shield_pierce: bool = False
    shield_destroy: int = 0
    buff_stat: str | None = None
    buff_amount: int = 0
    buff_duration: int = 0
    debuff_stat: str | None = None
    debuff_amount: int = 0
    debuff_duration: int = 0
