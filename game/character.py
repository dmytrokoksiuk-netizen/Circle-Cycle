from __future__ import annotations

from dataclasses import dataclass, field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.card import Card


@dataclass
class Character:
    """Represents a playable or enemy character in the battle system."""

    id: str
    name: str
    size: str
    hp: int
    attack: int
    speed: int
    color: str
    abilities: list[str]
    current_hp: int = field(init=False)
    status_effects: list[str] = field(default_factory=list)
    cooldowns: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.current_hp = self.hp
        self.cooldowns = {ability_id: 0 for ability_id in self.abilities}

    def take_damage(self, amount: int) -> int:
        """Apply damage to the character and return the amount dealt."""
        if amount <= 0:
            return 0

        if "shield" in self.status_effects:
            self.status_effects.remove("shield")
            return 0

        self.current_hp = max(0, self.current_hp - amount)
        return amount

    def heal(self, amount: int) -> int:
        """Heal the character and return the resulting current HP."""
        if amount <= 0:
            return 0

        self.current_hp = min(self.hp, self.current_hp + amount)
        return self.current_hp

    def apply_card(self, card: "Card") -> str:
        """Apply a card effect to the character and return a log string."""
        from game.card import apply_card

        return apply_card(card, self)

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
        burn_count = self.status_effects.count("burn")
        if burn_count == 0:
            return 0

        for _ in range(burn_count):
            self.status_effects.remove("burn")

        damage = burn_count * 5
        self.take_damage(damage)
        return damage
