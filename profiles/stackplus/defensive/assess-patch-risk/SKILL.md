---
name: assess-patch-risk
description: "Assess the risk of a proposed source change using the affected contracts and the evidence supporting the change."
---

# Assess patch risk

Pin the base and proposed revision. Identify the behavior that changes, its consumers, the data or permission boundary involved, and which failures the project can observe. Inspect the surrounding source, callers and existing tests. For each consequential concern record an exact location, the expected behavior, the evidence checked, a conventional regression test and what remains uncertain. Give the maintainer a release or revision recommendation supported by those observations.
