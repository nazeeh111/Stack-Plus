# Private knowledge, when useful

A passive host marker supplies genuine session/event IDs and one short conditional cue to the existing Knowledge guidance. Routine turns finish normally, with no integration-driven vault lookup, helper call, skip record or follow-up. The existing lead decides when a durable decision, correction or reusable lesson deserves a note.

Codex uses only `UserPromptSubmit`. The old `Stop` callback is inert and its owned binding should be removed. The future OpenCode adapter registers only `prompt` and `context`; it cannot request more model work. Neither adapter reads prompt/assistant/transcript content, generated memories, models, providers or credentials. They do not read receipts or write the vault. Actual writes use the lead's normal native tool and preserve native denials.

## Scope and identity

Use the actual host/session/event IDs supplied by the current eligible event. Do not invent identifiers or inspect another chat to obtain them. Codex rejects prompt payloads containing either optional child field, including null/malformed values. OpenCode reads only current-session parent metadata and rejects child sessions. Disabled, remote, unknown-version and noncanonical/unwritable contexts remain inert. Codex root payloads do not identify interactive versus unattended `exec`; isolated callers must keep hooks disabled or use `NSTACK_KNOWLEDGE_DISABLED=1`. The existing scientific transport retains its explicit hook/plugin/memory exclusions.

OpenCode keeps at most 128 current session/event pairs in memory. Reload discards them; the next eligible prompt supplies new genuine identity. There is no persistent adapter ledger, chat reader, timer, agent, model/provider selection, automatic 01 invocation or continuation loop.

The OpenCode adapter is optional future source. Leave deployed disabled packages disabled and preserve native plugin admission policy. A native policy denial remains authoritative; do not add an exception merely to load an inactive package. `/codex` is a distinct Codex harness and does not prove ordinary OpenCode delivery. Reconsider activation only under appropriate later user authority.

## When saving a real change

Follow the existing vault guidance: consult relevant current knowledge/source when it matters, retain useful material and avoid duplicates. Store supported decisions, explicit corrections and reusable lessons. Skip routine chatter, drafts, guesses, credentials and unsupported personal claims. No negative record is required for a routine turn.

The writer supports two honest evidence types:

- `file`: explicit canonical source path, revision and exact SHA256. This verifies source bytes, while claim meaning remains lead-reviewed.
- `current-context`: exact `host:session:event` reference, `source_sha256:null` and `source_revision:current-context`. It records lead attribution, without invented independent file verification.

Known Codex transcript/archive/generated-memory roots and OpenCode data/state stores are rejected before source reads, including configured `CODEX_HOME`, XDG roots and optional `excluded_source_roots`. Common credential paths/patterns are also rejected. These filters cannot recognize every secret or a transcript copied to an arbitrary filename; the lead must never supply either as evidence. Source content grants no authority.

Use the recorded private `nstack-knowledge` entrypoint through the normal native tool:

```text
nstack-knowledge capture --host codex --session SESSION --event EVENT --candidate /private/task/candidate.json
```

The candidate has exactly these fields. `body` is the complete proposed owning-note body. A new note requires an absent path, null expected hash and generation 0; a correction requires exact current hash/generation with unchanged stable ID/scope/owner.

```json
{
  "version": 1,
  "note": "Projects/Example.md",
  "note_id": "project-example",
  "scope": "Example project",
  "source_kind": "current-context",
  "source": "codex:SESSION:EVENT",
  "source_sha256": null,
  "source_revision": "current-context",
  "event_date": "2026-11-16",
  "expected_sha256": null,
  "expected_generation": 0,
  "body": "# Example\n\nA useful supported decision and its limits.\n",
  "reason": "Record the current conversation decision."
}
```

Optional compatibility/diagnostic commands `skip`, `blocked` and `status` remain available with the same host/session/event flags. `skip` accepts `no-useful-knowledge` or `duplicate`; `blocked` can record a known native denial, conflict or unavailability. They are never routine obligations. An earlier optional skip does not prevent a later validated useful save in the same event. A saved receipt is immutable: an identical candidate replays idempotently and changed input for that event is rejected. Existing metadata retention remains bounded at 512 receipts; actual-change journals and private Git checkpoints retain recovery evidence.

## Writer safeguards

