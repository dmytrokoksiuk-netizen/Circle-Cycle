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

    Mana is expected to have been spent before calling this function.
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

    if ability.effect == StatusEffect.BURN:
        for target in targets:
            target.status_effects.append(StatusEffect.BURN)
            logs.append(
                f"{target.name} is burned by {ability.name} and will take 5 damage each turn."
            )
            applied = True

    if ability.type == AbilityType.ULTIMATE and len(targets) > 1:
        for target in targets:
            result = target.take_damage(effective_damage)
            if result["shield_damage"] > 0 or result["hp_damage"] > 0:
                applied = True
            log_line = _format_damage_log(attacker, target, ability, effective_damage, result)
            logs.append(log_line)
            if result["shield_broken"]:
                logs.append(f"{target.name}'s shield is broken!")
        # Reset ultimate charge for attacker
        attacker.reset_special_count()
        logs.append(f"{attacker.name} unleashes {ability.name}! Charge reset.")
        return logs

    for target in targets:
        result = target.take_damage(effective_damage)
        if result["shield_damage"] > 0 or result["hp_damage"] > 0:
            applied = True
        log_line = _format_damage_log(attacker, target, ability, effective_damage, result)
        logs.append(log_line)
        if result["shield_broken"]:
            logs.append(f"{target.name}'s shield is broken!")

    # After resolving, update special-use charge for Special abilities
    if ability.type == AbilityType.SPECIAL and applied:
        attacker.increment_special_count()
        logs.append(
            f"{attacker.name} uses {ability.name}! Ultimate charge: {attacker.special_use_count}/{ULTIMATE_CHARGE_REQUIRED}"
        )
        if attacker.is_ultimate_ready:
            logs.append(f"{attacker.name}'s Ultimate is now READY!")

    return logs


def _format_damage_log(
    attacker: Character,
    target: Character,
    ability: Ability,
    effective_damage: int,
    result: dict[str, int | bool],
) -> str:
    """Format a damage log line based on the damage result breakdown."""
    shield_dmg = result["shield_damage"]
    hp_dmg = result["hp_damage"]
    total = shield_dmg + hp_dmg

    if total == 0:
        return f"{target.name}'s shield blocks {ability.name}."

    if shield_dmg > 0 and hp_dmg > 0:
        return (
            f"{attacker.name} hits {target.name} for {total} damage with {ability.name} "
            f"({shield_dmg} absorbed by shield, {hp_dmg} to HP)."
        )
    if shield_dmg > 0:
        return (
            f"{attacker.name} hits {target.name} for {shield_dmg} damage with {ability.name} "
            f"(absorbed by shield)."
        )
    return (
        f"{attacker.name} hits {target.name} for {hp_dmg} damage with {ability.name}."
    )
