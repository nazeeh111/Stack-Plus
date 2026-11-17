"""Build the pinned Remotion closures offline and replay their routing adaptation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from closure import links
from patch_media import REMOTION_ROUTER, finalize_remotion_router
from skill_build import materialize


PIN = '682cad29c569d7c36c2445e27ec07cb433f06b32'
SOURCE = Path(os.environ.get('NSTACK_TEST_P226_SOURCE', str(
    Path.home() / 'Library/Application Support/nstack/sources/remotion-dev--remotion' / PIN)))
ROUTED = {'remotion-best-practices', 'remotion-create', 'remotion-markup', 'remotion-captions', 'remotion-docs'}
TARGETS = ('../remotion-multimedia/SKILL.md', '../remotion-markup/timing-props.md',
           '../remotion-markup/cropping.md')


class RemotionRouting(unittest.TestCase):
    @unittest.skipUnless((SOURCE / '.nstack-source.json').is_file(), 'exact offline P226 source required')
    def test_pinned_closures_and_replay(self):
        registry = json.loads((ROOT / 'registry/manifest.json').read_text())
        specs = [s for s in registry['skills'] if s['candidate_id'] == 'P226']
        component = next(c for c in registry['components'] if c['id'] == 'P226')
        original = (SOURCE / REMOTION_ROUTER).read_bytes()
        routed = set()
        with tempfile.TemporaryDirectory() as tmp:
            for spec in specs:
                leaf = Path(spec['source_path']).parent.name
                with self.subTest(leaf=leaf):
                    self.assertEqual(spec['revision'], PIN)
                    out = Path(tmp) / leaf
                    out.mkdir()
                    materialize(SOURCE, out, spec, component, registry)
                    router = out / REMOTION_ROUTER
                    record = out / 'NATIVE-REMOTION-ROUTING'
                    if leaf not in ROUTED:
                        self.assertFalse(router.exists())
                        self.assertFalse(record.exists())
                        continue
                    routed.add(leaf)
                    data = router.read_bytes()
                    self.assertNotIn(b'such as trimming, cropping videos', data)
                    for target in TARGETS:
                        self.assertIn(target, list(links(router)))
                        self.assertTrue((router.parent / target).is_file())
                    meta = json.loads((record / 'SOURCE-ADAPTATION.json').read_text())
                    self.assertEqual(meta['revision'], PIN)
                    self.assertEqual(meta['path'], str(REMOTION_ROUTER))
                    self.assertEqual((out / meta['original']).read_bytes(), original)
                    self.assertEqual(meta['upstream_sha256'], hashlib.sha256(original).hexdigest())
                    self.assertEqual(meta['materialized_sha256'], hashlib.sha256(data).hexdigest())
                    self.assertEqual(list(record.rglob('SKILL.md')), [])
                    with tempfile.TemporaryDirectory() as replay:
                        copy = Path(replay) / REMOTION_ROUTER
                        copy.parent.mkdir(parents=True)
                        copy.write_bytes(original)
                        subprocess.run(['patch', '-s', '-p1', '-i', str(record / 'ADAPTATION.patch')],
                                       cwd=replay, check=True, stdin=subprocess.DEVNULL)
                        self.assertEqual(copy.read_bytes(), data)
        self.assertEqual(routed, ROUTED)
        self.assertEqual((SOURCE / REMOTION_ROUTER).read_bytes(), original)

    @unittest.skipUnless((SOURCE / '.nstack-source.json').is_file(), 'exact offline P226 source required')
    def test_rejects_changed_upstream_and_duplicate_or_missing_handoff(self):
        spec = {'candidate_id': 'P226', 'revision': PIN, 'source_repository': 'remotion-dev/remotion'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / 'source'
            out = root / 'bundle'
            raw = src / REMOTION_ROUTER
            raw.parent.mkdir(parents=True)
            active = out / REMOTION_ROUTER
            active.parent.mkdir(parents=True)
            shutil.copyfile(SOURCE / REMOTION_ROUTER, raw)
            line = next(line for line in raw.read_text().splitlines(True) if 'such as trimming, cropping' in line)
            for count in (0, 2):
                with self.subTest(occurrences=count):
                    preimage = 'intro\n' + line.replace('(./', '(../') * count
                    active.write_text(preimage)
                    with self.assertRaisesRegex(ValueError, 'exactly one'):
                        finalize_remotion_router(src, out, spec)
                    self.assertEqual(active.read_text(), preimage)
                    self.assertFalse((out / 'NATIVE-REMOTION-ROUTING').exists())
            raw.write_text(raw.read_text() + 'source drift\n')
            with self.assertRaisesRegex(ValueError, 'Pinned Remotion router changed'):
                finalize_remotion_router(src, out, spec)
            self.assertFalse((out / 'NATIVE-REMOTION-ROUTING').exists())

    def test_unrelated_mirrored_build(self):
        # Exercise the same materializer and closure step under a different candidate.
        spec = {'candidate_id': 'P094', 'source_path': 'skills/example/SKILL.md',
                'source_repository': 'fixture/n8n', 'revision': '1' * 40,
                'delivery': 'narrow-patched leaf'}
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            entry = source / spec['source_path']
            entry.parent.mkdir(parents=True)
            entry.write_text('---\nname: example\ndescription: n8n fixture\n---\nA workflow.\n')
            (source / 'LICENSE').write_text('Fixture notice\n')
            out = Path(tmp) / 'bundle'
            out.mkdir()
            materialize(source, out, spec, {}, {'skills': [spec]})
            self.assertIn('nstack runtime acceptance', (out / spec['source_path']).read_text())
            self.assertFalse((out / 'NATIVE-REMOTION-ROUTING').exists())
            self.assertFalse((out / REMOTION_ROUTER).exists())


if __name__ == '__main__':
    unittest.main()
