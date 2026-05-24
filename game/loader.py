from __future__ import annotations

import json
from pathlib import Path

from game.ability import Ability
from game.card import Card
from game.character import Character


class DataLoader:
    """Load game data from the JSON files in the data directory."""

    def __init__(self) -> None:
        self.data_dir = Path(__file__).resolve().parents[1] / "data"

    def _load_json(self, filename: str) -> list[dict[str, object]]:
        path = self.data_dir / filename
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"Missing JSON file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in {path}: {exc}") from exc

        if not isinstance(raw_data, list):
            raise ValueError(f"Expected a list in {path}, got {type(raw_data).__name__}.")

        return raw_data

    def load_abilities(self) -> dict[str, Ability]:
        """Load abilities and return a mapping keyed by ability id."""
        abilities: dict[str, Ability] = {}
        for entry in self._load_json("abilities.json"):
            if not isinstance(entry, dict):
                raise ValueError("Each ability entry must be an object.")

            try:
                ability = Ability(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    type=str(entry["type"]),
                    damage=int(entry["damage"]),
                    effect=entry["effect"] if entry["effect"] is not None else None,
                    cooldown=int(entry["cooldown"]),
                )
            except KeyError as exc:
                raise ValueError(f"Ability entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Ability entry has invalid values: {entry}") from exc

            abilities[ability.id] = ability

        return abilities

    def load_characters(self) -> dict[str, Character]:
        """Load characters and return a mapping keyed by character id."""
        characters: dict[str, Character] = {}
        for entry in self._load_json("characters.json"):
            if not isinstance(entry, dict):
                raise ValueError("Each character entry must be an object.")

            try:
                character = Character(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    size=str(entry["size"]),
                    hp=int(entry["hp"]),
                    attack=int(entry["attack"]),
                    speed=int(entry["speed"]),
                    color=str(entry["color"]),
                    abilities=[str(ability_id) for ability_id in entry["abilities"]],
                )
            except KeyError as exc:
                raise ValueError(f"Character entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Character entry has invalid values: {entry}") from exc

            characters[character.id] = character

        return characters

    def load_cards(self) -> dict[str, Card]:
        """Load cards and return a mapping keyed by card id."""
        cards: dict[str, Card] = {}
        for entry in self._load_json("cards.json"):
            if not isinstance(entry, dict):
                raise ValueError("Each card entry must be an object.")

            try:
                card = Card(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    description=str(entry["description"]),
                    effect={
                        "stat": str(entry["effect"]["stat"]),
                        "value": int(entry["effect"]["value"]),
                    },
                )
            except KeyError as exc:
                raise ValueError(f"Card entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Card entry has invalid values: {entry}") from exc

            cards[card.id] = card

        return cards
