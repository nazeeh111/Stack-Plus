# Playwright MCP

The optional `--playwright-mcp` skill supplies the tested browser workflow and
[complete runtime/configuration reference](../../addons/playwright-mcp/references/runtime.md).
It reuses the already commissioned P061 Playwright runtime and browser. No second
package tree, global MCP registration or background service is required.

Install it with the same native or Claude adapter selection used for the rest of
the collection. OpenCode discovers the shared native skill. Actual stdio browser
checks passed; native desktop pointer repair remains a separate unresolved issue.
