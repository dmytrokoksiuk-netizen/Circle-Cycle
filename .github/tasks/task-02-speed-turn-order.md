# Task 02 — Speed-Based Turn Order

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Read `roadmap.md` in the project root for full Phase 2 plan.

Task 01 (Planning Phase) has been completed. BattleEngine now collects 3 PlannedActions per side before execution. Currently the player side ALWAYS executes first (hardcoded). This task adds dynamic speed-based ordering.

## Goal
Determine which side acts first each turn by comparing total team Speed. The faster team executes all 3 actions first, then the slower team.

## Requirements

### Application Layer (`src/circle_cycle/application/services/`)

1. Add method to `BattleEngine`:
   ```python
   def _calculate_team_speed(self, characters: list[Character]) -> int:
       """Sum speed of all LIVING characters on a team."""
   ```
   - Only count characters with HP > 0
   - If a character has speed buffs/debuffs from cards (e.g., Quick Feet), those should already be reflected in `character.speed` — verify this is the case

2. Refactor execution order in `confirm_plan()` (or wherever execution happens):
   - Before executing, calculate: `player_speed = _calculate_team_speed(player_team)` and `enemy_speed = _calculate_team_speed(enemy_team)`
   - If `player_speed >= enemy_speed` → execute player_plan first, then enemy_plan (tie = player advantage)
   - If `enemy_speed > player_speed` → execute enemy_plan first, then player_plan
   - This should be a clean swap of execution order, NOT duplicated code. Example approach:
     ```python
     first_plan, second_plan = (player_plan, enemy_plan) if player_speed >= enemy_speed else (enemy_plan, player_plan)
     ```

3. Add speed comparison to Battle Log:
   - At the start of execution phase, log: "Player team speed: {X} vs Enemy team speed: {Y} — {Winner} acts first!"
   - This helps the player understand WHY a side went first

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)

4. Battle Screen — show turn order indicator:
   - Before execution starts, briefly display which side goes first (text label or highlight)
   - This can be simple — a label like ">> Your team strikes first! <<" or ">> Enemy moves first! <<"
   - Display for ~1.5 seconds before actions begin executing (use `after()`)

## Constraints
- Do NOT modify Character entity or Ability — speed data already exists
- Do NOT change the Planning Phase flow from Task 01
- Do NOT add individual character speed ordering within a team (all 3 on a side execute in plan order) — this keeps it simple and matches the game design
- Keep `_calculate_team_speed` as a pure calculation — no side effects

## Testing
- Unit tests:
  - `_calculate_team_speed` with all alive characters → correct sum
  - `_calculate_team_speed` with 1 dead character (HP=0) → excluded from sum
  - `_calculate_team_speed` with all dead → returns 0
  - Execution order: player speed 45 vs enemy 38 → player first
  - Execution order: player speed 30 vs enemy 42 → enemy first
  - Execution order: tied speed → player first
- Run ALL existing tests: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `ARCHITECTURE.md` — add speed-based ordering to the execution flow description
- Update `CLAUDE.md` if battle flow section exists — mention speed comparison
- Add docstrings to new/changed methods

## Verification
- Launch the game: `python -m circle_cycle` (check CLAUDE.md for run command)
- Play a battle and observe:
  - Battle Log shows speed comparison message
  - If enemy team is faster → they act first (you can verify by giving enemy Quick Feet buff or checking JSON data for speed values)
  - If player team is faster → player acts first
  - Game still works correctly when side that goes second has characters killed during first side's execution

## On completion
git add -A && git commit -m "feat: add speed-based turn order for execution phase" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"
