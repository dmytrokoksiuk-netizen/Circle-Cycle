"""Shared test fixtures for the Circle Cycle test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.card_stat import CardStat
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.interfaces.data_repository import DataRepository
from circle_cycle.domain.value_objects.card_effect import CardEffect


class InMemoryDataRepository(DataRepository):
    """In-memory implementation of DataRepository for testing."""

    def __init__(self) -> None:
        self._abilities: dict[str, Ability] = {
            "punch": Ability(
                id="punch",
                name="Punch",
                type=AbilityType.NORMAL,
                damage=20,
                effect=None,
                cooldown=0,
            ),
            "fire_spin": Ability(
                id="fire_spin",
                name="Fire Spin",
                type=AbilityType.SPECIAL,
                damage=40,
                effect=StatusEffect.BURN,
                cooldown=2,
            ),
            "earthquake": Ability(
                id="earthquake",
                name="Earthquake",
                type=AbilityType.ULTIMATE,
                damage=35,
                effect=None,
                cooldown=3,
            ),
        }
        self._characters: dict[str, Character] = {
            "ace": Character(
                id="ace",
                name="Ace",
                size=CharacterSize.SMALL,
                hp=85,
                attack=12,
                speed=18,
                color="#14b8a6",
                abilities=["punch", "fire_spin", "earthquake"],
            ),
            "nova": Character(
                id="nova",
                name="Nova",
                size=CharacterSize.MEDIUM,
                hp=115,
                attack=14,
                speed=12,
                color="#f59e0b",
                abilities=["punch", "fire_spin", "earthquake"],
            ),
            "stone": Character(
                id="stone",
                name="Stone",
                size=CharacterSize.LARGE,
                hp=150,
                attack=16,
                speed=8,
                color="#64748b",
                abilities=["punch", "fire_spin", "earthquake"],
            ),
        }
        self._cards: dict[str, Card] = {
            "iron_skin": Card(
                id="iron_skin",
                name="Iron Skin",
                description="Increase HP by 20.",
                effect=CardEffect(stat=CardStat.HP, value=20),
            ),
            "rage": Card(
                id="rage",
                name="Rage",
                description="Boost attack by 10.",
                effect=CardEffect(stat=CardStat.ATTACK, value=10),
            ),
            "full_heal": Card(
                id="full_heal",
                name="Full Heal",
                description="Restore 30 HP.",
                effect=CardEffect(stat=CardStat.HEAL, value=30),
            ),
        }

    def load_abilities(self) -> dict[str, Ability]:
        """Return in-memory abilities."""
        return dict(self._abilities)

    def load_characters(self) -> dict[str, Character]:
        """Return in-memory characters."""
        return dict(self._characters)

    def load_cards(self) -> dict[str, Card]:
        """Return in-memory cards."""
        return dict(self._cards)


@pytest.fixture
def repository() -> InMemoryDataRepository:
    """Provide an in-memory data repository for tests."""
    return InMemoryDataRepository()


@pytest.fixture
def data_dir() -> Path:
    """Provide the path to the test data directory."""
    return Path(__file__).resolve().parents[1] / "data"
