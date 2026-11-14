# Skill exposure names

These are actual installed names, not numbered workflow categories. Select a method by its description, source and the current task. Each source remains one method; source paths, support files, receipts and notices retain their original coordinates.

| Source / previous exposure | Installed exposure |
|---|---|
| `frontend-design` | `web-ui-design` |
| `unslop` | `ui-polish` |
| `impeccable-audit` | `ui-quality-audit` |
| `impeccable-harden` | `ui-reliability` |
| `taste-skill` | `ui-art-direction` |
| `core` | `browser-cli-guide` |

Native Codex/OpenCode and Claude indexes expose the canonical `name`, original `source_name` and legacy `aliases`. The 01 metadata helper searches those fields. Aliases are lookup metadata; they do not add another installed skill or establish that a host accepts legacy `$name` or `/name` invocations. Use the installed exposure for invocation.

Actual CLI, tool, plugin and API identifiers remain unchanged. For example, `browser-cli-guide` is the host skill exposure, while the agent-browser CLI's `skills get core` still uses `core`. Source command labels do not become new host invocation APIs.

Both adapters accept canonical or legacy **base-skill** names with `--only`, for example `--only web-ui-design` or `--only frontend-design`. Existing addon flags remain unchanged: `--unslop` installs `ui-polish`; other accepted selection flags keep their spelling. `--only` still selects base skills, while addon flags add their reviewed methods.

The naming policy is sealed into native release identity, and Claude derives its release from that native identity. Updating a managed selection replaces its previous exposure rather than leaving active duplicate aliases. Claude retires only its owned old links; unowned collisions and changed managed entries remain conflicts to reconcile. Existing transaction backups and rollback preserve the previous generation. Source archives are not renamed or rewritten.
