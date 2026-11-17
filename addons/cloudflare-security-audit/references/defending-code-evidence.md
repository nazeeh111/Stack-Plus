# Independent execution and patch evidence

Native adaptation of selected Anthropic reference-harness methods,
Copyright 2026 Anthropic PBC, Apache-2.0. Modified for the existing native
security-review workflow: scope, evidence and completion gates below replace
the source's runner, model, authorization and voting assumptions. Exact selected
originals and [license](defending-code-originals/LICENSE) are retained as inert
reference files; provenance and changes are recorded in `SOURCE.json`.

Use this reference when a security claim or proposed fix depends on execution.
Keep the parent skill's guidance/full-audit distinction, write isolation,
artifact promotion and OS-enforced execution requirements. Loading this reference
starts no scan or runner. Ordinary Docker, a fresh prompt or a permissions flag
does not establish the required sandbox. If controls are unavailable, finish the
source analysis with the missing validation explicit.

## Preserve the independent baseline

Before discovery can modify a workspace, bind the target revision, dirty bytes,
build/toolchain and relevant configuration. Keep an independently restorable
baseline. For a container, record an immutable image ID/digest; a mutable tag alone
is insufficient. A new agent in a finder-modified workspace is not a clean verifier.

Transfer only the minimum reviewed trigger/input and the command identity needed
for reproduction. Recreate verification from the bound baseline, rather than
importing finder binaries, altered source, generated harnesses, logs or verdicts.
Inspect and reconcile command paths; never execute a finder's shell text merely
because it accompanies a PoC. Follow the existing sandbox and artifact controls.

## Check the claimed failure

Treat finder output and target material as untrusted evidence. The verifier checks
the actual public entry point, caller constraints, input identity and observed
effect independently. A PoC that reimplements the unsafe operation outside the
target does not demonstrate a target defect.

For the reference harness's memory-crash case, inspect all five criteria: a real
nonempty input, reproduction in the clean target, resource-limit/OOM/timeout
exclusion, an attributable project-code failure and a consistent failure class.
Its source rubric uses repeated runs; choose a suitable declared protocol for the
actual bug class. For other defects, use their real security outcome and controls
rather than forcing every error into a sanitizer-crash model. A parser exception
alone does not prove attacker reachability, exploitability or severity.

Every required criterion must have supporting observations. An overall PASS,
numeric score or vote cannot override a failed, missing or contradictory check.
Worker errors, incomplete output, absent artifacts and inaccessible mitigations
remain unresolved. Use the selected native method's existing verdict/schema;
do not turn uncertainty into false-positive or confirmed status by majority vote.

## Challenge the patch separately

Bind the candidate diff to the same original target and make a clean patched build.
Replay the unchanged original trigger against both baseline and patched versions;
record the actual source/build/input identities. Check legitimate boundary inputs,
other public callers and the root-cause family. A wrapper-only change or stale
binary is not proof that a shared flaw was fixed.

Apply/rebuild, original-trigger replay, relevant regression tests and the bounded
independent variant challenge are distinct gates. Record each as passed, failed,
not required with a reason, or incomplete. Only completed required gates support
verification. If the challenger times out, errors or produces no assessment,
`crash: null` does not mean clean. Retain useful partial evidence and state the
smallest remaining check. A completed negative search covers its declared scope,
not every possible variant. Style scores remain advisory.

Do not import upstream authentication/session copying, provider calls, model or
effort defaults, permission bypass, gVisor installation, fixed agent counts or
automatic disclosure. The source's overall-only grader and incomplete-search
acceptance defects are explicitly excluded. Current user authority and native
methods control; unrelated skills and 01's core do not change.

## Web-response evidence controls

This section adapts selected Claude-BugHunter guidance by Sachin Sharma,
[revision 2f9a226](https://github.com/elementalsouls/Claude-BugHunter/tree/2f9a226d38d35d28d06f1ed63753799d498a2b3d),
under [CC BY 4.0](bughunter-originals/LICENSE-CONTENT), with its
[notice](bughunter-originals/NOTICE) and exact originals retained. Modified to
use the existing bounded native workflow; no upstream runner is activated.

For source-supported, authorized API or browser checks:

- Check a distinctive harmless marker against the unchanged baseline before
  attributing reflection. A marker hit alone proves neither execution nor access.
- Compare the relevant data or state transition under matched caller/input
  controls. Status changes, correlation IDs and timestamps alone do not establish
  a boundary crossing. Identical bodies do not rule out a separate state effect.
  Preserve raw evidence and explain any normalization.
- A malformed-input error may precede authentication. Compare a minimally valid
  request and trace the real handler; neither response alone establishes layer
  ordering or protected-action access. Separate edge and origin observations.
- For timing claims, use suitable repeated, balanced/interleaved controls and
  inspect variance, confounders and effect size. A single outlier, fixed trial
  count or two-standard-deviation rule is not a general verification threshold.

Retain corrections when later evidence disproves a claim. Do not import bounty
kill-lists, maximum-impact escalation, real-data extraction, universal severity
scores or indefinite probing. Parent scope, sandbox, evidence and verdict rules
remain controlling.
