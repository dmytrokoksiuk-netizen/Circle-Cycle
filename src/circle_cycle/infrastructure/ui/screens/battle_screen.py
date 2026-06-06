"""Battle screen displaying teams, log output, and action buttons."""

from __future__ import annotations

import re
import tkinter as tk
from typing import TYPE_CHECKING

from circle_cycle.domain.constants.game import TEAM_MAX_MANA
from circle_cycle.domain.enums.target_type import TargetType
from circle_cycle.infrastructure.ui.rendering.draw_character import (
    draw_circle_character,
    show_floating_number,
)

if TYPE_CHECKING:
    from circle_cycle.domain.entities.ability import Ability
    from circle_cycle.domain.entities.character import Character
    from circle_cycle.infrastructure.ui.app import App

# Layout constants
PLAYER_X = 180
BOT_X = 900
Y_BASE = 120
Y_STEP = 150
HIT_RADIUS = 55
BOT_ACTION_DELAY_MS = 800


class BattleScreen(tk.Frame):
    """Main battle view showing both teams, log output, and action buttons."""

    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, bg="#111827")
        self.app = app
        self.log_messages: list[str] = []
        self._pending_ability: Ability | None = None
        self._pending_actor: Character | None = None
        self._target_mode = False
        self._bot_acting = False
        self._build_layout()

    def _build_layout(self) -> None:
        """Create the widgets used by the battle screen."""
        # Top info bar: turn label + team mana
        top_frame = tk.Frame(self, bg="#111827")
        top_frame.pack(fill="x", pady=(8, 4))

        self.turn_label = tk.Label(
            top_frame, text="Turn: player", bg="#111827", fg="white",
            font=("Arial", 14, "bold"),
        )
        self.turn_label.pack(side="left", padx=12)

        self.enemy_mana_label = tk.Label(
            top_frame, text="Enemy Mana: 15/15", bg="#111827", fg="#f87171",
            font=("Arial", 11, "bold"),
        )
        self.enemy_mana_label.pack(side="right", padx=12)

        self.player_mana_label = tk.Label(
            top_frame, text="\u26a1 Team Mana: 15/15", bg="#111827", fg="#60a5fa",
            font=("Arial", 13, "bold"),
        )
        self.player_mana_label.pack(side="right", padx=12)

        # Instruction label (shown during target selection)
        self.instruction_label = tk.Label(
            self, text="", bg="#111827", fg="#fbbf24", font=("Arial", 12, "bold"),
        )

        # Canvas for characters
        self.canvas = tk.Canvas(self, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Control frame
        control_frame = tk.Frame(self, bg="#111827")
        control_frame.pack(fill="x", pady=(0, 8))

        self.normal_button = tk.Button(
            control_frame, text="Normal Attack (free)",
            command=lambda: self._select_ability("normal"),
            bg="#0f766e", fg="white", font=("Arial", 12, "bold"),
        )
        self.normal_button.pack(side="left", padx=8)

        self.special_button = tk.Button(
            control_frame, text="Special Attack",
            command=lambda: self._select_ability("special"),
            bg="#7c3aed", fg="white", font=("Arial", 12, "bold"),
        )
        self.special_button.pack(side="left", padx=8)

        self.ultimate_button = tk.Button(
            control_frame, text="Ultimate (free)",
            command=lambda: self._select_ability("ultimate"),
            bg="#dc2626", fg="white", font=("Arial", 12, "bold"),
        )
        self.ultimate_button.pack(side="left", padx=8)

        # Log frame
        log_frame = tk.Frame(self, bg="#111827")
        log_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(log_frame, text="Battle Log", bg="#111827", fg="white",
                 font=("Arial", 11, "bold")).pack(anchor="w")

        self.log_text = tk.Text(log_frame, height=5, bg="#0f172a", fg="white", wrap="word",
                                font=("Arial", 10))
        self.log_text.pack(fill="x", pady=(4, 0))

    # === Public entry point ===

    def on_enter(self) -> None:
        """Called when the battle screen becomes visible. Auto-plays bot turns if needed."""
        self._target_mode = False
        self._pending_ability = None
        self._pending_actor = None
        self._bot_acting = False
        self.refresh()
        if self.app.engine is None:
            return
        # If the current character is a bot, auto-play their turns with delays
        if self.app.engine.get_current_character() in self.app.engine.bot_team:
            self._schedule_bot_turn()

    # === Refresh / Drawing ===

    def refresh(self) -> None:
        """Refresh the battle view from the current engine state."""
        if self.app.engine is None:
            return

        self.canvas.delete("all")
        engine = self.app.engine

        for index, character in enumerate(engine.player_team):
            draw_circle_character(self.canvas, PLAYER_X, Y_BASE + index * Y_STEP, character)

        for index, character in enumerate(engine.bot_team):
            draw_circle_character(self.canvas, BOT_X, Y_BASE + index * Y_STEP, character)

        # Draw target highlights if in target selection mode
        if self._target_mode and self._pending_ability:
            self._draw_target_highlights()

        self._refresh_buttons()
        self._update_turn_label()
        self._update_mana_labels()
        self._refresh_log()

    def _draw_target_highlights(self) -> None:
        """Draw clickable target highlights based on ability target_type."""
        if self.app.engine is None or self._pending_ability is None:
            return
        engine = self.app.engine
        ability = self._pending_ability
        target_type = getattr(ability, "target_type", TargetType.SINGLE_ENEMY)

        if target_type in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES):
            for idx, ch in enumerate(engine.bot_team):
                if ch.is_alive():
                    x, y = BOT_X, Y_BASE + idx * Y_STEP
                    self.canvas.create_oval(
                        x - HIT_RADIUS, y - HIT_RADIUS,
                        x + HIT_RADIUS, y + HIT_RADIUS,
                        outline="#ef4444", width=3, dash=(6, 3),
                    )
        elif target_type in (TargetType.SINGLE_ALLY, TargetType.ALL_ALLIES):
            for idx, ch in enumerate(engine.player_team):
                if ch.is_alive():
                    x, y = PLAYER_X, Y_BASE + idx * Y_STEP
                    self.canvas.create_oval(
                        x - HIT_RADIUS, y - HIT_RADIUS,
                        x + HIT_RADIUS, y + HIT_RADIUS,
                        outline="#10b981", width=3, dash=(6, 3),
                    )

    def _update_turn_label(self) -> None:
        """Update the turn indicator text."""
        if self.app.engine is None:
            return
        current = self.app.engine.get_current_character()
        side = "player" if current in self.app.engine.player_team else "enemy"
        self.turn_label.config(text=f"Turn: {current.name} ({side})")

    def _update_mana_labels(self) -> None:
        """Update team mana display labels."""
        if self.app.engine is None:
            return
        engine = self.app.engine
        self.player_mana_label.config(
            text=f"\u26a1 Team Mana: {engine.player_team_mana}/{TEAM_MAX_MANA}"
        )
        self.enemy_mana_label.config(
            text=f"Enemy Mana: {engine.bot_team_mana}/{TEAM_MAX_MANA}"
        )

    def _refresh_buttons(self) -> None:
        """Enable or disable action buttons based on current turn, cooldowns, and team mana."""
        if self.app.engine is None:
            return

        engine = self.app.engine
        current = engine.get_current_character()
        is_player_turn = current in engine.player_team and not self._bot_acting

        for button, ability_type in (
            (self.normal_button, "normal"),
            (self.special_button, "special"),
            (self.ultimate_button, "ultimate"),
        ):
            button.config(state="normal" if is_player_turn else "disabled")

            ability = engine.get_ability_by_type(current, ability_type)
            if ability is None or current.cooldowns.get(ability.id, 0) > 0:
                button.config(state="disabled")
                continue

            # Ultimate gated by charge
            if ability.type.value == "ultimate" and not getattr(current, "is_ultimate_ready", False):
                button.config(state="disabled")
                continue

            # Team mana check
            if not engine.can_team_afford(current, ability.mana_cost):
                button.config(state="disabled")

            # Update button text with mana cost
            if ability.mana_cost > 0:
                button.config(text=f"{ability.name} ({ability.mana_cost} MP)")
            else:
                button.config(text=f"{ability.name} (free)")

        # If in target mode, disable buttons
        if self._target_mode:
            self.normal_button.config(state="disabled")
            self.special_button.config(state="disabled")
            self.ultimate_button.config(state="disabled")

    # === Player Action Flow (Fix 1: Target Selection) ===

    def _select_ability(self, ability_type: str) -> None:
        """Player clicks an ability button — enter target selection mode."""
        if self.app.engine is None:
            return
        engine = self.app.engine
        current = engine.get_current_character()
        if current not in engine.player_team:
            return

        ability = engine.get_ability_by_type(current, ability_type)
        if ability is None:
            return

        target_type = getattr(ability, "target_type", TargetType.SINGLE_ENEMY)

        # AoE abilities: auto-target all, skip selection
        if target_type == TargetType.ALL_ENEMIES:
            targets = [c for c in engine.bot_team if c.is_alive()]
            self._execute_player_action(current, ability, targets)
            return
        if target_type == TargetType.ALL_ALLIES:
            targets = [c for c in engine.player_team if c.is_alive()]
            self._execute_player_action(current, ability, targets)
            return
        if target_type == TargetType.SELF:
            self._execute_player_action(current, ability, [current])
            return

        # Single target: enter target selection mode
        self._pending_ability = ability
        self._pending_actor = current
        self._target_mode = True

        if target_type == TargetType.SINGLE_ALLY:
            self.instruction_label.config(text="Click an ally to target")
        else:
            self.instruction_label.config(text="Click an enemy to target")
        self.instruction_label.pack(pady=(2, 2))

        self.refresh()

    def _on_canvas_click(self, event: "tk.Event[tk.Canvas]") -> None:
        """Handle clicks on the canvas for target selection."""
        if not self._target_mode or self._pending_ability is None or self.app.engine is None:
            return

        engine = self.app.engine
        ability = self._pending_ability
        target_type = getattr(ability, "target_type", TargetType.SINGLE_ENEMY)

        # Determine which team to check for hit
        if target_type == TargetType.SINGLE_ALLY:
            team = engine.player_team
            base_x = PLAYER_X
        else:
            team = engine.bot_team
            base_x = BOT_X

        # Check if click is within any character's hit area
        for idx, character in enumerate(team):
            if not character.is_alive():
                continue
            cx = base_x
            cy = Y_BASE + idx * Y_STEP
            dx = event.x - cx
            dy = event.y - cy
            if (dx * dx + dy * dy) <= HIT_RADIUS * HIT_RADIUS:
                self._on_target_selected(character)
                return

    def _on_target_selected(self, target: "Character") -> None:
        """Target has been selected — execute the action."""
        if self._pending_actor is None or self._pending_ability is None:
            return

        actor = self._pending_actor
        ability = self._pending_ability

        # Exit target mode
        self._target_mode = False
        self._pending_ability = None
        self._pending_actor = None
        self.instruction_label.pack_forget()

        self._execute_player_action(actor, ability, [target])

    def _execute_player_action(
        self, actor: "Character", ability: "Ability", targets: list["Character"]
    ) -> None:
        """Execute a player action then advance the turn."""
        if self.app.engine is None:
            return
        engine = self.app.engine

        try:
            logs = engine.execute_action(actor, ability, targets)
        except Exception as error:
            self._append_logs([str(error)])
            self.refresh()
            return

        self._append_logs(logs)
        winner = engine.check_winner()
        if winner is not None:
            self._append_logs([f"{winner.title()} wins the battle!"])
            self.after(1200, self.app.show_select)
            return

        round_ended = engine.end_turn()
        if round_ended:
            self.app.show_card()
            return

        self.refresh()
        # If next character is a bot, schedule bot turns with delay
        if engine.get_current_character() in engine.bot_team:
            self._schedule_bot_turn()

    # === Bot Turn Flow (Fix 5: Delayed enemy actions) ===

    def _schedule_bot_turn(self) -> None:
        """Schedule a single bot turn after a delay for visual feedback."""
        self._bot_acting = True
        self._refresh_buttons()
        self.after(BOT_ACTION_DELAY_MS, self._execute_one_bot_turn)

    def _execute_one_bot_turn(self) -> None:
        """Execute one bot turn and schedule the next if needed."""
        if self.app.engine is None:
            self._bot_acting = False
            return

        engine = self.app.engine
        current = engine.get_current_character()
        if current not in engine.bot_team:
            self._bot_acting = False
            self.refresh()
            return

        # Highlight acting bot briefly
        bot_idx = engine.bot_team.index(current)
        bx, by = BOT_X, Y_BASE + bot_idx * Y_STEP
        self.canvas.create_oval(
            bx - HIT_RADIUS - 5, by - HIT_RADIUS - 5,
            bx + HIT_RADIUS + 5, by + HIT_RADIUS + 5,
            outline="#fbbf24", width=3,
        )

        logs = engine.bot_turn()
        self._append_logs(logs)

        winner = engine.check_winner()
        if winner is not None:
            self._append_logs([f"{winner.title()} wins the battle!"])
            self._bot_acting = False
            self.after(1200, self.app.show_select)
            return

        round_ended = engine.end_turn()
        if round_ended:
            self._bot_acting = False
            self.app.show_card()
            return

        self.refresh()

        # Check if next is still a bot — schedule another
        if engine.get_current_character() in engine.bot_team:
            self.after(BOT_ACTION_DELAY_MS, self._execute_one_bot_turn)
        else:
            self._bot_acting = False
            self.refresh()

    # === Log Display ===

    def _append_logs(self, logs: list[str]) -> None:
        """Append log lines, parse floating damage events, keep last 8 lines."""
        floating_events: list[tuple[str, str, str]] = []

        for log in logs:
            self.log_messages.append(log)

            # Shield broken event
            if "shield is broken" in log:
                tname = log.split("'s shield")[0]
                floating_events.append((tname, "SHIELD BROKEN!", "#f59e0b"))
                continue

            # Damage with shield absorption
            m_shield = re.search(
                r"\u2192 (.+?) for (\d+) damage.+?(\d+) absorbed by shield, (\d+) to HP", log
            )
            if m_shield:
                target_name = m_shield.group(1)
                shield_dmg = int(m_shield.group(3))
                hp_dmg = int(m_shield.group(4))
                floating_events.append((target_name, f"-{shield_dmg}", "#06b6d4"))
                floating_events.append((target_name, f"-{hp_dmg}", "#ef4444"))
                continue

            # Shield only
            m_shield_only = re.search(r"\u2192 (.+?) for (\d+) damage.+?\(absorbed by shield\)", log)
            if m_shield_only:
                target_name = m_shield_only.group(1)
                amount = int(m_shield_only.group(2))
                floating_events.append((target_name, f"-{amount}", "#06b6d4"))
                continue

            # Standard damage
            m = re.search(r"\u2192 (.+?) for (\d+) damage", log)
            if m:
                target_name = m.group(1)
                amount = int(m.group(2))
                floating_events.append((target_name, f"-{amount}", "#ef4444"))
                continue

            # Heal
            m_heal = re.search(r"\u2192 (.+?) for \+(\d+) HP", log)
            if m_heal:
                target_name = m_heal.group(1)
                amount = int(m_heal.group(2))
                floating_events.append((target_name, f"+{amount}", "#10b981"))
                continue

            # Buff
            m_buff = re.search(r"\u2192 (.+?) \((\w+) \+(\d+)", log)
            if m_buff:
                target_name = m_buff.group(1)
                stat_name = m_buff.group(2)
                amount = int(m_buff.group(3))
                floating_events.append((target_name, f"+{amount} {stat_name}", "#8b5cf6"))
                continue

            # Debuff
            m_debuff = re.search(r"\u2192 (.+?) \((\w+) -(\d+)", log)
            if m_debuff:
                target_name = m_debuff.group(1)
                stat_name = m_debuff.group(2)
                amount = int(m_debuff.group(3))
                floating_events.append((target_name, f"-{amount} {stat_name}", "#a855f7"))
                continue

        self.log_messages = self.log_messages[-8:]
        self._refresh_log()

        # Show floating numbers
        if floating_events and self.app.engine is not None:
            engine = self.app.engine
            for target_name, text, color in floating_events:
                found = False
                for idx, ch in enumerate(engine.player_team):
                    if ch.name == target_name:
                        show_floating_number(
                            self.canvas, PLAYER_X, Y_BASE + idx * Y_STEP - 20, text, color
                        )
                        found = True
                        break
                if found:
                    continue
                for idx, ch in enumerate(engine.bot_team):
                    if ch.name == target_name:
                        show_floating_number(
                            self.canvas, BOT_X, Y_BASE + idx * Y_STEP - 20, text, color
                        )
                        break

    def _refresh_log(self) -> None:
        """Redraw the battle log text widget."""
        self.log_text.delete("1.0", "end")
        for log in self.log_messages:
            self.log_text.insert("end", f"{log}\n")
        self.log_text.see("end")
