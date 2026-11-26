# Install nstack on a Mac

Use your existing Codex or OpenCode installation. From that host you can ask:

```text
Set up https://github.com/nazeeh111/nstack on this Mac using docs/ONBOARDING.md.
Show me the selected skill profile and rehearse it in a separate directory
before changing my current setup. Preserve my personal skills and settings, and
verify discovery in my chosen host.
```

You need Git, Python 3.11 or later, and access to the pinned public sources.
Run the commands below from a reviewed nstack checkout. Keep your existing
host, model, effort, personal instructions and projects. See
[everyday setup](EVERYDAY_SETUP.md) for optional tools and
[source fidelity](SOURCE_FIDELITY.md) for provenance and licenses.

## 1. Inspect the selection

```sh
python3 -m json.tool profiles/complete-skills.json
```

[The complete-skills profile](../profiles/complete-skills.json) records the
current portable selection of 216 methods: 170 base skills, 34 add-ons and
12 specialist skills. Inspecting the JSON reads the selection without fetching
source or changing profiles.

The profile selects skill instructions and support files. It does not enable
specialist runtimes, account connections, services or device permissions.
Review each selected runtime separately when a workflow needs it.

## 2. Try one skill in a separate home

Start with one design skill so the first rehearsal has a clear result. This
example uses the native installer's existing exact-name selector. It may
download pinned source. Run the entire block from the checkout in Bash or zsh.

```sh
(
  set -eu
  temp_root=$(cd -- "${TMPDIR:-/tmp}" && pwd -P)
  case "$temp_root" in /?*) ;; *) exit 1 ;; esac
  preview=$(mktemp -d "$temp_root/nstack-preview.XXXXXXXX")
  case "$preview" in "$temp_root"/nstack-preview.????????) ;; *) exit 1 ;; esac
  [ -d "$preview" ] && [ ! -L "$preview" ] || exit 1
  mkdir "$preview/home" "$preview/state"
  python3 native_setup.py install --only web-ui-design \
    --home "$preview/home" --codex-home "$preview/home/.codex" --state "$preview/state"
  python3 -m json.tool "$preview/state/native-profile.json"
)
```

Look for `web-ui-design` in the resulting profile. The installer also prints a
rollback path. The preview stays in its temporary directory for inspection.

## 3. Choose the permanent selection

For the same single-skill selection in a new shared root, run
`python3 native_setup.py install --only web-ui-design` when ready. The
default installation without `--only` selects all 170 base skills.

For a larger collection, use `python3 native_setup.py install --help` and
the [portable profile](../profiles/complete-skills.json) to review additions.
Supply selected add-on flags and repeated `--extra-skill NAME` pairs on the
same install command. Leave a group flag out to omit its whole group. Omit
`--academic-research` if the five academic skills’ CC BY-NC 4.0 license
is incompatible with your intended use. Omit an `--extra-skill NAME` pair
when you already maintain a separate user-owned copy outside the managed
collection. A replacement can remove an omitted managed copy. Rehearse the
exact selection with the three temporary target flags above before applying
it to your intended home.

Inventory existing shared and personal skills before replacing a collection.
Leave the saved profile's `--replace` argument out of a new installation.
An existing shared root requires deliberate reconciliation and a backup.
For custom Codex instructions, set `--codex-home /absolute/profile` or use
the host's existing `CODEX_HOME`; shared skills still go under the chosen home.

- **Codex.** Keep an existing compatible app or CLI. See the
  [optional CLI bootstrap](../README.md#install-on-a-mac) if you need a
  launcher. The pinned CLI bootstraps on Apple Silicon macOS.
- **OpenCode.** It discovers the same shared skill collection. Follow the
  [OpenCode V2 adapter guide](OPENCODE.md) if you want the adapter's shared
  instructions, launcher and reviewed configuration. It expects the default
  `~/.codex/AGENTS.md` and refuses conflicting configuration. Review the
  suggested configuration before applying it.

Keep the installer's reported rollback path. In a fresh ordinary session,
check that your host discovers the intended skills once each. For the single-skill example, look for
`web-ui-design`. To use [01](ADAPTIVE_ROUTING.md), include
`--adaptive-routing` when installing your larger collection. Then select it with `$01` in Codex or `@01` in OpenCode's skill
picker and try one
ordinary workflow that fits your task. See [workflows](WORKFLOWS.md) and verify
each needed runtime separately. An identical install should preserve owned
bytes and its original recovery journal. [Restore](RESTORE.md) explains what
must be backed up separately.

The [Claude Code adapter](CLAUDE.md) remains available for compatibility. It
uses its own documented selection flags and does not accept the full shared
profile as written. Codex and OpenCode are the current Mac workflows.
