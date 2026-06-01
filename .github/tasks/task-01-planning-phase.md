# Task 01 — Planning Phase (BattleEngine Refactor)

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Currently the battle flow is sequential: each character selects an action + target, it executes immediately, then the next character's turn. We need to refactor this into a two-phase system: Planning → Execution.

## Goal
Refactor BattleEngine so that the player assigns actions for ALL 3 characters BEFORE any execution happens. The bot (AI opponent) also plans all 3 actions. Then both sides execute.

## Requirements

### Domain Layer (`src/circle_cycle/domain/`)
1. Create a new DTO or dataclass `PlannedAction` in `domain/entities/` or `domain/value_objects/`:
   - `character: Character` — who acts
   - `ability: Ability` — what ability to use (Normal, Special, Ultimate)
   - `target: Character` — who to hit
   - This should be a frozen dataclass (immutable, consistent with existing value objects)

2. Add a new enum `BattlePhase` in `domain/enums/`:
   - `PLANNING` — player is assigning actions
   - `EXECUTION` — actions are being resolved
   - `TURN_END` — cleanup, status effects, etc.

### Application Layer (`src/circle_cycle/application/services/`)
3. Refactor `BattleEngine`:
   - Read the EXISTING code first. Understand the current turn flow before changing anything.
   - Add state: `current_phase: BattlePhase`, `player_plan: list[PlannedAction]` (max 3), `enemy_plan: list[PlannedAction]` (max 3)
   - Add `planning_index: int` to track which player character is currently being planned (0, 1, 2)
   - New methods:
     - `submit_player_action(ability: Ability, target: Character)` — adds one PlannedAction to player_plan, increments planning_index
     - `undo_last_action()` — removes last PlannedAction from player_plan, decrements planning_index
     - `confirm_plan()` — validates player_plan has 3 actions, generates enemy_plan via BotAI, transitions to EXECUTION phase, executes all actions
   - During EXECUTION: iterate player_plan, resolve each via AbilityResolver (existing logic). Then iterate enemy_plan same way. (For now player always goes first — Task 02 will add speed-based ordering)
   - After all 6 actions resolved → transition to TURN_END → cleanup → back to PLANNING for next turn
   - Handle edge case: if a target character dies mid-execution, skip that action or retarget (decide: skip is simpler, document the choice)

4. Refactor `BotAI`:
   - Instead of deciding one action at a time, add method `generate_plan(characters: list[Character], enemies: list[Character]) -> list[PlannedAction]`
   - Returns 3 PlannedActions for all bot characters at once
   - Reuse existing heuristic logic, just batch it

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)
5. Refactor Battle Screen:
   - PLANNING state UI:
     - Show header: "Plan actions: [character_name] (1/3)", "(2/3)", "(3/3)"
     - Show Normal Attack / Special Attack / Ultimate buttons (same as now)
     - After selecting ability → player clicks target enemy (same as now)
     - After target selected → action is submitted, advance to next character
     - Add "Undo" button to go back to previous character's choice
     - After 3rd character planned → show "Confirm Plan" button
     - Show a summary panel of planned actions: "Nova → Lightning Stab → Enemy Stone", etc.
   - EXECUTION state UI:
     - Disable all action buttons
     - Execute actions one by one with brief pause between each (use `after()` for timing, ~800ms between actions)
     - Update Battle Log as each action resolves
     - After all 6 actions → transition back to PLANNING

## Constraints
- Do NOT change domain entities (Character, Ability) structure
- Do NOT change AbilityResolver interface — it should still resolve one action at a time
- Do NOT break existing card selection flow (pre-battle phase)
- Skip dead characters during execution (don't error, just log "X is already defeated")
- All new code must follow existing project conventions (type hints, docstrings)

## Testing
- Write unit tests for:
  - `PlannedAction` creation and immutability
  - `BattleEngine.submit_player_action` — adds to plan correctly
  - `BattleEngine.undo_last_action` — removes last, handles empty plan
  - `BattleEngine.confirm_plan` — validates 3 actions, transitions phase
  - `BotAI.generate_plan` — returns exactly 3 PlannedActions for living characters
  - Edge case: target dies mid-execution, action is skipped
- Run ALL existing tests after refactor to ensure nothing is broken: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `CLAUDE.md` if battle flow description exists — reflect new Planning → Execution phases
- Update `ARCHITECTURE.md` Request Flow diagram to show new phase transitions
- Add docstrings to all new methods

## Verification
- Launch the game: `python -m circle_cycle` (or however the app starts — check CLAUDE.md)
- Play through: Card Select → Battle → verify you can plan 3 actions → confirm → watch execution → next turn
- Verify bot opponent still works correctly
- Verify Battle Log shows all 6 actions in correct order

## On completion
git add -A && git commit -m "feat: implement planning phase with batch action selection" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"