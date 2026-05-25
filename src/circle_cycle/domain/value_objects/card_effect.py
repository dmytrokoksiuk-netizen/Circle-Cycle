"""Immutable value objects for the domain layer."""

from __future__ import annotations

from dataclasses import dataclass

from circle_cycle.domain.enums.card_stat import CardStat


@dataclass(frozen=True)
class CardEffect:
    """Immutable representation of a card's stat modification."""

    stat: CardStat
    value: int
