---
name: verify-fix
description: "Independently verify a supplied remediation against its stated invariant and existing project tests."
---

# Verify fix

Pin the patch and the finding it addresses. Read the independently specified expected contract. Trace enforcement across affected callers and configuration paths. Compare the changed lines to the prior implementation without relying on the patch author’s conclusion.

Run the project’s conventional regression tests on the patched revision, covering valid use and expected denial. Record the commands, static evidence, result, and any untested configurations.

Use static source inspection and ordinary project contract tests. See [the evidence record](references/evidence.md) for the output fields.
