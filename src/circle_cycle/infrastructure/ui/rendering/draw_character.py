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

    # HP bar color thresholds: >50% green, 25-50% yellow, <25% red
    if hp_ratio > 0.5:
        bar_color = "#22c55e"
    elif hp_ratio > 0.25:
        bar_color = "#f59e0b"
    else:
        bar_color = "#ef4444"

    canvas.create_rectangle(
        x - bar_width // 2,
        y + radius + 10,
        x - bar_width // 2 + int(bar_width * hp_ratio),
        y + radius + 10 + bar_height,
        fill=bar_color,
        outline="",
    )

    # Numeric HP display
    canvas.create_text(
        x,
        y + radius + 30,
        text=f"{character.current_hp} / {character.hp}",
        fill="#e5e7eb",
        font=("Arial", 10, "bold"),
    )

    canvas.create_text(
        x,
        y + radius + 48,
        text=character.name,
        fill="white",
        font=("Arial", 10, "bold"),
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


# --- Floating number animation utility ---

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{int(max(0,min(255,c))):02x}" for c in rgb)


def _interpolate_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


def show_floating_number(canvas: tk.Canvas, x: int, y: int, text: str, color: str, size: int = 16) -> None:
    """Animate a number that floats upward and fades toward the background.

    Uses canvas.after to schedule lightweight animation steps.
    """
    bg = canvas.cget("bg") if canvas.cget("bg") else "#0f172a"
    item = canvas.create_text(x, y, text=text, fill=color, font=("Arial", size, "bold"))

    steps = 30
    dy = -2  # pixels per step

    def step(i: int) -> None:
        if i >= steps:
            try:
                canvas.delete(item)
            except Exception:
                pass
            return
        # move up
        canvas.move(item, 0, dy)
        # fade color toward bg
        t = i / steps
        new_color = _interpolate_color(color, bg, t)
        try:
            canvas.itemconfig(item, fill=new_color)
        except Exception:
            pass
        canvas.after(50, lambda: step(i + 1))

    step(0)
