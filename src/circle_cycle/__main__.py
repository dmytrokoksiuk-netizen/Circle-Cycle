"""Entry point for the Circle Cycle application."""

from __future__ import annotations

from circle_cycle.infrastructure.config.settings import Settings
from circle_cycle.infrastructure.persistence.repositories.json_data_repository import (
    JsonDataRepository,
)
from circle_cycle.infrastructure.ui.app import App


def main() -> None:
    """Bootstrap and launch the Circle Cycle game."""
    settings = Settings()
    repository = JsonDataRepository(settings.data_dir)
    app = App(repository, settings)
    app.run()


if __name__ == "__main__":
    main()
