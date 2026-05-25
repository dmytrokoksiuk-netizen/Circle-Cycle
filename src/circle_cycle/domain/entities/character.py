"""Domain entity representing a playable or enemy character."""

from __future__ import annotations

from dataclasses import dataclass, field

from circle_cycle.domain.constants.game import BURN_DAMAGE_PER_STACK
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.status_effect import StatusEffect


@dataclass
class Character:
    """Represents a playable or enemy character in the battle system."""

    id: str
    name: str
    size: CharacterSize
    hp: int
    attack: int
    speed: int
    color: str
    abilities: list[str]
    current_hp: int = field(init=False)
    status_effects: list[StatusEffect] = field(default_factory=list)
    cooldowns: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize mutable state after dataclass construction."""
        self.current_hp = self.hp
        self.cooldowns = {ability_id: 0 for ability_id in self.abilities}

    def take_damage(self, amount: int) -> int:
        """Apply damage to the character and return the amount dealt."""
        if amount <= 0:
            return 0

        if StatusEffect.SHIELD in self.status_effects:
            self.status_effects.remove(StatusEffect.SHIELD)
            return 0

        self.current_hp = max(0, self.current_hp - amount)
        return amount

    def heal(self, amount: int) -> int:
        """Heal the character and return the resulting current HP."""
        if amount <= 0:
            return 0

        self.current_hp = min(self.hp, self.current_hp + amount)
        return self.current_hp

    def is_alive(self) -> bool:
        """Return whether the character still has HP remaining."""
        return self.current_hp > 0

    def tick_cooldowns(self) -> None:
        """Reduce every cooldown by one turn."""
        for ability_id, value in list(self.cooldowns.items()):
            if value > 0:
                self.cooldowns[ability_id] = value - 1

    def tick_status_effects(self) -> int:
        """Apply burn damage and return the total damage dealt."""
        burn_count = self.status_effects.count(StatusEffect.BURN)
        if burn_count == 0:
            return 0

        for _ in range(burn_count):
            self.status_effects.remove(StatusEffect.BURN)

        damage = burn_count * BURN_DAMAGE_PER_STACK
        self.take_damage(damage)
        return damage
