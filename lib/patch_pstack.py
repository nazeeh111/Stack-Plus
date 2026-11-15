"""Native platform bindings for the complete selected pstack methods."""
import hashlib
import difflib
import json
import re

# text_port receives prose after the shared Claude Code -> native host binding.
# Guard the reviewed source, rather than silently patching a future method.
ADAPTER_SHA256 = 'cc2410d16baead66be39312fea96c172df7ce4fe2444add169467b898e9d48ad'
SOURCE_SHA256 = {
 'docs/harness/claude-code.md': 'c79e2283d3a83c6be3dd1cac33f9c074067c95e610ae6e0a16d9fdee84058927',
 'skills/architect/SKILL.md': 'dc74c4810a53a4ee25812278280f2580c00fb06408890e993be0623722a07aaa',
 'skills/arena/SKILL.md': 'a70df68e26420f783b09ac10b1ce6951b1438fa2233d5a0a5ad789720ba9c7b5',
 'skills/blast-radius/SKILL.md': '2e10745b97f5862323dcda3b29ca60d56b5c3c98e37020085d26b48efbe0a436',
 'skills/architect/references/runner-prompt.md': '21dd5314aab778c5007228027a4591d97693fbec6ab86524037772b63f40948e',
}
NATIVE_ADAPTER = '''# pstack in the active native host

Keep the complete selected pstack method. This file binds its source tool and
model names to the actual host; it does not install a controller or grant
authority. `<pstack>` is the folder containing `skills/` and `docs/`.

## Tools and worker scope

Use only tools and fields present in the current host schema. In Codex, when
available, use `collaboration.spawn_agent` for an owned worker task,
`collaboration.send_message` for clarification, `collaboration.followup_task`
to reuse a worker, and `collaboration.wait_agent` for its handoff. In OpenCode,
use its current native delegation interface after inspecting its schema. Do not
switch hosts to obtain a source tool. If delegation is unavailable, report the
missing independent-worker check and perform scoped sequential alternatives;
do not describe those as independent agents.

Read another pstack method from `<pstack>/skills/<name>/SKILL.md` and only the
support its operation needs. Source slash commands, `Task`, `Agent`, `Explore`,
`TodoWrite`, `AskUserQuestion` and named agent roles are not installed tools or
roles by implication. Use the current host's planning/input tools when available;
otherwise keep a concise task-local plan and ask in plain text only for material
missing information. Use current shell/file tools and `rg` for source inspection.

Pass each worker the actual inputs, owned output location, authority and checks.
Read-only work is an explicit brief and verified diff, not an invented tool flag.
Keep one writer per artifact; use an existing worktree or task-local directory
when isolation is needed. Do not create cloud agents or pair other applications.
Candidates produce only their assigned candidate, without launching arena,
delegating, implementing the chosen design or changing shared task state.

## Models, effort and judging

Inherit the user's current model and reasoning effort. In Codex omit `model`
and `reasoning_effort` overrides; other hosts use their supported inheritance.
Source runner defaults and family fallbacks do not authorize changing either.
Use a different model/provider only when explicitly authorized and actually
available within its existing budget. Never acquire providers, keys, credits or
subscriptions to fill a seat. Do not read or write retired Claude configuration,
role files, credential stores or transcripts. No source rule is auto-loaded by
this adapter, and setup-pstack configuration writes are not part of this port.

Retain independent candidates, rubric comparison, synthesis and verification.
A cross-family judge is available only when an authorized different-family
model is actually callable. If unavailable, report that limitation, skip that
judge and let the parent compare the candidates, as arena's fallback permits.
Do not label a same-model review as cross-family evidence. An explicitly
authorized alternative roster that fails must be reported, not silently replaced.

## Paths and unavailable features

Resolve bundled references relative to the actual skill folder. Keep outputs
and continuation records with the owning task; inspect only authorized current
source and artifacts. Never infer a current transcript or configuration path
from another host's conventions. The retained source path `claude-code.md` is
for closure compatibility, not a Claude runtime requirement.

Discover actual native capability before using any source-only feature. When
an operation is unavailable, report the missing operation and its effect on the
result; never fill a required output with a success-shaped placeholder. Commit,
push, publish, external messaging, new spending and credential changes require
their existing specific authority. A method invocation supplies none of them.
'''


def _line_binding(text, prefix, expected, replacement):
 lines = text.splitlines(keepends=True)
 matches = [i for i, line in enumerate(lines) if line.startswith(prefix)]
 if len(matches) != 1:
  raise ValueError('Pinned pstack binding anchor changed: ' + prefix)
 i = matches[0]
 original = lines[i].rstrip('\r\n')
 if hashlib.sha256(original.encode()).hexdigest() != expected:
  raise ValueError('Pinned pstack binding preimage changed: ' + prefix)
 lines[i] = replacement + lines[i][len(original):]
 return ''.join(lines)


