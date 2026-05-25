"""Domain enums for character size classification."""

from __future__ import annotations

from enum import StrEnum


class CharacterSize(StrEnum):
    """Size classification for characters affecting visual rendering."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
