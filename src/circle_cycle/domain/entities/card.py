"""Domain entity representing a game card."""

from __future__ import annotations

from dataclasses import dataclass

from circle_cycle.domain.value_objects.card_effect import CardEffect


@dataclass(frozen=True)
class Card:
    """Represents a single buff card loaded from data."""

    id: str
    name: str
    description: str
    effect: CardEffect
