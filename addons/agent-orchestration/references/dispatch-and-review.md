# Dispatch, context and independent review

Use the parts that change the work. Keep a small task's brief inline; retain a specification or dispatch record for substantial work in its existing task files. For original EGM document methods and personas, use `design-specification-workflow` when installed; this method coordinates native execution.

## A useful worker brief

State the concrete result, the authoritative requirements and inputs with their versions, and what decisions the worker owns. Specify allowed reads/writes, forbidden effects, dependencies, expected output, evidence and stopping conditions. Tell the worker which selected complete skills and support to read and how their method should contribute. A returned report should identify changed artifacts, checks actually run, failures, material uncertainty and remaining work. Keep credentials and irrelevant private context out of dispatches.

Use the [tier and quality method](tiers-and-quality.md) when selecting a user-mapped worker or when a contribution needs explicit acceptance/recovery gates. Its bounded handoff distinguishes worker status from lead acceptance, requested model from observed identity, and partial usage from a complete measured total. Do not accept a low-effort summary in place of the requested specialist result.

For example, a parser implementer can own `parser.py` and its behavior tests while a schema investigator independently owns a compatibility report. Both read the same frozen schema revision. Only the lead changes shared release notes. A reviewer reads the integrated diff and requirements after the implementation exists; it does not edit concurrently with the implementer.

Before dispatch, check whether all needed files, tools and authority are available to that worker. A path in a prompt does not load its contents. If a worker cannot read a required method or source, resolve the gap or return an incomplete result. When native traces expose reads, inspect them; when only self-report is available, label that evidence limit. Do not add a tracing framework merely to make stronger claims.

## Fresh-context specification and artifact review

Google's [Elephant-Goldfish Model](https://github.com/google/elephant-goldfish-model/tree/72d06f52a2482885d9a64bd24b291c6e8628942c) separates a context-rich author from reviewers who see the document and selected sources without the preceding conversation. Its [Codex integration](https://github.com/google/elephant-goldfish-model/blob/72d06f52a2482885d9a64bd24b291c6e8628942c/docs/codex.md) explicitly distinguishes fresh conversation context from filesystem, instruction-file and memory isolation. Reuse that distinction and its comprehension/readiness checks; do not claim to run the full EGM protocol or copy its fixed stages, interactive gates and round counts into every task.

For a consequential design, supply the target specification, actual source/API references, requirements and review scope. Ask the reviewer to explain the design from those inputs, identify missing prerequisites or assumptions, check that proposed interfaces exist and assess whether the acceptance checks would catch failure. A useful specification names the problem, boundaries, decisions, affected interfaces/files and observable success conditions. Detail should resolve uncertainty, not generate paperwork.

For a completed change, supply the integrated artifact/diff and acceptance criteria. Ask for reproducible defects, risks and missing evidence, with locations and supporting checks. Do not send the author's reasoning, expected verdict or a list of suspected bugs unless the review specifically requires them. Use a host-supported fresh-context option, such as Codex `fork_turns: "none"` in the reviewed schema. Confirm the current schema first. If conversation isolation is unavailable, report ordinary review with that limit; never present parent-context roleplay as independent fresh review.

Fresh workers still receive host/system instructions and may access the same project files or memory services. Restrict the brief's reading list, do not retrieve history to fill missing design context, and report what isolation was established. Give a reviewer only its own output path or keep it read-only. Its findings are advisory evidence; the lead checks and integrates them.

Treat a timeout, absent report, inaccessible source or missing required method read as incomplete. Reconcile any partial effects before deciding whether a bounded retry is justified. Accept, repair or reject each material finding with evidence. Re-review when a material repair, uncertainty or uncovered risk warrants it. Do not seek perpetual unanimous approval or use reviewer agreement as a substitute for tests.

## Failure and cost control

Separate setup failure, a tool error, a model's incomplete attempt, a real artifact defect and an uncertain external effect. Capture enough bounded evidence to distinguish them. Reuse a valid partial result; retry only after a changed input, repaired prerequisite or concrete new hypothesis. A timeout does not establish zero inference or zero cost. Native subscription workers and separately billed SDK/API calls have different authority and accounting.

Prefer useful results in separate bounded branches over large copies of the full transcript. Return concise conclusions with exact evidence pointers; keep raw logs and originals with their owner. Context reduction must retain authority, acceptance criteria, unresolved failures and the source needed to check claims. Use role-specific relevant tool exposure only through a supported host interface; do not globally prune orchestration, recovery or verification tools because they were unused in a previous task. An ended turn or an edited file is not accepted work. Benchmark a materially changed workflow on representative accepted tasks when worthwhile; compare correctness, recovery, latency and measured usage, not one successful example or token savings alone.

A [2026 dynamic-concurrency study](https://arxiv.org/abs/2610.10263v1) reports task-dependent gains and substantial resource increases across its tested agents and benchmarks. This supports selective delegation and explicit integration, not a universal agent count or a causal performance claim for this environment.
