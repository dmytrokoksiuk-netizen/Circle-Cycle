"""Application service implementing bot combat AI heuristics."""

from __future__ import annotations

from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType


class BotAI:
    """Select bot actions using a simple combat heuristic."""

    def __init__(self, abilities: dict[str, Ability]) -> None:
        self.abilities = abilities

    def choose_action(
        self, bot_team: list[Character], player_team: list[Character]
    ) -> tuple[Character, Ability, list[Character]]:
        """Choose a bot action and return the attacker, ability, and targets."""
        alive_bots = [character for character in bot_team if character.is_alive()]
        if not alive_bots:
            raise ValueError("Bot team has no alive characters.")

        target = min(
            [character for character in player_team if character.is_alive()],
            key=lambda character: (character.current_hp, character.name),
        )

        bot = max(alive_bots, key=lambda character: character.speed)

        special_candidates = [
            self.abilities[ability_id]
            for ability_id in bot.abilities
            if ability_id in self.abilities
            and self.abilities[ability_id].type != AbilityType.NORMAL
            and bot.cooldowns.get(ability_id, 0) == 0
        ]

        if special_candidates:
            ability: Ability | None = max(special_candidates, key=lambda a: a.damage)
        else:
            ability = next(
                (
                    self.abilities[ability_id]
                    for ability_id in bot.abilities
                    if ability_id in self.abilities
                    and self.abilities[ability_id].type == AbilityType.NORMAL
                ),
                None,
            )

        if ability is None:
            raise ValueError(f"No valid ability found for bot character {bot.name}.")

        targets = [target]
        if ability.type == AbilityType.ULTIMATE:
            targets = [character for character in player_team if character.is_alive()]

        return bot, ability, targets

    def generate_plan(self, bot_team: list[Character], player_team: list[Character]) -> list["PlannedAction"]:
        """Generate a planned action for each living bot character.

        Bot will only use Ultimate if the character's charge counter indicates it's ready.
        Prefer Special over Normal when charge is 1 to help unlock Ultimate.
        """
        from circle_cycle.domain.value_objects.planned_action import PlannedAction

        plans: list[PlannedAction] = []
        for bot in [b for b in bot_team if b.is_alive()]:
            # Build candidate lists
            special_candidates = [
                self.abilities[ability_id]
                for ability_id in bot.abilities
                if ability_id in self.abilities
                and self.abilities[ability_id].type == AbilityType.SPECIAL
                and bot.cooldowns.get(ability_id, 0) == 0
            ]

            ultimate_candidate = next(
                (
                    self.abilities[ability_id]
                    for ability_id in bot.abilities
                    if ability_id in self.abilities
                    and self.abilities[ability_id].type == AbilityType.ULTIMATE
                    and bot.cooldowns.get(ability_id, 0) == 0
                ),
                None,
            )

            normal_candidate = next(
                (
                    self.abilities[ability_id]
                    for ability_id in bot.abilities
                    if ability_id in self.abilities
                    and self.abilities[ability_id].type == AbilityType.NORMAL
                ),
                None,
            )

            ability = None
            # Use Ultimate only if charged
            if ultimate_candidate is not None and getattr(bot, "is_ultimate_ready", False):
                ability = ultimate_candidate
            else:
                # Prefer Special when available; if bot has 1 charge prefer Special to help unlock
                if special_candidates:
                    ability = max(special_candidates, key=lambda a: getattr(a, "damage", 0))
                elif normal_candidate is not None:
                    ability = normal_candidate

            if ability is None:
                continue

            if ability.type == AbilityType.ULTIMATE:
                targets = [character for character in player_team if character.is_alive()]
            else:
                alive_players = [c for c in player_team if c.is_alive()]
                if not alive_players:
                    targets = []
                else:
                    target = min(alive_players, key=lambda c: (c.current_hp, c.name))
                    targets = [target]

            plans.append(PlannedAction(actor=bot, ability=ability, targets=targets))

        return plans
