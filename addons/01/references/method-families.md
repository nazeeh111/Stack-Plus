# Distinguish useful contributions

These overlapping views help compare methods. They do not prescribe combinations or replace complete skills. Use current native IDs; prior IDs remain lookup aliases. Runtime readiness and authority must be checked separately.

| Need | Candidate contribution | Difference that changes the choice |
|---|---|---|
| Editorial diagram or chart | editorial-svg-diagrams | Self-contained HTML/inline SVG, readable composition and explicit fidelity to supplied source. |
| Validated diagram or explainer application | validated-html-diagrams-and-explainers | Structured diagram contract, CLI validation/finalization and browser verification. |
| Give a presentation a coherent visual design | presentation-visual-design, when installed | Visual identity, slide composition and data treatment alongside native presentation authoring; retain editable content, inspect rendered slides and use pptx-quality-gates for local PPTX. |
| Operate a physical mechanism interactively | interactive-mechanism-explainers | Physical parts, fixed isometric cutaway and meaningful controls tied to the real process. |
| Design a new interface with Hallmark | ui-design-hallmark, when installed | Interface direction, tokens and static/rendered checks; preserve user references and pair with behavior/accessibility methods when those add distinct checks. |
| Build pixel-art game effects | pixel-art-effects, when installed | Editable effect code, acted timing and PNG/sprite-atlas exports; validate actual output and metadata, not the process exit alone. |
| Inspect an existing interface | ui-quality-audit | Accessibility, responsive behavior, performance and implementation defects. |
| Give an interface visual direction | ui-art-direction or web-ui-design | Reference-led art direction versus implementation guidance for a distinctive new or reshaped UI. |
| Refine a working interface | ui-polish | Detailed visual refinement; it does not establish request/state correctness. |
| Handle request failure, racing updates or empty state | ui-reliability | Behavior and recovery under real asynchronous states. Pair with visual work only when both weaknesses exist. |
| Find the cause of a defect | diagnosing-bugs | Evidence-led diagnosis before repair. |
| Reproduce and repair an application failure | application-test-fix-verify | Hands-on browser/API/CLI reproduction, bounded repairs and regression verification. |
| Review a patch | code-diff-review | Structural defects, weakened checks and related callers. |
| Assess consequences beyond a patch | change-impact-review | Wider dependents, state and assumptions beyond the visible change. |
| Review a patch for vulnerabilities | security-change-review or the native Codex Security diff method | Security-focused attack/impact reasoning; a general diff review is not a security audit. |
| Verify execution-backed security claims or fixes | code-security-review and security-finding-verification | Preserve a pristine baseline; independently check trigger, patch and completed evidence gates. Failed or contradictory verification is unresolved. |
| Design code boundaries or competing architectures | module-interface-design or code-architecture-planning | Deep module interfaces versus competing sketches and synthesis. |
| Review an implementation plan | engineering-plan-review | Scope, failure modes, tests and rollout before implementation. |
| Keep concurrent writers or retries correct | concurrent-state-ownership and idempotent-operation-design | Who may mutate shared state versus whether an interrupted/repeated effect is safe. These address different failure modes. |
| Judge measured performance | performance-benchmark-review | Whether the measurement supports the claim, separately from performance optimization. |
| Frame a product problem | product-discovery-consultation | Product framing, alternatives and a practical design; not general engineering approval. |
| Plan a scientific experiment | experimental-design, statistical-power | Design and dependence assumptions before data; sample-size calculations depend on that design. |
| Analyze measurements | uncertainty-and-units, statistical-analysis | Measurement model/units/covariance versus inferential test/model choice and evidence. |
| Discover or synthesize literature | paper-lookup, literature-review, academic-deep-research | Targeted records versus a reproducible synthesis or a broader research workflow. |
| Research video content | agent-reach-platform-reading with native media tools | Preserve timed captions; inspect selected visual/audio intervals when the answer depends on them. A transcript alone is not watched video. |
| Write or review research | scientific-writing, ml-paper-writing, scientific-peer-review, academic-paper-panel-review | Scientific reporting, ML venue manuscript craft, manuscript peer-review drafting, or a panel workflow. Read actual scope before loading a whole pipeline. |
| Turn results into claims | experiment-claim-validation, scientific-critical-thinking | What completed results support versus broader appraisal of evidence/design. |
| Draft and review software specifications | design-specification-workflow, when installed | EGM-derived design documents, fresh-reader review, findings resolution and code/document comparison; choose only the needed stage. |
| Operate an explicitly authorized iPhone Mirroring target | iphone-mirroring-automation, when installed | OCR-guided steps and checked replay; verify the target, pairing and macOS permissions. Skill/protocol checks do not establish live phone readiness or authorize global MCP registration. |
| Coordinate substantial specialist work | multi-model-agent-orchestration | Native workers, owned artifacts, handoffs and integration; it does not replace 01's ongoing capability selection. |
| Compare independent answers or perspectives | llm-council-answer-review, persona-decision-council, business-council-roast-room | Anonymous answer review, persona-based deliberation, or a business council. None proves artifact correctness merely by agreement. |

