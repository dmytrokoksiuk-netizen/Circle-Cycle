"""Value object representing a planned action chosen during the planning phase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from circle_cycle.domain.entities.character import Character
from circle_cycle.domain.entities.ability import Ability


@dataclass(frozen=True)
class PlannedAction:
    """Represents a single action planned by a character.

    Attributes:
        actor: The character performing the action.
        ability: The ability being used.
        targets: The resolved target list for the ability at planning time.
    """

    actor: Character
    ability: Ability
    targets: List[Character]
