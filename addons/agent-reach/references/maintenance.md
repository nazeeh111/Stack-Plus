# Maintenance

Read when an update fails, a browser cannot start, a channel errors, or the user asks to uninstall.

The installed SKILL.md's anonymous-access and credential restrictions control this reference. Setup, browser/account, configure, update and uninstall commands below describe upstream maintenance interfaces; this reference does not authorize running them in this installation.

- Update: `agent-reach update` upgrades Agent Reach, tools for added channels and the skill; `agent-reach update --check` only checks for a newer version. Upstream requires user agreement before an update.
- Status: `agent-reach doctor --text` reads local status without networking; `agent-reach check <channel> --text` performs one live network check (`--search` checks only search/jobs). Installation success is not a passed live check.
- Browser: `agent-reach browser status` reads status, `browser setup` prepares the engine and extension, and `browser stop` closes it. If a CloakBrowser download failed, upstream offers `browser setup --retry-cloak` after the network is repaired.
- Distinguish the failed stage: dependency download, browser connection, login, page loading and platform rate limits are different failures. A network timeout does not establish an expired login.
- Upstream tool errors: record the error and version. Upstream permits one `agent-reach update` after user agreement; do not modify the upstream tool's installation or retry in a loop.
- `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN` and `BUSY` end this attempt. Wait for the user to resolve the issue; do not repeatedly open windows.
- Keys and proxies: upstream exposes `agent-reach configure groq-key | openai-key | proxy | github-token`, with values supplied by the user. These credential/configuration routes remain unadmitted here.
- Port conflict (`Port <n> belongs to an unmanaged browser`): another program owns the dedicated browser port (default 9222). Do not close that program. Upstream offers `agent-reach configure browser-port <free-port>` with user agreement.
- Uninstall: upstream first shows `agent-reach uninstall --dry-run`, then runs `agent-reach uninstall` after confirmation. Only Reach-owned files are removed; the user's other files and browsers are preserved.
