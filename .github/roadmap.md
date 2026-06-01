# Circle Cycle — Phase 2 Roadmap

## Overview

Phase 2 focuses on transforming the existing battle system into a strategic, polished turn-based RPG. All gameplay logic is built first (Tasks 1–3), then UI/UX improvements follow (Tasks 4–6). Infrastructure layer (Tkinter) may be replaced with Pygame/Godot in a future Phase 3 once all gameplay mechanics are solid.

Reference games: Summoners War, Raid: Shadow Legends, Marvel Strike Force.

---

## Task 1 — Planning Phase (BattleEngine Refactor)
**Priority:** Critical | **Layers:** Domain + Application + UI | **Complexity:** High

Current state: Player selects action + target for one character, it executes immediately, then next character's turn.

Target state: Player assigns action + target for ALL 3 characters before anything executes. After confirming the plan, both sides execute sequentially.

Key changes:
- New `PlannedAction` value object (character, ability, target)
- New `BattlePhase` enum (PLANNING → EXECUTION → TURN_END)
- BattleEngine refactored to collect 3 player actions, generate 3 bot actions, then resolve all 6
- Battle Screen shows planning progress (1/3, 2/3, 3/3), Undo button, Confirm Plan button
- Dead target during execution → skip action

Depends on: nothing (first task)

---

## Task 2 — Speed-Based Turn Order
**Priority:** High | **Layers:** Application | **Complexity:** Low

Current state: Player side always acts first (hardcoded in Task 1).

Target state: Sum total Speed of all living player characters vs all living enemy characters. Higher total acts first (all 3 characters execute). Tie → player goes first.

Key changes:
- BattleEngine calculates team speed totals before execution phase
- Execution order determined dynamically each turn
- Battle Log shows which side acts first and why ("Player team speed: 45 vs Enemy team speed: 38 — Player acts first!")

Depends on: Task 1 (Planning Phase must exist)

---

## Task 3 — Ultimate Cooldown System
**Priority:** High | **Layers:** Domain + Application + UI | **Complexity:** Medium

Current state: Ultimate button exists but no charge mechanic.

Target state: Ultimate is locked by default. Using Special Attack increments a charge counter. After 2 Special Attack uses, Ultimate unlocks for one use, then counter resets to 0.

Key changes:
- Domain: Add `special_use_count: int` to Character entity (tracks charges, 0→1→2)
- Application: AbilityResolver increments counter on Special use; BattleEngine checks unlock status before allowing Ultimate selection
- UI: Display charge indicator per character ("0/2", "1/2", "READY!")
- Ultimate button greyed out / disabled until charged
- After Ultimate used → counter resets, button locks again

Depends on: Task 1 (planning flow must handle ability availability)

---

## Task 4 — Attack Preview & Confirmation
**Priority:** Medium | **Layers:** UI (Infrastructure) | **Complexity:** Low

Current state: Normal Attack / Special Attack / Ultimate buttons with no description. Player doesn't know what an ability does until it fires.

Target state: Clicking an ability button shows a preview tooltip or modal with: ability name, description, damage/effect info. Player can Confirm (lock in choice) or Cancel (go back).

Key changes:
- Infrastructure/UI: Preview panel or modal component
- Reads ability data from existing Ability entities (name, description, damage fields)
- Confirm → submits action to BattleEngine (existing `submit_player_action`)
- Cancel → returns to ability selection

Depends on: Task 1 (submit/undo flow)

---

## Task 5 — HP Display + Floating Damage Numbers
**Priority:** Medium | **Layers:** UI (Infrastructure) | **Complexity:** Medium

Current state: HP bars exist but without numeric values. Damage only visible in Battle Log text.

Target state: Each character shows "current/max HP" numerically (e.g., "78/115"). When damage is dealt, a floating red number ("-42") animates upward and fades out over ~2 seconds. Critical hits use a different color/size.

Key changes:
- Infrastructure/UI: Add numeric HP label next to each health bar
- Floating damage: Tkinter Canvas text item + `after()` animation loop (move up + fade)
- Color coding: red for normal damage, yellow/larger for crits, green for healing
- Numbers appear during execution phase, tied to AbilityResolver results

Depends on: Task 1 (execution phase timing for animation sync)

---

## Task 6 — Expanded Card Pool
**Priority:** Low | **Layers:** Domain (JSON data) + UI | **Complexity:** Low

Current state: 3 cards available (Full Heal, Iron Skin, Quick Feet). Player always sees the same 3.

Target state: Pool of 10+ cards in JSON data. Each round, player is offered 3–4 random cards from the pool to choose from. More variety → more strategic depth.

Key changes:
- Domain/Data: Expand `cards.json` with 7+ new cards (attack buffs, debuffs, shields, poison, speed manipulation, etc.)
- Application: Card selection service picks random subset from pool each round
- UI: Card Select Screen handles variable card offerings
- Balance: New cards should create meaningful choices, not obvious best picks

Depends on: nothing (can be done in parallel with Tasks 2–5)

---

## Future Considerations (Phase 3+)

| Item | Notes |
|------|-------|
| Card visual redesign | Card-style UI with art, rarity, borders (reference: collectible card games) |
| Turn order bar | Visual indicator showing who acts next (reference: Raid: Shadow Legends top bar) |
| UI engine migration | Replace Tkinter with Pygame or Godot for animations, sprites, sound, potential 3D |
| Multiplayer | Player vs Player over network (WebSocket server) |
| Character roster expansion | More characters with unique abilities beyond Nova/Stone/Ace |

---

## Task File Convention

Each task has a detailed agent prompt saved to `.github/tasks/task-XX-[name].md`.

Usage: `@.github/tasks/task-01-planning-phase.md`
