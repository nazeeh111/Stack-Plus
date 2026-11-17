# Owned Linux REA backend

This optional, on-demand backend preserves the full official REA6.9.0 CLI/MCP/skill payload and adds Ghidra12.1.4 for useful JavaScript and native investigations. It uses one Linuxamd64 image under an existing Docker engine, including emulation on Apple Silicon. It is separate from the existing macOS export-table route, Craft Anything and RAEA.

The host client ignores inherited Docker contexts, remote endpoints, proxy and
credential configuration. Each invocation uses a fresh temporary HOME/config,
removed on exit, and an existing local Unix socket. `--docker-host
unix:///absolute/socket` (before the command) can select another existing local
socket. Standard Docker Desktop binary locations work with a reduced PATH.

The image is not a default service. Preparation does not register an agent, change its model/provider, install host Java/Node, alter native permissions or start Docker. Docker must already be running through its supported controls. No hosted model or provider is used by the recipe.

## Prepare and build

```sh
python3 /absolute/nstack/recipes/rea_linux.py prepare
python3 /absolute/nstack/recipes/rea_linux.py metadata
python3 /absolute/nstack/recipes/rea_linux.py build
python3 /absolute/nstack/recipes/rea_linux.py verify
```

`prepare --acquired DIRECTORY` accepts previously acquired artifacts with exactly the filenames in `PINS.json` (`rea.tgz`, `ghidra.zip`, `InRelease`, `Packages.xz` and14 named .debs). All hashes are required. The official pinned base image must be acquired explicitly before `metadata` or `build`; the recipe never silently pulls another image:

```sh
docker pull --platform linux/amd64 node@sha256:c8c4a7483bb04544293c82a3eecc3081c37ff5dfedcaf819d60e6e4aaad35b12
```

Before build, the exact base's existing sqv verifies Debian InRelease with its built-in official keyring and default cryptographic policy. Authenticated index identity and an actual apt no-install simulation must agree with the frozen14-package set. A new dependency or failed signature stops. There is no signature, policy, permission or unrestricted fallback. The reviewed install uses dpkg on exactly those local hash-verified .debs, with build networking disabled. The full original archives, package notices, Ghidra notices and distro notices remain; no npm/lifecycle hook or upstream setup runs.

A changed prepared tree, archive, source identity or built image is refused and preserved. Source updates require a separate reviewed preparation; the recipe does not overwrite changed installations. Default private state is `~/Library/Application Support/nstack/native-tools/rea-linux/6.9.0`; `--state` precedes the command when a different explicit state root is needed.

## Static MCP for one selected task

```sh
python3 /absolute/nstack/recipes/rea_linux.py mcp \
  --input /absolute/authorized/artifact-directory \
  --outdir /absolute/new/private/task-evidence
```

Connect that command as a task-scoped stdio MCP server in the client that needs REA. Root/client registration owns the chosen server configuration; installing a skill or building this image does not establish a connected native host. Keep one registration owner and avoid duplicate plugin and setup-owned servers.

The source must be one explicit, link-free artifact directory, not a home, account, credential store, vault or host root. Nested sensitive paths and special files are refused. Default input budget is128MiB/10,000entries. The controller copies a frozen source snapshot through no-follow file descriptors, mounts that snapshot read-only at `/input`, and maps supplied host paths within the selected source to guest paths. Writes stay in a fresh `/output` task directory or bounded guest temporary storage. Existing output and overlapping runtime/input/output paths are preserved and refused. Keep returned Evidence IDs and input digests; guest paths are analysis-machine coordinates, not Mac paths.

The controller enforces the explicit72-tool static list in `static-tools.json`: it filters actual `tools/list` results and rejects direct calls to omitted tools before upstream execution. Family advertisements are not its enforcement mechanism. Selected operations cover JavaScript graphs/feature tracing/comparisons, native Ghidra functions/assembly/references, managed readers, retained views, bundles and reconstruction checks. `open_binary` is bound to the reviewed Ghidra provider. Unsupported methods and server-to-client model sampling, elicitation and host-root requests are rejected. Input paths outside selected input/output are refused.

The original255 tools and196 CLI commands remain in the payload. Availability and acceptance remain operation-specific. Optional engines, firmware/device/browser/debugger operations, live target execution and environment solving are **not activated by this static policy**. Broader operations require a separate explicit task mode with reviewed prerequisites, tool effects and actual host authority; do not widen the list merely to repair an unavailable tool. Existing source/helper methods cannot grant spending, credentials, phone access or target execution. No claim of all255-tool acceptance is made.

## Containment and lifecycle

Runtime uses nonroot UID1000, default Docker seccomp, all capabilities dropped, no-new-privileges, private PID/network namespaces, network none, read-only root and input,4GiB memory,2CPUs,256PIDs and512MiB guest `/tmp`. No host process table, home, private apps, vault, credentials or Docker socket is mounted. The host controller invokes Docker; the analysis container has no Docker socket.

Ghidra's Unix sockets and owned runtime files use native guest `/tmp`, preserving their POSIX permission checks. Host-shared output filesystems need not support Unix-socket chmod. Docker's existing `--init` reaps adopted children. The runner verifies that exact init ancestor, waits boundedly for actual reaping and records every remaining process, including zombies. It does not ignore leftover workers to turn cleanup into success. EOF closes the actual REA connection; owned cleanup failure remains a failure. No unchanged operation is restarted because an observer timed out.

Each task retains `CONTROLLER.json`, actual final Docker controls/mounts/state, upstream stderr, input ownership/hash and `output/lifecycle.json`. Use REA's `export_evidence_bundle` to save useful complete session Evidence before `reset_investigation`; consuming partial output never repairs a failed producer. For new sessions, import authenticated bundles and use retained references rather than resending large inline Evidence or recomputing matching analysis. Runtime and task checks do not establish universal parser safety or behavior equivalence of a reconstruction.

## Provenance

- [Official REA6.9.0](https://github.com/morluto/rea/tree/d74549e495c58eb4a560279fd9f05508401ea0a0): MIT; original package and dependency notices retained.
- [Official Ghidra12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build): original license/component notices retained.
- [Official Node image](https://hub.docker.com/_/node) and [Debian signed release metadata](https://deb.debian.org/debian/dists/trixie/InRelease): exact identities and package hashes in `PINS.json`.

This image/recipe is a scoped integration of upstream tools. It does not patch REA, replace its analysis with another parser or change the denied macOS JavaScript route.
