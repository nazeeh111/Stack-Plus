"""Native platform bindings for the complete selected pstack methods."""
import hashlib
import difflib
import json
import re
import shutil

# text_port receives prose after the shared Claude Code -> native host binding.
# Guard the reviewed source, rather than silently patching a future method.
ADAPTER_SHA256 = 'cc2410d16baead66be39312fea96c172df7ce4fe2444add169467b898e9d48ad'
SOURCE_SHA256 = {
 'skills/show-me-your-work/SKILL.md': '4936325425064cbbbd1e82a7813cef5593ed8a273671d43ac5b1360de93f880a',
 'skills/why/references/synthesizer-prompt.md': '11c62671aa7b7a6e3d36929ffe2b59bf95e6ca664eee4d93e6ee527dd3390ddb',
 'skills/why/SKILL.md': '09405adc5afda90841f16318e471f25329d17da908956d79973edb34cdccb188',
 'skills/how/SKILL.md': 'f2aad836aa83cac7385e734ab888d573e1736def5b061aa8a72b1717f085606c',
 'docs/harness/claude-code.md': 'c79e2283d3a83c6be3dd1cac33f9c074067c95e610ae6e0a16d9fdee84058927',
 'skills/architect/SKILL.md': 'dc74c4810a53a4ee25812278280f2580c00fb06408890e993be0623722a07aaa',
 'skills/arena/SKILL.md': 'a70df68e26420f783b09ac10b1ce6951b1438fa2233d5a0a5ad789720ba9c7b5',
 'skills/blast-radius/SKILL.md': '2e10745b97f5862323dcda3b29ca60d56b5c3c98e37020085d26b48efbe0a436',
 'skills/architect/references/runner-prompt.md': '21dd5314aab778c5007228027a4591d97693fbec6ab86524037772b63f40948e',
}

