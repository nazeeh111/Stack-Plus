# Host and application mechanisms

Reviewed 2026-11-14. These are source-backed decision references, not an installed model menu or proof of endpoint access. Recheck the actual host/version before use. No framework, model endpoint or provider is installed by this skill.

## Native Codex

Inspect the current collaboration tool schema. In the reviewed host, `spawn_agent` accepts optional `model` and `reasoning_effort` only with `fork_turns: "none"`; full-history forks inherit the parent's model and effort. Its finite model selectors and concurrent slots are host-specific. Supply the required task context when using a fresh worker and keep the chosen lead unchanged. An unavailable arbitrary provider ID cannot be made available by a prompt.

[Official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes configurable model/effort defaults and parent orchestration. Custom agents inherit the parent's provider, permissions and MCP servers; custom files cannot override those controls. Product documentation does not override the current session's supported tool arguments.

## OpenCode 2.3.0

Pinned release: [`a6b15d33daf6ab7d35569f6d711fdb630b9f04e7`](https://github.com/anomalyco/opencode/tree/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7).

The native [`subagent` tool](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/core/src/tool/plugin/subagent.ts) takes `agent`, `description`, `prompt`, optional `model`, and optional `sessionID`. Its model override uses `providerID/modelID` or `providerID/modelID#variant`. The source requires an explicit user request for that model/variant and lookup through `models`; it validates availability, chat-model type and variant. New children resolve explicit override, then configured agent model, then parent model. Fresh children need supplied context; `sessionID` continues the same child. Follow native completion notifications rather than polling this tool's background jobs.

No persistent agent or global config change is needed for that per-call route. [V2 agent definitions](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/services/site/src/docs/content/agents.mdx) support a model preference, `steps` and ordered `permissions` rules. Parent `subagent` permission governs launching; a child uses its own configured permissions, so verify its scope separately. Avoid V1 fields such as `permission`, `tools`, `maxSteps`, `prompt` or top-level `temperature`. V2 `request` overlays are preserved but not yet sent by the runner. These are reviewed source mechanisms, not evidence that a particular provider/model was configured or executed locally.

## Other hosts

Inspect their actual worker selectors and model inheritance. Use available native capabilities without assuming Codex/OpenCode APIs exist there. If per-worker model selection is absent, report that gap; do not simulate heterogeneous execution, start a different host or alter provider configuration implicitly.

## Produced applications

Choose a manager that calls agents as tools when it must retain the conversation and synthesize results. A handoff instead transfers active conversation ownership. Deterministic code or a durable graph is useful when the application requires explicit control flow, checkpointing or pause/resume. Native host coordination does not need that extra runtime.

- **OpenAI Agents SDK:** existing OpenAI Developers Agents skill covers caller-owned loops. [`Agent.as_tool()` versus handoffs](https://openai.github.io/openai-agents-python/multi_agent/) changes ownership; [per-agent models/providers](https://openai.github.io/openai-agents-python/models/) require compatible tool, structured-output and input features. Reviewed source pin: [`64fbde5d02b42ae5f9db668eb0184cdb3fc9d775`](https://github.com/openai/openai-agents-python/tree/64fbde5d02b42ae5f9db668eb0184cdb3fc9d775). SDK/API calls are separate from host subscription sign-in; this method grants no new spending or credential authority.
- **LangGraph/LangChain:** [tool-wrapped subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) provide central control/context isolation; [orchestrator/worker graphs](https://docs.langchain.com/oss/python/langgraph/workflows-agents) support dynamic worker tasks. The nstack AI-workflows wrapper is offline and provider-free; resolve its actual installed entrypoint before use. A networked application requires separate commissioning. Reviewed upstream pin: [`08a2016953789a4f579b4d36bd1967941ec62012`](https://github.com/langchain-ai/langgraph/tree/08a2016953789a4f579b4d36bd1967941ec62012); installed versions may differ. For concurrent durable workers, [subgraph persistence](https://docs.langchain.com/oss/python/langgraph/use-subgraphs) must not share an unsafe per-thread checkpoint namespace. The [supervisor library itself](https://github.com/langchain-ai/langgraph-supervisor-py/blob/88859b34017ac3569bbd4a3092c7e77593a0a960/README.md) recommends direct tool-based supervision for most uses.
- **PydanticAI, only if a project needs it:** [typed agent delegation](https://github.com/pydantic/pydantic-ai/blob/7689e1b2d1541c8d77f50039bf8273fb092e905d/docs/multi-agent-applications.md) returns control to the parent. Forwarding `ctx.usage` aggregates delegate usage; `UsageLimits` can bound the supported request/token/tool/cost dimensions. Cost across different models cannot be reconstructed from aggregate token counts. This is a reference alternative, not an installed dependency or a reason to replace an existing working application.

Source references establish mechanisms, not a successful mixed-model run or a quality/latency/cost advantage. Record those separately when actual task evidence exists.
