# Native operation

This binds achimala/dream-loop at `9bddb901f7d071cfefdd21e264267c757177a9df` to Codex, ChatGPT and OpenCode without changing the user's model or effort. Read this before the selected workflow. The complete original source is preserved under `upstream/`, with exact file hashes and native diffs in `SOURCE.json`. Active Pro workflow text is unchanged; active Plus retains its delegated build passes and three-round stop. This document supersedes only native execution, paid-provider defaults, model overrides, and unavailable tool paths.

## Start with actual tools and an owned project

Use the host's existing image-generation capability, image viewing, fresh-context native subagents, supported live product capture, and the registered local Blender. No new runtime helper, service, provider account, host configuration, global package or model is needed. Installed instructions alone do not prove these capabilities work. Check required tool availability for the current task; report a gap when no supported route exists.

Resolve the explicit product directory and inspect its repository state before editing. Keep sources and editable assets with that project. Create `.dream-loop/` inside it for target, rounds, screenshots and asset records; preserve existing ignores when adding `.dream-loop/`. Preserve unrelated work and previous valid renders. Do not use an account/config directory as the preview root. Installation does not authorize publication, commits, messages, or paid services.

Select exactly one workflow as described in SKILL.md. If no tier is known, record the native Pro default instead of guessing the user's subscription. A Plus invocation still uses workers and stops after three loops; a Pro invocation still uses the independent judge and its score/FPS/stall rules. Do not combine both recipes.

## Target generation and inspection

Use an actual user-supplied target or the host's built-in image-generation tool. For an existing product, capture its current state and pass the image into generation to preserve its identity. Prompt for an achievable exact screenshot of the requested product, not unrelated concept art. Save and inspect the real generated output at `.dream-loop/target.png`; do not invent a local path when the tool returned only inline media. Use the host's supported generated-file mechanism, or report that saving is unavailable. Do not use screenshots of the generator UI as the target.

Keep the locked target stable during a refinement loop. Record dimensions, source/generation provenance, chosen workflow, required controls/FPS and start time after target lock. Check time between rounds when a time budget exists. Follow the upstream fidelity and time policy, including its warning about token use for an unbounded loop.

## Native worker and critic calls

Use the actual host's native agent tools in this chat, with a fresh empty context for each worker or judge. Do not create separate user-owned chats. Omit model and effort overrides so agents inherit the user's selection. Host tool names differ: discover the supported native capability rather than simulating a worker or starting an external paid model session. If no independent agent route exists, report the gap; an orchestrator self-score is not a fresh critique.

For Plus, pass the worker the actual target image, latest product screenshot, user's request, and absolute path to `plus-mode/assets-3d.md`; keep the source high-level worker directive, no worker testing, and orchestrator validation. Count exactly three loops before the review handoff.

For Pro, read and use the entire [source workflow and judge prompt](pro-mode/workflow.md), including all four rubric categories and fractional scoring. Give each judge the actual target and latest screenshot, previous screenshot/verdict when available, and the complete prompt. Local files must be visually opened by the judge through image viewing, not inferred from filenames or prose descriptions. Save its complete feedback and scores by round. The builder must implement actionable feedback, test and capture again; no invented judge, withheld blocker, or automatic score increase.

## Blender and 3D assets

Follow the selected workflow's complete asset sourcing order. Free external assets require user allowance. Fal or any other separately billed image-to-3D provider requires explicit provider, scope and budget authorization. The installed presence of keys grants none; do not inspect credentials to determine authority. Without such authorization, image-to-3D is disallowed. The Pro asset recipe explicitly advances to Blender in this case. Plus explicitly excludes Blender and advances to its procedural route when image-to-3D is disallowed. This is a source-supported fallback, not permission to skip generated textures or lower the visual target.

For Pro modeling, resolve Blender's recorded `command` in nstack's `native-tools/index.json`; use the existing Blender production/modeling/material/lighting skills needed for the scene. The reviewed current native build is 5.2.1 LTS, located at:

```text
~/Library/Application Support/nstack/native-tools/blender/5.2.1/Blender.app/Contents/MacOS/Blender
```

Expand `~` for the shell or use the index's actual absolute command. Verify the command/version, then use its Python scripting interface for task-owned source and editable `.blend` output. Preserve the user's installed app and other versions. No MCP registration or new Blender install is required. Model scale/orientation, camera, lighting, textures, normals and materials still need actual visual validation. Use image generation for relevant textures/normal maps/skyboxes as the source requests; do not silently replace unavailable generated inputs with flat or noisy substitutes.

The optional Fal commands and endpoint recipes remain in [fal.md](fal.md), with unchanged reviewed helper/tests under `scripts/`. Live provider availability and schema currentness are not established by installation or mocked tests. If separately authorized later, restrict input/output paths to the trusted project, preserve job IDs/uncertainty and the helper's manifest lock, and preview real downloaded GLBs before calling assets ready. Respect native network denials; do not switch tools to evade them.

## Actual product captures and exit

Test the actual requested product before each capture. For an interactive app, open its real local app/server in the supported browser or native app and exercise requested controls. Capture a consistent viewport/camera/state and measure the requested FPS under a stated sample interval and scene. A Blender still image or test script output does not establish browser behavior or interactive FPS.

For a still scene, inspect a fresh actual Blender render and reopen its editable source. Record interactive FPS as not applicable and explicitly scope acceptance to the still deliverable; never label a still-render check as full game/app acceptance. For an animation, inspect representative fresh frames and the exported playback as appropriate to the request.

The upstream [Pro exit criteria](pro-mode/workflow.md) govern the loop: score >=8 plus acceptable requested FPS; optimize/rejudge when FPS fails; after two insufficient-improvement or repeated-gap rounds make the specified larger rethink; if that fails, stop for the user's judgment. Preserve the actual feedback and artifacts for the stopping condition. Missing screenshots, failed controls or unreadable judge inputs block acceptance even when code/tests succeed. Show the latest real screenshot and accurately state progress, score, functional/performance checks and any material limit. Plus retains its separate three-loop handoff.

An optional unchanged `scripts/preview-server.py` can serve a selected task directory on 127.0.0.1 and save POSTed PNG captures. It does not itself capture screenshots. It has no authentication/origin controls; standard Python serving can expose files and follow symlinks. Use only a trusted project without private data or external symlinks, preserve timestamped captures, and stop the server afterward. Prefer supported host capture when available. No server is enabled by this skill.
