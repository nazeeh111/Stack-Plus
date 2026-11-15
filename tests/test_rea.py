"""Pinned distribution admission and meaningful offline-route negative controls."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rea_recipe', ROOT / 'recipes/rea.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReaRecipe(unittest.TestCase):
    def archive(self, path, rows):
        with tarfile.open(path, 'w:gz') as stream:
            for name, data, link in rows:
                member = tarfile.TarInfo(name)
                if link is not None:
                    member.type = tarfile.SYMTYPE
                    member.linkname = link
                    stream.addfile(member)
                else:
                    member.size = len(data)
                    member.mode = 0o644
                    stream.addfile(member, io.BytesIO(data))

    def test_archive_rejects_escape_duplicate_special_and_link_parent(self):
        cases = [
            [('package/../escape', b'x', None)],
            [('/package/absolute', b'x', None)],
            [('package/link', b'', '../../escape')],
            [('package/file', b'x', None), ('package/file', b'y', None)],
            [('package/link', b'', 'dir'), ('package/link/file', b'x', None)],
        ]
        for rows in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                self.archive(base / 'archive.tgz', rows)
                with self.assertRaises(ValueError):
                    m.safe_extract(base / 'archive.tgz', base / 'output', 'package')
                self.assertFalse((base / 'escape').exists())

    def test_internal_symlink_and_original_regular_bytes_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            self.archive(base / 'archive.tgz', [('node/lib/tool', b'original', None), ('node/bin/tool', b'', '../lib/tool')])
            m.safe_extract(base / 'archive.tgz', base / 'output', 'node')
            self.assertEqual((base / 'output/bin/tool').read_bytes(), b'original')
            self.assertEqual((base / 'output/bin/tool').readlink(), Path('../lib/tool'))

    def test_wrong_download_never_extracts_or_assesses(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            wrong = base / 'wrong'; wrong.write_bytes(b'not-upstream')
            with patch.object(m, 'host'), patch.object(m, 'safe_extract') as extract, patch.object(m, 'assess_node') as assess:
                with self.assertRaises(ValueError):
                    m.install(base / 'state', wrong, wrong)
                extract.assert_not_called(); assess.assert_not_called()
            self.assertFalse(m.runtime_root(base / 'state').exists())

    def test_manifest_pin_cannot_be_forged_in_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary).resolve()
            root = m.runtime_root(state)
            for folder in ('package', 'node'):
                (root / folder).mkdir(parents=True)
                (root / folder / 'file').write_text('original')
            package_hash = m.manifest_hash(m.manifest(root / 'package'))
            node_hash = m.manifest_hash(m.manifest(root / 'node'))
            saved = {'version': m.VERSION, 'revision': m.REVISION, 'package_sha256': m.PACKAGE_SHA256,
                     'node_version': m.NODE_VERSION, 'node_sha256': m.NODE_SHA256}
            m.write(root / 'SOURCE.json', saved)
            with patch.object(m, 'host'), patch.object(m, 'assess_node'), patch.object(m, 'PACKAGE_MANIFEST', package_hash), patch.object(m, 'NODE_MANIFEST', node_hash):
                m.verify(state)
                (root / 'package/file').write_text('changed')
                saved['package_manifest_sha256'] = m.manifest_hash(m.manifest(root / 'package'))
                m.write(root / 'SOURCE.json', saved)
                with self.assertRaises(ValueError):
                    m.verify(state)
            self.assertEqual((root / 'package/file').read_text(), 'changed')

    def test_native_signature_denial_has_no_execution_fallback(self):
        with patch.object(m, 'capture', return_value={'exit_code': 1, 'stdout': '', 'stderr': 'rejected'}) as capture:
            with self.assertRaises(ValueError):
                m.assess_node('/synthetic/node')
        self.assertEqual(capture.call_count, 1)
        self.assertEqual(capture.call_args.args[0][0], '/usr/bin/codesign')

    def test_environment_omits_ambient_provider_model_host_proxy(self):
        with patch.dict(m.os.environ, {'HOME': '/personal', 'CODEX_HOME': '/personal/.codex',
                                      'OPENAI_API_KEY': 'synthetic', 'HTTPS_PROXY': 'synthetic',
                                      'NODE_OPTIONS': '--require=/synthetic', 'REA_IDA_MCP_CONFIG': '/synthetic'}):
            env = m.environment('/private/owned/run')
        for name in ('CODEX_HOME', 'OPENAI_API_KEY', 'HTTPS_PROXY', 'NODE_OPTIONS', 'REA_IDA_MCP_CONFIG'):
            self.assertNotIn(name, env)
        self.assertEqual(env['HOME'], '/private/owned/run/home')
        self.assertEqual(env['REA_DARWIN_MODULE_CACHE_PATH'], '/private/owned/run/module-cache')
        self.assertEqual(env['NO_UPDATE_NOTIFIER'], '1')

    def test_unsupported_operation_never_verifies_or_executes(self):
        with patch.object(m, 'verify') as verify:
            for operation in ('setup', 'mcp', 'capture', 'update', 'install', 'rebuild'):
                with self.assertRaises(ValueError):
                    m.execute('/unused', '/unused', '/unused', operation)
            verify.assert_not_called()

    def test_foreign_output_and_runtime_overlap_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); source = base / 'source'; source.mkdir()
            out = base / 'foreign'; out.mkdir(); (out / 'keep').write_text('unrelated')
            with self.assertRaises(ValueError):
                m.own_output(out, source, 'identity', base / 'state', 'inspect')
            self.assertEqual(list(out.iterdir()), [out / 'keep'])
            self.assertEqual((out / 'keep').read_text(), 'unrelated')
            for out in (source / 'output', m.runtime_root(base / 'state') / 'output', base):
                with self.assertRaises(ValueError):
                    m.own_output(out, source, 'identity', base / 'state', 'inspect')

    def test_link_secret_and_size_limits_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); target = base / 'target'; target.mkdir()
            (target / 'main.js').write_text('fixture')
            (target / 'linked').symlink_to(target / 'main.js')
            with self.assertRaises(ValueError): m.approved_source(target)
            (target / 'linked').unlink()
            with patch.object(m, 'MAX_BYTES', 2):
                with self.assertRaises(ValueError): m.approved_source(target)
            secret = base / '.ssh'; secret.mkdir()
            with self.assertRaises(ValueError): m.approved_source(secret)

    def test_nested_sensitive_directory_refused_before_hashing(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve() / 'artifact'
            (target / '.ssh').mkdir(parents=True)
            (target / '.ssh/synthetic').write_text('synthetic-only')
            with patch.object(m, 'manifest') as manifest:
                with self.assertRaises(ValueError): m.approved_source(target)
                manifest.assert_not_called()

    def test_native_export_acceptance_requires_table_facts_and_hash(self):
        def document(format, positive):
            row = ({'name': 'nstack_answer', 'value': '0x1020', 'binding': 'global', 'type': 'function'} if format == 'elf' else
                   {'name': 'nstack_answer', 'address': '0x180002000', 'ordinal': 1, 'forwarder': None})
            return {'operation': 'inspect_native_exports', 'normalized_result': {'format': format,
                    'artifact': {'sha256': 'a' * 64}, 'coverage': {'status': 'complete', 'exports': int(positive)},
                    'issues': [], 'exports': [row] if positive else []}}
        for format in ('elf', 'pe'):
            for positive in (True, False):
                doc = document(format, positive)
                m.assert_native_fixture(doc, format, 'a' * 64, positive)
                with self.assertRaises(ValueError): m.assert_native_fixture(doc, format, 'b' * 64, positive)
            doc = document(format, True)
            doc['normalized_result']['exports'][0]['name'] = 'nstack_absent'
            doc['parameters'] = {'query': 'nstack_answer'}
            with self.assertRaises(ValueError): m.assert_native_fixture(doc, format, 'a' * 64, True)

    def test_native_fixture_negative_retains_name_bytes_but_changes_table(self):
        for format, magic in [('elf', b'\x7fELF'), ('pe', b'MZ')]:
            positive = m.native_fixture(format, True)
            negative = m.native_fixture(format, False)
            self.assertTrue(positive.startswith(magic))
            self.assertEqual(len(positive), len(negative))
            self.assertNotEqual(positive, negative)
            for raw in (positive, negative):
                self.assertIn(b'nstack_answer\0', raw)
                self.assertIn(b'nstack_absent\0', raw)

    def test_native_lane_accepts_regular_file_and_refuses_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            file = base / 'library'; file.write_bytes(m.native_fixture('elf'))
            self.assertEqual(m.approved_source(file, native=True)[1], m.digest(file))
            with self.assertRaises(ValueError): m.approved_source(base, native=True)

    def test_pins_match_recipe(self):
        pins = json.loads((ROOT / 'integrations/rea/PINS.json').read_text())
        self.assertEqual(pins['package_manifest_sha256'], m.PACKAGE_MANIFEST)
        self.assertEqual(pins['node_manifest_sha256'], m.NODE_MANIFEST)
        self.assertEqual(pins['revision'], m.REVISION)


if __name__ == '__main__':
    unittest.main()
