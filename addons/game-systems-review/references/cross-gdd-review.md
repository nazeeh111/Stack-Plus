# Review All GDDs

This skill reads every system GDD simultaneously and performs two complementary
reviews that cannot be done per-GDD in isolation:

1. **Cross-GDD Consistency** — contradictions, stale references, and ownership
   conflicts between documents
2. **Game Design Holism** — issues that only emerge when you see all systems
   together: dominant strategies, broken economies, cognitive overload, pillar
   drift, competing progression loops

**This is distinct from `the requested single-GDD completeness review`**, which reviews one GDD for internal
completeness. This skill reviews the *relationships* between all GDDs.

**When to run:**
- After all MVP-tier GDDs are individually approved
- After any GDD is significantly revised mid-production
- Before `the owning architecture design method` begins (architecture built on inconsistent GDDs
  inherits those inconsistencies)

Use the [native callback mapping](../NATIVE-BINDINGS.md) for input, review coverage, writing and follow-up behavior. Read [game evidence qualifications](method-notes.md) before evaluating the design-theory examples.

**Argument modes:**

**Focus:** `the requested scope` (blank = `full`)

- **No argument / `full`**: Both consistency and design theory passes
- **`consistency`**: Cross-GDD consistency checks only (faster)
- **`design-theory`**: Game design holism checks only
- **`since-last-review`**: Only GDDs modified since the last review report (git-based)

---

**Existing project requirements.** Use the owning game's actual document requirements and explicit review scope. The source's tiers describe coverage when that project already uses them: full covers all eight sections; standard requires five with numeric Formulas conditional, and treats optional sections as advisory. No tier, project configuration or required artifact is installed by this skill. Voluntarily authored GDDs remain reviewable at minimal. No GDDs means missing inputs, never a clean pass. See [native input mapping](../NATIVE-BINDINGS.md#project-inputs).

## Phase 1: Load Everything

**Read [1-load.md](cross-gdd/1-load.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

### Complementary review passes

Consistency and design theory consume the same admitted GDD set and produce separately labeled findings. Apply both directly, or use supported bounded native reviewers when useful and authorized. No fixed pair, studio roster or model change is required. Record which work was direct and which review was independent.

Provide a reviewer the complete phase-relevant source content or readable native paths with exact revision/hash and clear permission to read them: consistency needs Dependencies, Cross-References, Detailed Design/Rules, Edge Cases, Formulas, Tuning Knobs and Acceptance Criteria, plus any rules elsewhere in the document; design theory needs Player Fantasy, progression/reward structure and the game pillars. Interaction scenarios consume all applicable rules, including edge-only overrides. Supply the loaded entity registry and actual engine/version constraints when relevant. Search excerpts must not truncate the material needed for a finding. Verify that each pass produced its promised report before combining results; absent output is not a clean result.

## Phase 2: Cross-GDD Consistency

**Read [2-consistency.md](cross-gdd/2-consistency.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Phase 3: Game Design Holism

**Read [3-design-holism.md](cross-gdd/3-design-holism.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Phase 4: Cross-System Scenario Walkthrough

**Read [4-scenarios.md](cross-gdd/4-scenarios.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Phase 5: Output the Review Report

**Read [5-report.md](cross-gdd/5-report.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Phase 6: Write Report and Flag GDDs

**Read [6-write.md](cross-gdd/6-write.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Phase 7: Handoff

**Read [7-handoff.md](cross-gdd/7-handoff.md) now and follow it** — this phase's steps are in that file, not here. Read it again if the conversation was compacted or resumed during this phase.

## Error Recovery Protocol

Verify every promised report or artifact actually exists and supports the reported coverage. If a pass is blocked or returns no output, surface its missing input/output, continue independent work, and preserve a partial report with NOT ASSESSED coverage. Never invent the missing pass. Resume an available reviewer only within existing authority and proportional scope; do not launch an automatic pipeline. Use [native recovery](../NATIVE-BINDINGS.md#review-coverage-and-recovery).

## Collaborative Protocol

1. **Read the admitted scope** before judging its relationships; report the manifest and gaps.
2. **Show both analyses** before acting on findings, unless the user requested only one focus.
3. **Distinguish blocking from advisory** with evidence for each classification.
4. **Preserve design authority**: flag conflicting rules and options; do not choose which design wins without source evidence or the user's material decision.
5. **Write within actual authority** using the existing task/report conventions; no per-write ritual or studio session log is required.

6. **Be specific** — every issue must cite the exact GDD, section, and text
   involved; no vague warnings
