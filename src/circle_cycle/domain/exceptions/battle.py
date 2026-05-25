"""Domain-specific exceptions for the battle system."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain-level errors."""


class BattleNotStartedError(DomainError):
    """Raised when an action is attempted before the battle starts."""


class InvalidActionError(DomainError):
    """Raised when an invalid combat action is requested."""


class InvalidTargetError(DomainError):
    """Raised when an action target is not valid."""


class AbilityOnCooldownError(DomainError):
    """Raised when an ability is still on cooldown."""


class DataLoadError(DomainError):
    """Raised when game data cannot be loaded."""
