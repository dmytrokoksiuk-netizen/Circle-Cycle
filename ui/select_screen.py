from __future__ import annotations

import tkinter as tk

from game.character import Character


class SelectScreen(tk.Frame):
    """Frame used to select up to three player characters."""

    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg="#111827")
        self.app = app
        self.selected_ids: list[str] = []
        self.character_buttons: dict[str, tk.Frame] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        """Create the selection screen widgets."""
        title = tk.Label(
            self,
            text="Choose your team",
            bg="#111827",
            fg="white",
            font=("Arial", 20, "bold"),
        )
        title.pack(pady=(24, 12))

        subtitle = tk.Label(
            self,
            text="Select exactly 3 characters to begin the battle.",
            bg="#111827",
            fg="#cbd5e1",
            font=("Arial", 12),
        )
        subtitle.pack(pady=(0, 24))

        grid = tk.Frame(self, bg="#111827")
        grid.pack(fill="both", expand=True)

        for index, character in enumerate(self.app.character_pool.values()):
            row = index // 3
            column = index % 3
            button_frame = tk.Frame(grid, bg="#111827", bd=2, relief="solid")
            button_frame.grid(row=row, column=column, padx=12, pady=12, sticky="nsew")
            self.character_buttons[character.id] = button_frame

            button = tk.Button(
                button_frame,
                text=f"{character.name}\nHP: {character.hp}\nATK: {character.attack}\nSPD: {character.speed}",
                bg=character.color,
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                activebackground=character.color,
                command=lambda chosen=character.id: self.toggle_selection(chosen),
            )
            button.pack(fill="both", expand=True)

        self.confirm_button = tk.Button(
            self,
            text="Confirm Selection",
            state="disabled",
            bg="#2563eb",
            fg="white",
            font=("Arial", 14, "bold"),
            command=self.confirm_selection,
        )
        self.confirm_button.pack(pady=20)

    def toggle_selection(self, character_id: str) -> None:
        """Toggle a character selection and refresh the button highlights."""
        if character_id in self.selected_ids:
            self.selected_ids.remove(character_id)
        elif len(self.selected_ids) < 3:
            self.selected_ids.append(character_id)

        self._refresh_highlights()
        self.confirm_button.config(state="normal" if len(self.selected_ids) == 3 else "disabled")

    def confirm_selection(self) -> None:
        """Start a battle using the selected characters."""
        if len(self.selected_ids) != 3:
            return

        self.app.start_battle(self.selected_ids)

    def _refresh_highlights(self) -> None:
        """Update the visual highlight for selected characters."""
        for character_id, frame in self.character_buttons.items():
            if character_id in self.selected_ids:
                frame.configure(highlightbackground="#facc15", highlightthickness=4)
            else:
                frame.configure(highlightbackground="#94a3b8", highlightthickness=2)
