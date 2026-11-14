# Playwright MCP without another browser installation

Use Microsoft's [Playwright MCP](https://github.com/microsoft/playwright-mcp)
for an explicitly selected browser workflow that benefits from persistent page
state and structured tool calls. The commissioned P061 Playwright 1.65.0 already
contains the official `mcp` subcommand. Reuse it; no separate `@playwright/mcp`,
browser download, extension, account or global MCP connection is needed.
Ordinary browser work can keep the host's supported browser tools.

## Run on demand

Commission P061/test first if absent. Resolve its existing Chromium executable
from the commissioned receipt/browser directory; the author's verified path is
also recorded in the private native-tools index. Keep the runtime lock and
browser version together. Create a task-owned configuration, replacing all
three placeholders with the actual browser, authorized origin and output folder:

```json
{
  "browser": {
    "browserName": "chromium",
    "isolated": true,
    "launchOptions": {
      "headless": true,
      "chromiumSandbox": true,
      "executablePath": "ABSOLUTE_COMMISSIONED_CHROMIUM_EXECUTABLE"
    },
    "contextOptions": { "serviceWorkers": "block" }
  },
  "network": { "allowedOrigins": ["AUTHORIZED_TASK_ORIGIN"] },
  "outputDir": "ABSOLUTE_TASK_OUTPUT_DIRECTORY",
  "webmcp": false,
  "ignoreRoots": true,
  "saveSession": false,
  "codegen": "none"
}
```

Connect a task-owned stdio MCP client to:

```sh
nstack run P061 test -- mcp --config /absolute/task/playwright.json
```

This is a server process, not a one-shot page command. Keep the same client
connection for the workflow, inspect current page state between dependent
actions, and call `browser_close` before closing its transport. Use a short
non-synced temporary directory for browser scratch files; long socket paths can
exceed the Unix limit. Do not attach an everyday authenticated profile or enable
remote debugging on an existing app as incidental setup. Origin/output settings
help scope a task; they are not an operating-system security boundary.

For a project-specific Codex connection, retain unrelated configuration and use
the native client's [tool allow list](https://learn.chatgpt.com/docs/config-file/config-reference):

```toml
[mcp_servers.playwright_task]
command = "/absolute/path/to/nstack"
args = ["run", "P061", "test", "--", "mcp", "--config", "/absolute/task/playwright.json"]
enabled_tools = ["browser_navigate", "browser_snapshot", "browser_fill_form", "browser_click", "browser_wait_for", "browser_take_screenshot", "browser_close"]
```

The raw server lists 25 tools, including server-side `browser_run_code_unsafe`.
Its capabilities setting does not remove core tools. Select tools in the actual
client; an allow-list field in nstack's discovery metadata is only a selection
hint. The seven operations above were exercised directly; native-client filter
enforcement was not separately tested in this acceptance. Choose other tools
only when the task requires them and the host permits them.

## Observed acceptance and limits

Seven real stdio checks passed four times against the unchanged existing
runtime: two normal nstack launches, one stripped-PATH launch using its Node
fallback, and one direct existing CLI launch. They covered initialization/tool
schemas, visible form results with independent fixture events, delayed DOM,
reload persistence, separate-process cookie/storage isolation, missing-target
failure/recovery and close-reset. Actual screenshots were inspected; owned
browser/server processes and loopback listeners were cleaned up.

The separately reviewed `@playwright/mcp` 0.0.85 comparison also passed twice,
but its duplicate package tree was removed. Existing runtime file hashes and
receipt stayed unchanged. This is bounded Chromium/loopback acceptance, not
proof of every website, account, upload or native desktop operation. Headless
browser work needs no desktop rearrangement. It does not repair macOS native
`noWindowsAvailable` or control arbitrary desktop apps.
