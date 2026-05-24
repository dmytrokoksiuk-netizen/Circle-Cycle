from __future__ import annotations

import tkinter as tk

from game.card import Card


class CardScreen(tk.Frame):
    """Frame used for selecting a card and assigning it to a player character."""

    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg="#111827")
        self.app = app
        self.selected_card: Card | None = None
        self.selected_target = None
        self.card_panels: dict[str, tk.Frame] = {}
        self.target_buttons: dict[str, tk.Button] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        """Create the card screen widgets."""
        title = tk.Label(
            self,
            text="Choose a card",
            bg="#111827",
            fg="white",
            font=("Arial", 18, "bold"),
        )
        title.pack(pady=(20, 8))

        self.card_container = tk.Frame(self, bg="#111827")
        self.card_container.pack(fill="x", padx=24, pady=12)

        self.target_container = tk.Frame(self, bg="#111827")
        self.target_container.pack(fill="x", padx=24, pady=12)

        self.confirm_button = tk.Button(
            self,
            text="Apply Card",
            state="disabled",
            bg="#16a34a",
            fg="white",
            font=("Arial", 14, "bold"),
            command=self.apply_card,
        )
        self.confirm_button.pack(pady=20)

    def refresh(self) -> None:
        """Refresh the card choices and target buttons."""
        if self.app.engine is None:
            return

        for widget in self.card_container.winfo_children():
            widget.destroy()

        for widget in self.target_container.winfo_children():
            widget.destroy()

        self.card_panels = {}
        self.target_buttons = {}
        self.selected_card = None
        self.selected_target = None

        cards = self.app.engine.get_card_choices()
        for index, card in enumerate(cards):
            panel = tk.Frame(
                self.card_container,
                bg="#1f2937",
                bd=2,
                relief="solid",
                highlightbackground="#94a3b8",
                highlightthickness=2,
            )
            panel.grid(row=0, column=index, padx=8, sticky="nsew")
            self.card_panels[card.id] = panel

            tk.Label(
                panel,
                text=card.name,
                bg="#1f2937",
                fg="white",
                font=("Arial", 12, "bold"),
            ).pack(padx=12, pady=(10, 4))
            tk.Label(
                panel,
                text=card.description,
                bg="#1f2937",
                fg="#cbd5e1",
                wraplength=240,
                justify="left",
            ).pack(padx=12, pady=(0, 10))

            panel.bind("<Button-1>", lambda event, chosen=card: self.select_card(chosen))

        for index, character in enumerate(self.app.engine.player_team):
            button = tk.Button(
                self.target_container,
                text=f"{character.name}\nHP {character.current_hp}/{character.hp}",
                bg=character.color,
                fg="white",
                font=("Arial", 12, "bold"),
                command=lambda chosen=character: self.select_target(chosen),
            )
            button.grid(row=0, column=index, padx=8)
            self.target_buttons[character.id] = button

        self.confirm_button.config(state="disabled")

    def select_card(self, card: Card) -> None:
        """Select a card and highlight the matching panel."""
        self.selected_card = card
        for card_id, panel in self.card_panels.items():
            if card_id == card.id:
                panel.configure(highlightbackground="#facc15", highlightthickness=4)
            else:
                panel.configure(highlightbackground="#94a3b8", highlightthickness=2)

        self._update_confirm_state()

    def select_target(self, target) -> None:
        """Select a player character to receive the chosen card."""
        self.selected_target = target
        for character_id, button in self.target_buttons.items():
            if character_id == target.id:
                button.config(relief="solid", bd=4)
            else:
                button.config(relief="flat", bd=1)

        self._update_confirm_state()

    def _update_confirm_state(self) -> None:
        """Enable the apply button when both card and target are selected."""
        if self.selected_card is not None and self.selected_target is not None:
            self.confirm_button.config(state="normal")
        else:
            self.confirm_button.config(state="disabled")

    def apply_card(self) -> None:
        """Apply the selected card and return to the battle screen."""
        if self.app.engine is None or self.selected_card is None or self.selected_target is None:
            return

        log = self.app.engine.apply_card_choice(self.selected_card, self.selected_target)
        self.app.battle_screen.log_messages.append(log)
        self.app.battle_screen.refresh()
        self.app.show_battle()
