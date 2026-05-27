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
            and (
                self.abilities[ability_id].type != AbilityType.ULTIMATE
                or bot.can_use_ultimate()
            )
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
