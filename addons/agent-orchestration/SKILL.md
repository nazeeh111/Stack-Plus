---
name: agent-orchestration
description: Coordinate a lead and useful specialists using user-supplied model tiers or inherited models, bounded handoffs, quality gates and independent fresh-context review. Preserve the chosen lead and integrate checked results through the native host.
---

# Agent orchestration

Keep one lead responsible for understanding the task, integrating contributions and delivering the checked result. Preserve the user's chosen host, lead model and effort. This method complements 01: 01 selects useful methods; this method coordinates agents once delegation is useful and authorized. It does not require a team for routine work or install an orchestration framework.

## Choose the next contribution

Inspect the current artifact, requirements, authority and actual host tools. Identify work whose independent result can change the outcome: an uncertain dependency, a bounded implementation, a competing approach or a consequential review. Delegate when the benefit earns the extra context, latency and usage. Keep tightly coupled decisions with the lead; parallelize independent work, sequence dependencies and reassess as evidence changes. Avoid fixed rosters, recursive reviewer chains and duplicated exploration.

Read the relevant [host mechanisms](references/hosts.md). Inspect supported context controls, model selectors, tools, completion notifications and concurrency limits. Require current-model/effort inheritance when tiers are unset and confirm actual host resolution; an omitted selector alone may not establish inheritance. When the user authorizes worker model selection and the host permits it, choose among actually available models by required reasoning, domain/tool support, context, latency and observed task quality. Use a smaller or faster model for a bounded check only when its error is detectable; retain stronger reasoning for ambiguous synthesis or consequential review. Do not infer capability from a brand or hard-code a permanent hierarchy. A model preference is not proof of effective run identity or subscription coverage. Never silently substitute, change the lead or effort, create provider access or incur separately billed usage.

For user-defined tiers, read [tiers and quality](references/tiers-and-quality.md). Keep the current chosen model as lead. The user can later map worker Y and optional lower tier Z, or use their own labels, in chat or a task-local profile. Unset tiers inherit the current model; they are not permission to pick an alternative. The lead chooses among available, authorized mappings by task ambiguity, whether errors can be detected and dependency risk. Relative labels express user intent, not measured quality. Do useful bounded specialist work, reject unsupported output and retain synthesis and consequential decisions with the lead unless evidence supports a different allocation.

## Dispatch and coordinate

Give each worker the outcome, relevant inputs and versions, scope it owns, authority, expected artifact and acceptance checks. Include the actual selected skill paths and require complete relevant method/support reads and application, not acknowledgement. Choose inherited context when ongoing history is needed; otherwise send a self-contained brief to a fresh worker. A fresh transcript still shares host instructions and may share files and memory services.

Keep one writer per artifact. Parallel writers need separate files or isolated worktrees with explicit integration ownership. Reuse a productive worker for follow-up context; use a new one when independence matters. Set a finite attempt/elapsed-work cap before dispatch; retries and escalation require a changed hypothesis and remaining authority. Wait for actual results, inspect produced bytes and evidence, resolve contradictions against source, and stop redundant branches. A launch or a confident summary is not completion.

## Integrate and independently check

Read [dispatch and review](references/dispatch-and-review.md) for substantial delegation, fresh-context specification review or uncertain recovery. Before consequential implementation, make the requirements, interfaces, constraints and acceptance checks understandable without chat history. Where useful, have a fresh reviewer inspect that specification and its cited sources. After integration, give a fresh reviewer the actual result and requirements without the author's favored conclusion. Select the review lens by the remaining risk; a different model is not required for independence.

Verify findings against artifacts, make justified repairs and check the affected result. Apply the [acceptance gates](references/tiers-and-quality.md#accept-or-recover) before integration. Review failure, timeout or missing required input means incomplete review, never zero findings. Continue only when another pass has a concrete purpose within authority; preserve unresolved findings and stop churn. The lead remains responsible for integration tests and honest reporting.

Keep task state in the existing entrypoint: owners, artifact versions, accepted work, failed or uncertain effects, checks and next action. On a failed branch, reconcile partial artifacts and external effects before retrying. Repeated identical failures without new evidence call for diagnosis or a different supported route, not more agents. Record measured usage when available; unknown usage stays unknown. Optimize accepted task quality, elapsed time and cost together, not token count alone.

Use existing LangGraph or the OpenAI Developers Agents skill only when a produced application needs durable state, explicit branching or an SDK-owned loop. See the [framework comparison](references/hosts.md#produced-applications). Native host coordination remains the default for engineering tasks.
