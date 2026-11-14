"""Language ports retain real pinned methods and reject source/input drift."""
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import academic_addon
import native_setup
import nstack
import install as profile_install
import patch_english as english
from closure import validate


class EnglishPorts(unittest.TestCase):
    def source(self, repository, revision):
        source = (pathlib.Path.home() / 'Library/Application Support/nstack/sources'
                  / repository.replace('/', '--') / revision)
        if not (source / '.nstack-source.json').is_file():
            self.skipTest('Reviewed offline source absent; no acquisition')
        return nstack.check_source(source)

    def test_real_pinned_builds_retain_originals_and_untouched_shot_library(self):
        manifest = json.loads((english.ASSETS / 'manifest.json').read_text())
        selections = {}
        for row in manifest['files']:
            if row.get('candidate_id'):
                selections[(row['candidate_id'], row['entry_source'])] = row
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(nstack, 'STATE', pathlib.Path(temp).resolve()), patch.object(nstack, 'acquire', side_effect=self.source):
                for (candidate, entry), row in selections.items():
                    with self.subTest(candidate=candidate):
                        built = nstack.build(candidate, entry)
                        nstack.registered_release(built)
                        validate(built)
                        fidelity = nstack.load(built / 'ENGLISH-PORT/SOURCE-FIDELITY.json')
                        source = self.source(row['repository'], row['revision'])
                        for item in fidelity['files']:
                            self.assertEqual((built / item['archival_upstream']).read_bytes(), (source / item['source_path']).read_bytes())
                            self.assertEqual(nstack.sha((built / item['target']).read_bytes()), item['active_sha256'])
                        if candidate == 'P224':
                            originals = {str(p.relative_to(source / 'references/shots')): p.read_bytes()
                                         for p in (source / 'references/shots').rglob('*.md')}
                            self.assertEqual(len(originals), 125)  # 124 cards and attribution.
                            self.assertEqual(originals, {str(p.relative_to(built / 'source/references/shots')): p.read_bytes()
                                                         for p in (built / 'source/references/shots').rglob('*.md')})

    def test_real_academic_overrides_keep_private_bilingual_guidance_and_guard_sources(self):
        source = self.source(academic_addon.REPOSITORY, academic_addon.REVISION)
        with patch.object(nstack, 'acquire', return_value=source):
            for name in academic_addon.DESCRIPTIONS:
                with self.subTest(name=name):
                    spec = academic_addon.definition(nstack, name)
                    files = native_setup.addon_files(spec)
                    self.assertEqual(files['shared/references/review_form_note.md'][0],
                                     (source / 'shared/references/review_form_note.md').read_bytes())
                    for item in json.loads(files['ENGLISH-PORT/SOURCE-FIDELITY.json'][0])['files']:
                        self.assertEqual(files[item['archival_upstream']][0], (source / item['source_path']).read_bytes())
                        self.assertEqual(nstack.sha(files[item['target']][0]), item['active_sha256'])
        row = english.rows(academic_addon.REPOSITORY, academic_addon.REVISION)[0]
        original = (source / row['source_path']).read_bytes()
        with self.assertRaisesRegex(ValueError, 'pinned source changed'):
            english.adapted(row, original + b'changed', original)

    def test_changed_operative_input_rejects_before_replacement(self):
        row = next(r for r in json.loads((english.ASSETS / 'manifest.json').read_text())['files']
                   if r.get('candidate_id') == 'P403')
        source = self.source(row['repository'], row['revision'])
        with self.assertRaisesRegex(ValueError, 'operative input changed'):
            english.adapted(row, (source / row['source_path']).read_bytes(), b'changed native input')

    def test_changed_replacement_anchor_rejects_even_with_verified_source(self):
        row = english.rows(academic_addon.REPOSITORY, academic_addon.REVISION)[0]
        source = self.source(row['repository'], row['revision'])
        original = (source / row['source_path']).read_bytes()
        span = json.loads((english.ASSETS / row['english']).read_text())
        span['replacements'][0]['old'] += 'stale anchor'
        with tempfile.TemporaryDirectory() as temp:
            assets = pathlib.Path(temp)
            file = assets / row['english']
            file.parent.mkdir(parents=True)
            file.write_text(json.dumps(span))
            with patch.object(english, 'ASSETS', assets):
                with self.assertRaisesRegex(ValueError, 'span changed'):
                    english.adapted(row, original, original)

    def test_every_english_asset_and_agent_support_edit_changes_build_identity(self):
        portable = {str(rel) for _, rel in profile_install.portable_files()}
        for asset in (ROOT / 'ports/english').rglob('*'):
            if asset.is_file():
                self.assertIn(str(asset.relative_to(ROOT)), portable)
        with tempfile.TemporaryDirectory() as temp:
            clone = pathlib.Path(temp)
            shutil.copy2(ROOT / 'nstack.py', clone / 'nstack.py')
            for directory in ['lib', 'ports/english', 'addons/agent-reach']:
                shutil.copytree(ROOT / directory, clone / directory, ignore=shutil.ignore_patterns('__pycache__'))
            assets = list((clone / 'ports/english').rglob('*'))
            assets += list((clone / 'addons/agent-reach/references').glob('*.md'))
            with patch.object(nstack, 'ROOT', clone):
                baseline = nstack.builder_identity()
                for asset in assets:
                    if not asset.is_file():
                        continue
                    raw = asset.read_bytes()
                    asset.write_bytes(raw + b'\n')
                    self.assertNotEqual(nstack.builder_identity(), baseline, str(asset))
                    asset.write_bytes(raw)
                self.assertEqual(nstack.builder_identity(), baseline)


if __name__ == '__main__':
    unittest.main()