# Exact correctness/diagnostic backports from cursor/plugins. Keep model defaults,
# workflow changes and dependency bootstrap outside this source delta.
STATECHART_BACKPORT_REVISION = 'bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7'
STATECHART_BACKPORTS = {'run.ts': {'before_sha256': 'f330e0a3b0a9f8181c2e52252c4a47db3f0a64f79a7cca5490263e33a5f13c72',
            'after_sha256': '751d97cfde3c241bfeed8913fc74a7a7cbc6acd3829e37a441016af3eb78f0e0',
            'edits': [(70,
                       70,
                       '',
                       'const SANY_ERRORS = /^\\*\\*\\* ?(?:Errors|Abort messages|Parse '
                       'Error)/m;\n'),
                      (229,
                       229,
                       '',
                       'const firstLines = (text: string) => {\n'
                       '  const lines = text.trim().split("\\n");\n'
                       '  if (lines.length > 40) lines.splice(40, Infinity, `... ${lines.length - '
                       '40} more lines`);\n'
                       '  return lines.join("\\n");\n'
                       '};\n'
                       '\n'),
                      (240,
                       243,
                       '  const lines = [...plainText(errors)].join("").trim().split("\\n");\n'
                       '  if (lines.length > 40) lines.splice(40, Infinity, `... ${lines.length - '
                       '40} more lines`);\n'
                       '  return { status: r.status, message: lines.join("\\n") };\n',
                       '  return { status: r.status, message: '
                       'firstLines([...plainText(errors)].join("")) };\n'
                       '};\n'
                       '\n'
                       'const sanyErrors = (r: FileResult) => {\n'
                       '  if (r.error) return undefined;\n'
                       '  const text = [...plainText(messagesOf(r.output))].join("");\n'
                       '  const at = text.search(SANY_ERRORS);\n'
                       '  return at === -1 ? undefined : firstLines(text.slice(at));\n'),
                      (307,
                       309,
                       '    if (xml.status !== 0)\n'
                       '      throw new Error(`SANY could not read ${specFile} (exit '
                       '${xml.status}):\\n${tail(xml)}`);\n',
                       '    if (xml.status !== 0) {\n'
                       '      const errors = xml.error\n'
                       '        ? undefined\n'
                       '        : sanyErrors(\n'
                       '            await runJava(\n'
                       '              "sany-errors",\n'
                       '              "tla2sany.SANY",\n'
                       '              [path.resolve(specFile)],\n'
                       '              ["-XX:TieredStopAtLevel=1"],\n'
                       '            ),\n'
                       '          );\n'
                       '      throw new Error(\n'
                       '        `SANY could not read ${specFile} (exit ${xml.status}):\\n${errors '
                       '?? tail(xml)}`,\n'
                       '      );\n'
                       '    }\n')]},
 'backends/mermaid.ts': {'before_sha256': '75704b2704a9399a39479ff704a580d5b9a1d0fede01fe771df28bf799b434b6',
                         'after_sha256': 'ce293d34ce3928d93329bd6d1a889d5722620008dae4339add79ef226c3f9b88',
                         'edits': [(95,
                                    95,
                                    '',
                                    'type Edge = { from: string[]; start: boolean; to: string[]; '
                                    'label: string | undefined };\n'
                                    '\n'
                                    'const within = (parent: string[], path: string[]) =>\n'
                                    '  path.length >= parent.length && parent.every((p, i) => '
                                    'path[i] === p);\n'
                                    'const wayIn = (e: Edge) => tupleKey([e.start, e.from]);\n'
                                    '\n'
                                    'export function drawnEdges(r: Region): Edge[] {\n'
                                    '  let out: Edge[] = [];\n'
                                    '  for (const s of r.states)\n'
                                    '    if (s.start) out.push({ from: [], start: true, to: '
                                    's.path, label: undefined });\n'
                                    '  for (const s of r.steps)\n'
                                    '    out.push({\n'
                                    '      from: s.from,\n'
                                    '      start: false,\n'
                                    '      to: s.to,\n'
                                    '      label: s.label + (s.when ? ` [${s.when}]` : ""),\n'
                                    '    });\n'
                                    '  const parents = new Map<string, string[]>();\n'
                                    '  for (const s of r.states)\n'
                                    '    for (let i = 1; i < s.path.length; i++) {\n'
                                    '      const prefix = s.path.slice(0, i);\n'
                                    '      parents.set(tupleKey(prefix), prefix);\n'
                                    '    }\n'
                                    '  for (const parent of [...parents.values()].sort((a, b) => '
                                    'a.length - b.length)) {\n'
                                    '    const into = out.filter(\n'
                                    '      (e) => e.to.length > parent.length && within(parent, '
                                    'e.to) && !within(parent, e.from),\n'
                                    '    );\n'
                                    '    if (!into.length || into.some((e) => wayIn(e) !== '
                                    'wayIn(into[0]))) continue;\n'
                                    '    const one = into.length === 1;\n'
                                    '    const at = out.indexOf(into[0]);\n'
                                    '    out = out.filter((e) => !into.includes(e));\n'
                                    '    out.splice(\n'
                                    '      at,\n'
                                    '      0,\n'
                                    '      { ...into[0], to: parent, label: one ? into[0].label : '
                                    'undefined },\n'
                                    '      ...into.map((e) => ({\n'
                                    '        from: parent,\n'
                                    '        start: true,\n'
                                    '        to: e.to,\n'
                                    '        label: one ? undefined : e.label,\n'
                                    '      })),\n'
                                    '    );\n'
                                    '  }\n'
                                    '  return out;\n'
                                    '}\n'
                                    '\n'),
                                   (123,
                                    123,
                                    '',
                                    '    const drawn = drawnEdges(r);\n'
                                    '    const line = (e: Edge, indent: string) =>\n'
                                    '      `${indent}${e.start ? "[*]" : idOf(e.from)} --> '
                                    '${idOf(e.to)}${e.label === undefined ? "" : `: '
                                    '${esc(e.label)}`}`;\n'),
                                   (136,
                                    136,
                                    '',
                                    '          const key = tupleKey(path);\n'
                                    '          for (const e of drawn)\n'
                                    '            if (e.start && tupleKey(e.from) === key) '
                                    'out.push(line(e, `${indent}  `));\n'),
                                   (155,
                                    160,
                                    '    for (const s of r.states) if (s.start) out.push(`  [*] '
                                    '--> ${idOf(s.path)}`);\n'
                                    '    for (const s of r.steps)\n'
                                    '      out.push(\n'
                                    '        `  ${idOf(s.from)} --> ${idOf(s.to)}: ${esc(s.label + '
                                    '(s.when ? ` [${s.when}]` : ""))}`,\n'
                                    '      );\n',
                                    '    for (const e of drawn) if (!e.start || !e.from.length) '
                                    'out.push(line(e, "  "));\n')]}}


