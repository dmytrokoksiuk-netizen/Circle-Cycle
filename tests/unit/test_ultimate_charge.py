"""Unit tests for the Ultimate charge mechanic."""

from __future__ import annotations

import copy

from circle_cycle.application.services.battle_engine import BattleEngine
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.enums.ability_type import AbilityType
from tests.conftest import InMemoryDataRepository


def test_character_charge_and_ready(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    ace = copy.deepcopy(chars["ace"])
    assert ace.special_use_count == 0
    assert ace.is_ultimate_ready is False

    # simulate one special
    ace.increment_special_count()
    assert ace.special_use_count == 1
    assert ace.is_ultimate_ready is False

    ace.increment_special_count()
    assert ace.special_use_count == 2
    assert ace.is_ultimate_ready is True

    ace.reset_special_count()
    assert ace.special_use_count == 0
    assert ace.is_ultimate_ready is False


def test_battle_engine_rejects_unready_ultimate(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]
    bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]

    eng = BattleEngine(player_team, bot_team, repository)
    eng.start_battle()

    abilities = repository.load_abilities()
    ultimate = next(a for a in abilities.values() if a.type == AbilityType.ULTIMATE)

    # Attempt to submit ultimate for first player character (should raise)
    try:
        eng.submit_player_action(ultimate, bot_team[0])
        raised = False
    except Exception as e:
        raised = True
        assert "Ultimate not ready" in str(e)
    assert raised is True


def test_bot_ai_does_not_use_ultimate_when_unready(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]
    bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]

    eng = BattleEngine(player_team, bot_team, repository)
    eng.start_battle()

    plans = eng.bot_ai.generate_plan(eng.bot_team, eng.player_team)
    # Ensure none of bot plans use an ultimate (they start uncharged)
    assert all(p.ability.type != AbilityType.ULTIMATE for p in plans)


def test_specials_accumulate_and_ultimate_resets(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]
    bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]

    eng = BattleEngine(player_team, bot_team, repository)
    eng.start_battle()

    abilities = repository.load_abilities()
    punch = abilities["punch"]
    special = abilities["fire_spin"]
    ultimate = abilities["earthquake"]

    # Manually execute two special uses for ace
    logs1 = eng.execute_action(player_team[0], special, eng.get_action_targets(player_team[0], special))
    logs2 = eng.execute_action(player_team[0], special, eng.get_action_targets(player_team[0], special))
    assert player_team[0].special_use_count == 2
    assert player_team[0].is_ultimate_ready is True

    # Now execute ultimate and ensure it resets
    logs3 = eng.execute_action(player_team[0], ultimate, eng.get_action_targets(player_team[0], ultimate))
    assert player_team[0].special_use_count == 0
    assert player_team[0].is_ultimate_ready is False
