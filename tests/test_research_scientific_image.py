"""Frozen source/closure, inert preparation and no fallback at dependency boundaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'integrations/research/scientific-image'
spec = importlib.util.spec_from_file_location('scientific_image', HERE / 'runtime.py')
runtime = importlib.util.module_from_spec(spec)
old_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    spec.loader.exec_module(runtime)
finally:
    sys.dont_write_bytecode = old_bytecode


class ScientificImage(unittest.TestCase):
    def test_recipe_is_closed_and_contains_no_binary_or_private_machine_files(self):
        pins, context = runtime.verify_recipe()
        self.assertNotEqual(context['sha256'], pins['historical_acceptance']['context_sha256'])
        self.assertEqual(len([p for p in context['files'] if p.startswith('debs/')]), 115)
        self.assertEqual(len([p for p in context['files'] if p.startswith('wheelhouse/')]), 79)
        for file in HERE.rglob('*'):
            if file.is_file():
                self.assertNotIn(file.suffix, ('.whl', '.deb', '.so', '.pyc'))
                text = file.read_bytes()
                self.assertNotIn(b'/Users/', text)
                self.assertNotIn(b'/private/tmp/', text)

    def test_original_source_roots_and_python_closure_stay_exact(self):
        import tomllib
        source = tomllib.loads((HERE/'source/pyproject.toml').read_text())
        self.assertEqual(len(source['project']['dependencies']), 12)
        wheels = runtime.read(HERE/'manifests/wheels.json')
        self.assertEqual(len(wheels['selected']), 77)
        self.assertEqual(len(wheels['bootstrap']), 2)
        self.assertEqual({r['name'] for r in wheels['bootstrap']}, {'setuptools', 'wheel'})
        self.assertEqual(sum(r['size'] for r in wheels['selected']), 129187043)
        for row in wheels['selected'] + wheels['bootstrap']:
            target = 'wheelhouse/' + row['filename']
            self.assertEqual(runtime.read(HERE/'manifests/context.json')['files'][target], row['sha256'])
        built = [r for r in wheels['selected'] if 'upstream_sdist' in r]
        self.assertEqual({r['name'] for r in built}, {'antlr4-python3-runtime', 'bibtexparser'})
        self.assertTrue(all('url' not in r for r in built))

    def test_antlr_actual_license_and_original_installer_are_retained(self):
        notice = HERE/'context/notices/source-notices/antlr4-python3-runtime/PROJECT-LICENSE.txt'
        self.assertEqual(runtime.sha(notice), 'b1b379fcaf3219593a4c433feb1b35c780bed23fafaae440b1ae2771a9521e3a')
        self.assertEqual(runtime.sha(HERE/'context/Dockerfile'), 'd5b72f2d7bf481992eb6d5d6bfd28b0727be412b670cc9708c1081feae64a520')
        dockerfile = (HERE/'context/Dockerfile').read_text()
        self.assertIn('dpkg -i /opt/offline-debs/*.deb', dockerfile)
        for forbidden in ('--force', '--ignore', 'apt-get update', 'pip install -U'):
            self.assertNotIn(forbidden, dockerfile)

    def test_local_artifact_drift_and_extras_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); file = root/'file'; file.write_text('exact')
            frozen = runtime.inventory(root)
            runtime.exact(root, frozen)
            file.write_text('changed')
            with self.assertRaises(ValueError): runtime.exact(root, frozen)
            file.write_text('exact'); (root/'extra').write_text('extra')
            with self.assertRaises(ValueError): runtime.exact(root, frozen)
            (root/'extra').unlink(); (root/'link').symlink_to(file)
            with self.assertRaises(ValueError): runtime.exact(root, frozen)

    def test_prepare_is_inert_preserves_existing_state_and_pins_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); recipe = root/'recipe'; recipe.mkdir()
            (recipe/'context').mkdir(); (recipe/'context/config').write_text('recipe')
            (recipe/'fixtures').mkdir(); (recipe/'fixtures/check.py').write_text('fixture')
            (recipe/'RECIPE.json').write_text('{}')
            (recipe/'manifests').mkdir()
            artifacts = root/'artifacts'; (artifacts/'wheelhouse').mkdir(parents=True)
            (artifacts/'wheelhouse/test.whl').write_bytes(b'inert fake fixture')
            (artifacts/'metadata').mkdir(); (artifacts/'metadata/InRelease').write_text('inert signature fixture')
            inputs = {'artifacts': {'wheelhouse/test.whl': runtime.sha(artifacts/'wheelhouse/test.whl')},
                      'metadata': {'InRelease': {'sha256': runtime.sha(artifacts/'metadata/InRelease')}}}
            (recipe/'manifests/inputs.json').write_text(json.dumps(inputs))
            context = {'sha256': 'synthetic-generation', 'files': {
                'config': runtime.sha(recipe/'context/config'), **inputs['artifacts']}}
            (recipe/'manifests/context.json').write_text(json.dumps(context))
            state = root/'state'
            with patch.object(runtime, 'HERE', recipe), patch.object(runtime, 'verify_recipe', return_value=({}, context)), \
                    patch.object(runtime.subprocess, 'run', side_effect=AssertionError('prepare must not execute')):
                self.assertEqual(runtime.prepare(artifacts, state)['state'], 'prepared-inert')
                runtime.verify_state(state)
                with self.assertRaises(ValueError): runtime.prepare(artifacts, state)
                self.assertEqual((state/'context/wheelhouse/test.whl').read_bytes(), b'inert fake fixture')
                (state/'OWNER.json').write_text('{}')
                with self.assertRaises(ValueError): runtime.verify_state(state)

    def test_offline_closure_parser_rejects_removal_or_unexpected_records(self):
        self.assertEqual(runtime.closure_versions('Inst a [0] (1 local-deb [arm64])\nInst b (2 local-deb [all])'), {'a':'1','b':'2'})
        for text in ('Remv a [1]', 'Inst unexpected-format', 'Inst a (1 x)\nInst a (2 x)'):
            with self.assertRaises(ValueError): runtime.closure_versions(text)

    def test_base_drift_stops_before_execution(self):
        base = runtime.read(HERE/'PINS.json')['base']
        runtime.assert_base(base, base)
        for key in ('Id', 'Architecture', 'Os', 'RootFS', 'RepoDigests'):
            changed = {**base, key: None}
            with self.assertRaises((ValueError, TypeError)): runtime.assert_base(changed, base)
        with patch.object(runtime.subprocess, 'run', side_effect=AssertionError('mutable image must not run')):
            with self.assertRaises(ValueError): runtime.check('/missing', 'mutable:tag', None)

    def test_original_fixture_hashes_and_native_scope(self):
        # Template files are frozen exact upstream source, not a generated paper.
        provenance = runtime.read(HERE/'manifests/source-support.json')
        for relative, digest in provenance['files'].items():
            self.assertEqual(runtime.sha(HERE/relative), digest)
        core = (HERE/'fixtures/core.py').read_text()
        self.assertIn('python-expected.json', core)
        self.assertIn('np.linalg.solve', core)
        self.assertIn('distutils-precedence.pth', core)
        compiler = (HERE/'fixtures/compile.sh').read_text()
        self.assertEqual(compiler.count('pdflatex -recorder -no-shell-escape'), 3)
        self.assertIn('bibtex paper', compiler)


if __name__ == '__main__': unittest.main()
