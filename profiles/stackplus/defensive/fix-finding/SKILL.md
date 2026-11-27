---
name: fix-finding
description: "Repair a source-grounded defensive finding and verify expected behavior through ordinary unit tests."
---

# Fix finding

Pin the checkout and identify the confirmed finding, code owner and intended contract. Trace the root cause to the smallest shared validation, authorization, or configuration decision. Preserve API compatibility and existing user changes.

Apply a narrow change. Exercise ordinary valid inputs and expected rejection behavior, run the relevant project test and static rule, inspect the final diff, and record the precondition and any remaining evidence gap.

Use static source inspection and ordinary project contract tests. See [the evidence record](references/evidence.md) for the output fields.
