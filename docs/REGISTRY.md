# Registry and runtime commands

Use this reference when maintaining a registry-based installation or provisioning a specific runtime. For the single native 01 selection, start with [Mac onboarding](ONBOARDING.md). Commands below run from the checkout. An installed management profile also provides `nstack`.

## Inspect a route

```sh
./stack+ search web-ui-design --brief
./stack+ show L010
./stack+ route L010
```

The first two commands identify the selected source and revision. The route lists the prerequisites, activation steps and acceptance check. For a worked local lookup with recorded outputs, follow the [keyboard and mobile layout example](presentation/ui-audit.md). For skills that live in the project or on the shelf, use [selection and support-file discovery](stackplus-selections.md). New searches reflect the current selected inputs.

## Use an existing installation profile

`python3 native_setup.py install --help` lists exact-name, optional group and specialist selections. Specify all intended additions in one native transaction. The [historical complete-skills profile](../profiles/complete-skills.json) records a different setup from a single 01 installation. The management command binds its installing Python interpreter and uses the captured Node directory as a fallback when available. Retain the interpreter or reinstall after moving it. Private management state defaults to `~/Library/Application Support/nstack/`. Use `NSTACK_STATE` for a separate deployment.

The optional pinned CLI bootstrap targets native Apple Silicon macOS. Run its staging command to inspect the result.

```sh
python3 install.py install --stage-only --bootstrap-cli
```

The older CLI cutover can move the old user skill collection into private recovery storage with `--retire-personal`. Reconcile hooks, profiles, jobs and existing user-managed entries before that deliberate replacement. An existing compatible CLI or Desktop application can be kept. [Source fidelity](SOURCE_FIDELITY.md) · [Transactions](TRANSACTIONS.md) · [Recovery](RESTORE.md)

## Use a runtime in a project

For a small end-to-end test, decode a synthetic job posting with the pinned standard-library helper. It accepts a file inside the calling project. Run this block from the Stack+ checkout. Both the fixture and the runtime registry are disposable.

```sh
(
  set -eu
  cli="$PWD/stack+"
  scratch=$(mktemp -d "${TMPDIR:-/tmp}/stackplus.XXXXXXXX")
  scratch=$(cd "$scratch" && pwd -P)
  export NSTACK_STATE="$scratch/registry"
  mkdir "$scratch/project"
  cd "$scratch/project"
  printf '%s\n' '<h1>Junior engineer</h1><p>Build exhibits.</p>' > posting.html
  "$cli" route P355
  "$cli" commission P355 posting
  "$cli" check P355 posting
  "$cli" run P355 posting -- posting.html
  "$cli" remove-runtime P355 posting
)
```

The result includes the cleaned posting text and the input's SHA-256 digest. Removal sends the owned environment into recovery storage. For a numerical example with a known 0.8-second decay, follow the [room-decay recipe](../examples/clap/README.md). That recipe acquires a larger source tree and a locked scientific environment.

Source-built routes may instead use `./stack+ workspace ID /absolute/project` and `./stack+ retire-workspace ID /absolute/project`. Follow the recorded working directory and project prerequisites. Application, account, device, GPU and service access are verified in the project that uses them. [On-demand workflows](WORKFLOWS.md)

`./stack+ inventory /absolute/project --plugins` reads native skill, local MCP and plugin metadata. A working connector requires an actual operation under the host's current grants. [Native integration reference](EVERYDAY_SETUP.md) · [OpenCode and alternative harnesses](HARNESSES.md)

## Recover a project record

A registry project can retain an evidence-backed claim with `./stack+ knowledge set /absolute/project NAME --claim TEXT --source FILE`. Use `./stack+ knowledge read /absolute/project NAME` to retrieve its generation. Corrections and deletions take `--expected-generation N` to detect intervening edits. The separate [private knowledge writer](../integrations/knowledge-continuity/README.md) keeps durable vault decisions with their evidence.

Toolkit code uses [MIT](../LICENSE). Publisher material keeps its own terms and notices. [Third-party notices](../THIRD_PARTY_NOTICES.md)
