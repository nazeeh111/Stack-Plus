---
name: security-finding-verification
description: "Check a reported code finding against the source, build configuration, and an existing regression test."
---

# Security finding verification

Collect the reported rule, file, line, commit and claimed invariant. Open the cited code and trace its types, guards, conditions and configuration to the policy owner. Distinguish a demonstrated missing guard, an unreachable branch, a disabled feature, and a report lacking enough evidence.

Record an ordinary expected behavior, run the project’s existing unit test for that contract, and record the command and result. Propose source remediation if static evidence confirms the issue. Keep inconclusive findings open.

Use static source inspection and ordinary project contract tests. See [the evidence record](references/evidence.md) for the output fields.
