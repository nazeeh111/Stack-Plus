"""Read-only catalog discovery and user-facing CLI contracts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class DiscoveryCLI(unittest.TestCase):
    def run_cli(self, state, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / 'nstack.py'), *args],
            cwd=ROOT, env={**os.environ, 'NSTACK_STATE': str(state),
                          'PYTHONDONTWRITEBYTECODE': '1'},
            text=True, capture_output=True, check=False,
        )

    def test_canonical_name_finds_component_without_creating_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'absent'
            result = self.run_cli(state, 'search', 'web-ui-design', '--brief')
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(result.stdout)
            row = next(row for row in rows if row['id'] == 'L010')
            self.assertIn('web-ui-design', row['selected_native_names'])
            self.assertFalse(state.exists())
            for command in ('show', 'route'):
                result = self.run_cli(state, command, 'L010')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['id'], 'L010')
                self.assertFalse(state.exists())

    def test_source_name_and_default_full_json_remain_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(Path(tmp)/'state', 'search', 'frontend-design')
            self.assertEqual(result.returncode, 0, result.stderr)
            row = next(r for r in json.loads(result.stdout) if r['id'] == 'L010')
            self.assertIn('trigger', row)
            self.assertNotIn('selected_native_names', row)

    def test_no_result_is_valid_json_and_has_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(Path(tmp)/'state', 'search', 'no-such-skill-6c8e', '--brief')
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), [])
            self.assertIn('broader terms', result.stderr)

    def test_references_are_not_presented_as_selected_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(Path(tmp)/'state', 'search', 'diagnosing-bugs', '--brief')
            row = next(r for r in json.loads(result.stdout) if r['id'] == 'P001')
            self.assertIn('diagnosing-bugs', row['selected_native_names'])
            self.assertIn('test-driven-development', row['selected_native_names'])
            self.assertNotIn('untangle-codebase', row['selected_native_names'])

    def test_catalog_names_match_native_selection(self):
        # Compare the public catalog view with the installer selection policy.
        sys.path.insert(0, str(ROOT))
        try:
            import native_setup
            import nstack
            expected = {}
            for name, row in native_setup.selection():
                expected.setdefault(row['candidate_id'], []).append(name)
            self.assertEqual(nstack.discovery_names(), expected)
        finally:
            sys.path.remove(str(ROOT))

    def test_discovery_reads_one_manifest_per_operation(self):
        sys.path.insert(0, str(ROOT))
        try:
            import nstack
            actual_load = nstack.load
            reads = []
            def counted(path):
                if Path(path) == ROOT / 'registry/manifest.json':
                    reads.append(path)
                return actual_load(path)
            with patch.object(nstack, 'load', side_effect=counted):
                first = nstack.discovery_names()
                self.assertEqual(len(reads), 1)
                second = nstack.discovery_names()
                self.assertEqual(len(reads), 2)
            self.assertEqual(first, second)
        finally:
            sys.path.remove(str(ROOT))

    def test_invalid_id_and_limit_explain_next_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)/'state'
            bad_id = self.run_cli(state, 'show', 'P999999')
            self.assertNotEqual(bad_id.returncode, 0)
            self.assertIn('search TERMS --brief', bad_id.stderr)
            bad_limit = self.run_cli(state, 'search', 'test', '--limit', '0')
            self.assertNotEqual(bad_limit.returncode, 0)
            self.assertIn('between 1 and 535', bad_limit.stderr)
            self.assertFalse(state.exists())

if __name__ == '__main__':
    unittest.main()
