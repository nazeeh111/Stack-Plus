# Economy

## Summary
A finite purse for three fights; death costs are requested by combat.

## Overview
Economy owns purse writes and listens to combat events.

## Player Fantasy
A clear purse outcome on defeat supports legible death costs.

## Detailed Design
Handle each combat death event once by applying its requested purse loss.
No interest, farming rewards or repeatable purchases exist. The purse resets
after the third victory.

## Dependencies
Depends on combat.md for death events. Depended on by combat.md for purse writes.

## Cross-References
| Target GDD | Specific Element Referenced | Nature |
|---|---|---|
| combat.md | death events | Apply each requested purse loss once |

## Acceptance Criteria
No death event is handled twice. A completed session retains no purse.

## Edge Cases
The Null Seal status overrides every damage floor: while active, an attack
with modified damage below 10 resolves to zero final damage. The same status
preserves the entire purse on death and suppresses all requested gold loss,
even when current_gold is at least 25.
