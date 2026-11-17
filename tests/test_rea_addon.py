"""REA is an optional portable skill; shared discovery does not activate its runtime."""
import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native
import claude_setup as claude
from transaction import fingerprint


class ReaAddon(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nstack-rea-addon-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.state = self.base / 'state'
        state = patch.object(native.nstack, 'STATE', self.state)
        state.start()
        self.addCleanup(state.stop)

    def args(self, home, enabled=True):
        return argparse.Namespace(home=str(home), state=str(self.state), only=None,
                                  agent_reach=False, repository_docs=False,
                                  replace=True, vault=None, rea=enabled)

    def assert_provenance(self, entry):
        self.assertEqual(entry.name, 'rea-software-analysis')
        name_line = next(line for line in (entry / 'SKILL.md').read_text().splitlines()
                         if line.startswith('name: '))
        name = name_line.removeprefix('name: ')
        self.assertEqual(json.loads(name) if name.startswith('"') else name, 'rea-software-analysis')
        self.assertEqual(list(entry.rglob('SKILL.md')), [entry / 'SKILL.md'])
        provenance = json.loads((entry / 'SOURCE.json').read_text())
        self.assertEqual(provenance['repository'], 'morluto/rea')
        self.assertEqual(provenance['revision'], 'ab16163061094a6c28e9133c9c618e0850c9cb2f')
        self.assertEqual(provenance['method_revision'], provenance['revision'])
        self.assertEqual(provenance['runtime_dependency']['source_revision'],
                         'd74549e495c58eb4a560279fd9f05508401ea0a0')
        for rel, item in provenance['upstream_files'].items():
            self.assertEqual(hashlib.sha256((entry / rel).read_bytes()).hexdigest(), item['sha256'])
        recipe = Path(provenance['runtime_recipe'])
        self.assertTrue(recipe.is_absolute())
        self.assertTrue(recipe.is_relative_to(self.state / 'releases'))
        self.assertEqual(recipe.read_bytes(), (ROOT / 'recipes/rea.py').read_bytes())
        self.assertTrue((recipe.parents[1] / 'integrations/rea/PINS.json').is_file())
        self.assertFalse((self.state / 'native-tools').exists())
        self.assertFalse((self.state / 'runtimes').exists())
        self.assertFalse((self.state / 'native-tools/index.json').exists())

    def test_both_host_flags_are_optional_and_route_only_when_requested(self):
        for host in (native, claude):
            for enabled in (False, True):
                with self.subTest(host=host.__name__, enabled=enabled):
                    argv = [str(ROOT / (host.__name__ + '.py')), 'install']
                    if enabled:
                        argv.append('--rea')
                    with patch.object(sys, 'argv', argv), patch.object(host, 'apply', return_value={}) as apply:
                        with redirect_stdout(io.StringIO()):
                            host.main()
                    self.assertEqual(apply.call_args.args[0].rea, enabled)
        with patch.object(native, 'selection', return_value=[]):
            for enabled in (False, True):
                self.assertEqual(claude.selected(self.args(self.base / 'home', enabled))[1],
                                 ['rea'] if enabled else [])

    def test_native_opt_in_preserves_dirty_bytes_repeats_and_rolls_back_without_runtime(self):
        home = self.base / 'home'
        home.mkdir()
        dirty = home / '.agents/skills/personal/SKILL.md'
        dirty.parent.mkdir(parents=True)
        dirty.write_text('Unrelated uncommitted personal skill.\n')
        before = fingerprint(dirty.parents[1])
        config = home / '.config/opencode/opencode.json'
        config.parent.mkdir(parents=True)
        config.write_text('{"model":"keep-model","provider":{"unchanged":true}}\n')
        config_before = fingerprint(config)
        with patch.object(native, 'selection', return_value=[]), \
             patch.object(native.nstack, 'build', side_effect=AssertionError('No base build expected')), \
             patch.object(native.nstack, 'acquire', side_effect=AssertionError('No source acquisition expected')):
            result = native.apply(self.args(home))
            shared = home / '.agents/skills'
            self.assertEqual({p.name for p in shared.iterdir()}, {'rea-software-analysis'})
            self.assert_provenance(shared / 'rea-software-analysis')
            rows = json.loads((self.state / 'native-skill-index.json').read_text())
            self.assertEqual([row['name'] for row in rows], ['rea-software-analysis'])
            self.assertEqual(rows[0]['source_name'], 'rea')
            self.assertEqual(rows[0]['runtime_recipe'], json.loads(
                (shared / 'rea-software-analysis/SOURCE.json').read_text())['runtime_recipe'])
            journal = Path(result['run']) / 'journal.json'
            stable = {p: fingerprint(p) for p in (shared, journal, self.state / 'native-skill-index.json')}
            self.assertFalse(native.apply(self.args(home))['changed'])
            for path, expected in stable.items():
                self.assertEqual(fingerprint(path), expected)
            self.assertEqual(fingerprint(config), config_before)
            native.rollback(result['run'], False)
        self.assertEqual(fingerprint(home / '.agents/skills'), before)
        self.assertEqual(fingerprint(config), config_before)

    def test_portable_claude_view_retains_shared_provenance_without_host_activation(self):
        with patch.object(native.nstack, 'acquire', side_effect=AssertionError('No acquisition expected')):
            shared, native_rows = native.prepare(self.state, [], ['rea'])
            before = fingerprint(shared)
            release, rows = claude.prepare(self.state, [], ['rea'])
            entry = Path(rows[0]['skill_path']).parent
            self.assert_provenance(entry)
            self.assertEqual(fingerprint(shared), before)
            self.assertEqual(rows[0]['native_skill_path'], native_rows[0]['skill_path'])
            repeated, repeated_rows = claude.prepare(self.state, [], ['rea'])
            self.assertEqual(release, repeated)
            self.assertEqual(rows, repeated_rows)
            self.assertFalse((self.base / 'home/.claude').exists())
            # Runtime recipe remains usable from staged code after checkout movement.
            provenance = json.loads((entry / 'SOURCE.json').read_text())
            durable = Path(provenance['runtime_recipe']).parents[1]
            with patch.object(native, 'ROOT', durable):
                definition = native.addon_definition('rea-software-analysis')
            self.assertEqual(definition['frozen_files']['SKILL.md'][0],
                             (ROOT / 'addons/rea/SKILL.md').read_bytes())


if __name__ == '__main__':
    unittest.main()
