"""Exact source archives, fresh read-only generations and explicit native prerequisites."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'integrations/research/source-runtime'
spec = importlib.util.spec_from_file_location('research_source_runtime', HERE/'runtime.py')
runtime = importlib.util.module_from_spec(spec)
old = sys.dont_write_bytecode; sys.dont_write_bytecode = True
try: spec.loader.exec_module(runtime)
finally: sys.dont_write_bytecode = old


def archive(root, entries):
    target = root/'source.tar'
    members, files = [], {}
    with tarfile.open(target, 'w', format=tarfile.USTAR_FORMAT) as tar:
        for name, raw, kind in entries:
            row = tarfile.TarInfo(name); row.mode = 0o755 if kind == 'directory' else 0o644
            row.type = tarfile.DIRTYPE if kind == 'directory' else tarfile.SYMTYPE if kind == 'symlink' else tarfile.REGTYPE
            row.size = len(raw) if kind == 'file' else 0
            if kind == 'symlink': row.linkname = '/outside'
            tar.addfile(row, io.BytesIO(raw) if kind == 'file' else None)
            record = {'path':name,'type':kind,'mode':row.mode,'size':row.size}
            if kind == 'file':
                record['sha256'] = hashlib.sha256(raw).hexdigest()
                files[name] = {key:record[key] for key in ('mode','size','sha256')}
            members.append(record)
    specification = {'archive_sha256':runtime.sha(target),'archive_bytes':target.stat().st_size,
        'members':members,'files':files,'revision':'fixture-revision'}
    return target, specification


class SourceRuntime(unittest.TestCase):
    def test_recipe_closed_and_private_paths_binary_outputs_absent(self):
        runtime.verify_recipe()
        for path in HERE.rglob('*'):
            if path.is_file():
                self.assertNotIn(path.suffix, ('.whl','.deb','.tar','.so','.pyc'))
                data = path.read_bytes()
                self.assertNotIn(b'/Users/', data)
                self.assertNotIn(b'/private/tmp/', data)

    def test_exact_upstream_file_counts_and_patch_preimages(self):
        self.assertEqual(len(runtime.read(HERE/'manifests/shinka.json')['files']),361)
        ais = runtime.read(HERE/'manifests/ai-scientist.json')
        self.assertEqual(len(ais['files']),575)
        patches = runtime.read(HERE.parent/'codex-transport/patches/manifest.json')
        self.assertEqual(len(patches['files']),11)
        self.assertEqual(ais['revision'],patches['commit'])
        for row in patches['files']:
            self.assertEqual(ais['files'][row['path']]['sha256'],row['original_sha256'])
        for relative, digest in runtime.read(HERE/'manifests/patch-support.json')['files'].items():
            self.assertEqual(runtime.sha(HERE.parent/relative),digest)

    def test_unsafe_archive_paths_links_duplicates_and_content_drift_rejected(self):
        for entries in ([('../outside',b'bad','file')],[('/absolute',b'bad','file')],
                [('link',b'','symlink')],[('same',b'a','file'),('same',b'b','file')]):
            with tempfile.TemporaryDirectory() as temporary:
                file, specification = archive(Path(temporary),entries)
                with self.assertRaises(ValueError): runtime.archive_entries(file,specification)
        with tempfile.TemporaryDirectory() as temporary:
            file, specification = archive(Path(temporary),[('safe',b'original','file')])
            self.assertEqual(runtime.archive_entries(file,specification),{'safe':b'original'})
            specification['files']['safe']['size'] += 1
            with self.assertRaises(ValueError): runtime.archive_entries(file,specification)
            specification['archive_sha256'] = '0'*64
            with self.assertRaises(ValueError): runtime.archive_entries(file,specification)

    def test_inert_source_prepare_preserves_original_and_detects_later_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); recipe = root/'recipe'; (recipe/'manifests').mkdir(parents=True)
            (recipe/'RECIPE.json').write_text('{}')
            file, specification = archive(root,[('pkg',b'','directory'),('pkg/source.py',b'raise RuntimeError("must never execute")\n','file')])
            (recipe/'manifests/shinka.json').write_text(json.dumps(specification))
            pin = {'revision':'fixture-revision','archive_sha256':specification['archive_sha256']}
            (recipe/'PINS.json').write_text(json.dumps({'shinka':pin}))
            state = root/'state'
            with patch.object(runtime,'HERE',recipe),patch.object(runtime,'verify_recipe'), \
                    patch.object(runtime.subprocess,'run',side_effect=AssertionError('No target execution')):
                result = runtime.prepare_source('shinka',file,state)
                self.assertEqual(result['state'],'source-prepared-readonly')
                self.assertEqual(runtime.sha(state/'original.tar'),runtime.sha(file))
                runtime.verify_source(state,'shinka')
                with self.assertRaises(ValueError): runtime.prepare_source('shinka',file,state)
                source = state/'source/pkg/source.py'
                self.assertEqual(source.stat().st_mode & 0o777,0o444)
                source.chmod(0o644)
                with self.assertRaises(ValueError): runtime.verify_source(state,'shinka')
                source.chmod(0o444)
                (state/'source').chmod(0o755); (state/'source/extra').mkdir(); (state/'source/extra').chmod(0o555); (state/'source').chmod(0o555)
                with self.assertRaises(ValueError): runtime.verify_source(state,'shinka')

    def test_missing_reviewed_bash_stops_before_applier_import_or_execution(self):
        with patch.object(runtime.subprocess,'run',side_effect=AssertionError('No shell fallback')):
            with self.assertRaises((ValueError,OSError)): runtime.patcher('/missing/gnu-bash')

    def test_all_shinka_mandatory_dependencies_and_bootstrap_stay_pinned(self):
        dependencies = runtime.read(HERE/'manifests/shinka-dependencies.json')
        self.assertEqual(dependencies['mandatory_roots'],26)
        self.assertEqual(dependencies['resolved_dependencies'],101)
        self.assertEqual(len(dependencies['wheels']),103)
        ordinary = [r for r in dependencies['wheels'] if not r['input_path'].startswith('build-tools/')]
        bootstrap = [r for r in dependencies['wheels'] if r['input_path'].startswith('build-tools/')]
        self.assertEqual(len(ordinary),101)
        self.assertEqual({r['name'] for r in bootstrap},{'setuptools','wheel'})
        lock=(HERE/'runtime-exact.lock').read_text()
        for row in ordinary:
            self.assertIn(f"{row['name']}=={row['version']} --hash=sha256:{row['sha256']}",lock)
        for name in ('openai','anthropic','boto3','google-genai'):
            self.assertIn(name.lower(),{r['name'].lower() for r in ordinary})
        self.assertEqual(dependencies['source_built_antlr']['wheel_sha256'],
            'c9f8f85b5b2f8123ed285abf77261b5a9ca197c514590b3da7fddd2ebfc14295')

    def test_native_profile_denies_network_and_account_reads(self):
        profile = runtime.native_profile(Path('/synthetic/home'))
        self.assertIn('(deny network*)',profile)
        for path in ('.codex','.ssh','.aws','.docker','Library/Keychains','.netrc'):
            self.assertIn('/synthetic/home/'+path,profile)
        with patch.object(runtime,'verify_source',return_value=Path('/source')), \
                patch.object(runtime.platform,'system',return_value='Linux'), \
                patch.object(runtime.subprocess,'run',side_effect=AssertionError('No platform fallback')):
            with self.assertRaises(ValueError): runtime.prepare_shinka('/source-state','/artifacts','/python','/new')


if __name__ == '__main__': unittest.main()
