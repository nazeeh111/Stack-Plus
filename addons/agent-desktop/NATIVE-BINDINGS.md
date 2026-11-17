# Native Agent Desktop binding

This skill preserves Vercel Labs Agent Desktop's complete core method and all
three platform guides. The upstream name and CLI identifier remain
`agent-desktop`. Read [the macOS guide](platforms/macos/GUIDE.md) on this Mac;
the [Linux](platforms/linux/GUIDE.md) and
[Windows](platforms/windows/GUIDE.md) guides describe those platforms only.
Their references are retained beside each guide. They are support documents,
not additional host skills. [SOURCE.json](SOURCE.json) records exact source
coordinates, support-file hashes, unchanged originals and the adaptation diff.

## Select the actual supported route

An explicit user selection of Agent Desktop is sufficient to select this
skill. Historical catalog conditions do not override the current request.
For other requests, prefer the appropriate connected application or native
host tools, then choose a CLI only for a concrete capability need. Preserve
one controller per desktop and one writer for a complete edit sequence.
Agent Desktop is a desktop accessibility CLI; agent-browser is a separate
browser CLI, and Cua Driver is a separate native desktop service. Their refs,
sessions, captures, grants and acceptance evidence are not interchangeable.

## Runtime admission comes before invocation

Resolve Agent Desktop from the current private nstack native-tools index at
`~/Library/Application Support/nstack/native-tools/index.json`. Use its exact
recorded executable, paired helper, version, readiness and evidence. A skill
being installed does not establish that its runtime is installed or admitted.
If its runtime entry is absent or blocked, report that state and use these
local guides for planning. Do not execute a random PATH match, install a
mutable npm package, or present another desktop tool as Agent Desktop.

Observed November 15, 2026: the official v1.3.1 macOS arm64 archive has SHA-256
`9b7b7cfc74892eab46c2c85d6cb7dc4863bf8dab0a222cfcfb8ae4604c69c86c`.
It matches the release asset digest and official `checksums.txt`. It contains
`agent-desktop` and `agent-desktop-macos-helper`. Both have valid ad-hoc code
signatures without a developer Team Identifier; native Gatekeeper assessment
rejects each with exit 3. Neither was executed during this review. No native
permission, trust, quarantine, signing or application profile was changed.
This is a blocked runtime, not an accepted desktop capability.

The corresponding release source is
`b0b7277bea09b770ef9d1fb45aad667bc432cd57`. Do not silently use a build from main
with these version-matched guides or claim that release provenance proves
notarization, runtime acceptance or source-to-binary reproducibility.

The CLI has a startup side effect before parsing even `version`, `--help` or
`skills`: it enumerates same-user processes, reads process argument and
environment buffers looking for legacy Agent Desktop command hosts, and can
send SIGKILL to a matching host after ownership, signing-identifier and start
time checks. A future interface probe must account for this behavior; these
commands are not purely read-only. Do not run them while runtime admission is
blocked. Do not patch, rebuild, re-sign, remove quarantine or switch package
channels to evade a native rejection.

## After a supported native admission

Recheck the exact executable and helper hashes and native admission at their
recorded destination. Keep the helper beside the executable. Verify the
actual launching host and permissions independently for Codex, OpenCode and
ChatGPT: a grant or successful test from another host does not transfer.
The plain `permissions` command does not request grants, but `--request` can
prompt and `--guide` opens System Settings with a guide. Those are separate
native permission workflows and require applicable authority. Do not run a
doctor, permission guide, prompt, Automation operation or screenshot merely
to test whether a missing grant can be obtained.

Use one absolute task-owned `AGENT_DESKTOP_HOME` and a unique explicit
`--session` on each call. Start sessions with `--no-trace` unless tracing is
needed and authorized; screenshots and UI snapshots can contain private data.
Do not inspect credentials or unrelated clipboard, notifications or apps.
Keep outputs private with the owning task. Never run broad session garbage
collection or remove another task's state. End only the owned session.

For an admitted runtime, the upstream sequence is `status`, plain
`permissions`, and version-matched platform help before an unfamiliar
operation. Those observations must succeed for the actual host. Target a
specific observed application and window, use fresh qualified refs, read
`data.complete`, and inspect `disposition.delivery` and `disposition.retry`.
After uncertain delivery, observe before repeating or substituting an action.
A semantic acknowledgement or field value alone does not prove document-level
success. Verify the intended effect independently.

Use physical input only when the user's actual task already authorizes it
and it is necessary. Existing task authority need not be requested again for
every gesture. Do not automatically escalate a failed semantic action to
`--headed` or `--force`, and never use another tool to bypass an OS or target
denial. Coordinates must come from the exact fresh target observation.
Physical input takes the shared foreground and cannot safely be owned by
several actors at once.

The upstream sandbox VM, IPSW download, guest SSH credentials, provider
installation, MCP registration, cursor overlay and `launch --cdp` examples
are preserved documentation. They are not activated by installing this skill.
Do not close/restart a real app, expose a debugging port, modify its profile,
request new grants or set up credentials without matching task authority.
Use the ordinary accessibility route for an already-running Electron app.

## Acceptance before broader claims

After admission and host permission checks, validate a small task-owned test
application: observe an exact control, perform one reversible semantic edit,
verify actual state, prove stale-ref refusal, and restore the starting state.
Test screenshot or physical input only if required and already authorized.
Record the exact host, binary/helper/source versions, target, returned delivery
and effect, refusals and cleanup. Do not call Calculator, Obsidian or any
desktop application accepted based only on Cua Driver or native host results.
