# On-demand Mac control with Cua Driver

Use the native host's supported tools first. Cua Driver supplies an independent
Mac window/accessibility route when that route has a concrete capability gap.
It does not repair every native pointer failure or require rearranging windows
for CLI/browser data operations.

The reviewed official build is **0.51.3**, from the
[release](https://github.com/trycua/cua/releases/tag/cua-driver-rs-v0.51.3).
The universal macOS archive is `cua-driver-rs-0.51.3-darwin-universal.tar.gz`,
SHA256 `671915bd79e019c8456d804691bb9fd728571f04d8ca5dfcd8e4aaad8e10ec99`.
Its app is `com.trycua.driver`, signed by team `YCK386LBJ7`; executable SHA256
`86f2ef7b7a2306bf00792ea03158a322e4359c7c8ae199cecf0b26c32ae5213e`.
This verifies the reviewed distribution, not a reproducible build.

Read the MIT license and retained third-party notices. Matching operation guides
are at [source revision ebb4f0a](https://github.com/trycua/cua/tree/ebb4f0a5b635b5cd2fc885573de9555ed4f68b11/libs/cua-driver/rust/Skills/cua-driver).
Keep them beside the user-owned runtime, outside active skill discovery; the
selected fallback skill's older source version is separate from the installed
executable. Native bindings and user authority govern their setup examples.

Before replacing an existing app, inspect its version and ownership, back up its
actual bytes/metadata, and separately rehearse restoration. Preserve a shared
service or concurrent desktop task. Verify the downloaded archive, complete app
signature (`codesign --verify --deep --strict`) and notarization (`spctl --assess
--type execute`) before installing. Do not remove security attributes, approve
permission prompts with another tool, run the mutable updater, or change global
security settings. Missing native access belongs to the user/operator grant flow.

Record the exact executable, matching guide and scoped checks in the private
runtime index. A user-owned launcher may disable telemetry and update checks
for its process; no new global daemon or MCP registration is required. Use a
temporary owned socket/session when no suitable service exists. Read the actual
`describe TOOL` schema, use fresh exact-window tokens/captures, and verify the
requested effect before retrying a partial or uncertain action.

Author-Mac acceptance: background Calculator pixel7 through accessibility
hit-testing and semantic7×6=42, fresh image/value readback, stale capture refusal,
restoration to0 and owned cleanup. Pure HID, drag, arbitrary applications and
off-Space pixels remain unproved. Foreground activation can redirect concurrent
user input. End only the session/service this task owns.
