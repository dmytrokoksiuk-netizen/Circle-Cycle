"""Application settings loaded from environment or defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    data_dir: Path = field(default_factory=lambda: _resolve_data_dir())
    window_title: str = "Circle Cycle"
    window_width: int = 1200
    window_height: int = 760
    bg_color: str = "#111827"


def _resolve_data_dir() -> Path:
    """Resolve the data directory from environment or default location."""
    env_path = os.environ.get("CIRCLE_CYCLE_DATA_DIR")
    if env_path:
        return Path(env_path).resolve()
    return Path(__file__).resolve().parents[4] / "data"
