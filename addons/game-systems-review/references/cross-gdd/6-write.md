# game-systems-review cross-GDD workflow — Phase 6: Write Report and Flag GDDs

> Part of the [complete cross-GDD method](../cross-gdd-review.md). Use the [native mapping](../../NATIVE-BINDINGS.md) for execution and authority.

## Phase 6: Write Report and Flag GDDs

Save the requested review within existing artifact authority to the owning project's report location; the source convention is `design/gdd/gdd-cross-review-[date].md`. Preserve existing files. Ask only when the destination or scope is materially unresolved.

> **`[date]` here means ISO 8601 — `YYYY-MM-DD`, e.g.
> `gdd-cross-review-2026-08-19.md`. This is not a style preference.**
> The source's archived incremental helper picks the prior review with
> `sort | tail -1`, so lexical order IS chronological order only for ISO dates.
> Written as `aug-19-2026` or `19-08-2026`, the wrong file is chosen as the
> baseline, the changed-set is computed from it, and GDDs modified since the
> real last review silently escape the next one. That is the same
> quiet-escape failure the three fixes documented at the top of that script
> exist to prevent.

If GDDs are flagged, update the owning systems index only within the actual requested scope; otherwise report the proposed status edits. Preserve unrelated rows. When the project uses the source's exact `Needs Revision` status, do not append parentheticals that its consumers cannot parse.

### Session State Update

When a durable handoff is needed, update the existing owning task record, not a new studio log, with these fields:

    ## Session Extract — game-systems-review cross-GDD workflow [date]
    - Verdict: [PASS / NOT ASSESSED / CONCERNS / FAIL]
    - GDDs reviewed: [N of M present]
    - Phases not run: [names, or "None"]
    - Flagged for revision: [comma-separated list, or "None"]
    - Blocking issues: [N — brief one-line descriptions, or "None"]
    - Recommended next: [the Phase 7 handoff action, condensed to one line]
    - Report: design/gdd/gdd-cross-review-[date].md   ← only when actually saved within authority
    - Report: (not written — user declined at [date])  ← only if user declined the write

Use the appropriate line for the actual report result. Reuse the existing task record; if no durable handoff is needed, the requested report is sufficient. Confirm only what was actually saved.

---
