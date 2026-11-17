# game-systems-review cross-GDD workflow — Phase 7: Handoff

> Part of the [complete cross-GDD method](../cross-gdd-review.md). Use the [native mapping](../../NATIVE-BINDINGS.md) for execution and authority.

## Phase 7: Handoff

After the requested report is complete, summarize actionable findings and gaps. These source next-step choices are optional when useful; do not automatically start a new phase or ask a closing widget when no material decision remains.

Before building options, check project state:
- Are there any Warning-level items that are simple edits (flagged with "30-second edit", "brief addition", or similar)? → offer inline quick-fix option
- Are any GDDs in the "Flagged for Revision" table? → offer the requested single-GDD completeness review option for each
- Read systems-index.md for the next system with Status: Not Started → offer the owning game system design method option
- Is the verdict PASS or CONCERNS on a review that ran both passes? → offer the owning project readiness check or the owning architecture design method. A focus run (`consistency` or `design-theory`) checked one pass, so it never offers either

Build the option list dynamically — only include options that apply:

**Option pool:**
- `[_] Apply quick fix: [W-XX description] in [gdd-name].md — [effort estimate]` (one option per simple-edit warning; only for Warning-level, not Blocking)
- `[_] Run the requested single-GDD completeness review [flagged-gdd-path] — address flagged warnings` (one per flagged GDD, if any)
- `[_] Run the owning game system design method [next-system] — next in design order` (include only if requested and the actual system exists)
- `[_] Run the owning architecture design method — begin architecture (verdict is PASS/CONCERNS)` (include only if the verdict is PASS or CONCERNS on a review that ran both passes — never on FAIL, NOT ASSESSED or a focus run)
- `[_] Run the owning project readiness check — validate Systems Design phase gate` (include if verdict is PASS on a review that ran both passes)
- `[_] Stop here`

Assign letters A, B, C… only to included options. Recommend only an action justified by the current scope and evidence.

Print the actual verdict and useful next action. Save a durable decision in the owning task record when needed; no studio automation mode, widget or decision-log hook is installed.

---
