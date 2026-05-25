"""Application service for resolving ability effects."""

from __future__ import annotations

from circle_cycle.domain.constants.game import ATTACK_SCALING_DIVISOR
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.status_effect import StatusEffect


def resolve_ability(attacker: Character, targets: list[Character], ability: Ability) -> list[str]:
    """Resolve an ability against the provided targets and return a log."""
    if not targets:
        return [f"{attacker.name} used {ability.name}, but no targets were available."]

    logs: list[str] = []
    effective_damage = max(0, ability.damage + attacker.attack // ATTACK_SCALING_DIVISOR)

    if ability.effect == StatusEffect.SHIELD:
        for target in targets:
            target.status_effects.append(StatusEffect.SHIELD)
            logs.append(f"{target.name} gains a shield from {ability.name}.")
        return logs

    if ability.effect == StatusEffect.BURN:
        for target in targets:
            target.status_effects.append(StatusEffect.BURN)
            logs.append(
                f"{target.name} is burned by {ability.name} and will take 5 damage each turn."
            )

    if ability.type == AbilityType.ULTIMATE and len(targets) > 1:
        for target in targets:
            if StatusEffect.SHIELD in target.status_effects:
                target.status_effects.remove(StatusEffect.SHIELD)
                logs.append(f"{target.name}'s shield blocks {ability.name}.")
                continue
            target.take_damage(effective_damage)
            logs.append(
                f"{attacker.name} hits {target.name} for {effective_damage} "
                f"damage with {ability.name}."
            )
        return logs

    for target in targets:
        if StatusEffect.SHIELD in target.status_effects:
            target.status_effects.remove(StatusEffect.SHIELD)
            logs.append(f"{target.name}'s shield blocks {ability.name}.")
            continue
        target.take_damage(effective_damage)
        logs.append(
            f"{attacker.name} hits {target.name} for {effective_damage} damage with {ability.name}."
        )

    return logs
