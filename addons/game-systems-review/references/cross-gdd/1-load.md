# game-systems-review cross-GDD workflow — Phase 1: Load Everything

> Part of the [complete cross-GDD method](../cross-gdd-review.md). Use the [native mapping](../../NATIVE-BINDINGS.md) for execution and authority.

## Phase 1: Load Everything

**In this file:**

- Phase 1a — L0: Summary Scan (fast, low tokens)
- Phase 1b — Registry Pre-Load (fast baseline)
- Phase 1c — L1/L2: Section Load

### Phase 1a — L0: Summary Scan (fast, low tokens)

Before reading any full document, use a native text search to locate `## Summary` sections
from all GDD files:

```
rg -n -A 5 "## Summary" design/gdd/*.md
```

**Fail open on a missing Summary.** Establish the denominator: glob
`design/gdd/*.md` and count **N**. A scan matching fewer than N means those GDDs
predate `## Summary` — never treat an absent Summary as a system out of scope.
A zero-match scan means "no GDD carries a Summary yet", not "nothing to review".
This review is holistic and loads its in-scope GDDs regardless (see Phase 1c);
the Summary scan only builds the manifest and narrows `since-last-review`, it
never shrinks the review set.

Display a manifest to the user:
```
Found [N] GDDs. Summaries:
  • combat.md — [summary text]
  • inventory.md — [summary text]
  ...
```

For `since-last-review`, follow [native incremental scope](../../NATIVE-BINDINGS.md#incremental-scope). With no verified prior receipt or complete changed/dependency set, use full review and disclose the fallback. A filename date or mtime alone is not proof of the reviewed source generation. Record the exact changed set, missing/deleted inputs and dependency expansion before reading sections. This integration does not execute the archived studio helper.

### Phase 1b — Registry Pre-Load (fast baseline)

Before full-reading any GDD, check for the entity registry:

```
Read the owning game's design/registry/entities.yaml when present.
```

If the registry exists and has entries, use it as a **pre-built conflict
baseline**: known entities, items, formulas, and constants with their
authoritative values and source GDDs. In Phase 2, grep GDDs for registered
names first — this is faster than reading all GDDs in full before knowing
what to look for.

If the registry is empty or absent: proceed without it. Note in the report:
"Entity registry is empty — consistency checks rely on full GDD reads only.
An entity-registry consistency pass is an optional follow-up only within requested scope."

### Phase 1c — L1/L2: Section Load

Read whole (small, and every part is used):

1. `design/gdd/game-concept.md` — game vision, core loop, MVP definition (or
   `design/game-brief.md`, the one-page brief that replaces it at `rigor: minimal` —
   pitch, core loop, Features list)
2. `design/gdd/game-pillars.md` if it exists — design pillars and anti-pillars
3. `design/gdd/systems-index.md` — authoritative system list, layers, dependencies, status

Read each document by complete relevant sections with supported native file tools. Locate headings with `rg -n "^#"`; accommodate the actual tool's output limits without dropping content. There is no imported 40 KB host read rule.

For **every in-scope system GDD**, admit all rule-bearing sections. Read small
GDDs in full. For a large structured GDD, locate its headings and scan the prose
for rules, invariants and overrides before narrowing complete section reads.
The usual consumed sections are:

```
rg -n "^## (Dependencies|Cross-References|Detailed Rules|Detailed Design|Edge Cases|Formulas|Tuning Knobs|Acceptance Criteria|Player Fantasy)" design/gdd/*.md
# Then read each located section to the next heading, not only a fixed search context.
```

Phase 2 needs dependency/reference declarations, rules, formulas, ownership and
acceptance criteria. Phase 3 needs player fantasy, progression/reward structure
and the game's pillars. **Edge Cases is included**: minimum/maximum states,
floor bypasses, death/respawn, timing, stacking and combined-state rules can be
defined only there, with no link from Detailed Design. Phases 2 and 4 must read
those constraints before judging contradictions or interaction scenarios.

These headings are locators, not a closed whitelist. A rule in Overview or any
other heading is also an input, even if no admitted section references it. Read
each rule-bearing section completely and follow its relevant cross-references.
If the scan cannot establish where all relevant rules live, read that GDD in
full or mark the uncovered material NOT ASSESSED. Never count an omitted
rule-bearing section as reviewed just because other expected headings matched.

Accept **either** `## Detailed Rules` or `## Detailed Design`; the design standard
and the GDD template disagree on the name and they denote the same section.

**Escalate to a full read of one GDD** when relevant rule coverage cannot be
established, a scanned section cross-references material outside itself that
cannot be bounded, or a GDD matched **zero** sections — that GDD predates the
template, and a zero-match there means "unstructured", not "empty".
Never let a zero-match silently drop a system: the scan narrows the *read*, it
never shrinks the *review set*.

Report: "Loaded [N] system GDDs covering [M] systems. Pillars: [list]. Anti-pillars: [list]."

If fewer than 2 system GDDs exist (count the files present; an empty one is handled under NOT ASSESSED in Phase 5, not here), stop:
> "Cross-GDD review requires at least 2 system GDDs. Write more GDDs first,
> then re-run `game-systems-review cross-GDD workflow`."

---
