---
name: production-observability-release
description: "Instrument and verify a production service or release: user-facing reliability, correlated telemetry, canary decisions, data migrations and rollback. Use for operational readiness, incidents or a concrete rollout; use project-scoped evidence before changing production."
metadata:
  category: Reliability and release engineering
---

# Production observability and release

Start with the user journey that must keep working and the actual service, version and environment. Inspect existing instrumentation, deployment and incident procedures. Reuse the project's supported stack; a new monitoring service or deployment framework needs a concrete missing capability. This method installs none.

## Define evidence before a release

Define the service-level indicator (SLI), its numerator/denominator, time window and exclusions; agree a service-level objective (SLO) and applicable error-budget/release policy. Include user-visible failures, timeouts, retries and tail latency, not just successful HTTP responses. Keep target values project-specific. An error budget is the allowed unreliability within that window, not a per-release allowance.

Identify version/configuration/feature-flag and schema/data dependencies. Bind the candidate to immutable artifact/source/dependency identities. Check backward compatibility and recovery order across clients, workers and storage. A reversible binary change may have an irreversible migration; preserve data and rehearse restore before that change. Record the actual last working version and recovery prerequisites.

## Observe the complete path

Use correlated traces, metrics and structured logs where they answer different questions. Carry request/trace identity across asynchronous boundaries and record service version/environment. Distinguish accepted, completed, failed, cancelled and unknown effects. Investigate a user-visible failure through the request, dependency and persisted result; an empty error log is not proof of success.

Keep metric labels bounded. Put individual request IDs in traces/logs, not high-cardinality metric dimensions. Redact payloads, credentials and private attributes before export; sampling and retention are deliberate choices. Verify telemetry's own delivery, freshness and sampling limits. Missing or biased telemetry produces unknown readiness, not zero failures.

For AI applications, bind model/prompt/tool versions and input dataset identities to held-out task outcomes. Reuse agent-evaluation-harness for capability/regression evaluation and performance-benchmark-review for measured speedups. Report attempts, failures, quality, latency, token usage and measured cost separately. Do not infer prices, total billing or model identity from partial counters. A faster failure or cheaper incorrect answer is not an optimization. Data pipelines also need schema, uniqueness, missingness, freshness and lineage checks before publishing derived outputs.

## Decide and recover

Compare candidate and control over comparable traffic, cohorts, load and observation windows. Predefine enough exposure and the quality/reliability/cost guardrails for the actual risk. A canary is a bounded operational trial; it does not replace a correctly designed product A/B test. Explain uncertainty and confounders rather than promote a noisy point estimate.

Stop expansion when guardrails fail, evidence is incomplete or the applicable budget policy blocks changes. Within existing authority, use the documented rollback or roll-forward plan and reconcile uncertain effects before retrying. Re-read the actual deployed version, health and persisted data afterward. Never treat an accepted deployment request or green process check as recovered user behavior.

## Verify a real journey

Exercise success, a dependency failure, missing telemetry, a late regression and recovery against the selected application. Check that changed inputs invalidate stale dashboards/approvals and that duplicate requests do not repeat writes. Include keyboard/focus/error-recovery and actual user-task checks from existing UI/reliability methods when a UI is involved. Preserve failed attempts and the last good output.

Return the release decision, supporting observations, unresolved limits and verified recovery state. Local failure injection proves that fixture's behavior; it does not commission real production monitoring or deployments. Primary research and scope are recorded in SOURCE.json.
