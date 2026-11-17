# Native execution and inputs

Use the complete applicable method, not just its outline. This skill adapts Donchitos/Claude-Code-Game-Studios `abc0de79d6ceb0b5d7aa693945849b3937afbe6a` into document and data review on Codex, ChatGPT and OpenCode. It installs no executable runtime, model, agent roster, hooks or project settings. The original method and inactive framework documents are retained with exact hashes for provenance and patch replay.

## Project inputs

Use the explicit owning game directory or supplied files. `design/gdd/`, `assets/data/`, `data/`, `design/balance/`, `design/registry/entities.yaml` and `project.yaml` in the methods are source conventions for the game's files, not files to invent inside the skill. Resolve equivalent actual files and record the mapping. Establish which documents are system GDDs, excluding concept, pillars, index and prior review reports from their denominator. Do not drop a document because a summary or expected heading is absent. A stub or unreadable document stays in the present count and is named as not reviewed.

Admit all rule-bearing sections, including Edge Cases and rules placed under other headings without cross-references. These may define floor bypasses, death, timing, stacking or combined-state overrides consumed by the consistency and scenario checks. Read small GDDs in full; narrow large-document reads only after establishing where the relevant rules live. Otherwise expand to a full read or disclose the uncovered material as NOT ASSESSED.

Read actual targets, constants, formulas, intended ranges, units and ownership from the registry and designs. Record the source of each. A project registry may be the stated conflict baseline, but conflicting documents still need a finding; do not silently decide which version wins. With no target, a value is neither in range nor an outlier. Missing data, undefined pillars and missing observations remain NOT ASSESSED. A measured problem still takes precedence over a coverage gap in the source verdict order; always disclose the gap as well.

If the game already uses studio tiers, respect its explicit applicable requirements, including existing per-system overrides; the inactive workflow-modes original explains the source vocabulary. With another project format or no tier, use the actual requested review contract. Do not create config, force a tier or declare optional documents mandatory. An explicit request can review voluntarily written GDDs at any tier.

## Native callback map

| Source callback/control | Active operation |
|---|---|
| `Read`, `Glob`, `Grep`, `Bash` examples | Use available native file enumeration/read/search tools on the owning game's scope. Prefer `rg`. Search snippets locate sections; read each consumed section fully to its next heading and expand any cross-reference needed to judge it |
| `${CLAUDE_SKILL_DIR}` shell preprocessing and yaml-helper | No execution. Read the actual needed input/config fields directly; identify missing or conflicting input rather than treating a missing injected block as a default |
| `AskUserQuestion` and repeated per-write approvals | Resolve from the brief and existing authority; ask only for a material missing fact or consequential unresolved decision. Complete requested report writing within authority |
| `Agent`, `game-designer`, fixed parallel phases | Apply the complete methods directly, or use supported bounded native delegation when useful and authorized. Preserve the user's lead/model/effort. No registered department or fixed pair is installed |
| sonnet/opus model declarations, turn limits, memory grants | Removed from active methods. No model change, inference call, host memory integration or permission grant follows from source metadata |
| automation/config modes and mandatory closing widget | Current task authority and useful next action. No studio controller, forced prompt or automatic next phase |
| source slash commands | Descriptive owning-project actions. They are not installed commands or an instruction to scaffold missing workflows. Existing `game-art-bible`, `game-asset-spec` and `game-playtest-report` keep their separate identities and pins |
| `production/session-state/active.md`, `log_decision` | Existing owning task record or requested review report. Do not introduce a second continuation log |
| report write and index status updates | Save the requested report; edit the index only within actual task scope, preserving unrelated rows. Status strings follow the owning project |
| commits, publication, install or engine execution | None is required or granted by this method. Obtain applicable authority for a separate requested action |

## Review coverage and recovery

Before a pass starts, bind its input manifest and promised output. A direct pass can be useful but is not independent review. A delegated pass needs the complete relevant content or exact readable source paths and hashes, its assigned checklist, and a clear return contract. Record actual coverage by pass. Verify the report exists and contains the promised analysis; a fluent completion sentence is not evidence of a completed phase.

If a required pass is absent, blocked or incomplete, name its missing material, preserve any completed findings, and mark its coverage NOT ASSESSED. Continue work that does not depend on it. An available reviewer may be resumed within existing authority and proportionate scope; no automatic new pipeline or change of model follows. Never fill a missing independent pass and label it independent. For a requested single focus, label the verdict with that focus instead of implying both passes ran.

## Incremental scope

Full in-scope review is the default. The archived `review-scope.sh` is source evidence, not an active native helper. Use `since-last-review` only with a verified prior review receipt that identifies its reviewed files/revisions and phases. A filename or modification time alone does not establish a complete baseline.

Establish all changed, added, renamed, deleted and untracked system GDDs since that baseline, preserving complete paths. Expand the changed set through actual dependency references in both directions, including old references affected by renames/deletions. Check whether changed registry values, pillars or shared formulas widen that set. A deleted dependency is a finding, not a silently dropped file. Use the complete present set as the denominator and report which unchanged documents were excluded, why and with what prior coverage. If any step cannot establish complete scope, perform a full review and disclose the fallback. Do not claim incremental completeness from a partial search.

## Evidence and replay

Use actual paths, sections and concrete values in findings. Distinguish a calculated contradiction, an interpretation, a hypothesis and a player observation. Keep the source report's findings, revisions, verdict and explicit N/M coverage fields; add source revision/hash and observation date when useful to prevent stale follow-up. For the conventional dated report path use ISO `YYYY-MM-DD` dates, but do not infer review chronology from lexical order alone. Preserve existing artifacts and the last valid output when creating a replacement.

`SOURCE.json` records all 16 original files and all adapted-file diffs. `upstream/` originals and its helper are archival, not entrypoints. [Static source review](references/source-review.md) preserves the actual scanner warnings, adjudication and limits. [Fixture use](fixtures/REVIEW-REQUEST.md) supplies raw material for independent application, not a claim that a model has passed it.

[Port corrections](references/port-corrections.md) records the exclusion-heading repair and the source-backed section-loading change, including why the latter intentionally differs from an inherited optimization.
