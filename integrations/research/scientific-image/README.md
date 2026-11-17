# Scientific dependency image

Offline preparation for the original AI Scientist v3 dependency environment on **Linux arm64, CPython3.12.16, Debian13 trixie**. This is an on-demand prerequisite, not a research-engine launcher or an activated service.

The original reviewed image `sha256:29762e2a922f00169b2b95ffaa12238bbdced34036996efc52c9635aacc89b96` passed all115 Debian version checks, all12 mandatory imports, numerical/plot fixtures and the original ICLR template's four compiler passes. Its context hash was `024f7fe5a78147ab7bf55eb0aea7bfc72c80f91ea73acfb0bb915168308559bc`. This portable recipe keeps those exact package/native/installer inputs, replaces private diagnostic reports with public manifests, and retains missing ANTLR and bootstrap notices explicitly. Its context hash is separate; a rebuilt image can have a different image ID. The portable build has not been executed or accepted merely by packaging it.

## Commands

Use an absolute path to `runtime.py` in the retained nstack checkout. Moving the whole checkout preserves its shared `lib/docker_client.py` import. Python3.11+ and an ordinary non-root host account are required.

```sh
python3 /absolute/nstack/integrations/research/scientific-image/runtime.py prepare --artifacts /absolute/private/artifacts --state /absolute/private/fresh-state
python3 /absolute/nstack/integrations/research/scientific-image/runtime.py build --state /absolute/private/fresh-state
python3 /absolute/nstack/integrations/research/scientific-image/runtime.py check --state /absolute/private/fresh-state --image sha256:EXACT_IMAGE_ID
```

`prepare` only verifies and copies inert files into a fresh private directory. It refuses existing state, changed hashes and symlinks. It never downloads, resolves, installs, builds or calls Docker. Failed partial preparation is preserved. `build` is an explicit offline build, bounded to1200seconds. `check` performs bounded dependency fixtures. Both use the existing local Docker engine through the shared helper-free client with an empty private HOME/config. Optional `--docker-host unix:///absolute/local/socket` selects an existing local socket. Neither command starts Docker, pulls images, changes global settings or accesses accounts.

Build/check require the exact official base already available locally under the recorded tag, with its immutable image ID, official RepoDigest and original RootFS layers. The normal base Debian signature policy must verify the exact frozen InRelease and Packages index. An offline simulation must select all115 exact package versions with no removals. Verification containers are read-only, networkless, non-root, capability-free, constrained by time/CPU/memory/PIDs, and mount only task inputs/outputs. Cleanup only removes a container with its own unique ownership label. Failures retain logs and require diagnosis; no privilege, signature, dependency or hash bypass exists.

## Artifact inputs and limits

Caller-supplied artifacts use exactly the relative names and SHA256 values in `manifests/inputs.json`:

- `debs/`:115 signed-index Debian archives,102,482,700bytes.
- `wheelhouse/`:77 runtime wheels,129,187,043bytes, plus the two exact original bootstrap wheels.
- `runtime/bin/codex-exec-server` and `runtime/bin/codex-resources/bwrap`: the reviewed extracted official release members. `manifests/executor.json` records archive URLs, hashes and member names. The exact extracted hashes are in the input manifest.
- `metadata/InRelease` and `metadata/Packages.xz`: frozen official signed metadata. Their public URLs are mutable and may no longer serve these bytes; absence/expiry is a real prerequisite gap, never a reason to relax policy.

The manifest keeps every original mandatory dependency and platform marker. `source/{pyproject.toml,uv.lock,LICENSE}` is retained verbatim at the pinned upstream revision. Wheel and Debian manifests record versions, URLs, source hashes and notices; native wheel members have their own hashes/architecture inventory. This is a frozen reviewed selection, not a general cross-platform resolver. The previous image occupied1,328,641,644bytes; no GPU, Torch, provider SDK, full TeX distribution or browser was added.

Two pure-Python dependencies, ANTLR4.9.3 and bibtexparser1.4.4, were originally built from reviewed source archives. Their exact wheel hashes, upstream sdists and original build inputs/commands are retained. Those wheel bytes have no public wheel URL and are not published here. A new machine must supply the matching reviewed wheels, or separately review a source build and its resulting manifest generation. This entrypoint does not secretly build them, pretend an sdist is a wheel, download unpinned tooling or weaken hashes.

Selenium's mandatory wheel contains an x86_64 Linux manager on this aarch64 target. Browser/manager and scholarly network fallback are uncommissioned. Two reviewed Python startup hooks remain: setuptools' `distutils-precedence.pth` and Sphinx's namespace hook. Image-local `policy-rc.d` exit101 and truthful `container=docker` suppress service/init/sysctl side effects without modifying the host. LGPL/GPL and other upstream notices retain their original terms; this repository does not relicense dependencies or redistribute their binaries. Required corresponding source locations are recorded, including the pinned Codex source with its bundled bubblewrap source.

`check` tests exact Debian/Python versions, pip consistency, imports, NumPy/SciPy/Pandas/PyYAML native work, a Matplotlib/Pillow figure, actual TeX/Poppler tools and original source ICLR/BibTeX compilation with shell escape disabled. Original templates include placeholders and example branding. This proves a dependency prerequisite only. It does not validate a manuscript, scientific discovery, model call, engine phase, browser operation or full campaign. Whole-engine policy and activation belong to the separate research integration.