def statechart_backport(text, relative):
 """Apply reviewed exact-source edits; refuse drift before touching bytes."""
 change = STATECHART_BACKPORTS[relative]
 if hashlib.sha256(text.encode()).hexdigest() != change['before_sha256']:
  raise ValueError('Pinned pstack statechart preimage changed: ' + relative)
 lines = text.splitlines(keepends=True)
 for start, stop, before, after in reversed(change['edits']):
  if ''.join(lines[start:stop]) != before:
   raise ValueError('Pinned pstack statechart backport anchor changed: ' + relative)
  lines[start:stop] = after.splitlines(keepends=True)
 rendered = ''.join(lines)
 if hashlib.sha256(rendered.encode()).hexdigest() != change['after_sha256']:
  raise ValueError('Pinned pstack statechart backport result changed: ' + relative)
 return rendered


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
support its operation needs. Resolve source companion names inside this local
pstack tree. Its `unslop` edits prose; it is distinct from the global `ui-polish` skill. Source slash commands, `Task`, `Agent`, `Explore`,
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
  'skills/show-me-your-work/SKILL.md': [
   ('At the end of the run, before handing back, check the log told the truth.', '22d6f51492086b26e2bb848bb0c17ba1855ee05e073acf22828f90968d71f6c7',
    "At the end of the run, before handing back, check the log against actually available evidence for this run only. Read a current-run transcript only through a supported native tool or an explicitly identified authorized task-owned transcript. Do not infer another host's transcript paths, glob private chats or inspect unrelated sessions. If current-run transcript access is unavailable, name that audit gap and verify available artifact/command evidence without claiming a complete transcript audit. Walk this run's rows against what actually happened; do not audit another run's rows as your own:"),
   ('Before handing back, spawn a subagent on a different model family', '6507928f20ed85168a44706a75721d664447b9d45a594600428188f19b566d0f',
    "Before handing back, obtain the original independent different-family review of the trail only when an explicitly authorized different-family model is actually callable. Preserve the user's current model and effort and never acquire a provider or credentials for this seat. If unavailable, report the distinct-family review incomplete; self-review or a same-family reader does not satisfy it. Give an available reviewer only this run's authorized audit trail and actually available current-run evidence, and ask it to flag weak evidence, missed checks and risky choices. No source model rules or effort defaults apply."),
   ('Every reply for a run that produced a trail ends', '78887f8e28b9d33876702cd01f8618bb6d290cd763cfe5ff3187de7a2a1a6b43',
    'Every reply for a run that produced a trail ends with an "Attention" section. When the required reviewer actually ran, name its actual model and point flags to specific rows or moments. If it did not run, state that the required different-family review is unavailable/incomplete and name any transcript-evidence gap. Never invent a reviewer/model or present "No flags" as completed review evidence.'),
  ],
  'skills/how/SKILL.md': [
   ('Every spawn is', '38953263928bd4b30a3031b3480f729bf528652b18c6a3b546575c5515e63c6f',
    "Every spawn is an independent native worker, with a read-only brief and verified unchanged source. Use the actual host delegation interface and inherit the user's current model and reasoning effort. Preserve the simple one-explainer path and the complex 2 to 4 explorers followed by a separate explainer. Follow the native adapter for unavailable independent workers; do not claim inline work is independent."),
  ],
  'skills/why/SKILL.md': [
   ('Each spawn below', '1dee5fd9349d8afd63edf12351631752f325db5e043bb170918e05c0485d37aa',
    "Every investigator and synthesizer is an independent native worker, inheriting the user's current model and reasoning effort. Follow the native adapter for supported delegation tools and unavailable independent workers. No source model-rule defaults or automatic family substitutions apply."),
   ('Every spawn is', '68051d8304d730af366c8d88ac41e2dffd26eef3a07c5a508934e219358affc3',
    'Give every investigator and synthesizer a read-only brief while preserving access to actually available evidence tools. Use only fields supported by the native host; do not invent readonly, agent-mode or role flags. Investigators and the synthesizer must not write or change external state.'),
   ('Before spawning investigators, list', 'e13a8a92d392bf201d28cbb462fb51198278616a2a366a7080d6c0fab31bdc39',
    "Before spawning investigators, discover actually available connected tools through the native tool inventory. Use their descriptions and supported schemas; do not inspect another host's configuration directories or credentials."),
   ('Source control is always', 'a62c00a0ba3813672fefc6f3f1819c95d6170feef28fafe243a4480e52b5cf73',
    'Source control history is always available through local git. Use an existing authorized native GitHub connection or existing gh only when available for exact PR evidence; report unavailable PR access as a gap. For the other six categories, classify actually connected tools using their names, descriptions and schemas. If a tool could fit more than one category, choose its primary evidence and record ambiguous cases in the coverage map.'),
   ('Spawn one investigator per', '9aad2f123d9ca8486e9a8808336dccb564d171c9475467cd81aa3342159b2446',
    "Spawn one independent investigator per category that has an available matching evidence tool, concurrently where supported, each owning exactly one tool or connection. Do not ask one investigator to cover multiple connections. Inherit the user's current model and reasoning effort."),
   ('Spawn one synthesizer.', '0efbf980b2cb8e32ff58d5a7c7ab56afb54387874d3459d386466707fe26e65a',
    "Spawn one separate independent synthesizer, inheriting the user's current model and reasoning effort. It gets:"),
  ],
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
 if relative == 'skills/why/references/synthesizer-prompt.md':
  text = text.replace('[PR #123](url)', '`[PR #123](actual-source-URL)`')
 for prefix, expected, replacement in bindings.get(relative, []):
  text = _line_binding(text, prefix, expected, replacement)
 return text

