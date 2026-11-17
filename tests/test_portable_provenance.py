"""Keep declared upstream originals without admitting unrelated hidden state."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import install
import native_setup as native

ROOT = Path(__file__).resolve().parents[1]


class PortableProvenance(unittest.TestCase):
    def fixture(self, root):
        addon = root/'addons/fixture'
        original = addon/'upstream/.claude/skills/example/SKILL.md'
        original.parent.mkdir(parents=True)
        original.write_text('Full original source, never a live host skill.\n')
        manifest = addon/'SOURCE.json'
        manifest.write_text(json.dumps({'upstream_files': {
            'upstream/.claude/skills/example/SKILL.md': {
                'source_path': '.claude/skills/example/SKILL.md',
                'sha256': hashlib.sha256(original.read_bytes()).hexdigest()}}}))
        return addon, original, manifest

    def test_declared_original_is_portable_and_other_hidden_files_stay_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); addon, original, _ = self.fixture(root)
            hidden = addon/'upstream/.claude/unreviewed.txt'; hidden.write_text('unreviewed')
            (root/'.env').write_text('fixture only')
            with patch.object(install, 'ROOT', root):
                files = {str(rel) for _, rel in install.portable_files()}
            self.assertIn(str(original.relative_to(root)), files)
            self.assertNotIn(str(hidden.relative_to(root)), files)
            self.assertNotIn('.env', files)

    def test_reserved_private_and_vcs_paths_never_become_portable_by_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); addon, _, manifest=self.fixture(root)
            data=json.loads(manifest.read_text())
            for part in ('.git', 'private', '__pycache__', 'node_modules'):
                file=addon/'upstream'/part/'fixture.txt';file.parent.mkdir();file.write_text('not portable')
                data['upstream_files'][str(file.relative_to(addon))]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
            manifest.write_text(json.dumps(data))
            with patch.object(install,'ROOT',root):
                files={str(rel) for _,rel in install.portable_files()}
            self.assertFalse(any('/'+part+'/' in rel for part in ('.git','private','__pycache__','node_modules') for rel in files))

    def test_changed_declared_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,original,_=self.fixture(root);original.write_text('drift')
            with patch.object(install,'ROOT',root), self.assertRaisesRegex(ValueError,'provenance changed'):
                list(install.portable_files())

    def test_declared_link_is_rejected_without_reading_its_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,original,_=self.fixture(root)
            original.unlink();original.symlink_to(root/'missing-target')
            with patch.object(install,'ROOT',root), self.assertRaisesRegex(ValueError,'linked files'):
                list(install.portable_files())

    def test_actual_game_archives_and_native_identity_survive_portable_stage(self):
        # The regression was source-native prepare != staged-CODE-native prepare.
        with tempfile.TemporaryDirectory(prefix='nstack-provenance-stage-',dir='/private/tmp') as tmp:
            state=Path(tmp)
            with patch.object(install,'ROOT',ROOT):
                code=install.stage(state)
            receipt=json.loads((ROOT/'addons/game-systems-review/SOURCE.json').read_text())
            for relative,row in receipt['upstream_files'].items():
                self.assertEqual(hashlib.sha256((code/'addons/game-systems-review'/relative).read_bytes()).hexdigest(),row['sha256'])
            with patch.object(native,'ROOT',ROOT):
                original_release,original_index=native.prepare(state,[],['game-systems-review'])
            with patch.object(native,'ROOT',code):
                staged_release,staged_index=native.prepare(state,[],['game-systems-review'])
            self.assertEqual(staged_release,original_release)
            self.assertEqual(staged_index,original_index)
            self.assertFalse((state/'native-profile.json').exists())


if __name__=='__main__':unittest.main()
