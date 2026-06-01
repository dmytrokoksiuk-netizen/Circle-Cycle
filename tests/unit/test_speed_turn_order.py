"""Unit tests for speed-based turn order in BattleEngine."""

from __future__ import annotations

import copy

from circle_cycle.application.services.battle_engine import BattleEngine
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.value_objects.planned_action import PlannedAction
from tests.conftest import InMemoryDataRepository


def test__calculate_team_speed_all_alive(repository: InMemoryDataRepository) -> None:
    characters = repository.load_characters()
    # three alive characters
    chars = [copy.deepcopy(characters["ace"]), copy.deepcopy(characters["nova"]), copy.deepcopy(characters["stone"]) ]
    eng = BattleEngine(chars[:1], chars[1:], repository)
    # use the players list for calculation
    total = eng._calculate_team_speed(chars)
    assert total == sum(c.speed for c in chars)


def test__calculate_team_speed_excludes_dead(repository: InMemoryDataRepository) -> None:
    characters = repository.load_characters()
    chars = [copy.deepcopy(characters["ace"]), copy.deepcopy(characters["nova"])]
    chars[0].current_hp = 0
    eng = BattleEngine([chars[0]], [chars[1]], repository)
    assert eng._calculate_team_speed(chars) == chars[1].speed


def test__calculate_team_speed_all_dead(repository: InMemoryDataRepository) -> None:
    characters = repository.load_characters()
    chars = [copy.deepcopy(characters["ace"]), copy.deepcopy(characters["nova"]) ]
    for c in chars:
        c.current_hp = 0
    eng = BattleEngine(chars, [], repository)
    assert eng._calculate_team_speed(chars) == 0


def _make_planned(actor, ability: Ability, target) -> PlannedAction:
    return PlannedAction(actor=actor, ability=ability, targets=[target])


def test_execution_order_player_first(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    # create distinct instances for teams
    player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]
    bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]

    # set speeds so player sum = 45
    player_team[0].speed = 20
    player_team[1].speed = 15
    player_team[2].speed = 10
    # enemy sum = 38
    bot_team[0].speed = 12
    bot_team[1].speed = 13
    bot_team[2].speed = 13

    eng = BattleEngine(player_team, bot_team, repository)
    eng.start_battle()

    # build a complete player plan (TEAM_SIZE == 3)
    abilities = repository.load_abilities()
    punch = abilities["punch"]
    # plan actions for each player actor targeting the first bot
    for p in player_team:
        eng.player_plan.append(_make_planned(p, punch, bot_team[0]))

    logs = eng.confirm_plan()
    assert any("Player team speed" in line and "Player acts first" in line for line in logs)


def test_execution_order_enemy_first(repository: InMemoryDataRepository) -> None:
    chars = repository.load_characters()
    player_team = [copy.deepcopy(chars["ace"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]
    bot_team = [copy.deepcopy(chars["nova"]), copy.deepcopy(chars["nova"]), copy.deepcopy(chars["stone"]) ]

    # set speeds so player sum = 30, enemy sum = 42
    player_team[0].speed = 10
    player_team[1].speed = 10
    player_team[2].speed = 10

    bot_team[0].speed = 14
    bot_team[1].speed = 14
    bot_team[2].speed = 14

    eng = BattleEngine(player_team, bot_team, repository)
    eng.start_battle()

    abilities = repository.load_abilities()
    punch = abilities["punch"]
    for p in player_team:
        eng.player_plan.append(_make_planned(p, punch, bot_team[0]))

    logs = eng.confirm_plan()
    assert any("Enemy acts first" in line or ("Enemy team speed" in line and "Enemy acts first" in line) for line in logs)
