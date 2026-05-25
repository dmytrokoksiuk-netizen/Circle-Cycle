"""Integration tests for the JSON data repository."""

from __future__ import annotations

from pathlib import Path

from circle_cycle.infrastructure.persistence.repositories.json_data_repository import (
    JsonDataRepository,
)


class TestJsonDataRepository:
    """Tests for loading game data from actual JSON files."""

    def test_load_abilities(self, data_dir: Path) -> None:
        """Should load all abilities from abilities.json."""
        repo = JsonDataRepository(data_dir)
        abilities = repo.load_abilities()
        assert len(abilities) > 0
        assert "punch" in abilities

    def test_load_characters(self, data_dir: Path) -> None:
        """Should load all characters from characters.json."""
        repo = JsonDataRepository(data_dir)
        characters = repo.load_characters()
        assert len(characters) > 0
        assert "ace" in characters

    def test_load_cards(self, data_dir: Path) -> None:
        """Should load all cards from cards.json."""
        repo = JsonDataRepository(data_dir)
        cards = repo.load_cards()
        assert len(cards) > 0
        assert "iron_skin" in cards
