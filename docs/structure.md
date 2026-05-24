# Circle Cycle Structure

This project uses a flat object-oriented layout with a single class per file.

- `main.py` launches the Tkinter application.
- `game/` contains the engine, data models, and loading logic.
- `ui/` contains view code only and calls into the engine.
- `data/` stores runtime JSON definitions for abilities, characters, and cards.

All gameplay state and rules live in the engine and model classes. The UI is limited to drawing and forwarding user input.
