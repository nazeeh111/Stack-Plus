# Context and cost efficiency

TokenEconomizer is a researched candidate, not an activated nstack integration. The
reviewed source is [Microsoft TokenEconomizer
7042ea89](https://github.com/microsoft/TokenEconomizer/tree/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0),
Apache-2.0. No plugin, hooks, learned history or settings were installed by this
evaluation. These findings were observed on November 15, 2026.

## Compatibility and activation decision

| Host | Locally observed | Upstream evidence | Decision |
| --- | --- | --- | --- |
| Codex | CLI 0.169.0 | README tests 0.153.1–0.164.0; newer versions explicitly untested | Keep inactive until an isolated native hook and restore check passes on the actual version |
| OpenCode | 2.3.0 | Experimental 1.19.5/2.2.0, additional 2.2.5 CI checks; 2.x TUI untested | Keep inactive; tool pruning is not implemented for OpenCode |

The installed CLIs recognize the documented command surface, including Codex
plugins/ephemeral execution and OpenCode standalone execution. Help output proves
neither hooks nor model delivery. See the pinned [supported-version
table](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/README.md#supported-versions)
and [integration evidence and
limits](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/docs/PLUGIN.md).

The existing native orchestration route remains the working foundation. Do not
enable TokenEconomizer merely to shorten a prompt. Its default automatic Codex
pruning can disable collaboration, goals and image viewing, which heterogeneous
engineering work may need. Session non-use is weaker evidence than the current
task's requirements. OpenCode's existing plugin allowlist and Codex hook trust
remain native boundaries, not obstacles to work around.

## What the source actually does

The [paper](https://arxiv.org/abs/2610.22732) reports 18.4–30.9% lower average
SWE-Bench cost across five agent/model combinations, including controller overhead,
with Pass@1 improving in four combinations and falling in one. It evaluates
chronological task streams. This is evidence for adaptive cost control on those
tasks, not measured savings on this installation or proof that the live plugin
matches the benchmark controller.

- [Micro-skills](https://github.com/microsoft/TokenEconomizer/tree/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/microskills)
  learn short repository facts from recurring command outcomes. They are off by
  default. `envfacts` uses fixed templates without model calls; `on` also enables a
  model proposer. Facts require repeated support and retire on contradictions.
- [Pruning](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/plugin/denylist.py)
  writes native per-checkout settings after sufficient unused-session evidence.
  The default is automatic application after idle time; `propose` defers writes.
  Codex's live unit is a capability package. A completed use protects that package;
  deferred waiting is retained because removing it caused shell polling.
- [Failure-loop detection](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/loopguard/turn.py)
  combines repeated failures, edit churn and a repository's usual turn length.
  The live judge is gated and can write a redirect. A later fire becomes a user
  notice; the live plugin does not stop a turn. Its usual-length estimate uses an
  ended-green proxy that accepts edits with no verification, so it is never an
  acceptance oracle.

## Findings to resolve before a live trial

Thirty-six offline exact-source assertions ran with network connections and
subprocesses forbidden. They exercised capability retention/demotion, cold-start
calibration, productive reads, repeated failures, shell exit evidence, environment
fact formation/retirement, and the two counterexamples below. They establish local
source behavior, not native hook or model effectiveness.

1. The [judge digest](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/loopguard/state.py)
   hashes error signatures and omits file bodies, but retains the first 90
   characters of shell commands and search patterns. A synthetic private argument
   survived. Treat it as potentially sensitive command data, not a secret
   redaction boundary. OpenCode exports also retain tool arguments/results locally.
2. The [judge parser](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/loopguard/judge.py)
   coerces a nonempty string value for `stuck` to true. Synthetic JSON with the
   string `false` therefore became a positive stuck verdict. This is a malformed
   response counterexample, not a claim about normal model output.
3. [Side calls](https://github.com/microsoft/TokenEconomizer/blob/7042ea89dd5e5ecbc67ad865ad6e256e61be8bf0/tokeneconomizer/plugin/sidecall.py)
   use the existing CLI's default model unless configured. Codex disables these
   hooks and requests ephemeral read-only execution, but inherits the environment
   and user configuration without explicitly removing MCPs. That does not prove
   every external tool is contained. OpenCode denies four named tools and uses a
   standalone server. Neither route was model-tested here.

A future scoped trial should keep pruning off or in proposal mode, protect required
capabilities, leave learned facts off initially, verify exact native hook delivery
and removal without bypassing trust, and review what the judge can send or call.
Use synthetic input first. Preserve live configuration bytes and rehearse restore
separately. This is an acceptance condition for this uncommissioned integration,
not a requirement to add another proxy or framework.

## Apply the useful methods now

Use the existing lead and specialist workflow. At a repeated failure, compare the
failure with the last attempt and inspect partial effects before retrying. A
changed failure, narrower cause or newly passing check is progress. Repeating the
same action without a new hypothesis calls for a different test or fresh reviewer,
not automatic termination or a lower-effort model.

For large evidence, retain the original with its owner and return a bounded result
with source paths, unresolved points and relevant checks. Retrieve a passage or
tool interface when needed, then read the selected method fully. Stable compact
task state and focused worker context preserve continuity without repeatedly
injecting whole catalogues. These choices follow [context-engineering
guidance](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents);
their value still needs task-level verification.

Measure the whole accepted outcome: fresh input, cached input, output, review,
retries, latency, failures and user rework. Mark missing usage unknown. Compare
equivalent tasks and acceptance criteria before claiming savings; fewer tokens or
a nominally successful process exit alone is insufficient.

## Autoresearch boundary

[Karpathy autoresearch
228791fb](https://github.com/karpathy/autoresearch/tree/228791fb499afffb54b46200aca536f79142f117)
offers a small useful experimental contract: fixed evaluation, one mutable training
file, a baseline, fixed training time, and recorded keep/discard decisions. The
upstream runtime requires NVIDIA CUDA; no runtime, dependencies, training or model
campaign was launched here. Its permission-disabling, indefinite loop and Git
reset instructions are not adopted. Reuse the bounded hypothesis/evaluation/logging
pattern inside an authorized existing research engine, with held-out acceptance,
preserved failed artifacts and explicit attempt limits. It does not grant another
AI Scientist attempt.
