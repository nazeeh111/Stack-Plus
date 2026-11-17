# Combat

## Summary
Three fights with fixed damage and a purse outcome owned by economy.

## Overview
Combat emits kill and death events. Economy writes the purse.

## Player Fantasy
Predictable damage and clear defeat consequences support the two game pillars.

## Detailed Rules
Every successful attack deals at least 10 damage after all modifiers, including
status effects. On death the player loses exactly 25 gold when the purse has
at least 25 gold, otherwise the purse becomes zero. Each death event is emitted
once and economy applies that loss once. Three victories end the session.

## Formulas
final_damage = max(10, modified_damage).
death_loss = min(current_gold, 25).

## Dependencies
Depends on economy.md for purse writes. Depended on by economy.md for death
events.

## Cross-References
| Target GDD | Specific Element Referenced | Nature |
|---|---|---|
| economy.md | purse writes | Economy applies combat's death loss |

## Acceptance Criteria
Final attack damage is never below 10. Death removes up to 25 gold exactly once.
