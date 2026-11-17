"""Full FPGA source closure and explicitly selected real Icarus/Yosys evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT/'addons/fpga-development'
INTEGRATION = ROOT/'integrations/fpga'


class FPGADevelopment(unittest.TestCase):
    def test_complete_source_leaf_and_replayable_binding_only_diff(self):
        receipt = json.loads((ADDON/'SOURCE.json').read_text())
        self.assertEqual(receipt['revision'], '6e472b033750c23e3139fd83744e089a6ee66ad1')
        for relative, row in receipt['upstream_files'].items():
            self.assertEqual(hashlib.sha256((ADDON/relative).read_bytes()).hexdigest(), row['sha256'])
        for relative in receipt['unchanged_active_files']:
            self.assertEqual((ADDON/relative).read_bytes(), (ADDON/'upstream'/relative).read_bytes())
        self.assertEqual(len(list((ADDON/'references').glob('*.md'))), 7)
        self.assertEqual(len(list((ADDON/'templates').glob('*.md'))), 6)
        with tempfile.TemporaryDirectory(prefix='fpga-replay-') as tmp:
            (Path(tmp)/'SKILL.md').write_bytes((ADDON/'upstream/ORIGINAL-SKILL.md').read_bytes())
            subprocess.run(['git', 'apply', '--check', str(ADDON/'adaptations/SKILL.md.diff')], cwd=tmp, check=True, capture_output=True)
            subprocess.run(['git', 'apply', str(ADDON/'adaptations/SKILL.md.diff')], cwd=tmp, check=True, capture_output=True)
            self.assertEqual((Path(tmp)/'SKILL.md').read_bytes(), (ADDON/'SKILL.md').read_bytes())

    def test_missing_tools_are_incomplete_and_output_preserved(self):
        with tempfile.TemporaryDirectory(prefix='fpga-incomplete-') as tmp:
            output = Path(tmp)/'missing'
            result = subprocess.run([sys.executable, '-I', '-B', str(ADDON/'scripts/fpga_fixture.py'),
                                     '--json', '--output', str(output)],
                                    env={'PATH': '', 'HOME': tmp}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            data = json.loads(result.stdout)
            self.assertEqual(data['status'], 'incomplete')
            self.assertTrue(all(x['status'] == 'skipped' for x in data['simulation']+data['synthesis']))
            marker = output/'keep';marker.write_text('preserved')
            again = subprocess.run([sys.executable, str(ADDON/'scripts/fpga_fixture.py'), '--output', str(output)],
                                   capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual(marker.read_text(), 'preserved')

    def test_runtime_refuses_linked_or_separated_mount_paths(self):
        spec = importlib.util.spec_from_file_location('fpga_runtime', INTEGRATION/'runtime.py')
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='fpga-linked-', dir='/private/tmp') as tmp:
            target = Path(tmp)/'target';target.mkdir()
            alias = Path(tmp)/'alias';alias.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'canonical path'):
                module.canonical(alias/'new')
            for suffix in (',other', '\nother', '\rother'):
                with self.assertRaisesRegex(ValueError, 'mount separators'):
                    module.canonical(str(target)+suffix)
            self.assertTrue(alias.is_symlink())
            self.assertEqual(list(target.iterdir()), [])

    @unittest.skipUnless(os.environ.get('NSTACK_FPGA_STATE'), 'Explicit reviewed FPGA state not selected')
    def test_actual_icarus_yosys_and_data_loss_negative(self):
        with tempfile.TemporaryDirectory(prefix='fpga-test-', dir='/private/tmp') as tmp:
            output = Path(tmp)/'check'
            run = subprocess.run([sys.executable, str(INTEGRATION/'runtime.py'), 'check', '--state',
                os.environ['NSTACK_FPGA_STATE'], '--out', str(output)], capture_output=True, text=True, timeout=240)
            self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
            data = json.loads((output/'RESULT.json').read_text())
            self.assertTrue(data['passed'])
            self.assertFalse(data['hardware'])
            positive = json.loads((output/'positive/result.json').read_text())
            negative = json.loads((output/'data-loss-negative/result.json').read_text())
            self.assertEqual(positive['status'], 'passed')
            self.assertEqual(negative['status'], 'failed')
            self.assertTrue(all(x['status'] == 'failed' for x in negative['simulation']))
            self.assertTrue(all(x['status'] == 'passed' for x in negative['synthesis']))


if __name__ == '__main__':
    unittest.main()
