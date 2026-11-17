# Research source and native dependencies

Prepare the exact upstream source of ShinkaEvolve and AI Scientist v3 from **caller-supplied reviewed git-archive bytes**. This creates fresh, private, read-only source generations. It never clones, downloads, starts an engine, configures an account or invokes a model.

## Source preparation

Run through an absolute path in the retained nstack checkout:

```sh
python3 /absolute/nstack/integrations/research/source-runtime/runtime.py prepare-source --engine shinka --archive /absolute/private/shinka.tar --state /absolute/private/fresh-shinka-source
python3 /absolute/nstack/integrations/research/source-runtime/runtime.py prepare-source --engine ai-scientist --archive /absolute/private/ai-scientist.tar --state /absolute/private/fresh-ais-source --bash /absolute/reviewed/gnu-bash
python3 /absolute/nstack/integrations/research/source-runtime/runtime.py verify-source --state /absolute/private/fresh-ais-source --engine ai-scientist
```

Python3.11+ is required for this preparation helper. Source archives must match the exact archive SHA256, size, member list, file bytes and Git modes in `manifests/{shinka,ai-scientist}.json`. Both original sources contain no symlinks or submodules. Absolute/traversing/duplicate paths, links, devices and unexpected files are rejected. No archive extraction hook or target code executes. Archives can be created from reviewed existing checkouts using the exact inert `git archive --format=tar` commands in those manifests. A GitHub-generated archive can differ from these bytes and is not silently accepted.

The source revisions are:

- ShinkaEvolve `7ab55d7254d2732b26d9c30dde23ab777de631cb`, Apache-2.0,361 original files.
- AI Scientist v3 `df8313889a004f8a44a472e19a833cd547bb828a`, Apache-2.0,575 original files.

AI Scientist source preparation calls the existing sibling `codex-transport/apply_engine_patches.py`. Its exact helper, 11-file patch manifest and diffs are hash-checked before use. Each source preimage and patch result is checked. Original files, diffs and a patch receipt remain in the fresh state's `patch-originals/`; `original.tar` retains the full original source. The explicit supplied GNU Bash5.3.20 must have the previously reviewed binary SHA recorded in `manifests/patch-support.json`; it performs syntax-only `-n` validation with an empty environment. No fallback to another shell, new Bash acquisition or source execution occurs. A different host prerequisite requires separate review.

Prepared code is under `STATE/source`, with files0444 or0555 and directories0555. `verify-source` checks exact file/directory sets, hashes, permissions, owner, source revision, preserved archive, patch originals and preparation generation. Read-only permissions prevent accidental writes; the owner can still change them, so verification remains required. Existing state is never overwritten. A failed partial generation stays available for diagnosis and is not called ready. The whole checkout must be retained because AI Scientist's reviewed patch support is a sibling integration.

## Shinka native dependency preparation

The optional explicit command below prepares an isolated venv from already reviewed inert wheel files. It is **only** for Darwin arm64, CPython3.11. Supply an existing reviewed interpreter explicitly; there is no interpreter installation or PATH fallback.

```sh
python3 /absolute/nstack/integrations/research/source-runtime/runtime.py prepare-shinka --source-state /absolute/private/fresh-shinka-source --artifacts /absolute/private/shinka-artifacts --python /absolute/reviewed/python3.11 --state /absolute/private/fresh-shinka-dependencies
```

`manifests/shinka-dependencies.json` records the exact original artifact layout:100 wheels in `wheels/`, the original pure-Python ANTLR4.9.3 wheel in `built/`, and two original bootstrap wheels in `build-tools/`. All filenames, sizes, SHA256 values, wheel metadata, license notices and reviewed startup/native inventories are retained. `runtime-exact.lock` selects those101 resolved dependencies with one exact wheel hash each; `bootstrap-exact.lock` selects the original setuptools80.9.0 and wheel0.45.1. The source's26 mandatory roots remain intact, including original provider SDKs. No extra optional dependency group is enabled.

The two original multi-hash locks are retained with **comments removed only**, to keep machine-private acquisition paths out of public files. Requirement entries, hashes and markers remain unchanged. The upstream source contains the authoritative pyproject; its bytes are part of the archive/file manifest. The pure-Python ANTLR wheel has no public wheel URL; its reviewed source archive/hash is retained as provenance. A new machine must supply matching reviewed wheel bytes or separately review a source build and its resulting manifest. This helper does not build source distributions or replace hashes to get past a failure.

The command uses the existing macOS `sandbox-exec` route with network and account/config/keychain reads denied, an empty private HOME/environment, original venv tooling, pip isolated/no-index/no-deps/only-binary/hash verification, then pip consistency and exact installed-version checks. It never imports an engine or provider client, reads auth stores, inherits provider secrets or edits global installation/configuration. Dependency processes are time bounded and failures retain logs. If native controls deny preparation, it stops without an uncontained fallback.

The resulting Python is `DEPENDENCY_STATE/venv/bin/python`. Original source remains a **PYTHONPATH binding** for the separate reviewed engine launcher; no editable install, source build or extra wrapper changes the orchestration. Use the owning transport and launcher to establish actual model/effort inheritance and task isolation. Dependency preparation alone is not model, engine or research acceptance.

AI Scientist uses the separate `../scientific-image/` Linux dependency prerequisite. A second Mac AI Scientist venv is deliberately not prepared here. Full engine execution, source mounts, model metadata and launch authority remain with the research integration.
