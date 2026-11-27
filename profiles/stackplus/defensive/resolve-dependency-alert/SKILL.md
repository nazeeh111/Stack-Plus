---
name: resolve-dependency-alert
description: "Evaluate and remedy a reported dependency advisory for the project\u2019s actual resolved dependency."
---

# Resolve dependency alert

Read the advisory from its maintainer and identify the affected and repaired versions. Check the project’s lockfile, deployment configuration and direct or transitive consumers. Record applicability and the smallest compatible update. In the project’s normal isolated environment, regenerate the lock using its package manager and run build and conventional regression checks. Retain the original advisory, before and after versions, changed paths, test evidence and any blockers for the owner.
