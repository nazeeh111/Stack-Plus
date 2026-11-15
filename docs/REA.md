# REA software analysis

[REA](https://github.com/morluto/rea) is a separate software-analysis toolkit,
not Craft Anything or the RAEA rendering engine. The optional `--rea` addon
installs `rea-software-analysis` for native discovery in Codex, OpenCode and
the portable Claude adapter. It adds no provider, global MCP server or service.

## Install the private runtime

Use Python 3.11+ and the retained checkout's recipe:

```sh
python3 recipes/rea.py install
python3 recipes/rea.py verify
python3 recipes/rea.py check
```

The recipe installs the full official `rea-agents` 6.9.0 package and a private
Node 24.22.1 on Apple Silicon macOS. Exact archives, extracted trees and native
signature are verified. It runs no npm hooks and changes no global Node, model,
provider or host configuration. The returned `node` and `script` paths are the
original CLI entrypoint. Existing changed runtime bytes are never overwritten.

## Use the checked operations

```sh
python3 recipes/rea.py native-exports --source /absolute/authorized/file \
  --outdir /absolute/new/task-evidence
python3 recipes/rea.py summary --evidence /absolute/returned/evidence.json \
  --outdir /absolute/new/summary
```

Native export inventory supports PE/ELF files. The wrapper uses an isolated task
HOME and environment, denies network and unrelated personal reads, and proves
those controls with synthetic probes. Complete Evidence, errors and input hashes
stay with the task. Exports alone do not reveal an implementation or prove runtime
behavior. Saved-Evidence summary is a separate operation.

The JavaScript/Electron `inspect` route currently fails on this Mac during owned
worker cleanup when process-table inspection returns `spawn EPERM`. Its graph
output does not establish successful cleanup. It remains uncommissioned; no
unrestricted retry, runtime patch or security-attribute change is a remedy.

The full CLI retains other upstream operations. Inspect matching command help
and prerequisites for a concrete task before use. Runtime attachment, native
decompilation, device changes and paid evaluations have separate requirements;
installation and these offline checks do not establish their readiness. Use a
task-owned MCP connection only when it offers value. Tool-family filters reduce
advertised schemas but are not permissions. No global MCP entry is required.

The shared skill retains the exact upstream method and eight guides as references,
with an explicit native port and source provenance. See
[integration pins](../integrations/rea/PINS.json) and
[runtime details](../integrations/rea/README.md).
