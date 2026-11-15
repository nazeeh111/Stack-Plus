# Native REA binding

The selected implementation is `morluto/rea`, npm `rea-agents` **6.9.0**,
Git revision `d74549e495c58eb4a560279fd9f05508401ea0a0`. It is not the
existing Rust Craft Anything or the RAEA rendering engine.

Resolve this skill's `runtime_recipe` from its installed `SOURCE.json`, or
the REA record in nstack's `native-tools/index.json`. Native installation
rewrites that recipe path to durable code. A skill alone does not install
or commission the runtime.

```sh
python3 /absolute/retained/nstack/recipes/rea.py install
python3 /absolute/retained/nstack/recipes/rea.py verify
python3 /absolute/retained/nstack/recipes/rea.py check
```

The recipe acquires exact official package and Node archives into private
nstack state. REA needs a newer Node than the setup's existing 24.14 fallback;
its dedicated Node 24.22.1 leaves global PATH and other runtimes alone. The
published package already bundles its runtime dependencies: no npm install,
lifecycle hook, optional Frida install or upstream setup is required. Original
package bytes and notices remain. Preparation does not register MCP or launch
a target application.

## File analysis and saved Evidence

For an explicitly authorized PE/ELF file:

```sh
python3 /absolute/retained/nstack/recipes/rea.py native-exports \
  --source /absolute/authorized/artifact \
  --outdir /absolute/new/private/task-evidence
```

Use the returned complete Evidence path for a compact follow-up:

```sh
python3 /absolute/retained/nstack/recipes/rea.py summary \
  --evidence /absolute/task-evidence/actual-evidence-file.json \
  --outdir /absolute/new/private/summary-evidence
```

Use actual returned paths, not the illustrative filename. The static recipe
uses a constructed task HOME/environment, disables update notifications,
denies network access and proves its boundary with synthetic probes before
reading the target. It permits REA's own required analysis/ownership helpers,
not target execution. A refusal stops that route; do not remove its isolation
or substitute an unrestricted invocation to evade it.

The separate JavaScript/Electron `inspect` route is **not commissioned** on the
current Mac: analysis emitted Evidence, but worker cleanup failed with
`process table could not be inspected: spawn EPERM`. No supported REA 6.9.0
backend avoids that process-list operation. Do not retry the unchanged lane or
remove its isolation. The recipe's `check` commissions native export inventory
and summary separately; it does not assert JavaScript-worker readiness.

The returned `node` and `script` paths expose the original CLI. Use its actual
`--help` and selected command help; direct CLI invocation is separate from the
recipe's isolated static boundary. Do not pass unrelated personal apps, accounts or private
stores to it as a setup test. Runtime launch/attach, network acquisition,
device changes, paid evaluation and provider setup require their actual
prerequisites and existing task authority. No upstream default budget grants
spending permission. Static inspection cannot establish those routes.

Read the [complete JavaScript guide](upstream/references/javascript-applications.md)
when its module views, coverage or comparison mechanics are needed. The
remaining upstream guides describe additional operations, not current
acceptance. Check a matching provider before native decompilation; this setup
does not acquire proprietary engines or accounts.

## MCP only when the task benefits

The original server is available through the pinned Node and
`package/scripts/rea.mjs mcp`. Use a task-owned stdio connection when persistent
sessions/retained references are useful. Query its actual schemas and close
owned sessions/transports after saving useful Evidence.

`REA_MCP_TOOL_FAMILIES=electron,application` reduces advertised families for a
JavaScript workflow. It is **not** a read-only permission boundary: those
families include runtime/build operations too. Compact input/output schema
profiles can reduce metadata overhead, but neither grants access nor limits
what a tool can do. Use the actual client's supported tool selection and
permissions before relying on enforcement. No global server or automatic
hot/cold client refresh is established here.

Versioned contracts:
[REA MCP](https://github.com/morluto/rea/blob/d74549e495c58eb4a560279fd9f05508401ea0a0/docs/reference/mcp-contracts.md).

## Provenance and limits

`SOURCE.json` records exact upstream Git blobs; `upstream/` preserves the
original method and eight guides, and `PORT.patch` distinguishes this authored
native binding. REA is MIT; runtime components retain their own notices.
Package integrity and decoded registry provenance do not establish a
reproducible build or exhaustive dependency security review. The recorded
source review adjudicates the scanner's findings rather than claiming a clean
scan. Actual readiness is the recipe's current check result, not this document.
