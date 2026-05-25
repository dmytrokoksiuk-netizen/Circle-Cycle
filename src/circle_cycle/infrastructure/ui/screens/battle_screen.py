"""Battle screen displaying teams, log output, and action buttons."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from circle_cycle.infrastructure.ui.rendering.draw_character import draw_circle_character

if TYPE_CHECKING:
    from circle_cycle.infrastructure.ui.app import App


class BattleScreen(tk.Frame):
    """Main battle view showing both teams, log output, and action buttons."""

    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, bg="#111827")
        self.app = app
        self.log_messages: list[str] = []
        self._build_layout()

    def _build_layout(self) -> None:
        """Create the widgets used by the battle screen."""
        self.turn_label = tk.Label(
            self,
            text="Turn: player",
            bg="#111827",
            fg="white",
            font=("Arial", 16, "bold"),
        )
        self.turn_label.pack(pady=(12, 8))

        self.canvas = tk.Canvas(self, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        control_frame = tk.Frame(self, bg="#111827")
        control_frame.pack(fill="x", pady=(0, 12))

        self.normal_button = tk.Button(
            control_frame,
            text="Normal Attack",
            command=lambda: self.handle_action("normal"),
            bg="#0f766e",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.normal_button.pack(side="left", padx=8)

        self.special_button = tk.Button(
            control_frame,
            text="Special Attack",
            command=lambda: self.handle_action("special"),
            bg="#7c3aed",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.special_button.pack(side="left", padx=8)

        self.ultimate_button = tk.Button(
            control_frame,
            text="Ultimate",
            command=lambda: self.handle_action("ultimate"),
            bg="#dc2626",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.ultimate_button.pack(side="left", padx=8)

        log_frame = tk.Frame(self, bg="#111827")
        log_frame.pack(fill="x", padx=12, pady=(0, 12))

        log_title = tk.Label(
            log_frame,
            text="Battle Log",
            bg="#111827",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        log_title.pack(anchor="w")

        self.log_text = tk.Text(log_frame, height=6, bg="#0f172a", fg="white", wrap="word")
        self.log_text.pack(fill="x", pady=(6, 0))

    def refresh(self) -> None:
        """Refresh the battle view from the current engine state."""
        if self.app.engine is None:
            return

        self.canvas.delete("all")
        engine = self.app.engine
        player_x = 180
        bot_x = 900

        for index, character in enumerate(engine.player_team):
            draw_circle_character(self.canvas, player_x, 120 + index * 150, character)

        for index, character in enumerate(engine.bot_team):
            draw_circle_character(self.canvas, bot_x, 120 + index * 150, character)

        self._refresh_buttons()
        self._update_turn_label()
        self._refresh_log()

    def _update_turn_label(self) -> None:
        """Update the turn indicator text."""
        if self.app.engine is None:
            return

        current = self.app.engine.get_current_character()
        side = "player" if current in self.app.engine.player_team else "bot"
        self.turn_label.config(text=f"Turn: {current.name} ({side})")

    def _refresh_buttons(self) -> None:
        """Enable or disable action buttons based on current turn and cooldowns."""
        if self.app.engine is None:
            return

        current = self.app.engine.get_current_character()
        is_player_turn = current in self.app.engine.player_team

        for button, ability_type in (
            (self.normal_button, "normal"),
            (self.special_button, "special"),
            (self.ultimate_button, "ultimate"),
        ):
            button.config(state="normal" if is_player_turn else "disabled")

            ability = self.app.engine.get_ability_by_type(current, ability_type)
            if ability is None or current.cooldowns.get(ability.id, 0) > 0:
                button.config(state="disabled")

    def handle_action(self, ability_type: str) -> None:
        """Handle a player action request and advance the turn."""
        if self.app.engine is None:
            return

        engine = self.app.engine
        current = engine.get_current_character()
        if current not in engine.player_team:
            return

        ability = engine.get_ability_by_type(current, ability_type)
        if ability is None:
            return

        targets = engine.get_action_targets(current, ability)

        try:
            logs = engine.execute_action(current, ability, targets)
        except (ValueError, Exception) as error:
            self._append_logs([str(error)])
            return

        self._append_logs(logs)
        winner = engine.check_winner()
        if winner is not None:
            self._append_logs([f"{winner.title()} wins the battle!"])
            self.app.show_select()
            return

        round_ended = engine.end_turn()
        if round_ended:
            self.app.show_card()
            return

        if engine.get_current_character() in engine.bot_team:
            self._play_bot_turn()

        self.refresh()

    def _play_bot_turn(self) -> None:
        """Run the bot action and advance the turn."""
        if self.app.engine is None:
            return

        engine = self.app.engine
        logs = engine.bot_turn()
        self._append_logs(logs)
        winner = engine.check_winner()
        if winner is not None:
            self._append_logs([f"{winner.title()} wins the battle!"])
            self.app.show_select()
            return

        round_ended = engine.end_turn()
        if round_ended:
            self.app.show_card()
            return

        self.refresh()

    def _append_logs(self, logs: list[str]) -> None:
        """Append new log lines and keep only the most recent six events."""
        for log in logs:
            self.log_messages.append(log)

        self.log_messages = self.log_messages[-6:]
        self._refresh_log()

    def _refresh_log(self) -> None:
        """Redraw the battle log text widget."""
        self.log_text.delete("1.0", "end")
        for log in self.log_messages:
            self.log_text.insert("end", f"{log}\n")
        self.log_text.see("end")
