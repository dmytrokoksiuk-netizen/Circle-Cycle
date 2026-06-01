# Task 03 — Ultimate Cooldown System

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Read `roadmap.md` in the project root for full Phase 2 plan.

Tasks 01-02 are completed. BattleEngine has Planning → Execution phases with speed-based turn order. Currently the Ultimate button is always available. This task adds a charge mechanic: the player must use Special Attack twice before Ultimate unlocks.

## Goal
Ultimate ability starts locked. Each time a character uses Special Attack, their charge counter increments. At 2/2 charges, Ultimate unlocks for one use. After using Ultimate, counter resets to 0/2.

## Requirements

### Domain Layer (`src/circle_cycle/domain/`)

1. Add charge tracking to `Character` entity:
   - New field: `special_use_count: int = 0` (tracks how many times Special has been used)
   - New constant in `domain/constants/`: `ULTIMATE_CHARGE_REQUIRED = 2`
   - New property or method:
     ```python
     @property
     def is_ultimate_ready(self) -> bool:
         return self.special_use_count >= ULTIMATE_CHARGE_REQUIRED
     ```
   - New method:
     ```python
     def increment_special_count(self) -> None:
         self.special_use_count += 1

     def reset_special_count(self) -> None:
         self.special_use_count = 0
     ```
   - IMPORTANT: Check if Character is a frozen dataclass. If yes, you cannot add mutable fields directly. Options:
     a) If Character is NOT frozen → just add the field
     b) If Character IS frozen → `special_use_count` must be tracked externally (e.g., in BattleEngine state as a dict `{character_id: count}`). Choose the approach that is consistent with how HP mutation already works in the project. Look at how `take_damage()` is implemented — follow the same pattern.

2. Add `AbilityType` check:
   - Verify that `AbilityType` enum has distinct values for NORMAL, SPECIAL, and ULTIMATE
   - If Ultimate is not distinguishable from Special in the current enum, add it

### Application Layer (`src/circle_cycle/application/services/`)

3. Update `AbilityResolver`:
   - After resolving a Special Attack → call `character.increment_special_count()` (or update the external tracker)
   - After resolving an Ultimate → call `character.reset_special_count()`
   - Do NOT increment counter if the Special Attack misses or is blocked (if such mechanics exist — check current code)

4. Update `BattleEngine`:
   - During Planning Phase: when player selects ability for a character, validate:
     - If Ultimate selected AND `character.is_ultimate_ready` is False → reject the selection, show message "Ultimate not ready (X/2 charges)"
     - If Ultimate selected AND `is_ultimate_ready` is True → allow
   - Apply the same rules to `BotAI.generate_plan()` — bot should NOT use Ultimate unless charged
   - Reset `special_use_count` for all characters at the START of a new battle (not between turns — charges persist across turns within one battle)

5. Update `BotAI`:
   - Bot AI should be aware of Ultimate availability
   - Simple heuristic: if Ultimate is ready → use it (it's the strongest move, no reason to hold it in current design)
   - If Ultimate not ready → choose between Normal and Special based on existing heuristics
   - Bot should prefer Special over Normal when charges are at 1/2 (incentive to unlock Ultimate faster) — but this is a suggestion, not a hard rule. Use reasonable heuristics.

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)

6. Battle Screen — charge indicator:
   - Display charge counter next to or below each player character: "⚡ 0/2", "⚡ 1/2", "⚡ 2/2 READY!"
   - Update counter in real-time after execution phase
   - When Ultimate is NOT ready: Ultimate button should be visually disabled (greyed out, different color, or show lock icon + "1/2" on the button itself)
   - When Ultimate IS ready: Ultimate button becomes active, optionally with a glow/highlight color to draw attention
   - Show charge indicators for enemy characters too — so player can anticipate enemy Ultimates

7. Battle Log messages:
   - When Special is used: "[Character] uses [Special Name]! Ultimate charge: X/2"
   - When Ultimate unlocks: "[Character]'s Ultimate is now READY!"
   - When Ultimate is used: "[Character] unleashes [Ultimate Name]! Charge reset."

## Constraints
- Do NOT change the Planning Phase flow from Task 01
- Do NOT change speed-based ordering from Task 02
- Charges persist across turns within one battle, reset at battle start
- Both player AND enemy characters use the same cooldown rules
- Follow existing mutation patterns in the codebase (check how HP changes work)

## Testing
- Unit tests:
  - Character `special_use_count` starts at 0
  - After 1 Special: count = 1, `is_ultimate_ready` = False
  - After 2 Specials: count = 2, `is_ultimate_ready` = True
  - After using Ultimate: count resets to 0, `is_ultimate_ready` = False
  - BattleEngine rejects Ultimate selection when not charged
  - BattleEngine allows Ultimate selection when charged
  - BotAI does not select Ultimate when not charged
  - BotAI uses Ultimate when charged
  - Charges reset at battle start (new battle = 0/2 for all)
  - Charges survive across turns (turn 1 Special → turn 2 Special → turn 3 Ultimate ready)
- Run ALL existing tests: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `ARCHITECTURE.md` — add Ultimate cooldown to domain entities section
- Update `CLAUDE.md` — document the charge mechanic in game rules or battle flow section
- Add `ULTIMATE_CHARGE_REQUIRED` to constants documentation if it exists
- Add docstrings to all new methods and properties

## Verification
- Launch the game: `python -m circle_cycle` (check CLAUDE.md for run command)
- Play a battle and verify:
  - Ultimate button starts disabled/greyed out
  - Use Special Attack with one character twice across turns
  - Charge indicator updates: 0/2 → 1/2 → 2/2 READY!
  - Ultimate button becomes active
  - Use Ultimate → counter resets to 0/2, button disables again
  - Enemy characters also follow the same rules (observe via Battle Log)
  - Start a new battle → all charges reset to 0/2

## On completion
git add -A && git commit -m "feat: add ultimate cooldown system with charge tracking" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"
