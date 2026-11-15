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

    def test_each_reviewed_binding_rejects_changed_preimages(self):
        cases = {
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


if __name__ == '__main__':
    unittest.main()
