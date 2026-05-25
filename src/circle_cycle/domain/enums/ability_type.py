"""Domain enums for ability classification."""

from __future__ import annotations

from enum import StrEnum


class AbilityType(StrEnum):
    """Classification of ability types available in the game."""

    NORMAL = "normal"
    SPECIAL = "special"
    ULTIMATE = "ultimate"
    PASSIVE = "passive"
