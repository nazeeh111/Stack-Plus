# Combat

## Summary
Three fights award gold to the economy, with no XP or repeated-session progression.

## Overview
Combat owns damage; economy owns rewards and purse writes.

## Player Fantasy
Reading attacks and choosing safe openings supports readable combat mastery.

## Detailed Design
Successful attacks deal 100 damage. Kills request a 10-gold reward from economy. After three victories the session ends and the purse resets. Death removes up to 5 gold, through economy, and restarts the current fight. Equipment alters visual feedback only; there is no stacking modifier.

## Formulas
weapon_damage target 100 damage per attack. Requested kill_gold target 10 gold per kill.

## Dependencies
Depends on economy.md for reward and death purse writes. Depended on by economy.md for kill/death events.

## Cross-References
| Target GDD | Specific Element Referenced | Nature |
|---|---|---|
| economy.md | kill_gold | Reward request:10 gold |
| economy.md | death_loss | Purse write:up to 5 gold |

## Tuning Knobs
Combat owns weapon_damage, target 100.

## Acceptance Criteria
Every attack deals 100 damage; one kill requests 10 gold once; a death requests one loss of up to 5 gold; three wins end the session.
