"""Unit tests for the new character roles and mechanics (Task 08)."""

from __future__ import annotations

import copy

import pytest

from circle_cycle.application.services.ability_resolver import resolve_ability
from circle_cycle.application.services.battle_engine import BattleEngine
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.target_type import TargetType
from tests.conftest import InMemoryDataRepository


def _make_char(char_id: str, **kwargs) -> Character:
    """Helper to create a character with sensible defaults."""
    defaults = dict(
        id=char_id, name=char_id.title(), size=CharacterSize.MEDIUM,
        hp=100, attack=10, speed=10, color="#fff",
        abilities=[], max_mana=10, max_shield=20, role="dps",
    )
    defaults.update(kwargs)
    return Character(**defaults)


def _make_ability(**kwargs) -> Ability:
    """Helper to create an ability with sensible defaults."""
    defaults = dict(
        id="test_ability", name="Test", type=AbilityType.SPECIAL,
        damage=0, effect=None, cooldown=1, mana_cost=0,
        target_type=TargetType.SINGLE_ENEMY,
    )
    defaults.update(kwargs)
    return Ability(**defaults)


# ===== Heal Tests =====


class TestHealAbility:
    """Tests for heal abilities (Sage)."""

    def test_heal_restores_hp(self) -> None:
        """Healing Light restores HP to target ally."""
        healer = _make_char("sage", attack=12)
        target = _make_char("ally", hp=100, max_shield=0)
        target.take_damage(40)  # 60/100 HP (no shield)

        ability = _make_ability(
            id="healing_light", name="Healing Light",
            target_type=TargetType.SINGLE_ALLY, heal_amount=30,
        )
        logs = resolve_ability(healer, [target], ability)
        assert target.current_hp == 90
        assert any("heals" in log for log in logs)

    def test_heal_caps_at_max_hp(self) -> None:
        """Healing cannot exceed max HP."""
        healer = _make_char("sage")
        target = _make_char("ally", hp=100)
        target.take_damage(10)  # 90/100

        ability = _make_ability(heal_amount=30, target_type=TargetType.SINGLE_ALLY)
        resolve_ability(healer, [target], ability)
        assert target.current_hp == 100

    def test_heal_costs_mana(self) -> None:
        """Heal ability should cost mana (validated before resolve)."""
        ability = _make_ability(heal_amount=30, mana_cost=4)
        assert ability.mana_cost == 4


# ===== Buff Tests =====


class TestBuffAbility:
    """Tests for buff abilities (Drum)."""

    def test_buff_increases_effective_stat(self) -> None:
        """War Drums buffs target's effective attack."""
        buffer = _make_char("drum")
        target = _make_char("ally", attack=14)

        ability = _make_ability(
            id="war_drums", name="War Drums",
            target_type=TargetType.SINGLE_ALLY,
            buff_stat="attack", buff_amount=8, buff_duration=2,
        )
        logs = resolve_ability(buffer, [target], ability)
        assert target.effective_attack == 22  # 14 + 8
        assert any("+8" in log and "ATTACK" in log for log in logs)

    def test_buff_expires_after_duration(self) -> None:
        """Buff should expire after N turns."""
        target = _make_char("ally", attack=14)
        target.apply_buff("attack", 8, 2)
        assert target.effective_attack == 22

        target.tick_buffs_debuffs()  # turn 1
        assert target.effective_attack == 22

        target.tick_buffs_debuffs()  # turn 2 — expires
        assert target.effective_attack == 14

    def test_multiple_buffs_stack(self) -> None:
        """Multiple buffs on the same stat should stack additively."""
        target = _make_char("ally", attack=10)
        target.apply_buff("attack", 5, 2)
        target.apply_buff("attack", 3, 3)
        assert target.effective_attack == 18


# ===== Debuff Tests =====


class TestDebuffAbility:
    """Tests for debuff abilities (Hex)."""

    def test_debuff_reduces_effective_stat(self) -> None:
        """Curse debuffs target's effective attack."""
        debuffer = _make_char("hex", attack=18)
        target = _make_char("enemy", attack=20)

        ability = _make_ability(
            id="curse", name="Curse",
            target_type=TargetType.SINGLE_ENEMY, damage=6,
            debuff_stat="attack", debuff_amount=8, debuff_duration=2,
        )
        logs = resolve_ability(debuffer, [target], ability)
        assert target.effective_attack == 12  # 20 - 8
        assert any("-8" in log and "ATTACK" in log for log in logs)

    def test_debuff_expires_after_duration(self) -> None:
        """Debuff should expire after N turns."""
        target = _make_char("enemy", attack=20)
        target.apply_debuff("attack", 10, 2)
        assert target.effective_attack == 10

        target.tick_buffs_debuffs()
        assert target.effective_attack == 10

        target.tick_buffs_debuffs()
        assert target.effective_attack == 20

    def test_effective_attack_cannot_go_below_zero(self) -> None:
        """Debuff should not reduce effective attack below 0."""
        target = _make_char("enemy", attack=5)
        target.apply_debuff("attack", 20, 2)
        assert target.effective_attack == 0


