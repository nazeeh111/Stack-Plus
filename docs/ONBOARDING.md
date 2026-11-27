# Install Stack+ on a Mac

Run these commands from the Stack+ checkout in Bash or zsh, using Git, Python 3.11 or newer, and an existing Codex or OpenCode installation. The portable default described here exposes one skill called 01. The 219 selected methods have their own discovery and activation scopes. [Browse selections](stackplus-selections.md)

<a name="1-rehearse-the-one-skill-selection"></a><a name="2-try-one-skill-in-a-separate-home"></a>

## Try the installation and its rollback

```sh
preview=$(mktemp -d)
preview=$(cd "$preview" && pwd -P)
python3 native_setup.py install --only 01 \
  --home "$preview/home" --codex-home "$preview/home/.codex" --state "$preview/state"
python3 -m json.tool "$preview/state/native-profile.json"
"$preview/state/rollback.sh"
```

The profile's `names` field should contain exactly `01`. Running the printed rollback helper restores this disposable home. To rehearse another selection, use a new preview directory and the exact flags you plan to apply.

<a name="3-choose-the-permanent-selection"></a>

## Use it in your project

For a new shared root, run `python3 native_setup.py install --only 01`. Keep the rollback path it prints. Codex and OpenCode can discover the same shared skill under `~/.agents/skills`. Start an ordinary chat in your project and explicitly pick `$01` in Codex or `@01` in OpenCode. Ask for the outcome. You can change the requirement in the same conversation or say “turn 01 off.” [OpenCode adapter and Codex harness](OPENCODE.md) · [Two-turn skill discovery exercise](../evals/01/late-method/README.md)

For an existing collection, inspect your shared and personal skill roots and retain a backup before replacing anything. Replacing a managed selection can retire omitted entries. Rehearse all additions you intend to retain together. The native installer accepts a custom `--codex-home` or the current `CODEX_HOME`. Keep project-specific skills and connectors in their owning project. [Selection and staging](stackplus-selections.md) · [Existing native profiles and optional bootstrap](REGISTRY.md) · [Recovery](RESTORE.md)
