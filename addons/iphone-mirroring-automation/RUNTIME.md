# Rebuild the pinned Mirroir runtime when needed

Installing this skill copies instructions and original notices. It installs no executable, settings, MCP connection, background service or phone pairing. The reviewed source is [jfarcand/mirroir-mcp at 6b51c9f388b4d1956107cb0e664e75151e70d62d](https://github.com/jfarcand/mirroir-mcp/tree/6b51c9f388b4d1956107cb0e664e75151e70d62d), version 0.49.0, Apache-2.0. The active method and six original source documents have local hashes in SOURCE.json.

First discover an existing compatible runtime in the installation-local nstack native-tools index. Use its exact recorded executable and settings. Do not assume a saved path, method installation or another machine's check establishes current readiness.

If a runtime is missing and the task authorizes preparing one, acquire the exact source into a fresh, task-owned directory outside synced folders. For example, replace the three placeholders below with separate empty source, build and cache directories. Preserve any earlier working runtime.

```sh
git -c credential.helper= -c core.hooksPath=/dev/null -c protocol.file.allow=never clone --no-checkout https://github.com/jfarcand/mirroir-mcp.git /absolute/fresh/mirroir-source
git -c credential.helper= -c core.hooksPath=/dev/null -C /absolute/fresh/mirroir-source checkout --detach 6b51c9f388b4d1956107cb0e664e75151e70d62d
git -C /absolute/fresh/mirroir-source rev-parse HEAD
```

Require the displayed commit to equal that full pin. Review the retrieved Package.swift and Sources before running a build. Git source acquisition does not verify or execute an installed runtime. This route requires macOS and a compatible existing Xcode/Swift toolchain; installing Xcode or changing the active toolchain is a separate choice. The pinned manifest declares Swift tools 6.0 and uses embedded resources, so check compatibility with the actual installed compiler rather than relying only on that declared number.

The reviewed OCR-only configuration excludes optional Embacle FFI. It needs no Embacle installation, model download, provider or package registry dependency:

```sh
MIRROIR_DISABLE_EMBACLE=1 /usr/bin/swift build --package-path /absolute/fresh/mirroir-source --scratch-path /absolute/fresh/mirroir-build --cache-path /absolute/fresh/mirroir-cache -c release --product mirroir-mcp -j 4
```

Keep SwiftPM's normal sandbox. Do not copy the author's temporary acceptance-only re-execution guard or disable a sandbox as a general workaround. If a required environment control blocks the build, report that control and reconcile it within the authorized task.

After a successful build, retain the source pin, LICENSE, build command/toolchain and the resulting mirroir-mcp executable in durable installation-local storage. Resolve the product through the matching Swift build output rather than assuming a CPU-specific subdirectory. Record its actual SHA256 and absolute executable/settings paths in the private runtime record; do not publish those machine bindings or copy someone else's settings. The runtime's pinned source is recoverable from GitHub, while author binaries and compilation caches are intentionally absent from this repository.

Build success does not establish runtime or phone acceptance. Any protocol-only check needs an owned isolated HOME/CWD and updates disabled, limited to initialize, tools/list and ping with zero tools/call. Review the pinned source startup path before execution. Do not use doctor, status, check_health, an integration-test runner, phone capture or opening iPhone Mirroring as setup evidence. No global registration is required; connect the exact process only when the host and current task authorize it.

Normal phone operation remains separate: a real authorized target, iPhone Mirroring pairing, native macOS permissions and each private observation/action must be established for that task. Follow NATIVE-BINDINGS.md and the pinned permissions/security references. General setup does not authorize any of those effects.
