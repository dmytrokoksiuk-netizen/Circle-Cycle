"""Battle phase enumeration for the BattleEngine planning/execution flow."""

from __future__ import annotations

from enum import Enum


class BattlePhase(Enum):
    """Enumeration of the high-level battle phases.

    PLANNING: Players (and bots) select actions but nothing is executed yet.
    EXECUTION: Collected actions are being resolved sequentially.
    TURN_END: End-of-turn bookkeeping (cooldowns, status ticks, cards).
    """

    PLANNING = "planning"
    EXECUTION = "execution"
    TURN_END = "turn_end"
