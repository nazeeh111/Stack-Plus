import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from lib.runtime_paths import audit


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class RuntimePathTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.state = Path(scratch.name).resolve()
        self.index = self.state / 'native-tools/index.json'
        self.index.parent.mkdir()
        self.before = self.state / 'recovery.json'
        self.release_id = 'b' * 64
        self.release = self.state / 'releases' / self.release_id
        self.relative = 'integrations/media-editing/whisper_cpu.py'
        self.target = self.release / self.relative
        self.target.parent.mkdir(parents=True)
        self.payload = b"raise RuntimeError('should never run')\n"
        self.target.write_bytes(self.payload)
        self.original = str(self.state / 'releases' / ('a' * 64) / self.relative)
        self.seal = self.release / 'INSTALL-MANIFEST.json'
        self.seal.write_text(json.dumps({self.relative: sha(self.payload)}))
        self.row = {
            'name': 'Whisper.cpp CPU local ASR',
            'entrypoint': self.original, 'entrypoint_sha256': sha(self.payload),
            'invoke': ['python3', self.original, '--lang', 'en'],
            'adapter': self.original, 'adapter_sha256': sha(self.payload),
            'checks': self.original, 'documentation': self.original,
            'mac_historical': {'historical_invocation': [self.original]},
            'readiness': 'Only after a project-specific check.',
        }
        self.store([self.row])

    def store(self, rows):
        raw = json.dumps(rows).encode()
        self.before.write_bytes(raw)
        self.index.write_bytes(raw)

    def plan(self):
        return audit(self.state, release_id=self.release_id, reference=self.before,
                     reference_sha256=sha(self.before.read_bytes()), selected=[self.row['name']])['records'][0]

    def test_invocation_locations_preserve_history_and_authority(self):
        before = self.index.read_bytes()
        result = self.plan()
        self.assertEqual(len(result['proposals']), 1)
        binding = result['proposals'][0]
        self.assertEqual(binding['target'], str(self.target))
        self.assertEqual(binding['sha256'], sha(self.payload))
        self.assertEqual(binding['fields'], [['adapter'], ['entrypoint'], ['invoke', 1]])
        self.assertEqual(self.index.read_bytes(), before)
        self.assertFalse(Path(self.original).exists())
        self.assertEqual(audit(self.state)['records'][0]['proposals'], [])

    def test_newly_commissioned_name_is_only_compared_when_selected(self):
        self.row['name'] = 'Portable local captioner'
        self.store([self.row])
        self.assertEqual(len(self.plan()['proposals']), 1)
        report = audit(self.state, release_id=self.release_id, reference=self.before,
                       reference_sha256=sha(self.before.read_bytes()))
        self.assertEqual(report['records'][0]['proposals'], [])

    def test_nested_commands_and_paths_with_spaces(self):
        absent = str(self.state / 'missing helper')
        self.store([{'name': 'nested', 'commands': {'one': ['python', absent]},
                     'mcp': {'invoke': ['python', absent], 'documentation': '/historical'},
                     'linux_backend': {'support': absent}, 'args': [str(self.index.parent)],
                     'limits': [absent], 'checks': '/old-check'},
                    {'name': 'remote connection', 'native_mcp': 'endpoint'}])
        a, b = audit(self.state)['records']
        self.assertEqual(a['absolute_components'], 2)
        self.assertEqual(a['missing'], [{'path': absent, 'fields': [
            ['commands', 'one', 1], ['linux_backend', 'support'], ['mcp', 'invoke', 1]]}])
        self.assertEqual(b['absolute_components'], 0)

    def test_requires_separate_pinned_reference(self):
        for path, reference_hash in [(self.before, '0' * 64),
                                     (self.index, sha(self.index.read_bytes()))]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                audit(self.state, release_id=self.release_id, reference=path,
                      reference_sha256=reference_hash)
        with self.assertRaises(ValueError):
            audit(self.state, release_id='../another-release')

    def test_changed_scope_and_disabled_or_unreviewed_rows_get_no_proposals(self):
        updated = dict(self.row, readiness='New restriction')
        self.index.write_text(json.dumps([updated]))
        self.assertEqual(self.plan()['proposals'], [])
        for change in ({'callable': False}, {'runtime_accepted': False},
                       {'adapter_sha256': '0' * 64},
                       {'entrypoint_sha256': ''}, {'entrypoint_sha256': '0' * 64}):
            with self.subTest(change=change):
                self.store([{**self.row, **change}])
                self.assertEqual(self.plan()['proposals'], [])

    def test_type_changing_policy_is_not_the_same_original_record(self):
        self.store([{**self.row, 'provider_calls': 0}])
        self.index.write_text(json.dumps([{**self.row, 'provider_calls': False}]))
        self.assertEqual(self.plan()['proposals'], [])

    def test_current_bytes_and_seal_must_match_original(self):
        self.target.write_bytes(b'different')
        self.assertEqual(self.plan()['proposals'], [])
        self.target.write_bytes(self.payload)
        self.seal.write_text('{}')
        self.assertEqual(self.plan()['proposals'], [])

    def test_redirected_replacement_and_old_dangling_link_are_not_rebound(self):
        real = self.state / 'elsewhere'
        self.target.rename(real)
        self.target.symlink_to(real)
        self.assertEqual(self.plan()['proposals'], [])
        self.target.unlink()
        real.rename(self.target)
        parent = Path(self.original).parent
        parent.mkdir(parents=True)
        Path(self.original).symlink_to(parent / 'absent')
        self.assertEqual(self.plan()['proposals'], [])

    def test_preserves_ambiguous_or_redirected_indexes(self):
        self.index.write_text('[{"name":"alpha","invoke":[],"invoke":["other"]}]')
        with self.assertRaises(ValueError):
            audit(self.state)
        self.index.write_text(json.dumps([self.row, copy.deepcopy(self.row)]))
        with self.assertRaises(ValueError):
            audit(self.state)
        self.index.unlink()
        self.index.symlink_to(self.before)
        with self.assertRaises((ValueError, OSError)):
            audit(self.state)


if __name__ == '__main__':
    unittest.main()
