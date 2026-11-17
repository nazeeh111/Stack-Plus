# Prepare and invoke the original engines

Retain this whole toolkit checkout. The launchers import the adjacent transport and `lib/docker_client.py`; copying one script is insufficient. Source archives, dependency artifacts and task data are explicit inputs. Preparation never silently resolves packages, chooses a provider or starts an experiment.

## Common prerequisites

Use an existing reviewed Codex0.169.0 client or the explicit private [client recipe](CODEX-CLIENT.json). Verify the actual client version; an older0.167 bootstrap does not satisfy this requirement. Keep normal ChatGPT subscription login on the host. The host client alone uses its normal authentication; no credential files or provider keys enter scientific containers.

The AIS host dispatcher also needs the pinned optional `websockets==17.4`
dependency used by its executor relay. Bind the run to a verified existing host
Python that contains it, and check the dispatcher import before any launch.
The nstack-wide test interpreter, engine dependency interpreter and Linux
scientific-image Python are separate prerequisites. A passing inert launch plan
does not establish that the host can import the live dispatcher. Do not silently
install packages into a global interpreter or reuse an unverified default.

Each run supplies a private owner-controlled context-reference JSON with `source` (the native rollout metadata path), `thread_id` and `expected_turn_id`. The dispatcher rereads only metadata records and validates the latest exact turn, builtin provider, model and effort before every request. Refresh the reference for a new host turn. Do not copy a transcript, select an assumed model, or use another chat's reference.

Prepare the pinned original source using the [source/runtime recipe](source-runtime/README.md). Its manifests record official owning URLs, exact commits, archive/member hashes and dependency closure. AIS preparation applies all11 reviewed file patches, saves originals/diffs and requires the recorded GNU Bash syntax-check prerequisite. The result is a readonly `SOURCE_STATE/source` tree. Shinka preparation preserves all101 resolved mandatory packages plus2 bootstrap wheels. No reduced provider dependency set is substituted.

```sh
python3 integrations/research/source-runtime/runtime.py prepare-source \
  --engine shinka --archive EXACT_SHINKA_ARCHIVE --state FRESH_SHINKA_SOURCE_STATE
python3 integrations/research/source-runtime/runtime.py prepare-shinka \
  --source-state SHINKA_SOURCE_STATE --artifacts EXACT_SHINKA_ARTIFACT_DIRECTORY \
  --python ABSOLUTE_REVIEWED_CPYTHON311 --state FRESH_SHINKA_DEPENDENCY_STATE
python3 integrations/research/source-runtime/runtime.py prepare-source \
  --engine ai-scientist --archive EXACT_AIS_ARCHIVE --state FRESH_AIS_SOURCE_STATE \
  --bash ABSOLUTE_REVIEWED_GNU_BASH
```

Uppercase arguments denote caller-supplied paths, not installed aliases. The recipes refuse missing or wrong artifacts. Original source-built ANTLR/bibtexparser wheel bytes are explicit prerequisites with documented build sources; they are not fabricated public wheel downloads. Keep installed dependencies in durable user-owned runtime directories, not temporary acquisition storage.

## ShinkaEvolve

The general entrypoint is `shinka.py plan|run`. It invokes the unchanged original `shinka.cli.run` with the task's `initial.<supported extension>` and `evaluate.py`. Standard original `evo`, `db` and `job` settings can be passed with repeated `--set NS.FIELD=VALUE`. Scientific settings, task messages, islands, archives and optional native meta/prompt passes remain upstream. The final authority settings select local execution, the native headless transport for all four LLM roles, the scoped evaluator wrapper, no embedding provider and no W&B upload. They take precedence over task YAML/user overrides. `headless/codex` is a transport identifier; actual model and effort come from the current native metadata.

Create a clean task view without `.env`. Use a fresh results path under its declared workspace, and a fresh private control path outside every model-readable/writable root. The original headless provider writes its prompt files under the task workspace as the trusted orchestrator. Keep `evaluate.py` outside model-writable roots. The trusted engine runs locally; the evaluator and candidate run under a separate native permission profile with network/Unix sockets disabled and only that job's output directory writable.

