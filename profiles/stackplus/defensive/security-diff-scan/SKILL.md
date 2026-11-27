---
name: security-diff-scan
description: "Perform a static defensive review of a supplied code diff and return source-grounded remediation findings."
---

# Security diff scan

Open the immutable diff with its base and head. Group changed behavior by ownership, authorization, input validation, and data retention. Read the surrounding implementation and the tests for each affected invariant. Use installed static checks if supported by the project.

Record the source location, violated invariant, suggested correction, and verification command. Distinguish newly introduced issues from findings already present at the base.

Use static source inspection and ordinary project contract tests. See [the evidence record](references/evidence.md) for the output fields.