Functional categories describe contribution, domain and artifact independently. For example, a measurement report may need numerical reasoning, a truthful figure, interface reliability and a repeatable export. A shared domain is not enough to justify combining methods; identify the missing contribution and compatible handoff.

The machine-readable cards are curated navigation summaries with description fingerprints. A changed description invalidates its card. An unchanged description does not prove an unchanged body: follow the selected current source before applying a boundary or method. New host/plugin capabilities remain discoverable even before they have cards.

## Discover only what the work needs

Resolve 01's actual folder and use its helper when current native summaries are insufficient:

```text
python3 <01-folder>/scripts/capabilities.py CONCEPT OPERATION FAILURE
python3 <01-folder>/scripts/capabilities.py --need "measurement uncertainty" --need "asynchronous race"
python3 <01-folder>/scripts/capabilities.py --browse work
```

Views also include `domains` and `artifacts`. Optional filters use `--work`, `--domains` and `--artifacts`; membership overlaps, with OR within a facet and AND across facets. Browsing includes complete member IDs plus bounded examples, not a preferred shortlist. Remove filters to consider new or unclassified methods. Runtime invocation/readiness metadata and connected host tools remain separate from skill cards.

Repeated --need queries share one fresh observation within that command, including bounded body reads; each later command starts fresh. Per-need provenance describes that shared observation, not extra physical reads. Facet filters apply before body reads, so excluded methods cannot consume the selected scope's allowance. Oversized identity/prose metadata is omitted explicitly rather than flooding the result.

Queries match words, phrases and simple plurals; an exact identifier is a lookup, and a rank is a retrieval lead. Refine weak matches with alternate concepts. Add `--body` when summaries miss a useful technique or a consequential distinction. This reads bounded current SKILL bodies with inert excerpts and provenance, never supporting files or discovered code. Negative or misleading text can match, so read complete selected methods before applying them. Do not treat a lexical top hit as the best combination.

For a concrete remaining method gap, select find-skills without requiring the user to name it. Read its complete current method/native binding, identify the need, search the public directory with specific terms and inspect promising source. Popularity is a lead, not quality evidence. Reuse installed methods when adequate; carry a justified acquisition through source/dependency/rights review, required admission/trial checks and actual use within authority. Keep private context out of external searches and heavy dependencies project-scoped. An unsuitable search result is a reason to work directly or report the gap, not to install a weak match.

Domains now include explicit reverse-engineering, automation and workflow groups. These overlap the existing design, media, coding, research and infrastructure views; a group is not a required pipeline. Additional user-owned methods are attached only when their current description matches a navigation card. Skills supplied dynamically by a host/plugin still require native discovery.
