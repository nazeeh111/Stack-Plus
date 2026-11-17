"""New source bundles remain usable after their original checkout moves."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native
import claude_setup as claude


class ExpansionDelivery(unittest.TestCase):
    def test_source_closed_host_entries_and_durable_runtime_companions(self):
        additions = ['dream-loop', 'fpga-development', 'cirq',
                     'pstack-create-formal-verification',
                     'pstack-maintain-formal-verification', 'rea',
                     'shinka-evolve', 'ai-scientist']
        expected = {'visual-target-development', 'rtl-fpga-engineering',
                    'cirq-quantum-simulation',
                    'formal-verification-workflow-authoring',
                    'formal-verification-workflow-maintenance', 'rea-software-analysis',
                    'shinka-program-evolution', 'ai-scientist-study-pipeline'}
        with tempfile.TemporaryDirectory(dir='/private/tmp' if Path('/private/tmp').is_dir() else None) as temp:
            base = Path(temp).resolve()
            checkout, retained, state = base / 'checkout', base / 'retained', base / 'state'
            for name in additions:
                shutil.copytree(ROOT / 'addons' / name, checkout / 'addons' / name)
            (retained / 'lib').mkdir(parents=True)
            shutil.copy2(ROOT / 'lib' / 'docker_client.py', retained / 'lib' / 'docker_client.py')
            (retained / 'recipes').mkdir(parents=True)
            for name in ('rea.py', 'rea_linux.py'):
                shutil.copy2(ROOT / 'recipes' / name, retained / 'recipes' / name)
            shutil.copytree(ROOT / 'integrations' / 'rea', retained / 'integrations' / 'rea',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            # Only guide resolution is exercised here. Runtime/transport operation
            # remains owned by its separate actual-engine acceptance.
            (retained / 'integrations' / 'research').mkdir(parents=True)
            shutil.copy2(ROOT / 'integrations' / 'research' / 'README.md',
                         retained / 'integrations' / 'research' / 'README.md')
            with patch.object(native, 'ROOT', checkout), \
                    patch.object(native.nstack, 'STATE', state), \
                    patch.object(native.profile_install, 'stage', return_value=retained):
                release, index = native.prepare(state, [], additions)
                portable, portable_index = claude.prepare(state, [], additions)
                again, same_index = native.prepare(state, [], additions)
            self.assertEqual((again, same_index), (release, index))
            self.assertEqual({r['name'] for r in index}, expected)
            self.assertEqual({r['name'] for r in portable_index}, expected)
            for records in (index, portable_index):
                for row in records:
                    entry = Path(row['skill_path'])
                    self.assertTrue(entry.is_file(), row['name'])
                    self.assertEqual(list(entry.parent.rglob('SKILL.md')), [entry])
                    self.assertTrue((entry.parent / 'SOURCE.json').is_file())
            for records in (index, portable_index):
                row = next(r for r in records if r['name'] == 'rea-software-analysis')
                source = json.loads((Path(row['skill_path']).parent / 'SOURCE.json').read_text())
                self.assertEqual(row['runtime_recipe_linux'], source['runtime_recipe_linux'])
                self.assertEqual(row['runtime_recipe'], source['runtime_recipe'])
                self.assertEqual(Path(source['runtime_recipe_linux']), retained / 'recipes' / 'rea_linux.py')
                self.assertEqual(Path(source['runtime_recipe']), retained / 'recipes' / 'rea.py')
            for records in (index, portable_index):
                for name in ('shinka-program-evolution', 'ai-scientist-study-pipeline'):
                    row = next(r for r in records if r['name'] == name)
                    source = json.loads((Path(row['skill_path']).parent / 'SOURCE.json').read_text())
                    self.assertEqual(row['runtime_guide'], source['runtime_guide'])
                    self.assertEqual(Path(source['runtime_guide']), retained / 'integrations/research/README.md')
                    self.assertTrue(Path(source['runtime_guide']).is_file())
            checkout.rename(base / 'checkout-moved')
            # This exercises actual import-time companion resolution, without Docker,
            # acquisition, target analysis, providers or global profile changes.
            command = [sys.executable, str(retained / 'recipes' / 'rea_linux.py'), '--help']
            good = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(good.returncode, 0, good.stderr)
            pins = retained / 'integrations' / 'rea' / 'linux' / 'PINS.json'
            pins.rename(pins.with_suffix('.preserved'))
            bad = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('PINS.json', bad.stderr)
            self.assertFalse((state / 'native-tools').exists())
            self.assertTrue(portable.is_dir())


if __name__ == '__main__':
    unittest.main()
