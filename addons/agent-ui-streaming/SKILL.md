---
name: agent-ui-streaming
description: "Build and review streaming interfaces for agent-powered apps with AG-UI: messages, shared state, tool results and human decisions. Use for agent-to-frontend integration, not ordinary native Codex/OpenCode coordination."
metadata:
  category: "Agent applications and frontend interaction"
---

# Agent UI streaming

Use AG-UI when a produced application needs a portable event stream between an agent backend and an interactive client. Keep the chosen framework and project dependencies. MCP supplies tools; native orchestration or an agent framework controls execution; AG-UI carries interaction. It does not make host subscriptions, plugins, permissions or durable memory interchangeable.

Inspect the project's lockfile and current client/server contracts. The reviewed basis is the [1.0 specification](https://github.com/ag-ui-protocol/ag-ui/blob/79530a25f3476d0abb93cb00761906fda757a2d5/docs/spec/1.0/index.mdx) at the SOURCE.json pin. Prefer its normative rules over older concept pages or search snippets. Install project-local SDK dependencies only when needed; this skill installs no SDK, agent server, provider or global connection. A scaffold's model calls require separate applicable account/spending authority.

## Contract and ownership

Describe the UI outcome, event/state shape, run ownership and allowed effects. Use existing specification/reliability methods when they add useful checks. For durable typed shared data and reviewable branches, consider typed-graph-workflows if installed; a UI event stream alone is not durable storage. Preserve the private vault and host-owned memory boundaries.

Follow the [processing rules](https://github.com/ag-ui-protocol/ag-ui/blob/79530a25f3476d0abb93cb00761906fda757a2d5/docs/spec/1.0/basic/processing.mdx), including unknown-field/type handling and strict known-field validation. Python Pydantic parsing allows coercion and extra fields; model parsing alone does not establish wire conformance. Validate opaque tool arguments and application state against their own contracts. Set application byte/event/time bounds; SDK budgets do not cover every opaque input.

Associate events with the current stream/run and check lifecycle IDs where defined. A replacement input must not let delayed events from the prior run overwrite current state. Snapshots replace state. Apply a JSON Patch delta atomically; a failed path/test leaves the previous state intact. Distinguish an unknown forward-compatible event from a malformed known event. See [state events](https://github.com/ag-ui-protocol/ag-ui/blob/79530a25f3476d0abb93cb00761906fda757a2d5/docs/spec/1.0/events/state.mdx).

## Decisions, interruption and failure

Under [1.0 interrupt/resume](https://github.com/ag-ui-protocol/ag-ui/blob/79530a25f3476d0abb93cb00761906fda757a2d5/docs/spec/1.0/basic/patterns/interrupt-resume.mdx), the consumer checks complete answers and expiry for pending interrupts before submission on the matching thread, allowing expired entries to be explicitly abandoned. The producer may be stateless; do not assume it durably remembers pending decisions or rejects every unknown resume ID. Application authorization must independently bind actor, thread, intent and revision before an effect. Reuse existing explicit user authority; transport payloads and a presented tool are not permission.

For [HTTP+SSE](https://github.com/ag-ui-protocol/ag-ui/blob/79530a25f3476d0abb93cb00761906fda757a2d5/docs/spec/1.0/basic/transports/http-sse.mdx), consume data fields and tolerate comments; do not use Last-Event-ID or assume a broken stream can be resumed. A rerun has a new runId with retained context. HTTP200 or an exhausted iterator without a terminal event is incomplete, not success. Distinguish terminal success, interruption, cancellation and RUN_ERROR. Reconcile uncertain effects before retrying; application checkpoints and idempotency must protect repeated actions.

Keep diagnostics redacted. Some SDK failure warnings include full state/patches; do not forward those to production logs. Render only intended user-facing progress/data, never infer that hidden model reasoning or private state should be exposed.

## Verify the application

Exercise a real producer/client boundary using the selected SDK: normal streaming, a changed input mid-run, stale events, an atomic bad delta followed by a fresh snapshot, incomplete/expired decisions, denied effects, duplicate completion and truncated transport. Inspect actual persisted effects and final UI state. Label SDK checks, application guards and untested transports separately. A model-free fixture proves its integration contract, not production auth, all SDK conformance or provider quality.
