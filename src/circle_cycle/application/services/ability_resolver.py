"""Application service for resolving ability effects."""

from __future__ import annotations

from circle_cycle.domain.constants.game import ATTACK_SCALING_DIVISOR, ULTIMATE_CHARGE_REQUIRED
from circle_cycle.domain.entities.ability import Ability
from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.enums.ability_type import AbilityType
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.enums.target_type import TargetType


def resolve_ability(attacker: Character, targets: list[Character], ability: Ability) -> list[str]:
    """Resolve an ability against the provided targets and return a log.

    Handles damage, healing, buffs, debuffs, shield pierce, and shield destroy.
    Updates the attacker's special-use charge counter for Special abilities
    and resets the counter after an Ultimate is used.

    Mana is expected to have been spent before calling this function.
    """
    if not targets:
        return [f"{attacker.name} used {ability.name}, but no targets were available."]

    logs: list[str] = []
    applied = False

    # --- Heal ---
    if ability.heal_amount > 0:
        for target in targets:
            old_hp = target.current_hp
            target.heal(ability.heal_amount)
            healed = target.current_hp - old_hp
            if healed > 0:
                applied = True
                logs.append(f"{attacker.name} uses {ability.name} → {target.name} for +{healed} HP.")
            else:
                logs.append(f"{attacker.name} uses {ability.name} → {target.name} (already full HP).")

    # --- Shield Restore ---
    if ability.shield_restore > 0:
        for target in targets:
            restored = target.restore_shield(ability.shield_restore)
            if restored > 0:
                applied = True
                logs.append(f"{attacker.name} uses {ability.name} → {target.name} restores {restored} shield.")

    # --- Buff ---
    if ability.buff_stat and ability.buff_amount > 0:
        for target in targets:
            target.apply_buff(ability.buff_stat, ability.buff_amount, ability.buff_duration)
            applied = True
            logs.append(
                f"{attacker.name} uses {ability.name} → {target.name} "
                f"({ability.buff_stat.upper()} +{ability.buff_amount} for {ability.buff_duration}t)."
            )

    # --- Debuff ---
    if ability.debuff_stat and ability.debuff_amount > 0:
        for target in targets:
            target.apply_debuff(ability.debuff_stat, ability.debuff_amount, ability.debuff_duration)
            applied = True
            logs.append(
                f"{attacker.name} uses {ability.name} → {target.name} "
                f"({ability.debuff_stat.upper()} -{ability.debuff_amount} for {ability.debuff_duration}t)."
            )

    # --- Shield Destroy ---
    if ability.shield_destroy > 0:
        for target in targets:
            destroyed = min(target.shield, ability.shield_destroy)
            if destroyed > 0:
                target.shield -= destroyed
                applied = True
                logs.append(f"{attacker.name} uses {ability.name} → {target.name} loses {destroyed} shield!")
            if target.shield == 0 and destroyed > 0:
                logs.append(f"{target.name}'s shield is broken!")

    # --- Status Effects (burn, one-shot shield) ---
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

    # --- Damage ---
    if ability.damage > 0:
        effective_damage = max(0, ability.damage + attacker.effective_attack // ATTACK_SCALING_DIVISOR)

        if ability.shield_pierce:
            # Shield-piercing: damage goes directly to HP
            for target in targets:
                dealt = target.take_direct_damage(effective_damage)
                if dealt > 0:
                    applied = True
                logs.append(
                    f"{attacker.name} uses {ability.name} → {target.name} for {effective_damage} damage "
                    f"(ignores shield)."
                )
        else:
            # Normal damage flow
            for target in targets:
                result = target.take_damage(effective_damage)
                if result["shield_damage"] > 0 or result["hp_damage"] > 0:
                    applied = True
                log_line = _format_damage_log(attacker, target, ability, effective_damage, result)
                logs.append(log_line)
                if result["shield_broken"]:
                    logs.append(f"{target.name}'s shield is broken!")

    # --- Ultimate charge management ---
    if ability.type == AbilityType.ULTIMATE:
        attacker.reset_special_count()
        logs.append(f"{attacker.name} unleashes {ability.name}! Charge reset.")
    elif ability.type == AbilityType.SPECIAL and applied:
        attacker.increment_special_count()
        logs.append(
            f"{attacker.name} uses {ability.name}! Ultimate charge: "
            f"{attacker.special_use_count}/{ULTIMATE_CHARGE_REQUIRED}"
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
    """Format a damage log line showing attacker → target with damage breakdown."""
    shield_dmg = result["shield_damage"]
    hp_dmg = result["hp_damage"]
    total = shield_dmg + hp_dmg

    if total == 0:
        return f"{attacker.name} uses {ability.name} → {target.name} (blocked by shield)."

    if shield_dmg > 0 and hp_dmg > 0:
        return (
            f"{attacker.name} uses {ability.name} → {target.name} for {total} damage "
            f"({shield_dmg} absorbed by shield, {hp_dmg} to HP)."
        )
    if shield_dmg > 0:
        return (
            f"{attacker.name} uses {ability.name} → {target.name} for {shield_dmg} damage "
            f"(absorbed by shield)."
        )
    return (
        f"{attacker.name} uses {ability.name} → {target.name} for {hp_dmg} damage."
    )
