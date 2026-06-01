# Task 05 — HP Numeric Display + Floating Damage Numbers

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Read `roadmap.md` in the project root for full Phase 2 plan.

Tasks 01-04 are completed. Battle system is fully functional with planning phase, speed ordering, ultimate cooldowns, and attack previews. Currently HP bars exist but show NO numeric values — the player guesses HP from bar length. Damage is only visible in the Battle Log text. This task adds numeric HP and animated floating damage numbers like real RPGs (Summoners War, Raid: Shadow Legends).

## Goal
1. Show "current/max HP" as numbers on every character (player and enemy)
2. When damage is dealt, animate a floating red number above the target that rises and fades out
3. Healing shows green floating number, crits show yellow/larger

## Requirements

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)

#### Part A — Numeric HP Display

1. Add HP text to each character on the battle field:
   - Format: `"78 / 115"` below or on top of the existing HP bar
   - Font: smaller than character name, but clearly readable
   - Color: white or light gray (readable on dark background — check current theme)
   - Update after every action resolves during execution phase
   - Show for BOTH player and enemy characters

2. HP bar color thresholds (if not already implemented):
   - HP > 50%: green
   - HP 25-50%: yellow/orange
   - HP < 25%: red
   - These colors should update dynamically as HP changes

#### Part B — Floating Damage Numbers

3. Create a reusable animation component/function:
   ```
   def show_floating_number(canvas, x, y, text, color, size):
       """Animate a number that floats upward and fades out."""
   ```
   - Implementation approach using Tkinter Canvas:
     a) Create a Canvas text item at the target character's position
     b) Use `canvas.after()` loop to animate:
        - Move text upward by ~2px every 50ms
        - Reduce opacity over time (Tkinter doesn't support true opacity on text — use color stepping from full color → background color, OR use a sequence of progressively lighter colors)
        - Total animation duration: ~1.5-2 seconds
        - After animation completes: `canvas.delete(item_id)` to clean up
     c) Alternative to opacity: start with large font, shrink over time, then delete. Choose whichever looks better.

4. Damage number styling:
   - **Normal damage**: red color, standard size (e.g., 16-18px), prefix with "-" → "-42"
   - **Critical hit**: yellow or orange color, larger size (e.g., 22-24px), prefix with "-" → "-67!" (add exclamation)
   - **Healing**: green color, standard size, prefix with "+" → "+30"
   - **Buff applied**: blue or cyan, smaller size, text like "DEF UP" or "SPD +5"
   - **Miss / immune** (if such mechanic exists): gray, "MISS" text

5. Determine if critical hit:
   - Check existing code: is there a crit mechanic in AbilityResolver?
   - If YES → read the crit flag from the result and style accordingly
   - If NO → skip crit styling for now, use normal damage style for everything. Do NOT add crit mechanics — that's a separate feature.

6. Animation timing during execution:
   - Each action in execution phase already has ~800ms delay between actions (from Task 01)
   - When an action resolves:
     a) Show floating damage number on target
     b) Update HP bar + HP text
     c) Update Battle Log
   - All three should happen simultaneously per action
   - Multiple floating numbers should be able to coexist (e.g., AoE hits 3 targets → 3 numbers at once)

7. Position calculation:
   - Floating number appears ABOVE the target character sprite/icon
   - Starting Y position: top of character widget minus ~20px
   - X position: centered on character widget
   - Slight random X offset (±10px) to prevent overlap on repeated hits
   - Each number floats upward independently

#### Part C — Battle Screen Integration

8. If Battle Screen currently uses ONLY Frames and Labels (no Canvas):
   - You may need to convert the character display area to a Canvas, or overlay a Canvas on top
   - BEFORE making this change: assess the impact on existing layout. If converting to Canvas is too invasive, consider using a Toplevel window (transparent overlay) or placing Canvas items strategically
   - Whatever approach you choose: existing character display, HP bars, names, and charge indicators (from Task 03) MUST continue to work

## Constraints
- Do NOT modify domain or application layers — this is purely infrastructure/UI
- Do NOT add game mechanics (crits, miss chance, etc.) — only visualize what already exists
- Floating numbers must clean up after themselves — no memory leak from orphaned Canvas items
- Animation must not block the main Tkinter event loop — use `after()`, never `time.sleep()`
- Keep animation performant: if 6 numbers are floating simultaneously, it should not lag

## Testing
- Automated tests (limited for UI):
  - If you create a separate animation utility: test that `show_floating_number` creates and schedules cleanup correctly (mock canvas)
  - Data integrity: verify all characters have `max_hp` and `current_hp` accessible for display
- Manual testing is primary:
  - HP numbers visible on all 6 characters at battle start
  - HP numbers match actual values (cross-reference with Battle Log)
  - After damage: floating red number appears, rises, disappears
  - After healing (e.g., Full Heal card): floating green number appears
  - HP bar color changes at thresholds (>50% green, 25-50% yellow, <25% red)
  - Multiple simultaneous floating numbers (AoE attack) display correctly
  - No visual glitches after 5+ turns of combat
  - No orphaned text items accumulating (check via Battle Log if characters keep getting hit)
- Run ALL existing tests: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `CLAUDE.md` — mention floating damage animation in UI section
- Add docstrings to animation utility and modified UI methods
- If you converted any layout to Canvas: document the change and why in code comments

## Verification
- Launch the game: `python -m circle_cycle` (check CLAUDE.md for run command)
- Full playthrough:
  - Card Select → Battle
  - All 6 characters show numeric HP (format: "XX / YY")
  - Plan actions → Confirm → watch execution:
    - Each hit shows floating red number on target
    - HP numbers update after each hit
    - HP bar colors change at thresholds
  - Play 3+ rounds to verify no animation artifacts or memory buildup
  - If healing cards were applied pre-battle, verify green numbers work too

## On completion
git add -A && git commit -m "feat: add numeric HP display and floating damage numbers" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"
