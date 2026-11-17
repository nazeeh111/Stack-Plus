# Source audit and adoption limits

The complete public source was inventoried at revision `abc0de79d6ceb0b5d7aa693945849b3937afbe6a`; this skill retains only the explicit 16-file closure in SOURCE.json. Original framework/config/recovery/helper files under `upstream/` are inactive provenance, not native instructions or executable callbacks.

Pinned SkillSpector 2.12.0 (`9dbf4fc75386169275e5f18c47686cb0d7274afa`) completed an offline `--no-llm` scan of the 794-file repository. Its network-denial probe passed. Provider calls were false; semantic scanning disabled; live OSV, dependency artifact inspection and transitive fetching were unavailable or not requested. Score100/CRITICAL/DO_NOT_INSTALL, maximum issue severity HIGH, 716 findings (208 HIGH/289 MEDIUM/219 LOW). Coverage was partial:715/794 fully inspected,79 partially inspected,0 entirely uninspected. Raw report SHA-256:`8adc856900bcbb9e943265124d17e512425d6690e329c3b3004fbe6312ae3479`. This is not full source security acceptance.

The entire template was rejected for direct native installation. Broad flags include benign matches to safety examples, template comments and code located in `.claude/`, but all full-tree findings were not individually cleared. Separate source review found actual incompatible host/session access, browser fallback, destructive output replacement, model and Git controls outside this adopted method. None of those helpers is activated here.

All seven static findings within the retained 16-file closure were inspected against source:

| Rule | Source | Adjudication and native disposition |
|---|---|---|
| AR2 HIGH | review-scope.sh:16 | “without warning” describes prior silent data-loss bugs; it does not suppress warnings. Preserve original comment, helper inactive |
| SC9 HIGH | review-scope.sh:1 | Visible source Bash helper under `.claude/`, not an opaque nested executable. Entire helper read, with git/find/awk reads and output. No network/credential access observed. Incremental correctness is not accepted merely from this scan; active mode uses verified native scope or full review |
| AR2 HIGH | review-all-gdds/references/5-report.md:79 | “no warnings” defines a clean PASS. Same report exposes blockers/warnings/gaps. Retain |
| EA2 MEDIUM | review-all-gdds/references/4-scenarios.md:65 | Worked example of missing XP event guards is a defect to investigate, not an instruction to bypass checks. Retain |
| AS3 MEDIUM | workflow-modes.md:79 | Link to repository-bundled gate-check source, not a request to inspect native host skills or config. Framework original stays inactive |
| EA5 MEDIUM | balance-check/SKILL.md:7 | Actual sonnet declaration conflicts with preserving user's model. Removed from active method; original and exact patch retained |
| EA5 MEDIUM | review-all-gdds/SKILL.md:7 | Actual opus declaration conflicts with preserving user's model. Removed from active method; original and exact patch retained |

The narrow adapted method remains subject to its current source-fidelity and independent application acceptance. No static score proves correct game design, safe runtime behavior, engine execution or automatic native host discovery.
