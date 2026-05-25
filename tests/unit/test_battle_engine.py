"""Unit tests for the BattleEngine application service."""

from __future__ import annotations

import copy

import pytest

from circle_cycle.application.services.battle_engine import BattleEngine
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.exceptions.battle import (
    AbilityOnCooldownError,
    BattleNotStartedError,
)
from tests.conftest import InMemoryDataRepository


@pytest.fixture
def engine(repository: InMemoryDataRepository) -> BattleEngine:
    """Create a BattleEngine with predetermined teams for testing."""
    characters = repository.load_characters()
    player_team = [copy.deepcopy(characters["ace"])]
    bot_team = [copy.deepcopy(characters["nova"])]
    engine = BattleEngine(player_team, bot_team, repository)
    engine.start_battle()
    return engine


class TestBattleEngine:
    """Tests for BattleEngine core functionality."""

    def test_start_battle_sets_turn_order(self, engine: BattleEngine) -> None:
        """Starting a battle should establish a turn order sorted by speed."""
        assert len(engine.turn_order) == 2
        assert engine.turn_order[0].speed >= engine.turn_order[1].speed

    def test_get_current_character_before_start(self, repository: InMemoryDataRepository) -> None:
        """Accessing current character before start should raise."""
        characters = repository.load_characters()
        eng = BattleEngine(
            [copy.deepcopy(characters["ace"])],
            [copy.deepcopy(characters["nova"])],
            repository,
        )
        with pytest.raises(BattleNotStartedError):
            eng.get_current_character()

    def test_execute_action_deals_damage(self, engine: BattleEngine) -> None:
        """Executing a normal attack should reduce target HP."""
        attacker = engine.player_team[0]
        ability = engine.get_ability_by_type(attacker, "normal")
        assert ability is not None

        targets = engine.get_action_targets(attacker, ability)
        initial_hp = targets[0].current_hp

        engine.execute_action(attacker, ability, targets)
        assert targets[0].current_hp < initial_hp

    def test_execute_action_sets_cooldown(self, engine: BattleEngine) -> None:
        """Using an ability with cooldown should set the cooldown timer."""
        attacker = engine.player_team[0]
        ability = engine.get_ability_by_type(attacker, "special")
        assert ability is not None

        targets = engine.get_action_targets(attacker, ability)
        engine.execute_action(attacker, ability, targets)
        assert attacker.cooldowns[ability.id] == ability.cooldown

    def test_execute_action_on_cooldown_raises(self, engine: BattleEngine) -> None:
        """Using an ability on cooldown should raise AbilityOnCooldownError."""
        attacker = engine.player_team[0]
        ability = engine.get_ability_by_type(attacker, "special")
        assert ability is not None

        targets = engine.get_action_targets(attacker, ability)
        engine.execute_action(attacker, ability, targets)

        with pytest.raises(AbilityOnCooldownError):
            engine.execute_action(attacker, ability, targets)

    def test_check_winner_returns_none_when_ongoing(self, engine: BattleEngine) -> None:
        """Check winner should return None when both sides have living characters."""
        assert engine.check_winner() is None

    def test_check_winner_player_wins(self, engine: BattleEngine) -> None:
        """Check winner should return 'player' when all bots are dead."""
        for character in engine.bot_team:
            character.current_hp = 0
        assert engine.check_winner() == "player"

    def test_check_winner_bot_wins(self, engine: BattleEngine) -> None:
        """Check winner should return 'bot' when all players are dead."""
        for character in engine.player_team:
            character.current_hp = 0
        assert engine.check_winner() == "bot"

    def test_end_turn_advances_index(self, engine: BattleEngine) -> None:
        """End turn should advance the current turn index."""
        assert engine.current_turn_index == 0
        engine.end_turn()
        assert engine.current_turn_index == 1

    def test_end_turn_wraps_around_for_new_round(self, engine: BattleEngine) -> None:
        """End turn should wrap to 0 and increment round when all have acted."""
        engine.end_turn()
        round_ended = engine.end_turn()
        assert round_ended is True
        assert engine.current_turn_index == 0
        assert engine.round_number == 2


class TestCharacterEntity:
    """Tests for the Character domain entity."""

    def test_take_damage_reduces_hp(self) -> None:
        """Taking damage should reduce current HP."""
        char = Character(
            id="t",
            name="T",
            size=CharacterSize.SMALL,
            hp=100,
            attack=10,
            speed=10,
            color="#fff",
            abilities=[],
        )
        char.take_damage(30)
        assert char.current_hp == 70

    def test_take_damage_cannot_go_below_zero(self) -> None:
        """HP cannot go below zero."""
        char = Character(
            id="t",
            name="T",
            size=CharacterSize.SMALL,
            hp=50,
            attack=10,
            speed=10,
            color="#fff",
            abilities=[],
        )
        char.take_damage(999)
        assert char.current_hp == 0

    def test_heal_caps_at_max_hp(self) -> None:
        """Healing cannot exceed max HP."""
        char = Character(
            id="t",
            name="T",
            size=CharacterSize.SMALL,
            hp=100,
            attack=10,
            speed=10,
            color="#fff",
            abilities=[],
        )
        char.take_damage(20)
        char.heal(999)
        assert char.current_hp == 100

    def test_is_alive(self) -> None:
        """Character with HP > 0 should be alive."""
        char = Character(
            id="t",
            name="T",
            size=CharacterSize.SMALL,
            hp=100,
            attack=10,
            speed=10,
            color="#fff",
            abilities=[],
        )
        assert char.is_alive() is True
        char.current_hp = 0
        assert char.is_alive() is False
