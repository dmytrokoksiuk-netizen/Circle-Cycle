"""Unit tests for card offering and rarity weighting."""

from __future__ import annotations

import collections
import random
import copy

from circle_cycle.application.services.battle_engine import BattleEngine
from tests.conftest import InMemoryDataRepository
from circle_cycle.domain.enums.card_rarity import CardRarity


def test_card_offering_count_and_no_duplicates(repository: InMemoryDataRepository) -> None:
    repo = repository
    cards = repo.load_cards()
    # create engine with sample teams
    chars = repo.load_characters()
    eng = BattleEngine([copy.deepcopy(chars["ace"])], [copy.deepcopy(chars["nova"])], repo)

    # force the engine to use repo cards
    eng.cards = cards

    offering = eng.get_card_choices()
    assert 1 <= len(offering) <= 4
    # no duplicates
    ids = [c.id for c in offering]
    assert len(ids) == len(set(ids))


def test_card_offering_smaller_pool(repository: InMemoryDataRepository) -> None:
    repo = repository
    cards = repo.load_cards()
    # shrink pool to 2 cards
    small_pool = dict(list(cards.items())[:2])

    chars = repo.load_characters()
    eng = BattleEngine([copy.deepcopy(chars["ace"])], [copy.deepcopy(chars["nova"])], repo)
    eng.cards = small_pool

    offering = eng.get_card_choices()
    assert len(offering) == 2


def test_rarity_distribution(repository: InMemoryDataRepository) -> None:
    repo = repository
    cards = repo.load_cards()
    # ensure at least one common and one rare exist
    rarities = [getattr(c, "rarity", CardRarity.COMMON) for c in cards.values()]
    assert CardRarity.COMMON in rarities

    chars = repo.load_characters()
    eng = BattleEngine([copy.deepcopy(chars["ace"])], [copy.deepcopy(chars["nova"])], repo)
    eng.cards = cards

    counts = collections.Counter()
    trials = 500
    for _ in range(trials):
        eng.pending_card_choices = []
        offering = eng.get_card_choices()
        for c in offering:
            counts[getattr(c, "rarity", CardRarity.COMMON)] += 1

    # Common should appear more frequently than rare in aggregate
    assert counts[CardRarity.COMMON] >= counts[CardRarity.RARE]