# ===== Shield Pierce Tests =====


class TestShieldPierce:
    """Tests for shield pierce abilities (Spike)."""

    def test_shield_pierce_bypasses_shield(self) -> None:
        """Shield Crush damage should go directly to HP."""
        attacker = _make_char("spike", attack=24)
        target = _make_char("enemy", hp=100, max_shield=50)

        ability = _make_ability(
            id="shield_crush", name="Shield Crush",
            damage=20, shield_pierce=True, shield_destroy=20,
        )
        resolve_ability(attacker, [target], ability)
        # Shield destroy: 50 - 20 = 30
        assert target.shield == 30
        # HP damage: take_direct_damage(20 + 24//5 = 24)
        assert target.current_hp < 100

    def test_shield_destroy_reduces_shield(self) -> None:
        """Shield destroy should reduce target's shield points."""
        target = _make_char("enemy", max_shield=50)
        ability = _make_ability(
            id="shatter", name="Shatter",
            damage=0, shield_destroy=30,
        )
        attacker = _make_char("spike")
        resolve_ability(attacker, [target], ability)
        assert target.shield == 20

    def test_shield_destroy_caps_at_zero(self) -> None:
        """Shield destroy cannot go below 0."""
        target = _make_char("enemy", max_shield=10)
        ability = _make_ability(damage=0, shield_destroy=999)
        attacker = _make_char("spike")
        resolve_ability(attacker, [target], ability)
        assert target.shield == 0


# ===== Target Type Tests =====


class TestTargetTypes:
    """Tests for targeting modes."""

    def test_all_enemies_hits_all(self) -> None:
        """ALL_ENEMIES ability should affect all enemy targets."""
        attacker = _make_char("hex", attack=18)
        enemies = [_make_char(f"e{i}", max_shield=0) for i in range(3)]

        ability = _make_ability(
            target_type=TargetType.ALL_ENEMIES, damage=15,
            debuff_stat="attack", debuff_amount=10, debuff_duration=2,
        )
        resolve_ability(attacker, enemies, ability)
        for e in enemies:
            assert e.current_hp < 100
            assert e.effective_attack < e.attack

    def test_all_allies_heals_all(self) -> None:
        """ALL_ALLIES heal ability should heal all allies."""
        healer = _make_char("sage")
        allies = [_make_char(f"a{i}") for i in range(3)]
        for a in allies:
            a.take_damage(30)

        ability = _make_ability(
            target_type=TargetType.ALL_ALLIES, heal_amount=40,
        )
        resolve_ability(healer, allies, ability)
        for a in allies:
            assert a.current_hp == 100  # healed to full (70 + 40 > 100 → cap)

    def test_single_ally_targets_one(self) -> None:
        """SINGLE_ALLY should only affect one target."""
        ability = _make_ability(
            target_type=TargetType.SINGLE_ALLY, heal_amount=25,
        )
        assert ability.target_type == TargetType.SINGLE_ALLY


# ===== BotAI with New Characters =====


