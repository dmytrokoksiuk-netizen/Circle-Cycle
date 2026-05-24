from __future__ import annotations

import random

from game.ability import Ability
from game.character import Character


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
            and self.abilities[ability_id].type != "normal"
            and bot.cooldowns.get(ability_id, 0) == 0
        ]

        if special_candidates:
            ability = max(special_candidates, key=lambda ability: ability.damage)
        else:
            ability = next(
                (self.abilities[ability_id] for ability_id in bot.abilities if ability_id in self.abilities and self.abilities[ability_id].type == "normal"),
                None,
            )

        if ability is None:
            raise ValueError(f"No valid ability found for bot character {bot.name}.")

        targets = [target]
        if ability.type == "ultimate":
            targets = [character for character in player_team if character.is_alive()]

        return bot, ability, targets
