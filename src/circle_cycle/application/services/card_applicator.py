"""Application service for card effect application."""

from __future__ import annotations

from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.card_stat import CardStat


def apply_card(card: Card, target: Character) -> str:
    """Apply a card effect to a target character and return a log string."""
    stat = card.effect.stat
    value = card.effect.value

    if stat == CardStat.HP:
        target.hp += value
        target.current_hp = min(target.hp, target.current_hp + value)
        return f"{target.name} gains {value} HP from {card.name}."

    if stat == CardStat.ATTACK:
        target.attack += value
        return f"{target.name} gains {value} attack from {card.name}."

    if stat == CardStat.SPEED:
        target.speed += value
        return f"{target.name} gains {value} speed from {card.name}."

    if stat == CardStat.HEAL:
        target.heal(value)
        return f"{target.name} is healed for {value} HP by {card.name}."

    raise ValueError(f"Unknown card effect stat: {stat}")