def _delegation_bindings(text, file):
 path = file.as_posix()
 marker = '/harness/pstack/claude-code/'
 if marker not in path:
  return text
 relative = path.split(marker, 1)[1]
 if relative in SOURCE_SHA256:
  # The builder's copied file still contains the exact raw upstream bytes here.
  # Check those before applying this port, including untouched parts of a line.
  if hashlib.sha256(file.read_bytes()).hexdigest() != SOURCE_SHA256[relative]:
   raise ValueError('Pinned pstack source preimage changed: ' + relative)
 if relative == 'docs/harness/claude-code.md':
  if hashlib.sha256(text.encode()).hexdigest() != ADAPTER_SHA256:
   raise ValueError('Pinned pstack native adapter preimage changed')
  return NATIVE_ADAPTER
 bindings = {
  'skills/architect/SKILL.md': [
   ('Sketch types,', '3b2c15bc9be032fcb710f8e56d791d5ce7b13be75578bb26938776cf5450569d',
    'Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode. Synthesize independent design perspectives, then fill in code against the chosen sketch.'),
   ('Take the runners', '67769a2b1c21a18f45ff7c0559e3797db6f6544509e68cbb9f1fe82f4510d141',
    'Use independent candidate workers through the active native host, inheriting the user\'s current model and reasoning effort. Follow the native host adapter for actual tools, authorized alternatives and unavailable judging; do not load source model-rule files or adopt default provider slugs.'),
  ],
  'skills/arena/SKILL.md': [
   ('3. Pick the runners.', '7c111459a716e0a28446ba44aababff89f6e918100f70ba5905771e398226786',
    '3. Pick independent candidate workers for the distinct design directions. Use the active host\'s native delegation interface and inherit the user\'s current model and reasoning effort. Keep the selected method\'s required candidate count. A different model or provider requires explicit existing authority and actual availability; report a rejected authorized roster instead of substituting a model. Follow the native host adapter when independent workers are unavailable.'),
   ('Spawn all N subagents', 'ea996dc046fdacb73a4ff314ef0cdf0067d6716526d504b6dcf29051c4fa4345',
    'Launch the independent candidate tasks through the actual native delegation interface, using only supported fields. Give each worker the task, shared grounding path, owned output path and instructions to produce only its candidate artifact and a short rationale naming considered alternatives and rejections. Candidates do not launch arena or delegate further.'),
   ('After all Phase B', '58640ec1e89341baeac03f8033aafc6501350000d15adc43715ef1234d66082f',
    'After all Phase B candidates finish writing, use one read-only cross-family judge only if an explicitly authorized different-family model is actually callable. Preserve the user\'s selected model and effort otherwise. If that judge is unavailable, report the missing cross-family check, skip it and let the parent pick the base in Phase D. Do not replace it with an undisclosed same-family judge or acquire another provider. The judge sees the rubric and candidates by path label, scores each criterion and recommends a base with rationale; it may run while the parent reads in Phase D.'),
  ],
  'skills/architect/references/runner-prompt.md': [
   ('You are producing one candidate', '5b1780c159df359aef144b036eab5f401a0c0a952e152f519cf6d94b50f815a1',
    'You are producing one candidate design in architect\'s parallel exploration. Read the **architect** skill for design context only; the parent owns its workflow. Do not launch arena, delegate, implement the selected design or update shared task state. Output only your assigned candidate design package: type sketch, function signatures, module map and prose rationale shaped per [`rationale-template.md`](rationale-template.md).'),
   ('You are one of the parallel runners', '717dd727654c241d582ed1be20b2713c07b9a03c69e1780b542b9f28023a29e0',
    'You are one independent candidate worker, inheriting the selected model and reasoning effort unless the user explicitly authorized an alternative. Produce your strongest scoped design. Differences between candidates are the signal the parent uses to pick a base and graft. Converging on a safe-looking middle defeats the exploration.'),
  ],
  'skills/blast-radius/SKILL.md': [
   ('6. For a big or wide change,', '4b1d3738904eacd60839cd05810f1e50df4f613ae5322682cb19ba5de03f2ff0',
    '6. For a big or wide change, run it as an `arena`. Ask independent candidate workers the same question and merge their evidence. Inherit the user\'s selected model and effort; follow arena\'s native binding and report unavailable cross-family judging.'),
  ],
 }
 for prefix, expected, replacement in bindings.get(relative, []):
  text = _line_binding(text, prefix, expected, replacement)
 return text

