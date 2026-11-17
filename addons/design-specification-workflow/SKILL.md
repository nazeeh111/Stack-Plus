---
name: design-specification-workflow
description: Develop software ideas into self-contained design documents, review them with fresh-context specialists, resolve findings, document existing code or compare specifications with implementation. Use for Elephant-Goldfish (EGM) requests or substantial software design and document review; choose only the needed stage.
license: Apache-2.0
---

# Software design and fresh review

Native adaptation of Google's Elephant-Goldfish Model (EGM). The lead holds project context; fresh reviewers test what the written design and selected evidence actually explain. This is a workflow, not a new model, memory service or agent runtime.

Read [native operation](references/native-operation.md), then the complete method for the current stage. The original seven methods, reviewer prompts, standards and supporting templates are bundled below. Load only relevant support. Current user and host instructions govern execution; the originals do not grant extra permission or require a fixed process on every task.

## Select the contribution

| Current need | Complete original method |
| --- | --- |
| Clarify a software concept, alternatives and requirements | [Brainstorm](upstream/skills/egm-brainstorm/METHOD.md) |
| Turn agreed requirements or notes into a design document | [Draft](upstream/skills/egm-draft/METHOD.md) |
| Review a feature specification or implementation plan | [Review](upstream/skills/egm-review/METHOD.md) |
| Review a chosen document against selected standards | [Review loop](upstream/skills/egm-review-loop/METHOD.md) |
| Evaluate, contest or repair review findings | [Resolve](upstream/skills/egm-resolve/METHOD.md) |
| Document the observable contracts of existing code | [Bootstrap](upstream/skills/egm-bootstrap/METHOD.md) |
| Compare existing specifications with current code | [Drift report](upstream/skills/egm-drift-report/METHOD.md) |

Keep ordinary edits direct. 01 selects useful methods; this skill supplies the software design/document workflow. Use the existing agent-orchestration skill for worker allocation and integration, and the relevant coding, security or architecture skill for its own work. Visual art direction is a separate contribution.

## Establish the target

Read the actual brief, document and relevant source. Identify the intended outcome, constraints, unresolved decisions and checks that can establish completion. Use the current project design and task file; preserve the user's chosen host, model, effort and permission. Produce a self-contained artifact, not a transcript or an inventory of generic advice.

For a review, bind the exact target version and section, applicable standards, reading list, reviewer lenses and a finite work limit before dispatch. Keep target snapshots or hashes when concurrent edits or later rounds could change their meaning. Resolve source links against the actual owning folder; do not substitute similarly named project files for bundled prompts. Missing required evidence remains a gap.

## Use genuinely fresh reviewers

Use the actual native subagent interface with parent history excluded, such as `fork_turns: "none"` where supported. Give absolute paths to the target, selected persona, standards and allowed evidence; keep the author's preferred answer and conversation history out of the packet. Comprehension review starts by paraphrasing the proposal before listing issues.

Require the reviewer to read its assigned files and return findings with affected scope, severity and rationale. Keep reviewers read-only and give the lead ownership of changes. Wait for actual completion. A failed, timed-out or missing review is incomplete, not a clean review. When fresh dispatch is unavailable, report that limit rather than act out a reviewer in the lead's context.

## Resolve and finish

Verify findings against the artifact and source. Merge duplicates without hiding independent evidence. Decide whether to fix, contest with evidence or retain an unresolved trade-off; apply authorized repairs and check the affected result. Re-read changed sections before another pass and verify that earlier fixes still hold. Do not reopen settled findings without changed evidence, and do not dismiss reintroduced defects merely because a prior round fixed them.

Use only the stages and reviewers that serve the request. A bounded pass is the default; further passes need a concrete purpose within the available work limit. If the user selects the complete upstream protocol, preserve its declared stages, checkpoints and convergence definition. A shorter native run must not be called full EGM convergence.

Leave the document, review findings, verified changes and remaining limits with the project. Update its existing task file with the target version and next action. For end-to-end implementation requests, hand the agreed design to the coding workflow and continue the authorized work; this design skill does not itself implement production code.
