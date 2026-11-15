# OpenCode V2

Install nstack's native skill collection first, then run:

```sh
python3 opencode_setup.py install
opencode --version
opencode api skill.list
opencode mcp list
```

The adapter baseline was checked against OpenCode 2.2.6. Shared skill discovery,
including Playwright MCP and 01's explicit-selection policy, was also checked in 2.3.0. It uses the installed desktop
CLI, not another package installation. Pass `--cli /absolute/executable` for a
different existing V2 installation. The selected model, provider, effort,
credentials, conversations and native permissions are untouched.

OpenCode discovers the existing `~/.agents/skills` collection. The optional
`--playwright-mcp` addition to `native_setup.py` therefore reaches OpenCode too;
its [skill guide](../addons/playwright-mcp/SKILL.md) selects task-scoped browser
automation without activating another global MCP connection. Its global
`~/.config/opencode/AGENTS.md` links to the user-owned `~/.codex/AGENTS.md`.
Review that shared file for host-specific assumptions first. The optional
`templates/AGENTS.md` is a concise starting point, not an automatic replacement
for user preferences. The native installer continues to manage its nstack block.

Select **@01** through OpenCode's skill picker once for the chat. This attaches its instructions; Codex's `$01` syntax is not an OpenCode skill attachment. In a scripted `opencode run`, explicitly ask the model to load skill ID `01` with its `skill` tool, or use a native session prompt with `skills: [{"id":"01"}]`. [Skill loading](https://opencode.ai/docs/skills/#loading).

When starting OpenCode 2.3.0 from another program, set both the child's working directory and its `PWD` environment value to the intended project. Its CLI uses inherited `PWD` before `process.cwd()`; changing only a Python subprocess's `cwd` can target the caller's project. Ordinary shells maintain `PWD` already. [Pinned CLI behavior](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/cli/src/run/run.ts#L62).

A small V2 configuration disables background warming and connects the existing
free Context7 and GitMCP endpoints. If the selected Serena runtime is present,
it uses that runtime with no memories, dashboards or automatic project activation.
OpenCode gets a separate Serena state directory to avoid competing host writers.
The adapter refuses existing conflicting configuration or links before changing
anything. It never reads auth stores or service registration, copies provider
configuration, or rewrites existing JSONC. Existing customized configurations
require a scoped manual merge rather than an automatic reset.

Local hosts share canonical Markdown knowledge and project task handoffs.
The shared AGENTS.md supplies the same relevance-based lookup and durable-note
capture behavior to both hosts. OpenCode V2 [documents global instruction updates](https://opencode.ai/docs/instructions/#updates)
before its next model request; start a fresh Codex session after editing it.
Vault reads and writes use native permissions. `--vault /absolute/vault
--vault-write allow` explicitly permits edits there for build/general agents;
direct file edits to `.git` and `.obsidian` metadata remain denied. These guards
survive a later return to `ask`; normal Git CLI commands still follow native
shell approval. Read-only roles and existing narrow denials remain intact. Without this option,
the adapter preserves the current vault write choice, initially `ask`.
On the author Mac the private vault is `~/Knowledge`, with private local Git
history. Keep source, scope, note ID, generation/hash, dates and correction path
with each claim. Re-read the current note and source before reuse. Give concurrent
tasks separate files; reconcile a changed generation before writing a shared note.
For project JSON records, `nstack knowledge set/delete --expected-generation N`
serializes writers and rejects stale updates. Creation uses generation 0. This
protects that command, not arbitrary Markdown edits or host-generated memories.
No synchronizing daemon, extra database, automatic-memory export or public-vault
copy is needed. Native automatic memories and chat histories remain host-owned.

| Host | Shared local layer | Boundary |
|---|---|---|
| Codex CLI and desktop backend | User skills, instructions, canonical vault and project handoffs | Native accounts, tools and memories retain Codex permissions |
| ChatGPT desktop Work | Local files and skills when local access/tools are available | A cloud-only chat cannot read the Mac's vault; verify a fresh local chat |
| OpenCode | The same user skills, linked instructions, vault and handoffs | Its own tools, approvals, provider connection and chat history |

For a correction, update the owned canonical note once with its new generation
and source. Each host re-reads that note before reuse. This is shared knowledge,
not automatic synchronization of native memories. See [Work local access](https://learn.chatgpt.com/docs/get-started-with-work).

## Actual Codex harness

The optional Desktop launcher starts the installed native Codex CLI in an
OpenCode session terminal. It adds `/codex` and **Open Codex harness** to the
desktop command palette. This is a separate native Codex conversation beside
the OpenCode chat. It does not replace OpenCode's own agent engine.

```sh
python3 opencode_setup.py install --codex-harness "$(command -v codex)"
```

The launcher targets OpenCode Desktop 2.2.6's experimental GUI and persistent
terminal APIs. Recheck it before upgrading OpenCode. It runs only from a saved
session on the app's own server, in that session's current project directory.
Repeating the command selects its running Codex terminal. A normal OpenCode TUI
terminal can run `codex` directly; the desktop command is not a TUI extension.

No model request is made by opening the terminal. Codex inherits its own account,
model/effort, instructions, discovered skills and permissions. The launcher
does not send the OpenCode transcript or composer draft to another agent.
Use the project's current task handoff file to continue work across hosts;
review it in Codex and give the objective there. Both hosts still read the same
shared skill collection and canonical vault. Their native chats and generated
memories remain separate. Native refusals are reported without alternate routes.

The installer accepts the exact original nstack adapter configuration or the
exact desired launcher configuration. User-owned `permissions` and `policies`
are retained; other customized configuration or plugin bytes require a scoped merge. Installation backups and rollback cover the two plugin files
and configuration, while the existing adapter and user data remain recoverable.
See [the harness decision](HARNESSES.md) for the alternatives reviewed.

Codex's account connectors, app tools, built-ins, permissions, model support and
native automatic memory are not OpenCode plugins. Shared skill discovery does
not prove every host-dependent operation. Check actual available tools and use
supported native equivalents; report unavailable operations. Trials, substitutes,
paid/hardware/provider lanes retain their original activation conditions.

The install privately journals its exact targets, rehearses restoration of
existing targets and extends the normal `nstack` rollback chain. A second install
with unchanged inputs writes no target or journal changes. Later user edits
block a conflicting rollback instead of being discarded. Empty parent directories
may remain after rollback; projects, notes and conversations are preserved.

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

Quit Obsidian before the full chain if it includes an Obsidian application
replacement. Use `python3 opencode_setup.py rollback /exact/run` for just this
adapter without invoking older changes. Recovery code is staged outside the
checkout before any live mutation.

Guidance checked against [OpenCode instructions](https://opencode.ai/docs/instructions/),
[skills](https://opencode.ai/docs/skills/), [MCP](https://opencode.ai/docs/mcp-servers/)
and [warming](https://opencode.ai/docs/warming/), plus the installed API schema.
OpenAI recommends short, accurate [personal and project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and separating reusable skills from global rules in its [best practices](https://learn.chatgpt.com/docs/learn/best-practices).
Keep supported [permission configuration](https://learn.chatgpt.com/docs/permissions)
consistent; legacy sandbox settings override mixed modern defaults. Preserve the
current effective permissions when cleaning up redundant fields.

## Permissions and secrets

OpenCode 2.3.0 has built-in approval choices, with separate desktop and terminal preferences:

- **Desktop:** Settings → Preferences → General → **Auto-accept permissions** sets the app default. Projects can override it in their settings. It can answer requests from other active sessions on the connected server, including sessions this window has not opened.
- **Terminal:** `/settings` (or Ctrl+P → Open settings) → **Session → Permissions** chooses **prompt** or **auto accept**. Despite the Session label, this saves the global CLI preference. It is independent of the desktop setting.
- **One launch or script:** `opencode --auto` or `opencode run --auto "Your task"`. The scripted client's own auto acceptance requires this flag; it does not read the saved desktop or terminal preference. A connected desktop can independently answer requests on that same server.

Auto acceptance answers once and leaves explicit denials in force. The terminal and scripted clients limit their own replies to their session tree; the desktop follows the connected server's project settings as described above. Ordinary prompts also offer once, project-pattern always, or reject. No extra skill or approval wrapper is required. These choices do not grant macOS privacy permissions. Use the native settings controls to preserve other preferences and any legacy migration; the installer does not silently enable auto acceptance. [Desktop setting](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/app/src/settings/general/general.tsx#L24), [desktop request scope](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/app/src/session/requests/auto-approve.ts#L170), [terminal chooser](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/tui/src/component/dialog-config.tsx#L155), [approval semantics](https://opencode.ai/docs/permissions/#approvals).

Shared instructions do not give OpenCode Codex's operating-system sandbox.
[OpenCode permissions](https://opencode.ai/docs/permissions/) and
[hard-deny policies](https://opencode.ai/docs/policies/) are separate controls.
Prompt before shell commands and outside-project access when that matches the
user's authority. A shell command approved to run still has the host user's
access; file-tool deny rules are not a shell sandbox. Verify effective rules
for each agent, including agents with their own overrides.

Keep API keys in native credential handling, outside this repository. The
repository ignores local environment and account-store files while retaining
nonsecret example templates. Ignore rules do not protect already tracked or
force-added files; scan both the proposed tree and commit ancestry before
publishing. For ordinary OpenAI coding, restrict the existing project key to
the inference endpoints actually used, plus model listing when needed. Key
permissions, model access and spend limits are separate account controls;
verify whether the selected spend limit is enforced or only alerts.

## Agents and media

Use OpenCode's native agents for its own delegated work. The OpenAI Agents API
is a separate application interface, with additional key permissions and optional
hosted resources; it is not required to use OpenCode agents. The Decisions API
returns typed classifications and scores, rather than replacing the agent engine.
Do not add either service merely to route ordinary tasks.

For image input, choose a model whose current native catalog supports images and
attach a supported image. Audio attachments are not automatically sent to the
model, even when a listed model supports audio. Use an explicitly available
transcription or speech workflow for a real audio task. Catalog availability does
not prove endpoint permission, budget or successful execution. Keep existing
key restrictions; expand only for a concrete authorized task.

Sources: [OpenCode agents](https://opencode.ai/docs/agents/),
[attachments](https://opencode.ai/docs/attachments/),
[OpenAI Agents API](https://developers.openai.com/api/docs/guides/agents-api/quickstart),
[Decisions API](https://developers.openai.com/api/docs/guides/decisions).
