"""Source preservation, native boundaries and explicit optional CPU acceptance."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT/'addons/cirq'
INTEGRATION = ROOT/'integrations/cirq'


class CirqNative(unittest.TestCase):
    def test_complete_source_and_narrow_patch_replay(self):
        receipt = json.loads((ADDON/'SOURCE.json').read_text())
        self.assertEqual(receipt['revision'], 'a25cf9ec00e2745d03f8704acf6f6919694ccd9a')
        for relative, row in receipt['upstream_files'].items():
            self.assertEqual(hashlib.sha256((ADDON/relative).read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(len(list((ADDON/'references').glob('*.md'))), 7)
        for relative in receipt['unchanged_active_files']:
            self.assertEqual((ADDON/relative).read_bytes(), (ADDON/'upstream'/relative).read_bytes())
        original = (ADDON/'upstream/ORIGINAL-SKILL.md').read_text()
        active = (ADDON/'SKILL.md').read_text()
        # Every substantive source section survives byte-for-byte; only a binding
        # paragraph and the explicitly disclosed self-citation differ.
        before_citation = original.split('\n## Citing Scientific Agent Skills')[0].rstrip()+'\n'
        insertion = '\n\nRead [native bindings](NATIVE-BINDINGS.md) first. Exact source bytes and the narrow adaptation diff are recorded in [SOURCE.json](SOURCE.json).\n'
        self.assertEqual(active.replace(insertion, '', 1), before_citation)
        self.assertTrue((ADDON/'LICENSE.md').is_file())
        self.assertTrue((ADDON/'LICENSE-APACHE-2.0.txt').is_file())
        with tempfile.TemporaryDirectory(prefix='cirq-source-replay-') as tmp:
            (Path(tmp)/'SKILL.md').write_text(original)
            subprocess.run(['git', 'apply', '--check', str(ADDON/'adaptations/SKILL.md.diff')], cwd=tmp, check=True, capture_output=True)
            subprocess.run(['git', 'apply', str(ADDON/'adaptations/SKILL.md.diff')], cwd=tmp, check=True, capture_output=True)
            self.assertEqual((Path(tmp)/'SKILL.md').read_text(), active)

    def test_existing_evidence_is_preserved_before_execution(self):
        with tempfile.TemporaryDirectory(prefix='cirq-preserve-', dir='/private/tmp') as tmp:
            marker = Path(tmp)/'keep.txt';marker.write_text('original bytes')
            result = subprocess.run([sys.executable, str(INTEGRATION/'check.py'), '--python', sys.executable,
                                     '--out', tmp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(marker.read_text(), 'original bytes')
            self.assertEqual(list(Path(tmp).iterdir()), [marker])

    def test_linked_output_is_preserved_and_not_followed(self):
        with tempfile.TemporaryDirectory(prefix='cirq-linked-', dir='/private/tmp') as tmp:
            base = Path(tmp);target = base/'target';target.mkdir()
            alias = base/'alias';alias.symlink_to(target, target_is_directory=True)
            result = subprocess.run([sys.executable, str(INTEGRATION/'check.py'), '--python', sys.executable,
                '--out', str(alias/'new')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('canonical output path', result.stderr)
            self.assertTrue(alias.is_symlink())
            self.assertEqual(list(target.iterdir()), [])

    @unittest.skipUnless(os.environ.get('NSTACK_CIRQ_PYTHON'), 'Explicit reviewed Cirq interpreter not selected')
    def test_real_cpu_contract_and_wrong_result_controls(self):
        with tempfile.TemporaryDirectory(prefix='cirq-test-', dir='/private/tmp') as tmp:
            output = Path(tmp)/'check'
            result = subprocess.run([sys.executable, str(INTEGRATION/'check.py'), '--python',
                os.environ['NSTACK_CIRQ_PYTHON'], '--out', str(output)], capture_output=True, text=True, timeout=210)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr+(output/'execution.json').read_text())
            data = json.loads((output/'RESULT.json').read_text())
            self.assertTrue(data['passed'])
            self.assertEqual(len(data['checks']), 7)
            self.assertTrue(all(row['passed'] for row in data['checks'].values()))
            self.assertGreater(data['checks']['real_clifford_RB']['removed_inverse_piece_rejected'], 0)
            self.assertIn('(deny network*)', (output/'sandbox.sb').read_text())


if __name__ == '__main__':
    unittest.main()
