"""Pinned pstack architecture keeps its method without a retired host runtime."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from patch_native34 import materialize, native_text


class PstackNativeBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'registry/manifest.json').read_text())
        cls.component = next(c for c in cls.manifest['components'] if c['id'] == 'P028')
        cls.specs = [s for s in cls.manifest['skills']
                     if s['candidate_id'] == 'P028' and s.get('native_name')]
        cls.source = (Path.home() / 'Library/Application Support/nstack/sources'
                      / 'cursor--plugins' / cls.specs[0]['revision'])
        if not (cls.source / '.nstack-source.json').is_file():
            raise unittest.SkipTest('Pinned offline pstack absent; no acquisition')
        cls.pstack = cls.source / 'harness/pstack/claude-code'

    def port(self, relative, original=None):
        file = self.pstack / relative
        return native_text(file.read_text() if original is None else original,
                           'P028', file, self.source)

    def test_pinned_architecture_and_conditional_arena_keep_complete_design_contract(self):
        with tempfile.TemporaryDirectory(prefix='nstack-pstack-test-') as tmp:
            for name in ('pstack-architect', 'pstack-blast-radius'):
                spec = next(s for s in self.specs if s['native_name'] == name)
                out = Path(tmp) / name
                entry = materialize(self.source, out, spec, self.component)
                self.assertTrue((out / entry / 'SKILL.md').is_file())
                active = out / 'source/harness/pstack/claude-code'
                adapter = (active / 'docs/harness/claude-code.md').read_text()
                arena = (active / 'skills/arena/SKILL.md').read_text()
                self.assertIn('collaboration.spawn_agent', adapter)
                self.assertIn('omit `model`', adapter)
                self.assertIn('`reasoning_effort`', adapter)
                self.assertIn('skip it and let the parent pick', arena)
                self.assertNotIn('claude-opus', arena)
                self.assertNotIn('grok-4.7', arena)
                self.assertNotIn('pstack-models.mdc', arena)
                self.assertNotIn('~/.claude/', adapter)
                for phase in ('Frame', 'Fan out', 'Cross-judge', 'Pick a base',
                              'Graft', 'Verify'):
                    self.assertIn(': ' + phase, arena)
                architect = (active / 'skills/architect/SKILL.md').read_text()
                self.assertIn('at least two structurally distinct candidates', architect)
                self.assertIn('references/design-red-flags.md', architect)
                self.assertIn('references/rationale-template.md', architect)
                prompt = (active / 'skills/architect/references/runner-prompt.md').read_text()
                self.assertIn('the parent owns its workflow', prompt)
                self.assertIn('Do not launch arena, delegate, implement', prompt)
                self.assertIn('Caller\'s usage first', prompt)
                # Design support stays at its original path and byte-for-byte intact.
                for rel in ('skills/architect/references/design-red-flags.md',
                            'skills/architect/references/rationale-template.md'):
                    self.assertEqual((active / rel).read_bytes(), (self.pstack / rel).read_bytes())
                receipt = json.loads((out / 'PSTACK-PORT.json').read_text())
                restored = Path(tmp) / (name + '-restore')
                for rel, item in receipt['files'].items():
                    original = out / item['original']
                    self.assertTrue(original.name.endswith('.original'))
                    self.assertEqual(original.read_bytes(), (self.source / rel).read_bytes())
                    self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                                     item['before_sha256'])
                    dest = restored / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(original.read_bytes())
                patch = str(out / 'PSTACK-PORT.patch')
                subprocess.run(['git', 'apply', '--check', patch], cwd=restored, check=True,
                               capture_output=True)
                subprocess.run(['git', 'apply', patch], cwd=restored, check=True,
                               capture_output=True)
                for rel, item in receipt['files'].items():
                    self.assertEqual((restored / rel).read_bytes(), (out / 'source' / rel).read_bytes())
                    self.assertEqual(hashlib.sha256((restored / rel).read_bytes()).hexdigest(),
                                     item['after_sha256'])

    def test_all_selected_entries_resolve_source_names_in_the_bundled_tree(self):
        import skill_names
        self.assertEqual(skill_names.canonical('unslop'), 'ui-polish')
        with tempfile.TemporaryDirectory(prefix='pstack-name-bridge-') as tmp:
            self.assertEqual(len(self.specs), 6)
            for spec in self.specs:
                with self.subTest(method=spec['native_name']):
                    out = Path(tmp) / spec['native_name']
                    entry = out / materialize(self.source, out, spec, self.component)
                    self.assertIn('](../../docs/harness/claude-code.md)',
                                  (entry / 'SKILL.md').read_text())
                    adapter = (entry / '../../docs/harness/claude-code.md').resolve()
                    self.assertTrue(adapter.is_relative_to(out.resolve()))
                    binding = adapter.read_text()
                    self.assertIn('Resolve source companion names inside this local', binding)
                    self.assertIn('distinct from the global `ui-polish` skill', binding)
                    if spec['native_name'] == 'pstack-blast-radius':
                        local = entry.parent / 'unslop/SKILL.md'
                        self.assertTrue(local.is_file())
                        self.assertIn('Write it through `unslop`',
                                      (entry / 'SKILL.md').read_text())
                        self.assertEqual(local.read_bytes(),
                                         (self.pstack / 'skills/unslop/SKILL.md').read_bytes())

    def test_required_how_why_and_named_principles_are_callable_source_support(self):
        from patch_pstack import SOURCE_SHA256
        with tempfile.TemporaryDirectory(prefix='nstack-pstack-support-') as tmp:
            for name in ('pstack-architect', 'pstack-blast-radius'):
                spec = next(s for s in self.specs if s['native_name'] == name)
                out = Path(tmp) / name
                materialize(self.source, out, spec, self.component)
                skills = out / 'source/harness/pstack/claude-code/skills'
                how = (skills / 'how/SKILL.md').read_text()
                why = (skills / 'why/SKILL.md').read_text()
                self.assertIn('Spawn one explainer', how)
                self.assertIn('2 to 4 angles', how)
                self.assertIn('spawn one explainer', how)
                self.assertIn('Do not substantially rewrite it', how)
                self.assertIn('Always spawn', why)
                self.assertIn('all seven available category searches', why)
                self.assertIn('Spawn one separate independent synthesizer', why)
                self.assertIn('do not rewrite the confidence language', why)
                self.assertIn('Preserve / Change / Avoid / Risk', why)
                for text in (how, why):
                    for forbidden in ('pstack-models.mdc', 'grok-4.7', 'claude-opus',
                                      'subagent_type:', '`readonly:'):
                        self.assertNotIn(forbidden, text)
                for method in ('how', 'why'):
                    for ref in (self.pstack / 'skills' / method / 'references').rglob('*'):
                        if not ref.is_file():
                            continue
                        rel = ref.relative_to(self.pstack / 'skills')
                        if 'skills/' + rel.as_posix() not in SOURCE_SHA256:
                            self.assertEqual((skills / rel).read_text(), self.port('skills/' + rel.as_posix()))
                if name == 'pstack-architect':
                    architect = (skills / 'architect/SKILL.md').read_text()
                    self.assertIn('Run the **how** skill over the relevant subsystems.', architect)
                    self.assertIn('also run the **why** skill on the existing shape', architect)
                    self.assertIn('Re-run the **how** skill', architect)
                    for principle in ('exhaust-the-design-space', 'foundational-thinking',
                                      'outcome-oriented-execution', 'redesign-from-first-principles',
                                      'fix-root-causes', 'subtract-before-you-add', 'prove-it-works'):
                        rel = 'skills/principle-' + principle + '/SKILL.md'
                        expected = self.port(rel)
                        self.assertEqual((skills.parent / rel).read_text(), expected)
                    trail = (skills / 'show-me-your-work/SKILL.md').read_text()
                    self.assertIn('different-family review is unavailable/incomplete', trail)
                    self.assertIn('transcript access is unavailable', trail)
                    self.assertTrue((skills / 'unslop/SKILL.md').is_file())
                    self.assertTrue((skills / 'principle-encode-lessons-in-structure/SKILL.md').is_file())
                    self.assertTrue((skills / 'interrogate/SKILL.md').is_file())
                    self.assertTrue((skills / 'in-your-own-words/SKILL.md').is_file())
                else:
                    blast = (skills / 'blast-radius/SKILL.md').read_text()
                    self.assertIn('Use `why` step 2', blast)
                    self.assertIn('Same rules as `why`.', blast)
                # A port adds support only; it never installs the source controller.
                self.assertFalse((skills / 'setup-pstack').exists())
                self.assertFalse((skills / 'poteto-mode').exists())

    def test_each_reviewed_binding_rejects_changed_preimages(self):
        cases = {
            'skills/show-me-your-work/SKILL.md': ('family from the one that did the work', 'family changed from the one that did the work'),
            'skills/how/SKILL.md': ('Every spawn is a Task', 'Every spawn is changed Task'),
            'skills/why/SKILL.md': ('Each spawn below names', 'Each spawn below changed names'),
            'docs/harness/claude-code.md': ('# pstack in Claude Code', '# changed host'),
            'skills/architect/SKILL.md': ('Take the runners from', 'Take the runners changed from'),
            'skills/arena/SKILL.md': ('3. Pick the runners. Use', '3. Pick the runners. Changed use'),
            'skills/architect/references/runner-prompt.md':
                ('You are producing one candidate design', 'You are producing one candidate changed design'),
            'skills/blast-radius/SKILL.md':
                ('6. For a big or wide change, run', '6. For a big or wide change, changed run'),
        }
        for rel, (before, after) in cases.items():
            with self.subTest(relative=rel):
                raw = (self.pstack / rel).read_text()
                self.assertIn(before, raw)
                with self.assertRaisesRegex(ValueError, 'pstack.*preimage changed'):
                    self.port(rel, raw.replace(before, after, 1))
        rel = 'skills/arena/SKILL.md'
        raw = (self.pstack / rel).read_text()
        with self.assertRaisesRegex(ValueError, 'binding anchor changed'):
            self.port(rel, raw.replace('3. Pick the runners.', '3. Runners.', 1))

    def test_raw_source_guard_catches_changes_outside_replaced_lines(self):
        with tempfile.TemporaryDirectory(prefix='nstack-pstack-drift-') as tmp:
            relative = 'harness/pstack/claude-code/skills/architect/SKILL.md'
            file = Path(tmp) / relative
            file.parent.mkdir(parents=True)
            raw = (self.source / relative).read_text()
            changed = raw.replace('## Phase A: Ground the problem',
                                  '## Phase A: Unreviewed change', 1)
            self.assertNotEqual(raw, changed)
            file.write_text(changed)
            with self.assertRaisesRegex(ValueError, 'source preimage changed'):
                native_text(changed, 'P028', file, Path(tmp))

    def test_ownership_and_idempotency_bodies_remain_unmodified(self):
        for name in ('principle-separate-before-serializing-shared-state',
                     'principle-make-operations-idempotent'):
            relative = 'skills/' + name + '/SKILL.md'
            self.assertEqual(self.port(relative), (self.pstack / relative).read_text())

    def test_unrelated_same_filename_is_outside_binding_scope(self):
        raw = '# Unrelated adapter\nUse this project\'s own tools.\n'
        actual = native_text(raw, 'P028', Path('/tmp/unrelated/docs/harness/claude-code.md'),
                             Path('/tmp/unrelated'))
        self.assertEqual(actual, raw)


class PstackFormalLeaves(unittest.TestCase):
    def test_complete_formal_methods_and_statechart_support_replay(self):
        from closure import validate
        for kind in ('create', 'maintain'):
            addon = ROOT / 'addons' / ('pstack-' + kind + '-formal-verification')
            receipt = json.loads((addon / 'SOURCE.json').read_text())
            self.assertEqual(receipt['revision'], 'bb68f2365eceafa0cb2d253112f675acf5f144cc')
            self.assertEqual(len(receipt['upstream_files']), 409)
            self.assertEqual(list(addon.rglob('SKILL.md')), [addon/'SKILL.md'])
            self.assertTrue((addon/'support/statechart/METHOD.md').is_file())
            self.assertTrue((addon/'upstream/support/statechart/ORIGINAL-SKILL.md').is_file())
            self.assertEqual(receipt['relocations'][0]['source_path'],
                             'harness/pstack/claude-code/skills/statechart/SKILL.md')
            for relative, row in receipt['upstream_files'].items():
                self.assertEqual(hashlib.sha256((addon / relative).read_bytes()).hexdigest(), row['sha256'])
            for relative in receipt['unchanged_active_files']:
                self.assertEqual((addon / relative).read_bytes(), (addon / 'upstream' / relative).read_bytes())
            self.assertTrue((addon / 'support/statechart/scripts/statechart.ts').is_file())
            self.assertNotIn('const mise =', (addon / 'support/statechart/scripts/run.ts').read_text())
            validate(addon, provenance_roots=('upstream',))
            with tempfile.TemporaryDirectory(prefix='pstack-formal-replay-') as tmp:
                for change in receipt['adapted_files']:
                    dest = Path(tmp) / change['active_path']
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes((addon / change['original_path']).read_bytes())
                    subprocess.run(['git', 'apply', '--check', str(addon / change['diff'])], cwd=tmp,
                                   check=True, capture_output=True)
                    subprocess.run(['git', 'apply', str(addon / change['diff'])], cwd=tmp,
                                   check=True, capture_output=True)
                    self.assertEqual(dest.read_bytes(), (addon / change['active_path']).read_bytes())
            original = (addon / 'upstream/ORIGINAL-SKILL.md').read_text()
            active = (addon / 'SKILL.md').read_text()
            before = 'In Claude Code, read [the Claude Code adapter](../../docs/harness/claude-code.md) once per session before you follow this skill. It maps the Cursor names in pstack skills to Claude Code.'
            after = 'Read [native bindings](NATIVE-BINDINGS.md) before following this complete source method. Exact originals and adaptation diffs are in [SOURCE.json](SOURCE.json).'
            expected = original.replace(before, after).replace('(../statechart/SKILL.md)', '(support/statechart/METHOD.md)').replace('disable-model-invocation: true\n', '', 1)
            self.assertEqual(active, expected)
            # Native registration is conditional on the concrete project scope.
            binding = (addon / 'NATIVE-BINDINGS.md').read_text()
            self.assertIn('owning repository', binding)
            self.assertIn('[statechart method](support/statechart/METHOD.md)', binding)
            self.assertIn('A blocked check keeps its previous confirmed generation', binding)
            if kind == 'create':
                self.assertIn('strongest such target in the repo, not the one that is easiest', active)
                self.assertIn('broken variant of the code it guards', active)
                self.assertIn('A verify skill that was never run is a draft', active)
            else:
                self.assertIn('Run each check once before you change anything', active)
                self.assertIn('Never edit product code during a run', active)
                self.assertIn('Do not move the sync commit for a blocked check', active)
                self.assertIn('the old pass was on a stale description', active)


if __name__ == '__main__':
    unittest.main()
