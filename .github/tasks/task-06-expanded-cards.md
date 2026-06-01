# Task 06 — Expanded Card Pool

## Context
Read `CLAUDE.md` and `ARCHITECTURE.md` before starting.
Read `roadmap.md` in the project root for full Phase 2 plan.

Tasks 01-05 are completed. Battle system is fully functional with planning phase, speed ordering, ultimate cooldowns, attack previews, HP display, and floating damage. Currently there are only 3 cards (Full Heal, Iron Skin, Quick Feet) and the player sees the same 3 every round. This task expands the card pool and adds random card offering.

## Goal
1. Expand the card pool from 3 to 12+ cards with diverse strategic effects
2. Each round, offer the player a random selection of 3-4 cards from the pool
3. Cards should create meaningful strategic choices — no obvious "always pick this" cards

## Requirements

### Domain Layer (`src/circle_cycle/domain/`)

1. Review existing Card entity and CardEffect value object:
   - Understand how current cards (Full Heal, Iron Skin, Quick Feet) are structured
   - Understand what fields exist: name, description, stat affected, amount, target type, etc.
   - All new cards MUST use the same structure — do NOT change the Card/CardEffect schema unless absolutely necessary

2. If the Card entity lacks a `rarity` field — add one:
   - New enum `CardRarity` in `domain/enums/`: COMMON, RARE, EPIC
   - Add `rarity: CardRarity` field to Card entity
   - Existing 3 cards: assign COMMON rarity
   - This enables weighted random selection (rarer cards appear less often)

3. Design 9+ new cards (total pool = 12+). Ensure balance across categories:

   **Offensive (3-4 cards):**
   - "Battle Cry" — Increase attack by 10 for selected character (COMMON)
   - "Precision Strike" — Increase critical chance by 15% for selected character (RARE) — only if crit mechanic exists, otherwise: "Increase attack by 20" 
   - "Flame Enchant" — Next attack applies burn (2 turns, 5 damage/turn) for selected character (RARE)
   - "Berserker Rage" — Increase attack by 25 but decrease defense by 10 for selected character (EPIC)

   **Defensive (3-4 cards):**
   - "Stone Wall" — Increase defense by 15 for selected character (COMMON)
   - "Regeneration" — Heal 10 HP per turn for 3 turns for selected character (RARE)
   - "Mirror Shield" — Reflect 20% damage back to attacker for 2 turns (EPIC)
   - "Team Heal" — Restore 15 HP to ALL player characters (RARE)

   **Utility (2-3 cards):**
   - "Adrenaline Rush" — Reduce Ultimate charge requirement by 1 for selected character (this round only) (EPIC)
   - "Slow Trap" — Reduce speed by 8 for a random enemy character (RARE)
   - "Second Wind" — If selected character HP drops below 20%, auto-heal 25 HP once (RARE)

   IMPORTANT: These are suggestions. Check what CardEffect and CardApplicator currently support. If the current system only supports simple stat changes (HP, DEF, SPD), then:
   - SKIP cards that need new mechanics (reflect, regen over turns, conditional triggers)
   - ONLY add cards that work within existing CardEffect structure
   - Document which cards were skipped and why — they can be added when CardApplicator is extended
   
   Aim for at least 10 total cards that work with the current system.

### Domain Data (`data/`)

4. Update `cards.json` (or wherever card data is stored):
   - Add all new cards following existing JSON schema exactly
   - Include: name, description, effect values, rarity, target type
   - Validate JSON structure — agent must run the app and confirm cards load without errors

### Application Layer (`src/circle_cycle/application/services/`)

5. Add card offering logic — new service or method:
   ```python
   def get_card_offering(pool: list[Card], count: int = 3) -> list[Card]:
       """Select random cards from pool to offer the player."""
   ```
   - Weighted by rarity:
     - COMMON: 60% chance to appear
     - RARE: 30% chance to appear  
     - EPIC: 10% chance to appear
   - No duplicate cards in a single offering
   - If pool has fewer cards than `count`, return all available
   - Use `random.choices` with weights or similar approach

6. Integrate with existing battle/round flow:
   - Find where card selection happens between rounds (Card Select Screen)
   - Replace the current "show all 3 cards" with `get_card_offering()` result
   - Player still picks from the offered cards (same UI interaction, different pool)

7. Update `CardApplicator` if needed:
   - If new cards use effects that CardApplicator doesn't handle → extend it
   - Each new effect type should be a clean if/elif branch or strategy pattern, not a tangled mess
   - If CardApplicator becomes too complex → consider refactoring to a strategy/handler pattern, but only if there are 5+ effect types

### Infrastructure Layer (`src/circle_cycle/infrastructure/ui/`)

8. Card Select Screen updates:
   - Display 3-4 cards (based on offering) — layout may need to accommodate 4 instead of 3
   - Show rarity indicator on each card:
     - COMMON: gray/white border
     - RARE: blue border
     - EPIC: purple/gold border
   - Show card description text (already exists but verify it works with new cards)
   - If a card affects "all allies" or "random enemy" → display that clearly in the card text

9. Add a "Reroll" option (optional, nice-to-have):
   - Button that generates a new random offering (once per round)
   - Costs something? For now, free — balance later
   - If too complex, skip and document as future feature

## Constraints
- Do NOT change battle mechanics (BattleEngine, AbilityResolver) unless a new card requires it
- Do NOT add cards that require mechanics not yet in the game (e.g., don't add "reflect damage" if there's no reflect system)
- New cards must load from JSON — no hardcoded card data in Python
- Existing 3 cards must still work exactly as before
- Card balance: no single card should be obviously stronger than all others at the same rarity

## Testing
- Unit tests:
  - `get_card_offering` returns correct count (3 or 4)
  - `get_card_offering` returns no duplicates
  - `get_card_offering` handles pool smaller than count
  - All cards in JSON load without errors (data integrity test via JsonDataRepository)
  - Each new card can be applied via CardApplicator without errors
  - Rarity distribution: over 1000 calls, COMMON appears more than RARE, RARE more than EPIC (statistical test with tolerance)
  - Existing cards (Full Heal, Iron Skin, Quick Feet) still work unchanged
- Run ALL existing tests: `python -m pytest`
- Fix any broken tests before committing

## Documentation
- Update `CLAUDE.md` — document expanded card pool, rarity system, random offering
- Update `ARCHITECTURE.md` — add card offering service to application layer description
- Document each new card's effect in a comment block in the JSON file or in a separate `CARDS.md`
- If any suggested cards were SKIPPED due to system limitations, list them with reasons in `roadmap.md` under Future Considerations

## Verification
- Launch the game: `python -m circle_cycle` (check CLAUDE.md for run command)
- Full playthrough (3+ rounds):
  - Card Select Screen shows different cards each round (not always the same 3)
  - Rarity borders/indicators visible
  - Pick a new card → apply to character → effect works in battle
  - Existing cards still work (find Full Heal in offerings, apply it, verify healing)
  - No crashes when cycling through multiple rounds with random card offerings
  - Battle Log reflects card effects correctly
  - Play at least 5 rounds to verify randomization feels varied

## On completion
git add -A && git commit -m "feat: expand card pool with rarity system and random offering" on develop branch. Do NOT push.
Then run: powershell -Command "[Console]::Beep(1000,500)"
