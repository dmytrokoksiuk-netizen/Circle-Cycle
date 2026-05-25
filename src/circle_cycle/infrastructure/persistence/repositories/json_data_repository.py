"""JSON file-based implementation of the DataRepository interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.card_stat import CardStat
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.exceptions.battle import DataLoadError
from circle_cycle.domain.interfaces.data_repository import DataRepository
from circle_cycle.domain.value_objects.card_effect import CardEffect


class JsonDataRepository(DataRepository):
    """Load game data from JSON files in the data directory."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def _load_json(self, filename: str) -> list[dict[str, Any]]:
        """Read and parse a JSON array file from the data directory."""
        path = self.data_dir / filename
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DataLoadError(f"Missing JSON file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataLoadError(f"Malformed JSON in {path}: {exc}") from exc

        if not isinstance(raw_data, list):
            raise DataLoadError(f"Expected a list in {path}, got {type(raw_data).__name__}.")

        return raw_data

    def load_abilities(self) -> dict[str, Ability]:
        """Load abilities and return a mapping keyed by ability id."""
        abilities: dict[str, Ability] = {}
        for entry in self._load_json("abilities.json"):
            try:
                effect_raw = entry.get("effect")
                effect: StatusEffect | None = None
                if effect_raw is not None:
                    effect = StatusEffect(str(effect_raw))

                ability = Ability(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    type=AbilityType(str(entry["type"])),
                    damage=int(entry["damage"]),
                    effect=effect,
                    cooldown=int(entry["cooldown"]),
                )
            except KeyError as exc:
                raise DataLoadError(f"Ability entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise DataLoadError(f"Ability entry has invalid values: {entry}") from exc

            abilities[ability.id] = ability

        return abilities

    def load_characters(self) -> dict[str, Character]:
        """Load characters and return a mapping keyed by character id."""
        characters: dict[str, Character] = {}
        for entry in self._load_json("characters.json"):
            try:
                character = Character(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    size=CharacterSize(str(entry["size"])),
                    hp=int(entry["hp"]),
                    attack=int(entry["attack"]),
                    speed=int(entry["speed"]),
                    color=str(entry["color"]),
                    abilities=[str(aid) for aid in entry["abilities"]],
                )
            except KeyError as exc:
                raise DataLoadError(f"Character entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise DataLoadError(f"Character entry has invalid values: {entry}") from exc

            characters[character.id] = character

        return characters

    def load_cards(self) -> dict[str, Card]:
        """Load cards and return a mapping keyed by card id."""
        cards: dict[str, Card] = {}
        for entry in self._load_json("cards.json"):
            try:
                effect_data = entry["effect"]
                if not isinstance(effect_data, dict):
                    raise DataLoadError(f"Card effect must be an object: {entry}")

                card = Card(
                    id=str(entry["id"]),
                    name=str(entry["name"]),
                    description=str(entry["description"]),
                    effect=CardEffect(
                        stat=CardStat(str(effect_data["stat"])),
                        value=int(effect_data["value"]),
                    ),
                )
            except KeyError as exc:
                raise DataLoadError(f"Card entry is missing required key: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise DataLoadError(f"Card entry has invalid values: {entry}") from exc

            cards[card.id] = card

        return cards
