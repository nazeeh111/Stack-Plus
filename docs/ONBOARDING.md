# Install Stack+ on a Mac

Use a reviewed checkout of [Stack+](https://github.com/nazeeh111/Stack-Plus), Python 3.11 or newer and your existing Codex or OpenCode host. You can use `./stack+ selections`, `./stack+ find` and `./stack+ review` from that checkout. Each specialist’s scope and source are listed in the [portable selection catalog](stackplus-selections.md).

## 1. Rehearse the one-skill selection

```sh
preview=$(mktemp -d)
python3 native_setup.py install --only 01 \
  --home "$preview/home" --codex-home "$preview/home/.codex" --state "$preview/state"
python3 -m json.tool "$preview/state/native-profile.json"
```

Confirm the profile’s single selected skill is `01`. To use that selection in a new shared root, run `python3 native_setup.py install --only 01`, then inspect the normal skill picker in your project. Existing shared collections require deliberate reconciliation. Keep the rollback path printed by the installer. Select `$01` in Codex or `@01` from OpenCode’s skill picker. Project-specific evidence and packet files stay in the project.

The following sections describe the historical registry installers for people choosing a different collection. Additions keep their individual source, license, tooling requirements and activation policy. [Source fidelity](SOURCE_FIDELITY.md)

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

For this alternative design-skill example in a new shared root, run
`python3 native_setup.py install --only web-ui-design` when ready. The
default installation without `--only` selects all 170 base skills.

For a larger collection, use `python3 native_setup.py install --help` to inspect available additions. Existing profiles can continue using their recorded selections.
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