def entry_policy(text):
 """Expose the six selected conditional methods to native skill selection."""
 header, body = text.split('\n---\n', 1)
 if len(re.findall(r'(?m)^disable-model-invocation: true$', header)) != 1:
  raise ValueError('Pinned pstack invocation policy changed')
 header = re.sub(r'(?m)^disable-model-invocation: true\n?', '', header).rstrip('\n')
 if '](../../docs/harness/claude-code.md)' not in body:
  body = '\n> Read the [native pstack binding](../../docs/harness/claude-code.md) before using platform tools or source-named companion methods.\n' + body
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


def support_methods(source, root, transform):
 """Close named method calls omitted by the generic Markdown-link closure.

 Support is kept at its source path, not exposed as new global skills. The
 original method text determines which principles accompany a selected leaf.
 """
 base = 'harness/pstack/claude-code'
 skills = root / base / 'skills'
 upstream = source / base / 'skills'
 selected = {path.parent.name for path in skills.glob('*/SKILL.md')}
 needed = set()
 if 'architect' in selected:
  needed.update(('how', 'why', 'arena', 'interrogate', 'in-your-own-words'))
 if 'blast-radius' in selected:
  needed.update(('how', 'why', 'arena', 'unslop'))
 while True:
  # Only explicit source principle names, not ordinary category matches.
  files = [file for name in selected for file in (skills / name).rglob('*.md')]
  for file in files:
   text = file.read_text()
   for token in re.findall(r'\*\*([a-z][a-z0-9-]+)\*\*', text):
    if (upstream / token / 'SKILL.md').is_file():
     needed.add(token)
   for path in upstream.glob('principle-*/SKILL.md'):
    name = path.parent.name
    token = name.removeprefix('principle-')
    if re.search(r'(?<![\w-])' + re.escape(token) + r'(?![\w-])', text):
     needed.add(name)
  pending = needed - selected
  if not pending:
   break
  for name in sorted(pending):
   src, dest = upstream / name, skills / name
   if not (src / 'SKILL.md').is_file():
    raise ValueError('Pinned pstack named support missing: ' + name)
   shutil.copytree(src, dest)
   for file in dest.rglob('*.md'):
    file.write_text(transform(file.read_text(), file))
  selected.update(pending)


def helpers(root, source=None):
 for p in root.rglob('scripts/backends/mermaid.ts'):
  p.write_text(statechart_backport(p.read_text(), 'backends/mermaid.ts'))
 for p in root.rglob('scripts/run.ts'):
  p.write_text(statechart_backport(p.read_text(), 'run.ts'))
  t=p.read_text();a=t.index('  const mise =',t.index('async function findTlc'));b=t.index('\n}\n',a)
  t=t[:a]+'''  throw new Error("Set TLA2TOOLS to the verified TLC1.7.4 jar and JAVA to existing Java11+; automatic installs are disabled");'''+t[b:]
  p.write_text(t)

 if source is not None:
  base = 'harness/pstack/claude-code/'
  changes, patch = {}, []
  for active in sorted((root / base).rglob('*')):
   if not active.is_file():
    continue
   relative = active.relative_to(root / base).as_posix()
   upstream = source / base / relative
   if not upstream.is_file():
    raise ValueError('Pstack active file has no pinned source: ' + relative)
   original = upstream.read_bytes()
   expected = hashlib.sha256(original).hexdigest()
   if relative in SOURCE_SHA256 and expected != SOURCE_SHA256[relative]:
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
                                    'scope': 'Native method/delegation binding; originals are inert archival data.',
                                    'backport_source_revision': STATECHART_BACKPORT_REVISION,
                                    'backport_files': list(STATECHART_BACKPORTS),
                                    'files': changes}, sort_keys=True, indent=2) + '\n')):
    target = root.parent / filename
    if target.exists():
     raise ValueError('Pstack provenance collision: ' + filename)
    target.write_text(data)
