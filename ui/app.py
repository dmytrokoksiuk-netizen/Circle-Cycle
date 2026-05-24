from __future__ import annotations

import tkinter as tk

from game.engine import BattleEngine
from game.loader import DataLoader
from ui.battle_screen import BattleScreen
from ui.card_screen import CardScreen
from ui.select_screen import SelectScreen


class App:
    """Top-level application controller for the Circle Cycle game."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Circle Cycle")
        self.root.geometry("1200x760")
        self.root.configure(bg="#111827")

        self.loader = DataLoader()
        self.character_pool = self.loader.load_characters()
        self.card_pool = self.loader.load_cards()

        self.engine: BattleEngine | None = None
        self.current_frame: tk.Frame | None = None

        self.select_screen = SelectScreen(self.root, self)
        self.battle_screen = BattleScreen(self.root, self)
        self.card_screen = CardScreen(self.root, self)

        self.show_select()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()

    def show_select(self) -> None:
        """Display the character selection screen."""
        self._show_frame(self.select_screen)

    def show_battle(self) -> None:
        """Display the battle screen."""
        if self.engine is None:
            raise ValueError("Battle engine has not been initialized.")
        self.battle_screen.refresh()
        self._show_frame(self.battle_screen)

    def show_card(self) -> None:
        """Display the card selection screen."""
        if self.engine is None:
            raise ValueError("Battle engine has not been initialized.")
        self.card_screen.refresh()
        self._show_frame(self.card_screen)

    def start_battle(self, selected_ids: list[str]) -> None:
        """Create a new battle from the selected characters and switch to battle view."""
        self.engine = BattleEngine.create_from_selection(selected_ids, self.character_pool, self.loader)
        self.engine.start_battle()
        self.show_battle()

    def _show_frame(self, frame: tk.Frame) -> None:
        """Display the requested frame and hide the active one."""
        if self.current_frame is not None:
            self.current_frame.pack_forget()

        frame.pack(fill="both", expand=True)
        self.current_frame = frame
