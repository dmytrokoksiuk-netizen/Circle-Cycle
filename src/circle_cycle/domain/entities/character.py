"""Domain entity representing a playable or enemy character."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

from circle_cycle.domain.constants.game import BURN_DAMAGE_PER_STACK
from circle_cycle.domain.enums.character_size import CharacterSize
from circle_cycle.domain.enums.status_effect import StatusEffect
from circle_cycle.domain.exceptions.battle import InsufficientManaError


class DamageResult(TypedDict):
    """Breakdown of damage applied to a character."""

    shield_damage: int
    hp_damage: int
    shield_broken: bool


class ActiveEffect(TypedDict):
    """A timed stat modifier (buff or debuff)."""

    stat: str
    amount: int
    turns: int


@dataclass
class Character:
    """Represents a playable or enemy character in the battle system."""

    id: str
    name: str
    size: CharacterSize
    hp: int
    attack: int
    speed: int
    color: str
    abilities: list[str]
    max_mana: int = 0
    max_shield: int = 0
    role: str = "dps"
    current_hp: int = field(init=False)
    mana: int = field(init=False)
    shield: int = field(init=False)
    status_effects: list[StatusEffect] = field(default_factory=list)
    cooldowns: dict[str, int] = field(default_factory=dict)
    active_buffs: list[ActiveEffect] = field(default_factory=list)
    active_debuffs: list[ActiveEffect] = field(default_factory=list)
    # Number of times Special has been used (persists across turns within a battle)
    special_use_count: int = 0

    def __post_init__(self) -> None:
        """Initialize mutable state after dataclass construction."""
        self.current_hp = self.hp
        self.mana = self.max_mana
        self.shield = self.max_shield
        self.cooldowns = {ability_id: 0 for ability_id in self.abilities}

    # --- Effective stat properties (base + buffs - debuffs) ---
    @property
    def effective_attack(self) -> int:
        """Return attack stat including active buffs and debuffs."""
        buff_total = sum(e["amount"] for e in self.active_buffs if e["stat"] == "attack")
        debuff_total = sum(e["amount"] for e in self.active_debuffs if e["stat"] == "attack")
        return max(0, self.attack + buff_total - debuff_total)

    @property
    def effective_speed(self) -> int:
        """Return speed stat including active buffs and debuffs."""
        buff_total = sum(e["amount"] for e in self.active_buffs if e["stat"] == "speed")
        debuff_total = sum(e["amount"] for e in self.active_debuffs if e["stat"] == "speed")
        return max(1, self.speed + buff_total - debuff_total)

    def apply_buff(self, stat: str, amount: int, duration: int) -> None:
        """Apply a timed buff to this character."""
        self.active_buffs.append({"stat": stat, "amount": amount, "turns": duration})

    def apply_debuff(self, stat: str, amount: int, duration: int) -> None:
        """Apply a timed debuff to this character."""
        self.active_debuffs.append({"stat": stat, "amount": amount, "turns": duration})

    def tick_buffs_debuffs(self) -> list[str]:
        """Decrement durations and remove expired effects. Returns expiration log lines."""
        logs: list[str] = []
        remaining_buffs: list[ActiveEffect] = []
        for buff in self.active_buffs:
            buff["turns"] -= 1
            if buff["turns"] <= 0:
                logs.append(f"{self.name}'s {buff['stat'].upper()} +{buff['amount']} buff expired.")
            else:
                remaining_buffs.append(buff)
        self.active_buffs = remaining_buffs

        remaining_debuffs: list[ActiveEffect] = []
        for debuff in self.active_debuffs:
            debuff["turns"] -= 1
            if debuff["turns"] <= 0:
                logs.append(f"{self.name}'s {debuff['stat'].upper()} -{debuff['amount']} debuff expired.")
            else:
                remaining_debuffs.append(debuff)
        self.active_debuffs = remaining_debuffs
        return logs

    def take_damage(self, amount: int) -> DamageResult:
        """Apply damage to the character. Shield absorbs first, then HP.

        Returns a breakdown of damage distributed between shield and HP.
        """
        result: DamageResult = {"shield_damage": 0, "hp_damage": 0, "shield_broken": False}

        if amount <= 0:
            return result

        # One-shot StatusEffect.SHIELD blocks all damage
        if StatusEffect.SHIELD in self.status_effects:
            self.status_effects.remove(StatusEffect.SHIELD)
            return result

        # Numeric shield absorbs damage first
        if self.shield > 0:
            shield_damage = min(self.shield, amount)
            self.shield -= shield_damage
            amount -= shield_damage
            result["shield_damage"] = shield_damage
            if self.shield == 0:
                result["shield_broken"] = True

        # Remaining damage goes to HP
        if amount > 0:
            self.current_hp = max(0, self.current_hp - amount)
            result["hp_damage"] = amount

        return result

    def take_direct_damage(self, amount: int) -> int:
        """Apply damage directly to HP, bypassing shield. Returns HP damage dealt."""
        if amount <= 0:
            return 0
        actual = min(self.current_hp, amount)
        self.current_hp = max(0, self.current_hp - amount)
        return actual

    def restore_shield(self, amount: int) -> int:
        """Restore shield points, capped at max_shield. Returns amount restored."""
        if amount <= 0 or self.max_shield == 0:
            return 0
        old = self.shield
        self.shield = min(self.max_shield, self.shield + amount)
        return self.shield - old

    def heal(self, amount: int) -> int:
        """Heal the character and return the resulting current HP."""
        if amount <= 0:
            return 0

        self.current_hp = min(self.hp, self.current_hp + amount)
        return self.current_hp

    def is_alive(self) -> bool:
        """Return whether the character still has HP remaining."""
        return self.current_hp > 0

    def tick_cooldowns(self) -> None:
        """Reduce every cooldown by one turn."""
        for ability_id, value in list(self.cooldowns.items()):
            if value > 0:
                self.cooldowns[ability_id] = value - 1

    def tick_status_effects(self) -> int:
        """Apply burn damage directly to HP (bypasses shield) and return total damage."""
        burn_count = self.status_effects.count(StatusEffect.BURN)
        if burn_count == 0:
            return 0

        for _ in range(burn_count):
            self.status_effects.remove(StatusEffect.BURN)

        damage = burn_count * BURN_DAMAGE_PER_STACK
        self.take_direct_damage(damage)
        return damage

    # --- Mana helpers ---
    def spend_mana(self, amount: int) -> None:
        """Subtract mana. Raises InsufficientManaError if insufficient."""
        if amount <= 0:
            return
        if self.mana < amount:
            raise InsufficientManaError(
                f"{self.name} needs {amount} mana but only has {self.mana}."
            )
        self.mana -= amount

    def restore_mana(self, amount: int) -> None:
        """Add mana, capped at max_mana."""
        if amount <= 0:
            return
        self.mana = min(self.max_mana, self.mana + amount)

    def can_afford_ability(self, mana_cost: int) -> bool:
        """Check if character has enough mana for an ability."""
        return self.mana >= mana_cost

    # --- Ultimate charge helpers ---
    @property
    def is_ultimate_ready(self) -> bool:
        """Return whether this character has accumulated enough Special uses for Ultimate."""
        from circle_cycle.domain.constants.game import ULTIMATE_CHARGE_REQUIRED

        return self.special_use_count >= ULTIMATE_CHARGE_REQUIRED

    def increment_special_count(self) -> None:
        """Increment the Special-use charge counter for this character."""
        self.special_use_count += 1

    def reset_special_count(self) -> None:
        """Reset the Special-use charge counter (after Ultimate use or at battle start)."""
        self.special_use_count = 0
