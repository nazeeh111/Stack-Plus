"""Cached code must remain a sealed local release before installer reuse."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
spec = importlib.util.spec_from_file_location('stage_integrity_install', ROOT / 'install.py')
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


class CachedCodeIntegrity(unittest.TestCase):
    def fixture(self, base):
        source = base / 'source'
        (source / 'lib').mkdir(parents=True)
        (source / 'main.py').write_text('print("local fixture")\n')
        (source / 'lib/guide.md').write_text('Supporting source.\n')
        (source / 'addons/tool').mkdir(parents=True)
        tool = source / 'addons/tool/run.sh'
        tool.write_text('#!/bin/sh\nexit 0\n')
        tool.chmod(0o755)
        return source

    def test_public_checkout_launcher_survives_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source = self.fixture(base)
            (source/'stack+').write_bytes((ROOT/'stack+').read_bytes())
            (source/'nstack.py').write_text('def main():\n    print("Staged Stack+")\n')
            with patch.object(install, 'ROOT', source):
                release = install.stage(base/'state')
                import subprocess
                self.assertEqual(subprocess.check_output([release/'stack+'],text=True).strip(),'Staged Stack+')
                self.assertEqual(install.stage(base/'state'),release)

    def test_normal_cached_repeat_preserves_release_and_seal(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            with patch.object(install, 'ROOT', self.fixture(base)):
                release = install.stage(base / 'state')
                before = install.fingerprint(release)
                self.assertEqual(install.stage(base / 'state'), release)
                self.assertEqual(install.fingerprint(release), before)
                expected = {str(rel): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path, rel in install.portable_files()}
                self.assertEqual(json.loads((release / 'INSTALL-MANIFEST.json').read_text()), expected)

    def test_invalid_cached_release_is_rejected_without_repairing_bytes(self):
        faults = ('root-link', 'file-link', 'directory-link', 'dangling-link',
                  'seal-link', 'missing-seal', 'changed-seal', 'malformed-seal',
                  'unexpected-nested-seal', 'corrupt-content', 'addon-mode')
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                with patch.object(install, 'ROOT', self.fixture(base)):
                    release = install.stage(base / 'state')
                    release.chmod(0o755)
                    seal = release / 'INSTALL-MANIFEST.json'
                    if fault == 'root-link':
                        outside = base / 'outside-release'
                        release.rename(outside)
                        release.symlink_to(outside, target_is_directory=True)
                    elif fault in ('file-link', 'seal-link'):
                        target = seal if fault == 'seal-link' else release / 'main.py'
                        outside = base / 'outside-file'
                        outside.write_bytes(target.read_bytes())
                        target.unlink()
                        target.symlink_to(outside)
                    elif fault == 'directory-link':
                        outside = base / 'outside-support'
                        (release / 'lib').chmod(0o755)
                        (release / 'lib').rename(outside)
                        (release / 'lib').symlink_to(outside, target_is_directory=True)
                    elif fault == 'dangling-link':
                        (release / 'main.py').unlink()
                        (release / 'main.py').symlink_to(base / 'absent')
                    elif fault == 'missing-seal':
                        seal.unlink()
                    elif fault in ('changed-seal', 'malformed-seal'):
                        seal.chmod(0o644)
                        seal.write_text('{}\n' if fault == 'changed-seal' else '{')
                    elif fault == 'unexpected-nested-seal':
                        (release / 'lib').chmod(0o755)
                        (release / 'lib/INSTALL-MANIFEST.json').write_text('{}\n')
                    elif fault == 'corrupt-content':
                        (release / 'main.py').chmod(0o644)
                        (release / 'main.py').write_text('changed\n')
                    else:
                        (release / 'addons/tool/run.sh').chmod(0o444)
                    before = install.fingerprint(base)
                    with self.assertRaises(ValueError):
                        install.stage(base / 'state')
                    self.assertEqual(install.fingerprint(base), before)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'requires a named-pipe filesystem')
    def test_special_cached_path_is_rejected_without_opening_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            with patch.object(install, 'ROOT', self.fixture(base)):
                release = install.stage(base / 'state')
                release.chmod(0o755)
                pipe = release / 'special.py'
                os.mkfifo(pipe)
                # Reading a FIFO could block. A content-reader trap makes that
                # mistake fail immediately and keeps this negative control bounded.
                original = Path.read_bytes
                def read(path):
                    if path == pipe:
                        self.fail('Cached special path reached the content reader')
                    return original(path)
                with patch.object(Path, 'read_bytes', read), self.assertRaises(ValueError):
                    install.stage(base / 'state')
                self.assertTrue(pipe.exists())


if __name__ == '__main__':
    unittest.main()
