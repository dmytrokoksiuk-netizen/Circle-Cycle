from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING

from game.ability import Ability, resolve_ability
from game.bot import BotAI
from game.card import Card
from game.character import Character
from game.loader import DataLoader

if TYPE_CHECKING:
    from game.loader import DataLoader as LoaderType


class BattleEngine:
    """Manage the battle flow, turn order, and card phase."""

    def __init__(
        self,
        player_team: list[Character],
        bot_team: list[Character],
        loader: LoaderType | None = None,
    ) -> None:
        self.loader = loader or DataLoader()
        self.abilities = self.loader.load_abilities()
        self.cards = self.loader.load_cards()
        self.player_team = player_team
        self.bot_team = bot_team
        self.turn_order: list[Character] = []
        self.round_number = 0
        self.current_turn_index = 0
        self.card_phase_active = False
        self.pending_card_choices: list[Card] = []
        self.bot_ai = BotAI(self.abilities)

    def start_battle(self) -> None:
        """Reset the battle and establish the initial turn order."""
        self.round_number = 1
        self.current_turn_index = 0
        self.card_phase_active = False
        self.pending_card_choices = []
        self.turn_order = sorted(
            [*self.player_team, *self.bot_team],
            key=lambda character: character.speed,
            reverse=True,
        )

    def get_current_character(self) -> Character:
        """Return the character whose turn it is."""
        if not self.turn_order:
            raise ValueError("Battle has not started.")
        return self.turn_order[self.current_turn_index]

    @classmethod
    def create_from_selection(
        cls,
        selected_character_ids: list[str],
        character_pool: dict[str, Character],
        loader: LoaderType | None = None,
    ) -> "BattleEngine":
        """Create a battle from selected characters and a random bot team."""
        player_team = [copy.deepcopy(character_pool[character_id]) for character_id in selected_character_ids]
        bot_team = [
            copy.deepcopy(character)
            for character in random.sample(list(character_pool.values()), k=3)
        ]
        return cls(player_team, bot_team, loader)

    def get_ability_by_type(self, character: Character, ability_type: str) -> Ability | None:
        """Return the first ability matching the requested type for the character."""
        for ability_id in character.abilities:
            ability = self.abilities.get(ability_id)
            if ability is not None and ability.type == ability_type:
                return ability
        return None

    def get_action_targets(self, attacker: Character, ability: Ability) -> list[Character]:
        """Return the target list that should be used for the action."""
        if attacker in self.player_team:
            team = self.bot_team
        elif attacker in self.bot_team:
            team = self.player_team
        else:
            raise ValueError("Attacker is not part of the current battle.")

        alive_targets = [character for character in team if character.is_alive()]
        if ability.type == "ultimate":
            return alive_targets

        if not alive_targets:
            return []

        lowest_hp_target = min(alive_targets, key=lambda character: character.current_hp)
        return [lowest_hp_target]

    def execute_action(
        self, attacker: Character, ability: Ability, targets: list[Character]
    ) -> list[str]:
        """Execute an ability and return the resulting log lines."""
        if attacker not in self.turn_order:
            raise ValueError("Attacker is not part of the current battle.")

        if ability.id not in attacker.abilities:
            raise ValueError(f"{attacker.name} does not know {ability.id}.")

        if attacker.cooldowns.get(ability.id, 0) > 0:
            raise ValueError(f"{ability.name} is still on cooldown for {attacker.name}.")

        attacker.cooldowns[ability.id] = ability.cooldown
        logs = resolve_ability(attacker, targets, ability)
        return logs

    def bot_turn(self) -> list[str]:
        """Ask the bot AI for a move and execute it."""
        bot, ability, targets = self.bot_ai.choose_action(self.bot_team, self.player_team)
        return self.execute_action(bot, ability, targets)

    def end_turn(self) -> bool:
        """Advance the turn and return True when a round has ended."""
        if not self.turn_order:
            raise ValueError("Battle has not started.")

        for character in [*self.player_team, *self.bot_team]:
            character.tick_cooldowns()
            character.tick_status_effects()

        self.current_turn_index += 1

        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.card_phase_active = True
            self.pending_card_choices = self.get_card_choices()
            self._apply_bot_card_phase()
            return True

        return False

    def check_winner(self) -> str | None:
        """Return the winning side, or None if the battle is still ongoing."""
        player_alive = any(character.is_alive() for character in self.player_team)
        bot_alive = any(character.is_alive() for character in self.bot_team)

        if not player_alive and bot_alive:
            return "bot"
        if not bot_alive and player_alive:
            return "player"
        if not player_alive and not bot_alive:
            return "bot"
        return None

    def get_card_choices(self) -> list[Card]:
        """Return the current round's three card options."""
        if self.pending_card_choices:
            return list(self.pending_card_choices)

        card_pool = list(self.cards.values())
        self.pending_card_choices = random.sample(card_pool, k=min(3, len(card_pool)))
        return list(self.pending_card_choices)

    def apply_card_choice(self, card: Card, target: Character) -> str:
        """Apply a chosen card to the target and end the card phase."""
        if target not in self.player_team:
            raise ValueError("Only player characters can receive cards.")

        if card not in self.pending_card_choices:
            raise ValueError("Chosen card is not available in the current card phase.")

        log = target.apply_card(card)
        self.card_phase_active = False
        self.pending_card_choices = []
        return log

    def _apply_bot_card_phase(self) -> None:
        """Apply a random card to a bot character at the end of the round."""
        if not self.pending_card_choices:
            self.pending_card_choices = self.get_card_choices()

        if not self.pending_card_choices:
            return

        card = random.choice(self.pending_card_choices)
        bot_targets = [character for character in self.bot_team if character.is_alive()]
        if not bot_targets:
            return

        target = random.choice(bot_targets)
        target.apply_card(card)
