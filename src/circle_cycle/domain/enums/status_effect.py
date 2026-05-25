"""Domain enums for status effects applied to characters."""

from __future__ import annotations

from enum import StrEnum


class StatusEffect(StrEnum):
    """Status effects that can be applied to a character."""

    SHIELD = "shield"
    BURN = "burn"
