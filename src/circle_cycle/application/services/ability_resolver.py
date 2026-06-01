"""Application service for resolving ability effects."""

from __future__ import annotations

from circle_cycle.domain.constants.game import ATTACK_SCALING_DIVISOR, ULTIMATE_CHARGE_REQUIRED
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.status_effect import StatusEffect


def resolve_ability(attacker: Character, targets: list[Character], ability: Ability) -> list[str]:
    """Resolve an ability against the provided targets and return a log.

    This function also updates the attacker's special-use charge counter when a
    Special ability successfully applies (damage or effect) and resets the
    counter after an Ultimate is used.
    """
    if not targets:
        return [f"{attacker.name} used {ability.name}, but no targets were available."]

    logs: list[str] = []
    effective_damage = max(0, ability.damage + attacker.attack // ATTACK_SCALING_DIVISOR)

    applied = False  # whether the ability actually affected anyone (damage/effect)

    if ability.effect == StatusEffect.SHIELD:
        for target in targets:
            target.status_effects.append(StatusEffect.SHIELD)
            logs.append(f"{target.name} gains a shield from {ability.name}.")
            applied = True
        # Special-case: shield application still counts as having applied
        # Continue to post-processing below for charge updates

    if ability.effect == StatusEffect.BURN:
        for target in targets:
            target.status_effects.append(StatusEffect.BURN)
            logs.append(
                f"{target.name} is burned by {ability.name} and will take 5 damage each turn."
            )
            applied = True

    if ability.type == AbilityType.ULTIMATE and len(targets) > 1:
        for target in targets:
            if StatusEffect.SHIELD in target.status_effects:
                target.status_effects.remove(StatusEffect.SHIELD)
                logs.append(f"{target.name}'s shield blocks {ability.name}.")
                continue
            dealt = target.take_damage(effective_damage)
            if dealt > 0:
                applied = True
            logs.append(
                f"{attacker.name} hits {target.name} for {effective_damage} "
                f"damage with {ability.name}."
            )
        # Reset ultimate charge for attacker
        attacker.reset_special_count()
        logs.append(f"{attacker.name} unleashes {ability.name}! Charge reset.")
        return logs

    for target in targets:
        if StatusEffect.SHIELD in target.status_effects:
            target.status_effects.remove(StatusEffect.SHIELD)
            logs.append(f"{target.name}'s shield blocks {ability.name}.")
            continue
        dealt = target.take_damage(effective_damage)
        if dealt > 0:
            applied = True
        logs.append(
            f"{attacker.name} hits {target.name} for {effective_damage} damage with {ability.name}."
        )

    # After resolving, update special-use charge for Special abilities
    if ability.type == AbilityType.SPECIAL and applied:
        attacker.increment_special_count()
        logs.append(
            f"{attacker.name} uses {ability.name}! Ultimate charge: {attacker.special_use_count}/{ULTIMATE_CHARGE_REQUIRED}"
        )
        if attacker.is_ultimate_ready:
            logs.append(f"{attacker.name}'s Ultimate is now READY!")

    return logs
