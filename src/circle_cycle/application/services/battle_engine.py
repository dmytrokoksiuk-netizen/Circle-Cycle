"""Application service orchestrating the battle flow."""

from __future__ import annotations

import copy
import random

from circle_cycle.application.services.ability_resolver import resolve_ability
from circle_cycle.application.services.bot_ai import BotAI
from circle_cycle.application.services.card_applicator import apply_card
from circle_cycle.domain.constants.game import CARD_CHOICES_PER_ROUND, TEAM_SIZE
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.battle_phase import BattlePhase
from circle_cycle.domain.value_objects.planned_action import PlannedAction
from circle_cycle.domain.exceptions.battle import (
    AbilityOnCooldownError,
    BattleNotStartedError,
    InvalidActionError,
    InvalidTargetError,
)
from circle_cycle.domain.interfaces.data_repository import DataRepository


class BattleEngine:
    """Manage the battle flow, turn order, and card phase."""

    def __init__(
        self,
        player_team: list[Character],
        bot_team: list[Character],
        repository: DataRepository,
    ) -> None:
        self.repository = repository
        self.abilities = self.repository.load_abilities()
        self.cards = self.repository.load_cards()
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
        # Initialize planning phase for Task 1
        self.phase = BattlePhase.PLANNING
        self.planned_actions: list[PlannedAction] = []

    def get_current_character(self) -> Character:
        """Return the character whose turn it is."""
        if not self.turn_order:
            raise BattleNotStartedError("Battle has not started.")
        return self.turn_order[self.current_turn_index]

    @classmethod
    def create_from_selection(
        cls,
        selected_character_ids: list[str],
        character_pool: dict[str, Character],
        repository: DataRepository,
    ) -> BattleEngine:
        """Create a battle from selected characters and a random bot team."""
        player_team = [
            copy.deepcopy(character_pool[character_id]) for character_id in selected_character_ids
        ]
        bot_team = [
            copy.deepcopy(character)
            for character in random.sample(list(character_pool.values()), k=TEAM_SIZE)
        ]
        return cls(player_team, bot_team, repository)

    def get_ability_by_type(self, character: Character, ability_type: str) -> Ability | None:
        """Return the first ability matching the requested type for the character."""
        for ability_id in character.abilities:
            ability = self.abilities.get(ability_id)
            if ability is not None and ability.type == ability_type:
                return ability
        return None

    # --- Planning phase API (Task 1 initial implementation) ---
    def submit_player_action(self, attacker: Character, ability: Ability, targets: list[Character]) -> int:
        """Submit a planned action for a player character.

        Returns the number of planned actions submitted so far for the player.
        """
        if attacker not in self.player_team:
            raise InvalidActionError("Only player characters may submit planned actions.")
        if not attacker.is_alive():
            raise InvalidActionError("Dead characters cannot submit actions.")

        planned = PlannedAction(actor=attacker, ability=ability, targets=list(targets))
        self.planned_actions.append(planned)

        # If all player plans collected, generate bot plans and execute the full plan.
        if len([p for p in self.planned_actions if p.actor in self.player_team]) >= TEAM_SIZE:
            self._generate_bot_actions()
            return self.execute_planned_actions()

        return len([p for p in self.planned_actions if p.actor in self.player_team])

    def _generate_bot_actions(self) -> None:
        """Generate a simple bot action for each living bot and append to planned actions."""
        for bot in [b for b in self.bot_team if b.is_alive()]:
            # Simple bot selection: prefer non-normal abilities that are off-cooldown, else normal
            ability = None
            for ability_id in bot.abilities:
                candidate = self.abilities.get(ability_id)
                if candidate is None:
                    continue
                if bot.cooldowns.get(ability_id, 0) == 0 and candidate.type != AbilityType.NORMAL:
                    ability = candidate
                    break
            if ability is None:
                # find normal ability by id list order
                for ability_id in bot.abilities:
                    candidate = self.abilities.get(ability_id)
                    if candidate is not None and candidate.type == AbilityType.NORMAL:
                        ability = candidate
                        break
            if ability is None:
                continue
            targets = self.get_action_targets(bot, ability)
            planned = PlannedAction(actor=bot, ability=ability, targets=list(targets))
            self.planned_actions.append(planned)

    def execute_planned_actions(self) -> list[str]:
        """Execute all planned actions in the order they were collected.

        Returns a list of battle log lines produced during execution.
        """
        if not self.planned_actions:
            return []

        self.phase = BattlePhase.EXECUTION
        logs: list[str] = []

        # Execute each planned action sequentially. Skip if actor dead or targets all dead.
        for planned in list(self.planned_actions):
            actor = planned.actor
            ability = planned.ability
            targets = [t for t in planned.targets if t.is_alive()]

            if not actor.is_alive():
                logs.append(f"{actor.name} is dead — action skipped.")
                continue
            if not targets:
                logs.append(f"{actor.name}'s targets are dead — action skipped.")
                continue

            # Apply cooldown and resolve ability
            actor.cooldowns[ability.id] = ability.cooldown
            logs.extend(resolve_ability(actor, targets, ability))

        # Clear planned actions and enter turn end
        self.planned_actions = []
        self.phase = BattlePhase.TURN_END
        self.end_turn()
        return logs

    def get_action_targets(self, attacker: Character, ability: Ability) -> list[Character]:
        """Return the target list that should be used for the action."""
        if attacker in self.player_team:
            team = self.bot_team
        elif attacker in self.bot_team:
            team = self.player_team
        else:
            raise InvalidTargetError("Attacker is not part of the current battle.")

        alive_targets = [character for character in team if character.is_alive()]
        if ability.type == AbilityType.ULTIMATE:
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
            raise InvalidActionError("Attacker is not part of the current battle.")

        if ability.id not in attacker.abilities:
            raise InvalidActionError(f"{attacker.name} does not know {ability.id}.")

        if attacker.cooldowns.get(ability.id, 0) > 0:
            raise AbilityOnCooldownError(
                f"{ability.name} is still on cooldown for {attacker.name}."
            )

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
            raise BattleNotStartedError("Battle has not started.")

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
        """Return the current round's card options."""
        if self.pending_card_choices:
            return list(self.pending_card_choices)

        card_pool = list(self.cards.values())
        self.pending_card_choices = random.sample(
            card_pool, k=min(CARD_CHOICES_PER_ROUND, len(card_pool))
        )
        return list(self.pending_card_choices)

    def apply_card_choice(self, card: Card, target: Character) -> str:
        """Apply a chosen card to the target and end the card phase."""
        if target not in self.player_team:
            raise InvalidTargetError("Only player characters can receive cards.")

        if card not in self.pending_card_choices:
            raise InvalidActionError("Chosen card is not available in the current card phase.")

        log = apply_card(card, target)
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
        apply_card(card, target)