def entry_policy(text):
 """Expose the six selected conditional methods to native skill selection."""
 header, body = text.split('\n---\n', 1)
 if len(re.findall(r'(?m)^disable-model-invocation: true$', header)) != 1:
  raise ValueError('Pinned pstack invocation policy changed')
 header = re.sub(r'(?m)^disable-model-invocation: true\n?', '', header).rstrip('\n')
 return header+'\n---\n'+body

def text_port(text,file):
 text = _delegation_bindings(text, file)
 text=text.replace("<skill dir>/scripts/statechart SPEC.tla", 'node "<skill dir>/scripts/statechart.ts" SPEC.tla')
 text=text.replace('The first run installs TLC and Java with mise and needs the network.', 'Use existing compatible Node and Java11+. Set JAVA to the actual Java executable and TLA2TOOLS to the locally verified TLC1.7.4 jar (SHA256936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88). No automatic dependency bootstrap occurs. Inspect custom view code before execution; bound model size and run time.')
 text=text.replace('Render charts with Pele. When the user asks for an image, or a chart is too large to read as text, follow `references/render.md`. Do not use a different renderer unless the user asks for it.', 'Render Mermaid with the existing native viewer or selected diagram export capability. Follow `references/render.md` for mark semantics and source-preserving export; no global renderer installation is required.')
 if file.name=='render.md':
  text=re.sub(r'(?s)Render each.*?(?=## Colors)', 'Keep the actual Mermaid source and use the existing native Mermaid viewer or selected diagram exporter when an SVG/image is needed. Verify labels, bug paths and marks in the exported artifact. A renderer failure does not negate the model result; return source and error. No global Pele install or browser bootstrap is required.\n\n',text,count=1)
  text=text.replace('Pele ignores Mermaid `theme` and `themeVariables`.', 'Historical Pele-specific styles below are reference examples, not a required renderer. Native Mermaid uses its own theme support.')
 text=text.replace('If you cannot stop it, interleave the sides so both see the same noise, and say so in the report.', 'Do not stop unrelated processes; interleave the comparisons under similar load or defer them, and record the confound.')
 text=text.replace('`nproc`','`sysctl -n hw.logicalcpu` on macOS (`nproc` on Linux)')
 text=re.sub(r'(?m)^.*if you cannot stop.*$', 'Do not stop unrelated processes. Record contention and rerun at a suitable time or report the confound.',text)
 return text

def helpers(root, source=None):
 if source is not None:
  base = 'harness/pstack/claude-code/'
  changes, patch = {}, []
  for relative, expected in SOURCE_SHA256.items():
   active = root / base / relative
   if not active.is_file():
    continue
   original = (source / base / relative).read_bytes()
   if hashlib.sha256(original).hexdigest() != expected:
    raise ValueError('Pinned pstack archival preimage changed: ' + relative)
   rendered = active.read_bytes()
   if rendered == original:
    continue
   archive_relative = 'PSTACK-PORT-originals/' + base + relative + '.original'
   archive = root.parent / archive_relative
   if archive.exists():
    raise ValueError('Pstack archive collision: ' + relative)
   archive.parent.mkdir(parents=True, exist_ok=True)
   archive.write_bytes(original)
   changes[base + relative] = {'before_sha256': expected,
                               'after_sha256': hashlib.sha256(rendered).hexdigest(),
                               'original': archive_relative}
   patch.extend(difflib.unified_diff(original.decode().splitlines(keepends=True),
                                     rendered.decode().splitlines(keepends=True),
                                     fromfile='upstream/' + base + relative,
                                     tofile='source/' + base + relative))
  if changes:
   for filename, data in (
     ('PSTACK-PORT.patch', ''.join(patch)),
     ('PSTACK-PORT.json', json.dumps({'source_revision': 'bb68f2365eceafa0cb2d253112f675acf5f144cc',
                                    'scope': 'Native architecture/arena delegation binding; originals are inert archival data.',
                                    'files': changes}, sort_keys=True, indent=2) + '\n')):
    target = root.parent / filename
    if target.exists():
     raise ValueError('Pstack provenance collision: ' + filename)
    target.write_text(data)
 for p in root.rglob('scripts/run.ts'):
  t=p.read_text();a=t.index('  const mise =',t.index('async function findTlc'));b=t.index('\n}\n',a)
  t=t[:a]+'''  throw new Error("Set TLA2TOOLS to the verified TLC1.7.4 jar and JAVA to existing Java11+; automatic installs are disabled");'''+t[b:]
  p.write_text(t)
