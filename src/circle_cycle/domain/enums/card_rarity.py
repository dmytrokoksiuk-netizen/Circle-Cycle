from __future__ import annotations

from enum import StrEnum


class CardRarity(StrEnum):
    """Rarity tiers for card pool weighting."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