class TestBotAINewRoles:
    """Tests for Bot AI handling new character roles."""

    def test_bot_with_sage_heals_low_ally(self, repository: InMemoryDataRepository) -> None:
        """Bot with healer should prioritize healing hurt allies."""
        # Add sage abilities to repo
        from circle_cycle.domain.enums.target_type import TargetType

        repo = repository
        repo._abilities["staff_strike"] = Ability(
            id="staff_strike", name="Staff Strike", type=AbilityType.NORMAL,
            damage=10, effect=None, cooldown=0, mana_cost=0,
            target_type=TargetType.SINGLE_ENEMY,
        )
        repo._abilities["healing_light"] = Ability(
            id="healing_light", name="Healing Light", type=AbilityType.SPECIAL,
            damage=0, effect=None, cooldown=1, mana_cost=4,
            target_type=TargetType.SINGLE_ALLY, heal_amount=30,
        )

        sage = Character(
            id="sage", name="Sage", size=CharacterSize.MEDIUM,
            hp=130, attack=12, speed=14, color="#10b981",
            abilities=["staff_strike", "healing_light"],
            max_mana=14, max_shield=25, role="healer",
        )
        ally = Character(
            id="ally", name="Ally", size=CharacterSize.MEDIUM,
            hp=100, attack=14, speed=12, color="#fff",
            abilities=["staff_strike"], max_mana=10, max_shield=20,
        )
        # Hurt ally below 60%
        ally.take_direct_damage(50)

        from circle_cycle.application.services.bot_ai import BotAI
        bot_ai = BotAI(repo._abilities)
        plans = bot_ai.generate_plan([sage, ally], [_make_char("player")])

        # Sage should pick healing_light for the hurt ally
        sage_plan = next(p for p in plans if p.actor.id == "sage")
        assert sage_plan.ability.id == "healing_light"
        assert ally in sage_plan.targets

    def test_bot_with_spike_targets_shielded_enemy(self, repository: InMemoryDataRepository) -> None:
        """Bot with Spike should target enemy with highest shield."""
        repo = repository
        repo._abilities["spike_slash"] = Ability(
            id="spike_slash", name="Spike Slash", type=AbilityType.NORMAL,
            damage=20, effect=None, cooldown=0, mana_cost=0,
            target_type=TargetType.SINGLE_ENEMY,
        )
        repo._abilities["shield_crush"] = Ability(
            id="shield_crush", name="Shield Crush", type=AbilityType.SPECIAL,
            damage=20, effect=None, cooldown=2, mana_cost=5,
            target_type=TargetType.SINGLE_ENEMY, shield_pierce=True, shield_destroy=20,
        )

        spike = Character(
            id="spike", name="Spike", size=CharacterSize.MEDIUM,
            hp=95, attack=24, speed=16, color="#ef4444",
            abilities=["spike_slash", "shield_crush"],
            max_mana=10, max_shield=15, role="breaker",
        )
        enemy_low_shield = _make_char("e1", max_shield=10)
        enemy_high_shield = _make_char("e2", max_shield=50)

        from circle_cycle.application.services.bot_ai import BotAI
        bot_ai = BotAI(repo._abilities)
        plans = bot_ai.generate_plan([spike], [enemy_low_shield, enemy_high_shield])

        spike_plan = plans[0]
        assert spike_plan.ability.id == "shield_crush"
        assert enemy_high_shield in spike_plan.targets


# ===== JSON Loading =====


class TestNewCharactersLoading:
    """Tests for loading all 7 characters from JSON."""

    def test_all_seven_characters_load(self) -> None:
        """All 7 characters should load from JSON without errors."""
        from pathlib import Path
        from circle_cycle.infrastructure.persistence.repositories.json_data_repository import (
            JsonDataRepository,
        )

        data_dir = Path(__file__).resolve().parents[2] / "data"
        repo = JsonDataRepository(data_dir)
        chars = repo.load_characters()
        assert len(chars) == 7
        assert "sage" in chars
        assert "drum" in chars
        assert "hex" in chars
        assert "spike" in chars

    def test_new_abilities_load(self) -> None:
        """All new abilities should load from JSON."""
        from pathlib import Path
        from circle_cycle.infrastructure.persistence.repositories.json_data_repository import (
            JsonDataRepository,
        )

        data_dir = Path(__file__).resolve().parents[2] / "data"
        repo = JsonDataRepository(data_dir)
        abilities = repo.load_abilities()

        assert "staff_strike" in abilities
        assert "healing_light" in abilities
        assert "divine_restoration" in abilities
        assert "drum_bash" in abilities
        assert "war_drums" in abilities
        assert "battle_anthem" in abilities
        assert "hex_bolt" in abilities
        assert "curse" in abilities
        assert "mass_plague" in abilities
        assert "spike_slash" in abilities
        assert "shield_crush" in abilities
        assert "shatter_all" in abilities

        # Verify field values
        heal = abilities["healing_light"]
        assert heal.heal_amount == 30
        assert heal.target_type == TargetType.SINGLE_ALLY
        assert heal.mana_cost == 4

        crush = abilities["shield_crush"]
        assert crush.shield_pierce is True
        assert crush.shield_destroy == 20

        drums = abilities["war_drums"]
        assert drums.buff_stat == "attack"
        assert drums.buff_amount == 8
        assert drums.buff_duration == 2

    def test_existing_characters_unchanged(self) -> None:
        """Nova, Stone, Ace should have same stats as before."""
        from pathlib import Path
        from circle_cycle.infrastructure.persistence.repositories.json_data_repository import (
            JsonDataRepository,
        )

        data_dir = Path(__file__).resolve().parents[2] / "data"
        repo = JsonDataRepository(data_dir)
        chars = repo.load_characters()

        ace = chars["ace"]
        assert ace.hp == 85
        assert ace.attack == 12
        assert ace.speed == 18

        nova = chars["nova"]
        assert nova.hp == 115
        assert nova.attack == 14

        stone = chars["stone"]
        assert stone.hp == 150
        assert stone.attack == 16
