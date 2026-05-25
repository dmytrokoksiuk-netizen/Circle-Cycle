"""Abstract interface for loading game data."""

from __future__ import annotations

from abc import ABC, abstractmethod

from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character


class DataRepository(ABC):
    """Port for loading game entities from a data source."""

    @abstractmethod
    def load_abilities(self) -> dict[str, Ability]:
        """Load abilities and return a mapping keyed by ability id."""

    @abstractmethod
    def load_characters(self) -> dict[str, Character]:
        """Load characters and return a mapping keyed by character id."""

    @abstractmethod
    def load_cards(self) -> dict[str, Card]:
        """Load cards and return a mapping keyed by card id."""
