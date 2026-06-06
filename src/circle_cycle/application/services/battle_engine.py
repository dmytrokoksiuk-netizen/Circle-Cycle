"""Application service orchestrating the battle flow."""

from __future__ import annotations

import copy
import random

from circle_cycle.application.services.ability_resolver import resolve_ability
from circle_cycle.application.services.bot_ai import BotAI
from circle_cycle.application.services.card_applicator import apply_card
from circle_cycle.domain.constants.game import (
    CARD_CHOICES_PER_ROUND,
    MANA_REGEN_PER_TURN,
    TEAM_SIZE,
)
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.card import Card
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.battle_phase import BattlePhase
from circle_cycle.domain.value_objects.planned_action import PlannedAction
from circle_cycle.domain.exceptions.battle import (
    AbilityOnCooldownError,
    BattleNotStartedError,
    InsufficientManaError,
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
        # Separate plans for player and enemy and an index for planning progress
        self.player_plan: list[PlannedAction] = []
        self.enemy_plan: list[PlannedAction] = []
        self.planning_index: int = 0

        # Reset ultimate charges for all characters at battle start
        for character in [*self.player_team, *self.bot_team]:
            if hasattr(character, "reset_special_count"):
                character.reset_special_count()

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

    # --- Mana helpers ---
    def regenerate_mana(self) -> list[str]:
        """Restore mana for all living characters. Returns log lines."""
        logs: list[str] = []
        for character in [*self.player_team, *self.bot_team]:
            if character.is_alive() and character.max_mana > 0:
                old_mana = character.mana
                character.restore_mana(MANA_REGEN_PER_TURN)
                if character.mana > old_mana:
                    logs.append(
                        f"{character.name} regenerates {character.mana - old_mana} mana "
                        f"(now {character.mana}/{character.max_mana})"
                    )
        return logs

    # --- Planning phase API (Task 1) ---
    def submit_player_action(self, ability: Ability, target: Character) -> int:
        """Submit a planned action for the next player character in planning order.

        Returns the number of planned actions collected so far.
        """
        if self.phase != BattlePhase.PLANNING:
            raise InvalidActionError("Cannot submit actions outside of PLANNING phase.")
        if self.planning_index >= len(self.player_team):
            raise InvalidActionError("All player characters have already been planned.")

        attacker = self.player_team[self.planning_index]
        if not attacker.is_alive():
            raise InvalidActionError("Dead characters cannot submit actions.")
        if ability.id not in attacker.abilities:
            raise InvalidActionError(f"{attacker.name} does not know {ability.id}.")

        # Prevent selecting Ultimate unless character has enough charges
        from circle_cycle.domain.enums.ability_type import AbilityType
        if ability.type == AbilityType.ULTIMATE and not getattr(attacker, "is_ultimate_ready", False):
            raise InvalidActionError(
                f"Ultimate not ready ({attacker.special_use_count}/2 charges)"
            )

        # Mana validation
        if not attacker.can_afford_ability(ability.mana_cost):
            raise InsufficientManaError(
                f"Not enough mana (have {attacker.mana}, need {ability.mana_cost})"
            )

        targets = [target] if target is not None else []
        planned = PlannedAction(actor=attacker, ability=ability, targets=list(targets))
        self.player_plan.append(planned)
        self.planning_index += 1
        return len(self.player_plan)

    def undo_last_action(self) -> int:
        """Undo the last planned player action. Returns remaining planned count."""
        if not self.player_plan:
            return 0
        self.player_plan.pop()
        self.planning_index = max(0, self.planning_index - 1)
        return len(self.player_plan)

    def confirm_plan(self) -> list[str]:
        """Confirm the player's plan, generate enemy plan, and execute both plans.

        Returns accumulated battle log lines.
        """
        if len(self.player_plan) != TEAM_SIZE:
            raise InvalidActionError("Plan is incomplete; 3 player actions required.")

        # Generate enemy plan using BotAI
        self.enemy_plan = self.bot_ai.generate_plan(self.bot_team, self.player_team)

        # Determine which side acts first based on team speed totals (Task 2)
        player_speed = self._calculate_team_speed(self.player_team)
        enemy_speed = self._calculate_team_speed(self.bot_team)

        self.phase = BattlePhase.EXECUTION
        logs: list[str] = []

        if player_speed >= enemy_speed:
            logs.append(f"Player team speed: {player_speed} vs Enemy team speed: {enemy_speed} — Player acts first!")
            first_plan, second_plan = self.player_plan, self.enemy_plan
        else:
            logs.append(f"Player team speed: {player_speed} vs Enemy team speed: {enemy_speed} — Enemy acts first!")
            first_plan, second_plan = self.enemy_plan, self.player_plan

        # Execute first plan then second plan
        for planned in list(first_plan):
            actor = planned.actor
            ability = planned.ability
            targets = [t for t in planned.targets if t.is_alive()]

            if not actor.is_alive():
                logs.append(f"{actor.name} is dead — action skipped.")
                continue
            if not targets:
                logs.append(f"{actor.name}'s targets are dead — action skipped.")
                continue

            # Spend mana at execution time
            if not actor.can_afford_ability(ability.mana_cost):
                logs.append(
                    f"{actor.name} doesn't have enough mana for {ability.name} — action skipped."
                )
                continue
            actor.spend_mana(ability.mana_cost)
            if ability.mana_cost > 0:
                logs.append(f"{actor.name} uses {ability.name} (-{ability.mana_cost} MP)")

            actor.cooldowns[ability.id] = ability.cooldown
            logs.extend(resolve_ability(actor, targets, ability))

        for planned in list(second_plan):
            actor = planned.actor
            ability = planned.ability
            targets = [t for t in planned.targets if t.is_alive()]

            if not actor.is_alive():
                logs.append(f"{actor.name} is dead — action skipped.")
                continue
            if not targets:
                logs.append(f"{actor.name}'s targets are dead — action skipped.")
                continue

            # Spend mana at execution time
            if not actor.can_afford_ability(ability.mana_cost):
                logs.append(
                    f"{actor.name} doesn't have enough mana for {ability.name} — action skipped."
                )
                continue
            actor.spend_mana(ability.mana_cost)
            if ability.mana_cost > 0:
                logs.append(f"{actor.name} uses {ability.name} (-{ability.mana_cost} MP)")

            actor.cooldowns[ability.id] = ability.cooldown
            logs.extend(resolve_ability(actor, targets, ability))

        # Clear plans and enter turn end
        self.player_plan = []
        self.enemy_plan = []
        self.phase = BattlePhase.TURN_END
        self.end_turn()
        return logs

    def get_action_targets(self, attacker: Character, ability: Ability) -> list[Character]:
        """Return the target list that should be used for the action based on target_type."""
        from circle_cycle.domain.enums.target_type import TargetType

        if attacker in self.player_team:
            enemy_team = self.bot_team
            ally_team = self.player_team
        elif attacker in self.bot_team:
            enemy_team = self.player_team
            ally_team = self.bot_team
        else:
            raise InvalidTargetError("Attacker is not part of the current battle.")

        target_type = getattr(ability, "target_type", TargetType.SINGLE_ENEMY)

        if target_type == TargetType.ALL_ENEMIES:
            return [c for c in enemy_team if c.is_alive()]
        elif target_type == TargetType.ALL_ALLIES:
            return [c for c in ally_team if c.is_alive()]
        elif target_type == TargetType.SINGLE_ALLY:
            alive_allies = [c for c in ally_team if c.is_alive()]
            if not alive_allies:
                return []
            # Default: lowest HP ally (for heals) or highest ATK ally (for buffs)
            if ability.heal_amount > 0:
                return [min(alive_allies, key=lambda c: c.current_hp)]
            return [max(alive_allies, key=lambda c: c.effective_attack)]
        elif target_type == TargetType.SELF:
            return [attacker] if attacker.is_alive() else []
        else:
            # SINGLE_ENEMY (default)
            alive_targets = [c for c in enemy_team if c.is_alive()]
            if not alive_targets:
                return []
            # If shield_pierce, prefer target with most shield
            if ability.shield_pierce or ability.shield_destroy > 0:
                return [max(alive_targets, key=lambda c: c.shield)]
            lowest_hp_target = min(alive_targets, key=lambda c: c.current_hp)
            return [lowest_hp_target]

    def _calculate_team_speed(self, characters: list[Character]) -> int:
        """Return the total effective speed of all LIVING characters in the provided list.

        This is a pure calculation with no side effects. Characters with
        current_hp == 0 are considered dead and excluded. Uses effective_speed
        which accounts for active buffs and debuffs.
        """
        return sum(c.effective_speed for c in characters if c.is_alive())

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

        # Mana validation and spending
        if not attacker.can_afford_ability(ability.mana_cost):
            raise InsufficientManaError(
                f"Not enough mana (have {attacker.mana}, need {ability.mana_cost})"
            )
        attacker.spend_mana(ability.mana_cost)

        attacker.cooldowns[ability.id] = ability.cooldown
        logs: list[str] = []
        if ability.mana_cost > 0:
            logs.append(f"{attacker.name} uses {ability.name} (-{ability.mana_cost} MP)")
        logs.extend(resolve_ability(attacker, targets, ability))
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
            character.tick_buffs_debuffs()

        self.current_turn_index += 1

        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.card_phase_active = True
            self.pending_card_choices = self.get_card_choices()
            self._apply_bot_card_phase()
            # Regenerate mana at start of new round (before next planning phase)
            self.regenerate_mana()
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
        """Return the current round's card options using weighted rarity selection.

        Offers 3 or 4 cards (randomly) weighted by rarity. No duplicates in a single offering.
        """
        if self.pending_card_choices:
            return list(self.pending_card_choices)

        card_pool = list(self.cards.values())
        if not card_pool:
            return []

        # Determine offering size: 3 or 4 (favor 3)
        offering_size = random.choices([3, 4], weights=[80, 20], k=1)[0]
        offering_size = min(offering_size, len(card_pool))

        # Map rarities to weights
        from circle_cycle.domain.enums.card_rarity import CardRarity

        weight_map = {CardRarity.COMMON: 60, CardRarity.RARE: 30, CardRarity.EPIC: 10}

        # Make a weighted sample without replacement
        available = list(card_pool)
        chosen: list[Card] = []
        for _ in range(offering_size):
            weights = [weight_map.get(getattr(card, "rarity", CardRarity.COMMON), 60) for card in available]
            pick = random.choices(available, weights=weights, k=1)[0]
            chosen.append(pick)
            available.remove(pick)

        self.pending_card_choices = chosen
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
