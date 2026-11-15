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
| `codex-skill` | `cli-anything-harnesses` |
| `composition-patterns` | `react-composition-patterns` |
| `fp-check` | `security-finding-verification` |
| `differential-review` | `security-change-review` |
| `media-use` | `hyperframes-media` |
| `product-marketing` | `product-marketing-context` |
| `launch` | `product-launch-strategy` |
| `emails` | `email-sequences` |
| `interview-script` | `customer-interview-script` |
| `synthesize-research` | `user-research-synthesis` |
| `cloudflare-security-audit` | `code-security-review` |
| `finance-audit-xls` | `spreadsheet-formula-audit` |

Native Codex/OpenCode and Claude indexes expose the canonical `name`, original `source_name` and legacy `aliases`. The 01 metadata helper searches those fields. Aliases are lookup metadata; they do not add another installed skill or establish that a host accepts legacy `$name` or `/name` invocations. Use the installed exposure for invocation.

Actual CLI, tool, plugin and API identifiers remain unchanged. For example, `browser-cli-guide` is the host skill exposure, while the agent-browser CLI's `skills get core` still uses `core`. Source command labels do not become new host invocation APIs.

Both adapters accept canonical or legacy **base-skill** names with `--only`, for example `--only web-ui-design` or `--only frontend-design`. Existing addon flags remain unchanged: `--unslop` installs `ui-polish`, and `--cloudflare-security-audit` installs `code-security-review`; other accepted selection flags keep their spelling. `--only` still selects base skills, while addon flags add their reviewed methods.

The naming policy is sealed into native release identity, and Claude derives its release from that native identity. Updating a managed selection replaces its previous exposure rather than leaving active duplicate aliases. Claude retires only its owned old links; unowned collisions and changed managed entries remain conflicts to reconcile. Existing transaction backups and rollback preserve the previous generation. Source archives are not renamed or rewritten.

Reviewed host invocations in a closed set of operative Markdown files also use the current exposure names. Changed pre-exposure bytes remain under `EXPOSURE-ORIGINALS` with `.original` filenames, and `EXPOSURE-PORT.json` records before/after hashes and the exact replacements. These originals add no skill entrypoints. Source receipts remain provenance for their original generation; the native manifest seals the adapted bundle. CLI-installed catalogs, actual commands, source/data paths and licenses remain literal. The adapted Unslop README labels its usage examples as nstack invocations while preserving its original installation paths and archived bytes.

The established `gstack-office-hours` and `gstack-plan-eng-review` names stay. Their two exposure descriptions clarify product/startup diagnosis or builder design partnership, and engineering-plan review respectively. These metadata-only changes retain the complete method bodies and the same preimage/receipt trail; they do not modify the upstream builders or rewrite other descriptions.
