# User-supplied tiers and checked specialist work

This is a portable coordination method. It installs no router, model roster, provider, daemon or storage service. Read the actual [host mechanisms](hosts.md) before dispatch. The user's current lead and effort stay selected. ChatGPT, Codex and OpenCode are active hosts; analogies to another product's model family do not activate that product's retired workflows.

## Record only the user's mapping

The user may say, “keep this lead, use my selected worker Y for bounded work and Z for simple extraction.” Resolve those labels to the exact user-supplied, host-supported selectors. Do not guess brands, variants or a permanent hierarchy. A chat mapping is sufficient; when continuity needs a file, copy [the empty profile](../examples/tier-profile.json) into the existing task directory. This is a human-readable task record, not host configuration or an automatically loaded file. Do not edit the installed example or create persistent custom agents to activate it.

For each supplied tier, record its exact selector, user authority, permitted effort/variant, availability evidence/date, tool/context limits and relevant observed task results. Record task scope and any request/token/time/cost caps separately. A task profile may use arbitrary tier names; Y and Z are illustrative relative labels. With no mapping, `tiers: {}` or a null selector, omit native model and effort overrides so the worker inherits the current model and effort. Confirm host inheritance: a preconfigured specialist model is not the current model. If that host cannot preserve requested inheritance without changing configuration, choose an eligible inherited worker, keep the work with the lead or report the gap. An explicitly mapped but unavailable tier is unavailable, not an implicit fallback. Use another already authorized route only when it fits the task; disclose the change.

Verify availability using existing host metadata or its native model-list mechanism without inspecting credentials or making an inference test. A selector's presence proves neither tool support, account entitlement nor execution identity. A profile does not authorize a billed provider, spending, new credentials, access grants, native permission changes or changed lead/effort. A finite budget is a ceiling inside authority, never spending authority by itself. If the host cannot enforce a hard cap, disclose that before work that requires one; do not promise a prompt-based hard limit.

The empty example deliberately supplies no Y/Z models. Do not run mixed-model trials until the user supplies the mapping and the host permits it. Preserve source-backed native selection rules, including explicit model requests where required. `requested_selector`, host-reported metadata and independently attested effective identity are separate observations. Record unknown identity or usage as unknown, even when a tool accepted the request.

## Choose the contribution, then the tier

Before dispatch, name the expected useful result and the cheapest trustworthy acceptance check. Consider ambiguity (how much judgment is needed), error detectability (whether a test or source comparison exposes a wrong answer), dependency risk (what relies on this result), tool/context fit and integration overhead. Task length or an agent's confidence alone is insufficient.

| Contribution | Allocation and acceptance |
| --- | --- |
| Deterministic extraction or a constrained transformation | A user-configured lower tier can fit when the lead can check against complete source, exact counts, a schema or an executable test. The check must catch omissions, not only parse valid output. |
| Bounded implementation or source investigation | Choose an available mapped tier with the needed tools/context and relevant task evidence. Specify ownership, source versions, tests and what remains for integration. Split an investigation from shared-code editing when they can contribute independently. |
| Ambiguous design, conflicting evidence or a dependency with broad consequences | Keep the decision with the chosen lead or an appropriately supported mapped specialist, then obtain fresh independent review. A lower-tier self-rating or relative label is insufficient evidence for acceptance. |
| Trivial or tightly coupled work | The lead can finish directly when coordination/review overhead exceeds the expected contribution. Do not create busywork to use every tier or slot. |

Start unproven mappings with bounded, verifiable contributions when such work is actually needed. A failed extraction does not prove every task is unsuitable, and one accepted task does not establish general quality. Reassess on task-specific evidence. Calibration is useful only for a real recurring need and existing authority; do not start a benchmark campaign from this method. Do not remove required tools or silently shrink context to make an unsuitable tier appear cheaper.

## Brief and bounded return

Use the [dispatch method](dispatch-and-review.md) and supply:

1. Outcome, authoritative input versions, selected complete skills/support and the dependency this contribution resolves.
2. Owned files or read-only scope; forbidden effects; available tools; integration owner; what the worker may decide and what must return to the lead.
3. Requested tier/selector or inheritance, effort constraints, finite attempts and task bounds. Choose caps suited to the work; do not invent a user spending budget. Say which caps are enforced by the host and which are supervisory stopping rules.
4. Acceptance conditions, source/test evidence and stopping conditions for missing prerequisites, ambiguity, denial, partial failure or a limit reached.

