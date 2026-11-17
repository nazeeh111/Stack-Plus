# Local runtime

The accepted macOS arm64 pin is edge-20261117-54ced5d / 0.15.1-edge+54ced5d, source54ced5d3f573a45bfbe717dd2099cd1fa3b06220. This optional runtime is separate from skill installation. Its source runner/pin are under runtime/; no binary is committed here.

On an existing installation, resolve `Omnigraph local` in the nstack native-tools index. Invoke its recorded Python runner with an explicit owned project:

```text
python3 <runtime-root>/run-local.py --workspace /absolute/project -- version
python3 <runtime-root>/run-local.py --workspace /absolute/project -- lint --schema schema.pg --query read.gq
python3 <runtime-root>/run-local.py --workspace /absolute/project -- init --schema schema.pg --target ./graph.omni
python3 <runtime-root>/run-local.py --workspace /absolute/project -- query --query read.gq --target ./graph.omni --format json
```

Use the complete method and actual command help. Paths and graph targets must stay inside the project. Canonical init uses --target; positional creation addresses are intentionally refused. Account, cluster, provider, server/MCP, skill export, private host directories and operator overrides are unavailable. The runner verifies the binary every call and fails closed if bytes or native sandbox prerequisites differ. It does not grant data-write authority.

To recover on another Apple-silicon Mac, acquire the exact official archive URL in runtime/pin.json into owned temporary storage. Verify its SHA256 and official repository build attestation/source revision before extraction. Extract only the regular `omnigraph` member into a fresh runtime-root/bin; preserve the upstream MIT license. Verify the extracted SHA256, strict Developer ID signature and Apple notarized requirement (`codesign --verify --strict` and `codesign --verify -R=notarized --check-notarization`). Apple documents these non-app checks in https://developer.apple.com/forums/thread/130560 . Do not clear quarantine, re-sign or weaken protection if checks or launch fail.

Copy runtime/run-local.py beside bin and verify its recorded hash. Use a fresh owned fixture to execute version, schema/lint/init/load/query/branch/reopen and negative target/network/filesystem checks before registering its entrypoint for that host. Keep a prior working runtime/data until acceptance succeeds. This is an explicit reviewed recovery procedure, not an automatic downloader or promise that future platforms/artifacts will be accepted.

The prerelease writes format17 and serves14-17; stable0.15.0 cannot read17. Local graph and changing-workflow acceptance does not commission cluster authorization, MCP/cloud, all crash windows or real production. The private Knowledge vault remains curated through its existing writer, not graph-ingested or replaced.
