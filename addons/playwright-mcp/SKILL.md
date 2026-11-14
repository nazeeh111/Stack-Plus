---
name: playwright-mcp
description: Operate a task-scoped Microsoft Playwright MCP browser when the user selects that workflow or needs persistent page state and structured browser tools. Ordinary browsing stays with supported host browser tools.
---

# Playwright MCP

Read [the runtime guide](references/runtime.md) before configuring or starting this route. Resolve the existing Playwright entrypoint, browser executable and accepted scope from the installation's `native-tools/index.json`; a recipe or skill alone does not establish a commissioned runtime. Reuse P061's official `mcp` subcommand instead of adding another package or browser.

Start a task-owned stdio connection with a task configuration and keep that connection for the workflow. Use a fresh isolated headless context, the commissioned browser, its sandbox, an authorized origin and owned output directory. Short non-synced scratch paths avoid Unix socket path limits. Leave everyday browser profiles, extensions, accounts, provider settings and global MCP registration outside incidental setup. Browser isolation and origin/file guardrails are not operating-system containment.

Inspect `tools/list` and use its actual parameter schemas. Observe the current page, select a unique target or current snapshot reference, act, then verify the visible result. Refresh references after navigation or DOM changes. Wait for meaningful page state when content is delayed; an action acknowledgement or generated code is not a completed effect. On a missing target, inspect fresh state before retrying. Honor permission denials across routes. If a capability is unavailable, choose another authorized supported tool only when it fits the task and verify its actual effect.

The exercised operations are `browser_navigate`, `browser_snapshot`, `browser_fill_form`, `browser_click`, `browser_wait_for`, `browser_take_screenshot` and `browser_close`. The raw server exposes 25 tools, including `browser_run_code_unsafe`, which runs code in the server process. Its capability setting cannot exclude core tools. Select only task-needed tools through the actual client's supported controls; verify enforcement before relying on it. Discovery metadata and the seven-tool test selection are advisory, not enforced server restrictions. Do not invoke unsafe code execution merely to simplify an ordinary interaction.

Keep evidence proportional to the task: inspect a screenshot when needed and read back the actual changed value or result. The recorded acceptance covers isolated Chromium loopback workflows, not every site, login, upload or native Mac operation. This route does not repair native `noWindowsAvailable`.

Finish with `browser_close`, close the transport, and clean up owned processes and scratch files while retaining useful outputs.
