# Economy

## Summary
Convert arena gold into equipment; meaningful equipment choices should continue throughout a session.

## Player Fantasy
Choose equipment deliberately, supporting meaningful purchases throughout a session.

## Detailed Design
- All income is uncapped kill rewards. There is no ongoing sink.
- One permanent sword costs 50 gold and can be purchased once. There are no other purchases.
- Death preserves all gold. Economy never subtracts gold on a death event.
- A purchased curse bypasses every combat damage floor and can reduce final attack damage to zero.
- Every 1000 accumulated gold increases kill rate by 10% permanently. Kill rewards remain uncapped and unchanged, so higher kill rate increases gold income.
- The reward listener applies shared_reward_multiplier to every kill's reward after combat has applied it.

## Formulas
- incoming_kill_gold expected range:8–12 gold per kill, after all combat modifiers.
- sword_cost = 50 gold.
- Inventory capacity uses the encumbrance formula from combat.md.

## Dependencies
No dependencies or dependents.

## Tuning Knobs
Economy owns shared_reward_multiplier, default 2, as the final gold reward multiplier.

## Acceptance Criteria
- Gold is unchanged on death.
- A curse can produce zero final attack damage.
- Reward pacing stays between 8 and 12 gold per kill.
