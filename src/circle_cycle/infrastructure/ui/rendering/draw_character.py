"""Rendering utilities for drawing characters on the Tkinter canvas."""

from __future__ import annotations

import tkinter as tk

from circle_cycle.domain.entities.character import Character


def draw_circle_character(
    canvas: tk.Canvas,
    x: int,
    y: int,
    character: Character,
    scale: float = 1.0,
) -> None:
    """Draw a simple circle-based character sprite on the canvas."""
    radius = int(28 * scale)
    eye_radius = max(2, int(3 * scale))
    body_color = "#9ca3af" if not character.is_alive() else character.color
    outline_color = "#111827" if character.is_alive() else "#4b5563"

    canvas.create_oval(
        x - radius,
        y - radius,
        x + radius,
        y + radius,
        fill=body_color,
        outline=outline_color,
        width=2,
    )

    canvas.create_oval(
        x - radius // 2,
        y - radius // 3,
        x - radius // 2 + eye_radius * 2,
        y - radius // 3 + eye_radius * 2,
        fill="white",
        outline="black",
        width=1,
    )
    canvas.create_oval(
        x + radius // 2 - eye_radius * 2,
        y - radius // 3,
        x + radius // 2,
        y - radius // 3 + eye_radius * 2,
        fill="white",
        outline="black",
        width=1,
    )
    canvas.create_oval(
        x - radius // 2 + eye_radius - 1,
        y - radius // 3 + eye_radius - 1,
        x - radius // 2 + eye_radius + 1,
        y - radius // 3 + eye_radius + 1,
        fill="black",
    )
    canvas.create_oval(
        x + radius // 2 - eye_radius - 1,
        y - radius // 3 + eye_radius - 1,
        x + radius // 2 - eye_radius + 1,
        y - radius // 3 + eye_radius + 1,
        fill="black",
    )
    canvas.create_arc(
        x - radius // 2,
        y - radius // 4,
        x + radius // 2,
        y + radius // 4,
        start=200,
        extent=140,
        style="arc",
        outline="black",
        width=2,
    )
    canvas.create_line(
        x - radius,
        y,
        x - radius // 2,
        y + radius // 2,
        fill=outline_color,
        width=2,
    )
    canvas.create_line(
        x + radius,
        y,
        x + radius // 2,
        y + radius // 2,
        fill=outline_color,
        width=2,
    )
    canvas.create_line(
        x - radius // 2,
        y + radius,
        x - radius // 3,
        y + radius * 2,
        fill=outline_color,
        width=2,
    )
    canvas.create_line(
        x + radius // 2,
        y + radius,
        x + radius // 3,
        y + radius * 2,
        fill=outline_color,
        width=2,
    )

    hp_ratio = max(0, character.current_hp / character.hp)
    bar_width = 80 * scale
    bar_height = 8 * scale
    canvas.create_rectangle(
        x - bar_width // 2,
        y + radius + 10,
        x + bar_width // 2,
        y + radius + 10 + bar_height,
        fill="#4b5563",
        outline="black",
    )
    canvas.create_rectangle(
        x - bar_width // 2,
        y + radius + 10,
        x - bar_width // 2 + int(bar_width * hp_ratio),
        y + radius + 10 + bar_height,
        fill="#22c55e" if hp_ratio > 0.4 else "#ef4444",
        outline="",
    )

    canvas.create_text(
        x,
        y + radius + 30,
        text=character.name,
        fill="white",
        font=("Arial", 10, "bold"),
    )
    canvas.create_text(
        x,
        y + radius + 46,
        text=f"{character.current_hp}/{character.hp} HP",
        fill="#e5e7eb",
        font=("Arial", 9, "bold"),
    )
    charge_text = f"Ultimate {character.ultimate_charge_count}/2"
    charge_color = "#fbbf24" if character.can_use_ultimate() else "#cbd5e1"
    canvas.create_text(
        x,
        y + radius + 62,
        text=charge_text,
        fill=charge_color,
        font=("Arial", 8, "bold"),
    )

    if not character.is_alive():
        canvas.create_line(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill="#111827",
            width=3,
        )
        canvas.create_line(
            x + radius,
            y - radius,
            x - radius,
            y + radius,
            fill="#111827",
            width=3,
        )
