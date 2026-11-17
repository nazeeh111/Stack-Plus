# Combat

## Overview
Arena combat produces rewards used by the economy. This older document has no Summary section.

## Player Fantasy
Win by reading attacks and choosing safe openings, supporting readable combat mastery.

## Detailed Rules
- Every successful attack deals at least 10 damage after all modifiers, including curses.
- A kill gives exactly 100 gold and 60 XP. Economy receives the gold reward event.
- Dying removes exactly 25 gold from the player's current purse, floored at zero.
- A quest may complete on the same kill and award 120 XP. The XP handler emits a level-up event as soon as XP crosses each 100-XP threshold. Re-entrant reward handling during an outstanding level-up is unspecified.
- Buying equipment requests an economy transaction and applies shared_reward_multiplier once to the next kill's gold.

## Formulas
- weapon_damage target:90–110 damage per attack.
- kill_gold = 100 gold per kill.
- level_threshold = 100 XP per level.
- shared_reward_multiplier = 2, applied once per rewarded kill.

## Dependencies
Depends on economy.md for equipment purchases and purse writes. No dependent systems are declared.

## Tuning Knobs
Combat owns shared_reward_multiplier and weapon_damage.

## Acceptance Criteria
- No attack, cursed or otherwise, deals less than 10 damage.
- A death with at least 25 gold removes exactly 25 gold.
- Simultaneous kill and quest rewards must not duplicate or lose XP.
