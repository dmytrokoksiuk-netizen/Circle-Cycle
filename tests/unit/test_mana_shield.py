"""Unit tests for the Mana and Shield systems (Task 07)."""

from __future__ import annotations

import copy

import pytest

from circle_cycle.application.services.battle_engine import BattleEngine
from circle_cycle.domain.constants.game import TEAM_MAX_MANA, TEAM_MANA_REGEN_PER_TURN
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.exceptions.battle import InsufficientManaError
from tests.conftest import InMemoryDataRepository


# ===== Mana System Tests =====


class TestManaCharacter:
    """Tests for mana methods on Character entity (individual mana still exists for backward compat)."""

    def test_character_starts_with_full_mana(self, repository: InMemoryDataRepository) -> None:
        """Character should start with mana equal to max_mana."""
        chars = repository.load_characters()
        ace = copy.deepcopy(chars["ace"])
        assert ace.mana == ace.max_mana == 12

    def test_spend_mana_reduces_correctly(self) -> None:
        """spend_mana should reduce mana by the given amount."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=10, max_shield=0,
        )
        char.spend_mana(4)
        assert char.mana == 6

    def test_spend_mana_raises_when_insufficient(self) -> None:
        """spend_mana should raise InsufficientManaError when mana is too low."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=5, max_shield=0,
        )
        char.spend_mana(3)
        with pytest.raises(InsufficientManaError):
            char.spend_mana(4)

    def test_restore_mana_caps_at_max(self) -> None:
        """restore_mana should not exceed max_mana."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=10, max_shield=0,
        )
        char.spend_mana(3)
        char.restore_mana(100)
        assert char.mana == 10

    def test_can_afford_ability(self) -> None:
        """can_afford_ability should return True/False based on current mana."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=5, max_shield=0,
        )
        assert char.can_afford_ability(5) is True
        assert char.can_afford_ability(6) is False
        char.spend_mana(3)
        assert char.can_afford_ability(3) is False
        assert char.can_afford_ability(2) is True

    def test_normal_attack_always_costs_zero(self, repository: InMemoryDataRepository) -> None:
        """Normal Attack always has mana_cost=0."""
        abilities = repository.load_abilities()
        punch = abilities["punch"]
        assert punch.mana_cost == 0


