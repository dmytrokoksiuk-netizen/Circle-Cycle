from __future__ import annotations

from dataclasses import dataclass

from game.character import Character


@dataclass(frozen=True)
class Ability:
    """Represents a single game ability loaded from JSON data."""

    id: str
    name: str
    type: str
    damage: int
    effect: str | None
    cooldown: int


def resolve_ability(attacker: Character, targets: list[Character], ability: Ability) -> list[str]:
    """Resolve an ability against the provided targets and return a log."""
    if not targets:
        return [f"{attacker.name} used {ability.name}, but no targets were available."]

    logs: list[str] = []
    effective_damage = max(0, ability.damage + attacker.attack // 5)

    if ability.effect == "shield":
        for target in targets:
            target.status_effects.append("shield")
            logs.append(f"{target.name} gains a shield from {ability.name}.")
        return logs

    if ability.effect == "burn":
        for target in targets:
            target.status_effects.append("burn")
            logs.append(
                f"{target.name} is burned by {ability.name} and will take 5 damage each turn."
            )

    if ability.type == "ultimate" and len(targets) > 1:
        for target in targets:
            if "shield" in target.status_effects:
                target.status_effects.remove("shield")
                logs.append(f"{target.name}'s shield blocks {ability.name}.")
                continue
            target.take_damage(effective_damage)
            logs.append(
                f"{attacker.name} hits {target.name} for {effective_damage} damage with {ability.name}."
            )
        return logs

    for target in targets:
        if "shield" in target.status_effects:
            target.status_effects.remove("shield")
            logs.append(f"{target.name}'s shield blocks {ability.name}.")
            continue
        target.take_damage(effective_damage)
        logs.append(
            f"{attacker.name} hits {target.name} for {effective_damage} damage with {ability.name}."
        )

    return logs
