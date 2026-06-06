"""Domain enums for ability targeting modes."""

from __future__ import annotations

from enum import StrEnum


class TargetType(StrEnum):
    """Targeting mode for abilities."""

    SINGLE_ENEMY = "single_enemy"
    ALL_ENEMIES = "all_enemies"
    SINGLE_ALLY = "single_ally"
    ALL_ALLIES = "all_allies"
    SELF = "self"
