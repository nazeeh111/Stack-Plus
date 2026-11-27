---
name: security-change-review
description: "Review a supplied source change for weakened validation, authorization, isolation, or access-control contracts."
---

# Security change review

Pin the base and head. Identify the changed decisions and the resources each decision protects. Follow callers and configuration to establish the intended owner, trust boundary, and failure behavior. Cite exact lines of the change and relevant policy.

Compare the expected contract before and after the change using conventional success and denial unit cases in a disposable project fixture. Report each regression, its affected behavior, and the smallest maintainable fix.

Use static source inspection and ordinary project contract tests. See [the evidence record](references/evidence.md) for the output fields.
