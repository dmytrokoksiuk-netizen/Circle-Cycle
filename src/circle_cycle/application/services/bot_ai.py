"""Application service implementing bot combat AI heuristics."""

from __future__ import annotations

from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.target_type import TargetType


class BotAI:
    """Select bot actions using a simple combat heuristic."""

    def __init__(self, abilities: dict[str, Ability]) -> None:
        self.abilities = abilities

    def _resolve_targets(
        self, bot: Character, ability: Ability, bot_team: list[Character], player_team: list[Character]
    ) -> list[Character]:
        """Resolve target list for an ability based on its target_type."""
        target_type = getattr(ability, "target_type", TargetType.SINGLE_ENEMY)

        if target_type == TargetType.ALL_ENEMIES:
            return [c for c in player_team if c.is_alive()]
        elif target_type == TargetType.ALL_ALLIES:
            return [c for c in bot_team if c.is_alive()]
        elif target_type == TargetType.SINGLE_ALLY:
            alive_allies = [c for c in bot_team if c.is_alive()]
            if not alive_allies:
                return []
            # Heal: target lowest HP ally; Buff: target highest ATK ally
            if ability.heal_amount > 0:
                return [min(alive_allies, key=lambda c: c.current_hp)]
            return [max(alive_allies, key=lambda c: c.effective_attack)]
        elif target_type == TargetType.SELF:
            return [bot] if bot.is_alive() else []
        else:
            # SINGLE_ENEMY
            alive_enemies = [c for c in player_team if c.is_alive()]
            if not alive_enemies:
                return []
            # Shield pierce/destroy: target enemy with most shield
            if ability.shield_pierce or ability.shield_destroy > 0:
                return [max(alive_enemies, key=lambda c: c.shield)]
            return [min(alive_enemies, key=lambda c: (c.current_hp, c.name))]

    def choose_action(
        self, bot_team: list[Character], player_team: list[Character]
    ) -> tuple[Character, Ability, list[Character]]:
        """Choose a bot action and return the attacker, ability, and targets."""
        alive_bots = [character for character in bot_team if character.is_alive()]
        if not alive_bots:
            raise ValueError("Bot team has no alive characters.")

        bot = max(alive_bots, key=lambda character: character.speed)

        special_candidates = [
            self.abilities[ability_id]
            for ability_id in bot.abilities
            if ability_id in self.abilities
            and self.abilities[ability_id].type != AbilityType.NORMAL
            and bot.cooldowns.get(ability_id, 0) == 0
            and bot.can_afford_ability(self.abilities[ability_id].mana_cost)
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

        targets = self._resolve_targets(bot, ability, bot_team, player_team)
        return bot, ability, targets

    def generate_plan(self, bot_team: list[Character], player_team: list[Character]) -> list["PlannedAction"]:
        """Generate a planned action for each living bot character.

        Bot will only use Ultimate if the character's charge counter indicates it's ready.
        Prefer Special over Normal when charge is 1 to help unlock Ultimate.
        Checks mana affordability before selecting abilities.
        Uses target_type to determine proper targeting (ally vs enemy).
        """
        from circle_cycle.domain.value_objects.planned_action import PlannedAction

        plans: list[PlannedAction] = []
        for bot in [b for b in bot_team if b.is_alive()]:
            # Build candidate lists (mana-aware)
            special_candidates = [
                self.abilities[ability_id]
                for ability_id in bot.abilities
                if ability_id in self.abilities
                and self.abilities[ability_id].type == AbilityType.SPECIAL
                and bot.cooldowns.get(ability_id, 0) == 0
                and bot.can_afford_ability(self.abilities[ability_id].mana_cost)
            ]

            ultimate_candidate = next(
                (
                    self.abilities[ability_id]
                    for ability_id in bot.abilities
                    if ability_id in self.abilities
                    and self.abilities[ability_id].type == AbilityType.ULTIMATE
                    and bot.cooldowns.get(ability_id, 0) == 0
                    and bot.can_afford_ability(self.abilities[ability_id].mana_cost)
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
            # Use Ultimate only if charged and affordable
            if ultimate_candidate is not None and getattr(bot, "is_ultimate_ready", False):
                ability = ultimate_candidate
            else:
                # Prefer Special when available and affordable
                if special_candidates:
                    # For healers: prefer heal if any ally is below 60% HP
                    heal_ability = next((a for a in special_candidates if a.heal_amount > 0), None)
                    if heal_ability:
                        hurt_allies = [c for c in bot_team if c.is_alive() and c.current_hp < c.hp * 0.6]
                        if hurt_allies:
                            ability = heal_ability
                    if ability is None:
                        ability = max(special_candidates, key=lambda a: getattr(a, "damage", 0))
                elif normal_candidate is not None:
                    ability = normal_candidate

            if ability is None:
                # Fallback: always use Normal Attack (free)
                if normal_candidate is not None:
                    ability = normal_candidate
                else:
                    continue

            targets = self._resolve_targets(bot, ability, bot_team, player_team)
            if not targets:
                continue

            plans.append(PlannedAction(actor=bot, ability=ability, targets=targets))

        return plans
