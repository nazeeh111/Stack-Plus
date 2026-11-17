---
name: shinka-evolve
description: Set up or convert a measurable program-optimization task, run ShinkaEvolve candidate search, and inspect valid programs and archive evidence. Use when repeated executable evaluation can improve an algorithm, scientific computation or implementation.
---

# Shinka program evolution

This native entry selects the complete upstream Shinka workflows. Read
[NATIVE-BINDINGS.md](NATIVE-BINDINGS.md) and the installed ShinkaEvolve runtime
guide before executing a run; source examples are not the local launch configuration.

Choose the method for the current work:

- [Set up a new task](methods/skills/shinka-setup/METHOD.md) from a target and
  measurable success criteria.
- [Convert existing code](methods/skills/shinka-convert/METHOD.md) into a minimal
  runnable sidecar task while preserving its original source.
- [Run evolution](methods/skills/shinka-run/METHOD.md) once the candidate/evaluator
  contract exists, using explicit batch scope and supported runtime configuration.
- [Inspect programs](methods/skills/shinka-inspect/METHOD.md) from an existing
  results/archive directory before choosing the next search direction.

Read the selected complete method and its needed companions. Keep the evaluator
and correctness contract independent of candidate edits. An improved archive score
needs actual candidate-output checks and replay; the inspect helper's fallback to
incorrect rows is a diagnostic view, not a valid winner. Preserve parent/inspiration
and configuration evidence so later batches can explain what changed.

The original runner, mutation, evaluation and archive perform the search. This
entry adds no replacement evolution loop or always-on service. Scientific claim
validation remains separate from finding a higher-scoring candidate.
