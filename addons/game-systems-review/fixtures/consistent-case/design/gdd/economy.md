# Economy

## Summary
A finite purse with one optional purchase before the third and final fight.

## Overview
Economy owns rewards, purse writes and prices. No XP or power progression.

## Player Fantasy
One deliberate equipment purchase supports the intended session's equipment choice.

## Detailed Rules
A kill event grants 10 gold once. A death event removes min(current_gold,5) gold. One optional cosmetic shield costs 15 gold and can be bought once after the second victory. There are no modifiers, interest or other income. The session ends after three victories, and the purse resets, so no reward loop continues indefinitely. Keeping the remaining gold to the end is an intentional score choice.

## Formulas
kill_gold target 10 gold per kill; death_loss target 5 gold maximum per death; shield_cost target 15 gold.

## Dependencies
Depends on combat.md for kill/death events. Depended on by combat.md for reward and death purse writes.

## Cross-References
| Target GDD | Specific Element Referenced | Nature |
|---|---|---|
| combat.md | kill/death events | Each event handled once |

## Tuning Knobs
Economy owns kill_gold, death_loss and shield_cost. Their targets are 10,5 and 15 respectively.

## Acceptance Criteria
Each kill grants 10 gold once; death loses up to 5 gold;15 gold buys the shield once; no purse survives a completed session.