class TestTeamMana:
    """Tests for shared team mana in BattleEngine."""

    def test_team_mana_starts_at_max(self, repository: InMemoryDataRepository) -> None:
        """Both teams start with TEAM_MAX_MANA."""
        chars = repository.load_characters()
        player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"])]
        bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()

        assert engine.player_team_mana == TEAM_MAX_MANA
        assert engine.bot_team_mana == TEAM_MAX_MANA

    def test_team_mana_regen_at_round_end(self, repository: InMemoryDataRepository) -> None:
        """Team mana should regenerate when a round ends."""
        chars = repository.load_characters()
        player_team = [copy.deepcopy(chars["ace"])]
        bot_team = [copy.deepcopy(chars["nova"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()

        # Spend some team mana
        engine.player_team_mana = 10

        # Simulate round end (advance turn order until round wraps)
        engine.end_turn()
        engine.end_turn()  # wraps around, triggers regen

        assert engine.player_team_mana == 10 + TEAM_MANA_REGEN_PER_TURN

    def test_team_mana_regen_caps_at_max(self, repository: InMemoryDataRepository) -> None:
        """Team mana regen should not exceed TEAM_MAX_MANA."""
        chars = repository.load_characters()
        player_team = [copy.deepcopy(chars["ace"])]
        bot_team = [copy.deepcopy(chars["nova"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()

        # Already at full
        engine.end_turn()
        engine.end_turn()
        assert engine.player_team_mana == TEAM_MAX_MANA

    def test_can_team_afford(self, repository: InMemoryDataRepository) -> None:
        """can_team_afford should check the team pool."""
        chars = repository.load_characters()
        player_team = [copy.deepcopy(chars["ace"])]
        bot_team = [copy.deepcopy(chars["nova"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()
        engine.player_team_mana = 3

        assert engine.can_team_afford(player_team[0], 3) is True
        assert engine.can_team_afford(player_team[0], 4) is False


class TestManaInBattle:
    """Tests for mana enforcement in BattleEngine."""

    def test_engine_rejects_special_when_team_mana_insufficient(
        self, repository: InMemoryDataRepository
    ) -> None:
        """BattleEngine should reject Special when team lacks mana."""
        chars = repository.load_characters()
        player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"])]
        bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()

        abilities = repository.load_abilities()
        special = abilities["fire_spin"]

        # Drain team mana
        engine.player_team_mana = 2  # needs 5 for fire_spin

        with pytest.raises(InsufficientManaError):
            engine.submit_player_action(special, bot_team[0])

    def test_bot_falls_back_to_normal_when_cant_afford_special(
        self, repository: InMemoryDataRepository
    ) -> None:
        """Bot should use Normal Attack when team mana is too low for Special."""
        chars = repository.load_characters()
        bot_team = [copy.deepcopy(chars["ace"])]
        player_team = [copy.deepcopy(chars["nova"])]

        engine = BattleEngine(player_team, bot_team, repository)
        engine.start_battle()

        # Bot team has no mana
        plans = engine.bot_ai.generate_plan(bot_team, player_team, team_mana=0)
        assert len(plans) == 1
        assert plans[0].ability.type == AbilityType.NORMAL


# ===== Shield System Tests =====


class TestShieldCharacter:
    """Tests for shield mechanics on Character entity."""

    def test_damage_hits_shield_first(self) -> None:
        """40 damage vs 50 shield → shield=10, HP unchanged."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=50,
        )
        result = char.take_damage(40)
        assert char.shield == 10
        assert char.current_hp == 100
        assert result["shield_damage"] == 40
        assert result["hp_damage"] == 0
        assert result["shield_broken"] is False

    def test_damage_overflows_to_hp(self) -> None:
        """60 damage vs 30 shield → shield=0, HP takes 30."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=30,
        )
        result = char.take_damage(60)
        assert char.shield == 0
        assert char.current_hp == 70
        assert result["shield_damage"] == 30
        assert result["hp_damage"] == 30
        assert result["shield_broken"] is True

    def test_no_shield_all_to_hp(self) -> None:
        """When shield is 0, all damage goes to HP."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=0,
        )
        result = char.take_damage(25)
        assert char.current_hp == 75
        assert result["shield_damage"] == 0
        assert result["hp_damage"] == 25
        assert result["shield_broken"] is False

    def test_shield_broken_flag(self) -> None:
        """Shield broken flag should be True when shield goes to 0 from positive."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=20,
        )
        result = char.take_damage(20)
        assert char.shield == 0
        assert result["shield_broken"] is True

    def test_status_effect_shield_blocks_all(self) -> None:
        """StatusEffect.SHIELD should still block all damage (one-shot)."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=30,
        )
        char.status_effects.append(StatusEffect.SHIELD)
        result = char.take_damage(50)
        assert char.shield == 30  # numeric shield untouched
        assert char.current_hp == 100
        assert result["shield_damage"] == 0
        assert result["hp_damage"] == 0

    def test_burn_bypasses_shield(self) -> None:
        """Burn damage should bypass shield and hit HP directly."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=50,
        )
        char.status_effects.append(StatusEffect.BURN)
        damage = char.tick_status_effects()
        assert damage == 5
        assert char.shield == 50  # shield untouched
        assert char.current_hp == 95

    def test_take_damage_returns_correct_dict(self) -> None:
        """take_damage should always return a DamageResult dict."""
        char = Character(
            id="t", name="T", size=CharacterSize.SMALL,
            hp=100, attack=10, speed=10, color="#fff",
            abilities=[], max_mana=0, max_shield=10,
        )
        result = char.take_damage(15)
        assert isinstance(result, dict)
        assert "shield_damage" in result
        assert "hp_damage" in result
        assert "shield_broken" in result
        assert result["shield_damage"] == 10
        assert result["hp_damage"] == 5
        assert result["shield_broken"] is True
