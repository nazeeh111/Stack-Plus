# Restore the portable setup

GitHub stores the toolkit, source pins and portable recipes. Keep a verified private backup of notes, conversations, credentials, app permissions, runtime environments, container volumes and the original recovery journals.

## Roll back the portable installation

Run the rollback helper printed by the installer. For the default management state, run the following command.

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

The helper uses the private ownership journal and pinned release chain. It restores recorded changes and preserves unrelated later edits. A conflicting edit to an owned setting or a replaced parent directory needs reconciliation before retrying. Keep the backup after rollback. [Transaction ownership and recovery](TRANSACTIONS.md)

## Restore onto another Mac

Use a fresh checkout and Python 3.11 or newer. Rehearse the intended selection, then verify that the host discovers 01 and that the restored runtime can produce the project's required output. Existing registry installations can consult their saved profiles. The [historical complete profile](../profiles/complete-skills.json) recorded a 216-method selection distinct from the current on-demand library. [Onboarding](ONBOARDING.md) · [Registry commands](REGISTRY.md)

From the checkout, run the portable regression suite in a disposable environment.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

Restore project data with the tool version that wrote it. For example, Omnigraph format 17 requires a compatible build. Preserve the original graph when changing versions. For OpenCode, check the restored skill in a fresh project session. Use project-only idle refresh when active work would be interrupted by a service reload. [Omnigraph format and runtime](../addons/typed-graph-workflows/RUNTIME.md) · [OpenCode recovery](OPENCODE.md) · [Storage maintenance](storage.md)
