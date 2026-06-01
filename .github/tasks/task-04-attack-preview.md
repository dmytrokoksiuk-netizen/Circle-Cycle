# Task 04 — Attack Preview & Confirmation

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Read `roadmap.md` in the project root for full Phase 2 plan.

Tasks 01-03 are completed. BattleEngine has Planning → Execution phases, speed-based turn order, and Ultimate cooldown system. Currently when a player clicks Normal/Special/Ultimate, they go straight to target selection with no information about what the ability does. This task adds an informational preview step.

## Goal
When the player clicks an ability button during Planning Phase, show a preview panel with the ability's name, description, damage, and effects BEFORE committing to it. Player can Confirm (proceed to target selection) or Cancel (go back to ability choice).

## Requirements

### Domain Layer — NO CHANGES
- All required data (ability name, description, damage, effects) should already exist in the `Ability` entity and JSON data files
- If description or effect text is MISSING from `Ability` entity or JSON data:
  - Add a `description: str` field to `Ability` if it doesn't exist
  - Add descriptions to each ability in the JSON data files
  - Keep descriptions short (1 sentence): "Deals 35 damage to a single target", "Deals 25 damage to all enemies and applies burn for 2 turns"
  - Document what fields you added

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)

1. Create a preview panel component:
   - When player clicks Normal Attack / Special Attack / Ultimate → instead of going to target selection, show a preview panel
   - Panel content:
     - **Ability name** (large text, top)
     - **Type badge**: "Normal", "Special", or "Ultimate" (color-coded to match button colors)
     - **Description**: what the ability does in plain English
     - **Damage**: expected damage number or range (read from Ability entity)
     - **Effects**: status effects if any (burn, buff, AoE indicator, etc.)
     - **Target type**: "Single target" or "All enemies" (based on ability data)
   - Two buttons at the bottom:
     - **"Confirm"** → proceed to target selection (existing flow)
     - **"Cancel"** → return to ability button selection, nothing changes

2. Implementation approach — choose ONE:
   - **Option A — Overlay Frame**: A Tkinter Frame that appears on top of the battle screen (like a modal). Simpler, blocks interaction with battle field until dismissed.
   - **Option B — Side Panel**: A panel that slides in or appears to the right/left of the ability buttons. Non-blocking but takes more space.
   - Choose whichever fits the current screen layout better. Option A is recommended for simplicity.

3. Visual styling:
   - Match existing UI colors and fonts (inspect current battle screen code)
   - Ability name should be clearly readable
   - Damage number should be prominent (large font, colored)
   - If ability has status effects → show them with existing color conventions (e.g., burn = red/orange)
   - Panel should have a visible border or background contrast to distinguish from battle field

4. Ultimate preview — extra info:
   - If Ultimate is NOT ready: show preview but replace Confirm button with a disabled state showing "Not Ready (X/2 charges)"
   - If Ultimate IS ready: normal Confirm button
   - This prevents confusion — player sees what Ultimate does even before it's charged

5. Keyboard shortcuts (optional but nice):
   - Enter → Confirm
   - Escape → Cancel
   - Only active when preview panel is visible

## Constraints
- Do NOT change BattleEngine, AbilityResolver, or any application/domain logic
- Do NOT change the Planning Phase flow — this is purely a UI insertion between "click ability button" and "select target"
- Preview panel must be dismissed before any other interaction happens (modal behavior)
- Panel must work for both player characters — as player plans action for each of the 3 characters, preview appears each time

## Testing
- Unit tests (if testable without UI):
  - Verify all abilities in JSON data have a `description` field (data integrity test)
  - Verify all abilities have damage values
- Manual testing is primary for this task (UI-heavy):
  - Click Normal Attack → preview shows → Cancel → back to ability buttons
  - Click Special Attack → preview shows correct info → Confirm → target selection
  - Click Ultimate (not charged) → preview shows but Confirm is disabled
  - Click Ultimate (charged) → preview shows → Confirm → target selection
  - Preview displays correctly for all characters (Nova, Stone, Ace — each has different abilities)
  - Preview panel doesn't break layout or overlap incorrectly
- Run ALL existing tests: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `CLAUDE.md` — mention attack preview in UI section if one exists
- Add docstrings to new UI components/methods
- If you added `description` field to Ability or JSON, document the schema change in `ARCHITECTURE.md`

## Verification
- Launch the game: `python -m circle_cycle` (check CLAUDE.md for run command)
- Play through a full battle:
  - Card Select → Battle → click any ability → preview appears with correct info
  - Cancel → returns to buttons
  - Confirm → target selection works as before
  - Plan all 3 characters (each shows preview) → Confirm Plan → execution works normally
  - Ultimate shows charge status in preview
  - All text is readable, no layout glitches

## On completion
git add -A && git commit -m "feat: add attack preview panel with ability details" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"
