from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.character import Character


@dataclass(frozen=True)
class Card:
    """Represents a single buff card loaded from JSON data."""

    id: str
    name: str
    description: str
    effect: dict[str, str | int]


def apply_card(card: Card, target: "Character") -> str:
    """Apply a card effect to a target character and return a log string."""
    stat = str(card.effect.get("stat", ""))
    value = int(card.effect.get("value", 0))

    if stat == "hp":
        target.hp += value
        target.current_hp = min(target.hp, target.current_hp + value)
        return f"{target.name} gains {value} HP from {card.name}."

    if stat == "attack":
        target.attack += value
        return f"{target.name} gains {value} attack from {card.name}."

    if stat == "speed":
        target.speed += value
        return f"{target.name} gains {value} speed from {card.name}."

    if stat == "heal":
        target.heal(value)
        return f"{target.name} is healed for {value} HP by {card.name}."

    raise ValueError(f"Unknown card effect stat: {stat}")