The managed transport manifest is a private JSON file:

```json
{
  "schema_version": 1,
  "context_reference": "/absolute/private/current-context.json",
  "workspace": "/absolute/task",
  "read_roots": ["/absolute/task", "/absolute/reviewed/runtime"],
  "write_roots": [],
  "deny_roots": ["/absolute/private/sealed"],
  "receipt_dir": "/absolute/private/receipts",
  "timeout_seconds": 600,
  "web_search": "disabled"
}
```

Roots must already exist, be canonical, and grant only required reviewed interpreter/dependency/task paths. The receipt directory must be private. This example is a schema illustration, not a permission grant for any existing directory.

```sh
python3 integrations/research/shinka.py plan \
  --source-state SHINKA_SOURCE_STATE --python SHINKA_DEPENDENCY_STATE/venv/bin/python \
  --codex ABSOLUTE_COMPATIBLE_CODEX --manifest PRIVATE_MANIFEST \
  --task-dir TASK --results-dir FRESH_RESULTS --state FRESH_PRIVATE_CONTROL \
  --num-generations 3 --eval-time 00:01:30 --set db.num_islands=2
```

`plan` validates source, current metadata, exact dependency versions and client version, then prints the original CLI argv and evaluator policy. It does not import/run the engine, evaluate candidates or invoke a model. Replace `plan` with `run` only for an authorized experiment. `run` records `LAUNCH.json`, per-job evaluator policies and native request receipts. The original evaluator imports candidate code in-process; separate isolation does not make its metric immune to gaming. Independently replay numerical/structural checks before making a scientific claim.

The accepted installation trial exercised the original runner for three generations and two native requests, with two baseline-to-candidate branches and zero actual migration transfers. The general CLI's additional verification is a no-model plan and contract tests, not another inference trial. Its first separately recorded evaluator invocation was denied by macOS `sandbox-exec` before Python executed (`Operation not permitted`). General CLI evaluator commissioning therefore remains blocked; preserve the native denial and seek a scoped supported remedy before running an experiment. Do not broaden filesystem access or switch to an uncontained route to make this probe pass. Preserve the distinction between the accepted earlier runner and this uncommissioned general entrypoint.

## AI Scientist v3

First prepare the exact CPU scientific image using [scientific-image/runtime.py](scientific-image/README.md), and the durable reviewed Linux Docker CLI using `controller_client.py` and [its pin](CONTROLLER-CLIENT.json). No global Docker/client configuration changes are needed. The controller gets the ordinary local Docker socket; agent/candidate/evaluator containers do not. The official host app-server handles model requests while all native tools run solely inside their verified role container. Its External sandbox policy delegates isolation to that explicitly verified Docker boundary.

The concrete entrypoint is:

```sh
python3 integrations/research/ai_scientist.py plan --launch REVIEWED_LAUNCH.json
python3 integrations/research/ai_scientist.py run --launch REVIEWED_LAUNCH.json \
  --inputs EXACT_TASK_INPUT_DIRECTORY --state FRESH_PRIVATE_RUN_STATE \
  --docker-host unix:///ABSOLUTE_LOCAL_DOCKER_SOCKET
```

The launch document is intentionally task-specific trusted configuration, not model output or a default safe template. It binds the adapted source tree, all transport files and driver hashes, immutable reviewed image ID, durable Linux CLI hash, unique owner/volume, actual UID/GID/socket group, exact task input hashes, role mounts, guard policy, native metadata reference and finite request/time limits. `load_plan` in `ai_scientist.py` is the executable validation contract; `native_dispatch.py` and `docker_guard.py` define the actual role and launch-policy fields. `plan` verifies these bindings without Docker or inference. Do not reuse an old owner's volume, permit mutable images/host binds, or infer authorization from a launch document's descriptive state.

### Report a retained attempt offline