Request a compact structured handoff, as JSON or equivalent headings:

```text
task_id; status: complete | partial | blocked | failed
inputs: paths/revisions/hashes actually used; required_reads: observed or self-reported
result: artifact paths/hashes or source-supported findings
checks: command/source location, actual result and remaining gaps
uncertainties; remaining_work; partial_effects
requested_selector; requested_effort; host_reported_identity; effective_identity: known or unknown
usage: measured per-run dimensions, coverage and unavailable dimensions; cost: measured/estimated/unknown
```

Keep the handoff bounded to what integration needs; preserve detailed evidence beside the task. A request to return these fields does not prove the worker complied or read required files.

## Accept or recover

The lead checks the actual artifacts before merging contributions. Reject unrelated boilerplate, invented sources, unsupported conclusions, missing required inputs, stale revisions, unauthorized effects or claims unsupported by executed checks. `complete` is only a worker assertion. A complete-looking JSON object or passing style check cannot establish substantive correctness. Validate source fidelity and the failure cases relevant to the contribution, then exercise affected interfaces after integration.

Treat failed/partial/blocked, timeout, unread required source or unavailable evidence as incomplete. In particular, a failed reviewer with no findings is not a clean review. Preserve useful partial artifacts without promoting their unsupported conclusions. Record unresolved issues and reconcile external or partial effects before another attempt.

Before a retry, state the new hypothesis, why a changed brief/source/tool/authorized tier can resolve it, and the remaining attempt/time/budget cap. Do not repeat the same failing request or automatically walk every tier. Escalate to another already configured, available and authorized tier only for a concrete reason; otherwise let the lead diagnose, finish directly or report the missing capability. Stop at the cap or a native denial. Never retry through another tool/provider to bypass a rejected permission.

For ambiguous or consequential outcomes, use a fresh reviewer with the requirements, integrated artifact and relevant source, without the author's favored verdict. Independence needs a fresh context or separately disclosed limit, not a different brand. The lead resolves disagreements against source and tests, owns the final integration and reports review incompleteness. Maintain one writer per artifact throughout recovery and integration.

## Measure accepted outcomes honestly

Record accepted/rejected contributions, verification and retry overhead, elapsed time and measured per-run usage when exposed. Partial usage is a lower-bound observation with named coverage, not a total. Null/missing means unknown; an explicit measured zero is different. Separate token categories, cached/reasoning tokens when exposed, currency/rate date and provider billing from subscription-limit usage. Do not sum incomparable units or infer monetary cost from an aggregate token count across models. Report estimates with their assumptions. No telemetry is installed by this method.

## Research basis and limits

[FrugalGPT (Chen, Zaharia and Zou, 2023, v1)](https://arxiv.org/abs/2305.05176v1) learns cascades using labeled examples, response-quality scoring and cost constraints. Its API query benchmarks support investigating selective allocation with acceptance checks. They do not establish that any user's Y/Z pair can safely perform open-ended engineering work. Our bounded retry/lead integration procedure is an authored adaptation, not execution of that learned cascade. The [author implementation](https://github.com/stanford-futuredata/FrugalGPT/tree/2b23e6acbd4b39f71912816640dcc59e45aa4b5e) is reference-only and is not installed.

[RouteLLM (Ong et al., 2024, v1)](https://arxiv.org/abs/2406.18665v1) learns routing from preference data; its out-of-distribution results motivate checking evidence on the actual task distribution. Its [implementation's calibration guidance](https://github.com/lm-sys/RouteLLM/blob/0b64fdafe049e596a3f5657c219329f24af24198/README.md#threshold-calibration) similarly ties thresholds to representative queries. We reuse the need for task evidence, not its router, server, embedding/API dependencies, fixed model pair or reported savings. No trained threshold or numerical quality/cost advantage is claimed here.

Native hosts and the existing Agents SDK/LangGraph foundations provide supported execution mechanisms; EGM informs fresh-context review. See [the comparison](hosts.md#produced-applications). Static/profile/package checks establish fidelity only. An offline inherited-model exercise can expose bad handoffs, unsafe routing decisions or incomplete review accounting; it cannot prove live heterogeneous identity, calibrated tier quality, subscription coverage or savings. Those remain unproven until user-authorized live work provides direct evidence.