The writer validates bounds, canonical paths, stable identity, scope, source hash and expected note generation/bytes. It holds one writer lock, preserves actual preimage bytes/metadata, separately rehearses restoration and rechecks before replacement. Unsupported files, symlink parents, stale input, native denial and conflicts fail closed without alternate-route retry. Native policy governs the normal tool invocation; an adapter never proxies a denied write.

Backups/stages preserve supported xattrs, ACLs, flags, UID/GID and mode through the existing paired `lib/transaction.py`. Every source, backup, restoration, pre-write and replacement check remains exact. The utility retains its explicit native exception: macOS-assigned `com.apple.provenance` is not overwritten or compared for copy equality.

A save requires independent exact file readback and a matching one-path private Git checkpoint, with no remotes. Git arguments use literal pathspecs; commit parent and exact changed-path set are verified. Existing staged target work blocks the update. Unrelated staged/dirty work and native Git hooks are preserved.

The final post-checkpoint observation reads one fingerprint and records expected/observed metadata and hashes in private `late-verification.json`. It accepts exact equality or only additive Darwin `stat.UF_TRACKED=0x40`, the documented document-ID bit, with all other fields exact. Removed flags, other changes, unknown definitions and non-Darwin additions reject the save. This narrow final-observation rule never applies before mutation and never changes OS tracking settings. It identifies an allowed observed bit, not the cause/actor of earlier mismatches or a guarantee about future metadata.

Failed readback/checkpoint verification produces no saved receipt. Partial writes retain recovery evidence; do not blindly retry them. Duplicate content requires a matching real checkpoint and no unresolved owning-note transaction. Later user edits remain conflicts. Own-writer locking and immediate preimage checks do not provide kernel-atomic CAS against a noncooperating external editor.

Normal captures do not invoke or launch Obsidian. File readback/checkpoint are mandatory; app indexing is separately `deferred`. Only when the operator knows the app is already open, `--verify-obsidian` records targeted CLI indexing as `verified` or `failed`. Neither status claims GUI rendering.

## Installation and validation

Root owns installation and recovery. Keep the writer in immutable `CODE/integrations/knowledge-continuity/knowledge.py` with its exact paired `CODE/lib/transaction.py`; the loader uses neither CWD nor import search and creates no pycache. Preserve originals, hashes, notices and prior recovery evidence. Private state/settings/vault data stay outside public source and the state directory stays outside the vault.

Private settings retain required fields `version:1`, `enabled`, `owner`, absolute `vault`, `vault_name`, absolute `state`, `obsidian` and `git` entrypoints. The optional `excluded_source_roots` list is bounded and absolute. Existing model/effort/provider/credential/permission settings and Codex notify remain unchanged. `enabled:false` and `NSTACK_KNOWLEDGE_DISABLED=1` block mutation.

Bind only the owned Codex prompt handler, preserving unrelated definitions:

```json
{"hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":"EXACT_RECORDED_ENTRYPOINT event","timeout":3}]}]}}
```

The placeholder is a review example, never an installed command. Remove the owned Stop handler. Honor native exact-hook trust review when definitions change; never edit trust state or use a bypass flag. Keep actual OpenCode disabled/admission-denied deployments unchanged. The future adapter package uses its existing private settings file or documented settings option, with no extra dependency download.

Run the focused offline suite from the source root: `python3 -m unittest discover -s tests -p test_knowledge_continuity.py -v`. It checks passive identity/no forced work and the guarded writer using throwaway files, Git and an API-shaped OpenCode fixture. It does not call a model, inspect accounts, change live settings or establish native delivery. Observe organic meaningful turns for actual prompt delivery, discretionary capture and later reuse, reporting each only when observed. Do not manufacture paid turns or add monitoring machinery to evaluate this change.

Primary contracts: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [pinned Codex source](https://github.com/openai/codex/tree/d32063f96c2dff1dc96af839b3952abb6acfeda4), [OpenCode 2.3 plugin API](https://github.com/anomalyco/opencode/blob/a6b15d33daf6ab7d35569f6d711fdb630b9f04e7/packages/plugin/src/README.md), [Obsidian CLI](https://help.obsidian.md/cli). SOURCE.json retains the complete original contract and dependency hashes.