```sh
python3 -B integrations/research/ai_scientist.py report --state EXPLICIT_OWNED_STATE
```

`report` reads the canonical private run directory's `RUN.json`, artifact status
receipt, native request receipts/turn journals and matching queue response status.
It does not load a launch plan, compare the historical driver with the current
driver hash, inspect accounts, invoke a model, query/start Docker or extract an
archive. It therefore works for retained attempts made by an older driver. It
prints a bounded structured summary, excluding prompts, command text/output,
configuration, account data and raw journals. Alias paths, non-private/unowned
receipts and malformed counters are refused. Retained state must remain stable
under its owner's control while reporting.

The producer's retained recovery-volume name is projected as a boolean presence
flag; the name is not printed and an absent field remains unknown. External and
embedded journals must agree on every recorded request and turn identity before
completion can be reported. Early unknown-turn states remain valid; completed
evidence requires an identified turn. Matching counters alone cannot establish
that two journals belong to the same turn.

Positive native counters or completed command/model-item projections establish
observed inference even when a conservative interruption journal still says
`unknown`. The report preserves both observations rather than rewriting that
journal. It selects one native cumulative snapshot per request; partial snapshots
stay labelled partial, and missing counters remain unknown. Cached input and
reasoning output are included components, not amounts to add to total tokens.
Completed native-turn evidence is distinguished from dispatch/pipeline success.
Final unobserved usage and billing remain unknown; missing upstream usage or a
displayed zero cost is not proof of zero work or a bill. Artifact/cleanup statuses
are separately labelled as retained receipt reports, not freshly verified daemon
or archive state. A failed inference turn does not itself mean cleanup failed.

`plan` and `run` still require their exact `--launch` document. A blank exception
message now falls back to its type, such as `TimeoutError`, and a retained run's
owning `RUN.json` path is included in CLI diagnostics when present. Reporting is
not a retry or authorization to resume a consumed attempt. Any new campaign still
needs a fresh reviewed concrete proposal and the user's authority; no timeout,
transport, scientific gate, inference setting or budget changes follow from this
offline operation.

The original pipeline argv must retain all six phases: task drafting, investigation, ablations, final evaluation, posthoc and paper; native `agent.model=null` and `agent.reasoning_effort=null`; container execution and network `none`; and the exact approved image. Generated `setup.py` is currently unsupported and refused before controller-side execution. Candidate runtime dependencies must be available in the reviewed offline image/wheelhouse. Browser-based Scholarly/Selenium on Linux ARM, provider-native illustration commands, cloud/GPU tasks and other uncommissioned dependencies are not silently enabled. Matplotlib/TikZ/native LaTeX and an original strategy genuinely requiring no concept figure remain supported paths, subject to the original paper checks.

Before a new launch, inspect its task and all aliases/copies: raw/final data belongs only in trusted/evaluator views. Actual namespace verification independently requires readonly empty final-data mounts and sealed evaluator masks, including copied reviewer `/task-source` trees. Only original task-design roles may author evaluator source. Setup must be genuinely absent. Keep original baseline/qualification/reset/candidate RPC/final-use accounting and claim/reference checks. Unknown human paper authors stay empty; required third-party notices and honest experiment/model lineage remain retained.

The driver records request attempted/sent/completed/uncertain state and actual reported usage. Native event receipts retain a privacy-preserving item projection, not full command/file-read traces. Explicit local original-method delivery is recorded through original/effective prompt hashes and method file hashes; assess actual workflow application from real artifacts and available evidence without claiming a file-read trace the receipt does not contain.

On completion or failure, the driver exports a bounded raw tar archive, verifies footer/member/content hashes without host extraction, and retains producer stderr. A failed export or cleanup is incomplete and nonzero; its owned volume remains for scoped recovery. Preserve failed attempts. `RUN.json` is written at completion, so its absence during a running request is not a zero-inference result. Full six-phase readiness requires actual scientific artifacts and paper validation, not source preparation, image checks, a method bundle or a transport smoke.
