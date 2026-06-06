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

        # Transient banner to show which side acts first during execution phase
        self.order_label = tk.Label(
            self,
            text="",
            bg="#052e16",
            fg="#fef3c7",
            font=("Arial", 14, "bold"),
        )
        # Do not pack now; shown only when needed

        self.canvas = tk.Canvas(self, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        control_frame = tk.Frame(self, bg="#111827")
        control_frame.pack(fill="x", pady=(0, 12))

        self.normal_button = tk.Button(
            control_frame,
            text="Normal Attack (free)",
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
            text="Ultimate (free)",
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
        """Enable or disable action buttons based on current turn, cooldowns, and mana."""
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
            # Disable when ability doesn't exist or is on cooldown
            if ability is None or current.cooldowns.get(ability.id, 0) > 0:
                button.config(state="disabled")
                continue

            # Additional rule: Ultimate button disabled until character has 2 charges
            from circle_cycle.domain.enums.ability_type import AbilityType
            if ability.type == AbilityType.ULTIMATE and not getattr(current, "is_ultimate_ready", False):
                button.config(state="disabled")
                continue

            # Mana check: disable if can't afford
            if not current.can_afford_ability(ability.mana_cost):
                button.config(state="disabled")

            # Update button text with mana cost
            if ability.mana_cost > 0:
                button.config(text=f"{ability.name} ({ability.mana_cost} MP)")
            elif ability_type == "ultimate":
                button.config(text=f"{ability.name} (free)")
            else:
                button.config(text=f"{ability.name} (free)")

    def handle_action(self, ability_type: str) -> None:
        """Handle a player action request by showing an ability preview before proceeding."""
        if self.app.engine is None:
            return

        engine = self.app.engine
        current = engine.get_current_character()
        if current not in engine.player_team:
            return

        ability = engine.get_ability_by_type(current, ability_type)
        if ability is None:
            return

        # Show the preview modal; Confirm will perform the actual action flow
        self._open_preview(ability, current)

    def _open_preview(self, ability, actor) -> None:
        """Display a modal preview of the selected ability with Confirm/Cancel."""
        # Create modal window
        modal = tk.Toplevel(self)
        modal.transient(self)
        modal.grab_set()
        modal.configure(bg="#0b1220")

        title = tk.Label(modal, text=ability.name, bg="#0b1220", fg="white", font=("Arial", 16, "bold"))
        title.pack(pady=(12, 6), padx=12)

        # Type badge
        from circle_cycle.domain.enums.ability_type import AbilityType

        badge_text = ability.type.value if hasattr(ability.type, "value") else str(ability.type)
        badge = tk.Label(modal, text=badge_text.title(), bg="#111827", fg="white", font=("Arial", 10, "bold"))
        badge.pack(pady=(0, 8))

        # Description
        desc = ability.description if getattr(ability, "description", None) else "No description available."
        desc_label = tk.Label(modal, text=desc, wraplength=400, justify="left", bg="#0b1220", fg="#e5e7eb", font=("Arial", 12))
        desc_label.pack(padx=12, pady=(0, 8))

        # Damage and effects
        damage_label = tk.Label(modal, text=f"Damage: {ability.damage}", bg="#0b1220", fg="#f97316", font=("Arial", 14, "bold"))
        damage_label.pack(padx=12, pady=(0, 6))

        # Mana cost display
        mana_text = f"Mana Cost: {ability.mana_cost} MP" if ability.mana_cost > 0 else "Mana Cost: Free"
        mana_label = tk.Label(modal, text=mana_text, bg="#0b1220", fg="#60a5fa", font=("Arial", 11))
        mana_label.pack(padx=12, pady=(0, 6))

        effects = []
        if ability.effect is not None:
            effects.append(str(ability.effect).title())
        target_type = "All enemies" if ability.type == AbilityType.ULTIMATE else "Single target"
        effects_text = ", ".join(effects) if effects else "None"
        effects_label = tk.Label(modal, text=f"Effects: {effects_text} • Target: {target_type}", bg="#0b1220", fg="#e5e7eb", font=("Arial", 10))
        effects_label.pack(padx=12, pady=(0, 12))

        # Buttons frame
        btn_frame = tk.Frame(modal, bg="#0b1220")
        btn_frame.pack(pady=(0, 12))

        def on_confirm(event=None):
            modal.grab_release()
            modal.destroy()
            self._on_confirm_preview(actor, ability)

        def on_cancel(event=None):
            modal.grab_release()
            modal.destroy()

        # Confirm button is disabled if Ultimate and not ready
        confirm_state = "normal"
        if ability.type == AbilityType.ULTIMATE and not getattr(actor, "is_ultimate_ready", False):
            confirm_state = "disabled"
            confirm_text = f"Not Ready ({getattr(actor, 'special_use_count', 0)}/2)"
        elif not actor.can_afford_ability(ability.mana_cost):
            confirm_state = "disabled"
            confirm_text = f"Not enough mana ({actor.mana}/{ability.mana_cost})"
        else:
            confirm_text = "Confirm"

        confirm_btn = tk.Button(btn_frame, text=confirm_text, command=on_confirm, state=confirm_state, bg="#059669", fg="white", font=("Arial", 12, "bold"))
        confirm_btn.pack(side="left", padx=8)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, bg="#374151", fg="white", font=("Arial", 12))
        cancel_btn.pack(side="left", padx=8)

        # Key bindings
        modal.bind("<Return>", on_confirm)
        modal.bind("<Escape>", on_cancel)

        # Center modal over parent
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - modal.winfo_reqwidth() // 2
        y = self.winfo_rooty() + self.winfo_height() // 2 - modal.winfo_reqheight() // 2
        modal.geometry(f"+{x}+{y}")

    def _on_confirm_preview(self, actor, ability) -> None:
        """Callback executed when preview is confirmed — proceeds with action flow."""
        if self.app.engine is None:
            return

        engine = self.app.engine
        current = actor
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
        """Append new log lines and keep only the most recent six events.

        If a speed comparison log appears ("acts first"), briefly display a
        transient banner indicating which side will act first for ~1.5s.

        Additionally, parse logs for damage/heal events and show floating numbers
        on the canvas above the affected characters.
        """
        show_banner = None
        floating_events = []  # tuples of (target_name, text, color)
        import re
        from circle_cycle.infrastructure.ui.rendering.draw_character import (
            show_floating_number,
        )

        for log in logs:
            self.log_messages.append(log)
            if "acts first" in log:
                # Determine side from message content
                if "Player acts first" in log or "Player team speed" in log and "Player acts first" in log:
                    show_banner = ">> Your team strikes first! <<"
                elif "Enemy acts first" in log or "Enemy team speed" in log and "Enemy acts first" in log:
                    show_banner = ">> Enemy moves first! <<"

            # Shield broken event
            if "shield is broken" in log:
                tname = log.split("'s shield")[0]
                floating_events.append((tname, "SHIELD BROKEN!", "#f59e0b"))
                continue

            # Damage with shield absorption pattern
            m_shield = re.search(r"hits (.+?) for (\d+) damage.+?(\d+) absorbed by shield, (\d+) to HP", log)
            if m_shield:
                target_name = m_shield.group(1)
                shield_dmg = int(m_shield.group(3))
                hp_dmg = int(m_shield.group(4))
                floating_events.append((target_name, f"-{shield_dmg}", "#06b6d4"))
                floating_events.append((target_name, f"-{hp_dmg}", "#ef4444"))
                continue

            # Damage absorbed by shield only
            m_shield_only = re.search(r"hits (.+?) for (\d+) damage.+?\(absorbed by shield\)", log)
            if m_shield_only:
                target_name = m_shield_only.group(1)
                amount = int(m_shield_only.group(2))
                floating_events.append((target_name, f"-{amount}", "#06b6d4"))
                continue

            # Standard damage pattern: "<Attacker> hits <Target> for <N> damage"
            m = re.search(r"hits (.+?) for (\d+) damage", log)
            if m:
                target_name = m.group(1)
                amount = int(m.group(2))
                floating_events.append((target_name, f"-{amount}", "#ef4444"))
                continue

            # Heal patterns
            m2 = re.search(r"gains (\d+) HP from", log)
            if m2:
                amount = int(m2.group(1))
                # extract target name at start
                tname = log.split(" ")[0]
                floating_events.append((tname, f"+{amount}", "#10b981"))
                continue
            m3 = re.search(r"is healed for (\d+) HP", log)
            if m3:
                amount = int(m3.group(1))
                tname = log.split(" ")[0]
                floating_events.append((tname, f"+{amount}", "#10b981"))
                continue

        self.log_messages = self.log_messages[-6:]
        self._refresh_log()

        if show_banner:
            self._show_order_banner(show_banner)

        # Show floating numbers for parsed events
        if floating_events and self.app.engine is not None:
            engine = self.app.engine
            # positions match those used in refresh()
            player_x = 180
            bot_x = 900
            y_base = 120
            y_step = 150
            for target_name, text, color in floating_events:
                # find target in player or bot teams
                found = False
                for idx, ch in enumerate(engine.player_team):
                    if ch.name == target_name:
                        x = player_x
                        y = y_base + idx * y_step - 20
                        show_floating_number(self.canvas, x + (0), y, text, color)
                        found = True
                        break
                if found:
                    continue
                for idx, ch in enumerate(engine.bot_team):
                    if ch.name == target_name:
                        x = bot_x
                        y = y_base + idx * y_step - 20
                        show_floating_number(self.canvas, x + (0), y, text, color)
                        break

    def _show_order_banner(self, text: str) -> None:
        """Display the transient order banner for a short duration."""
        # Place banner above the canvas and remove after 1.5s
        self.order_label.config(text=text)
        self.order_label.pack(pady=(6, 6))

        def _hide() -> None:
            self.order_label.pack_forget()

        # 1500ms display
        self.after(1500, _hide)

    def _refresh_log(self) -> None:
        """Redraw the battle log text widget."""
        self.log_text.delete("1.0", "end")
        for log in self.log_messages:
            self.log_text.insert("end", f"{log}\n")
        self.log_text.see("end")
