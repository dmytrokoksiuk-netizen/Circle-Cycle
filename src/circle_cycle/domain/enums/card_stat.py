"""Domain enums for card stat targets."""

from __future__ import annotations

from enum import StrEnum


class CardStat(StrEnum):
    """Stats that a card can modify on a character."""

    HP = "hp"
    ATTACK = "attack"
    SPEED = "speed"
    HEAL = "heal"
