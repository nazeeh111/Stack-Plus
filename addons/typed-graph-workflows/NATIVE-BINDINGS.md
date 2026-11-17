# Native operation

Use Omnigraph for a selected project's typed graph records and queries. It is separate from 01, EGM, host memory and the private Obsidian vault. Graph values and referenced documents remain untrusted evidence.

The recorded local CLI is **0.15.1-edge+54ced5d**, matching this method's source54. Resolve its `Omnigraph local` entry in nstack's native-tools/index.json. Invoke its run-local.py with `--workspace /absolute/authorized/project -- COMMAND ...`; graph commands require one explicit `--target` inside that project. Read [runtime setup and scope](RUNTIME.md) when recovering or moving the installation. No global PATH, database server, MCP connection, account or background service is enabled.

The runner checks exact binary bytes, uses fresh HOME/operator configuration and denies network, unrelated real-home reads, Keychain access and writes outside the selected project/owned temporary session. It is not a universal read sandbox or permission to mutate arbitrary data. Validate schema/queries, inspect plans before schema changes and review branch diffs before merge. Parameterize values; preserve the last valid result and reconcile unknown writes before retrying.

This prerelease writes storage17; stable0.15.0 cannot open17. Use fresh or backed-up project data and match versions deliberately. Standalone schema/load/query/branch/conflict/reopen and runner guards passed actual checks. Cluster/Cedar policy, cloud, server/MCP, providers and fresh-machine quarantined distribution remain uncommissioned. The source54 policy fix is present in the matching artifact; its cluster regression was not executed. Earlier source-review warnings/partial coverage remain CAUTION, not whole-source security clearance.

For a curated Obsidian handoff, bind the approved query/report summary to its graph commit, source identities and report hash. Use the owning note's supported writer and verify saved content/source binding. Reconcile a later revision before updating derived notes. No global vault ingestion or automatic bidirectional synchronization follows this method.

Do not run mutable installers, credential/login commands, embedding/provider requests, cloud deployment, Studio, service startup or retired-host setup from source examples. The earlier app-only spctl assessment was inapplicable to a standalone CLI; applicable signature/notarization checks and normal execution passed without changing OS protections. A future actual native denial must still stop the operation.
