"""Source/method closure and portable selection, without research/provider activation."""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# Independently frozen from the reviewed Git pins, not derived from the receipt.
EXPECTED = {
    'shinka-evolve': {
        'repository': 'SakanaAI/ShinkaEvolve',
        'revision': '7ab55d7254d2732b26d9c30dde23ab777de631cb',
        'identity': '6b1ac3824daea05a35a270bcda67790ae5998dd30f34de9cfd895c9d002c4002',
        'license': 'c3e5b1c26607caf7208d5a105c113fe240630bb873fdb8ca5b4c2e32c721ddaf',
        'methods': {'shinka-setup', 'shinka-convert', 'shinka-run', 'shinka-inspect'},
        'files': 9,
        'executables': set(),
    },
    'ai-scientist': {
        'repository': 'SakanaAI/AI-Scientist-v3',
        'revision': 'df8313889a004f8a44a472e19a833cd547bb828a',
        'identity': '2139dd3eec0455f3a03eb97a0b2b6eb5303077927ce973af130374c72dc112cd',
        'license': '420f6e94d4266a7628735be654b7a99ead74976feb9e99f50bd834d92d03b6e5',
        'methods': {'draft-task', 'create-idea', 'edit-program', 'evaluate-program', 'verify-rubrics',
                    'memory-log', 'scientific-evidence', 'retrieve-references', 'write-paper',
                    'write-paper-standalone', 'validate-paper', 'review-paper', 'generate-concept-figure'},
        'files': 62,
        'executables': {'src/agents/skills/memory-log/scripts/append_memory.py',
                        'src/agents/skills/retrieve-references/scripts/s2_fetch.py',
                        'src/agents/skills/retrieve-references/scripts/scholarly_fetch.py',
                        'src/agents/skills/scientific-evidence/scripts/scientific_evidence.py',
                        'src/agents/skills/scientific-evidence/scripts/scientific_evidence.sh',
                        'src/agents/skills/validate-paper/scripts/compile_latex.sh',
                        'src/agents/skills/validate-paper/scripts/validate_tex_refs.py',
                        'src/agents/skills/write-paper/scripts/validate_claims.py',
                        'src/agents/skills/write-paper-standalone/scripts/validate_claims.py'},
    },
}
LPPL_SHA = 'c1ae6e179a6d28bbd5c483fbacc744acc75e922d598281dc3390aab26126e163'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(root, name):
    expected = EXPECTED[name]
    meta = json.loads((root / 'SOURCE.json').read_text())
    assert (meta['repository'], meta['revision']) == (expected['repository'], expected['revision'])
    assert meta['license'] == 'Apache-2.0'
    assert sha((root / 'LICENSE').read_bytes()) == meta['license_source_sha256'] == expected['license']
    assert len(meta['upstream_files']) == expected['files']
    adapted = {r['active_path']: r for r in meta['adapted_files']}
    actual_identity = {}
    for relative, row in meta['upstream_files'].items():
        file = root / relative
        assert file.is_file() and not file.is_symlink(), relative
        assert sha(file.read_bytes()) == row['sha256'], relative
        assert bool(file.stat().st_mode & 0o111) == row['source_executable'], relative
        assert row['source_executable'] == (row['source_path'] in expected['executables']), relative
        original = root / adapted[relative]['original'] if relative in adapted else file
        assert sha(original.read_bytes()) == row['source_sha256'], relative
        assert row['source_path'] not in actual_identity
        actual_identity[row['source_path']] = sha(original.read_bytes())
    identity = sha(json.dumps(actual_identity, sort_keys=True, separators=(',', ':')).encode())
    assert identity == meta['source_path_hashes_sha256'] == expected['identity']
    methods = {p.parent.name for p in (root / 'methods').rglob('METHOD.md')}
    assert methods == expected['methods']
    assert [p.relative_to(root).as_posix() for p in root.rglob('SKILL.md')] == ['SKILL.md']
    extras = {'SKILL.md', 'SOURCE.json', 'NATIVE-BINDINGS.md', 'LICENSE'}
    if name == 'ai-scientist':
        extras |= {'LICENSE-LPPL-1.3c.txt', 'THIRD-PARTY-NOTICES.md'}
        assert sha((root / 'LICENSE-LPPL-1.3c.txt').read_bytes()) == LPPL_SHA
        assert meta['additional_license_files']['LICENSE-LPPL-1.3c.txt']['sha256'] == LPPL_SHA
    for row in adapted.values():
        extras |= {row['original'], row['diff']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(meta['upstream_files']) | extras
    assert not any(p.is_symlink() for p in root.rglob('*'))
    assert meta['runtime_guide'] == 'integrations/research/README.md'
    assert '/Users/' not in json.dumps(meta) and '/private/tmp/' not in json.dumps(meta)
    return meta


class ResearchMethods(unittest.TestCase):
    def test_complete_shinka_methods_companions_and_source_rights(self):
        verify(ROOT / 'addons/shinka-evolve', 'shinka-evolve')

    def test_complete_scientist_methods_pipeline_support_and_component_notices(self):
        root = ROOT / 'addons/ai-scientist'
        verify(root, 'ai-scientist')
        self.assertIn('LaTeX Project Public License', (root / 'methods/src/agents/skills/write-paper/templates/iclr/paper.bst').read_text())
        # The validator's original sibling evidence-verifier resolution remains real.
        writer = root / 'methods/src/agents/skills/write-paper/scripts/validate_claims.py'
        verifier = writer.parent.parent.parent / 'scientific-evidence/scripts/scientific_evidence.py'
        self.assertTrue(verifier.is_file())

    def test_paper_link_corrections_replay_from_exact_originals(self):
        root = ROOT / 'addons/shinka-evolve'
        meta = verify(root, 'shinka-evolve')
        self.assertEqual(len(meta['adapted_files']), 2)
        patch = shutil.which('patch')
        self.assertIsNotNone(patch, 'Existing patch executable required for exact port replay')
        for row in meta['adapted_files']:
            source = (root / row['original']).read_text()
            active = (root / row['active_path']).read_text()
            self.assertEqual(active.replace('https://arxiv.org/abs/2509.19349', 'https://arxiv.org/abs/2212.04180'), source)
            expected = ''.join(difflib.unified_diff(source.splitlines(True), active.splitlines(True),
                                                 fromfile=row['source_path'], tofile=row['active_path']))
            self.assertEqual((root / row['diff']).read_text(), expected)
            with tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'method.md'; target.write_text(source)
                result = subprocess.run([patch, '-s', str(target), str(root / row['diff'])],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(target.read_text(), active)

    def test_active_links_and_doc_support_resolve_within_each_bundle(self):
        for name in EXPECTED:
            root = ROOT / 'addons' / name
            for file in root.rglob('*.md'):
                for target in re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)]+)\)', file.read_text()):
                    if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:|#', target):
                        continue
                    relative = target.split('#', 1)[0]
                    if relative:
                        resolved = (file.parent / relative).resolve()
                        self.assertTrue(resolved.is_relative_to(root.resolve()), (file, target))
                        self.assertTrue(resolved.is_file(), (file, target))

    def test_actual_portable_selection_keeps_every_method_companion_and_license(self):
        spec = importlib.util.spec_from_file_location('research_method_installer', ROOT / 'install.py')
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        # Enumeration only: never stage mutable research code or change a profile.
        selected = {str(rel): file for file, rel in installer.portable_files()}
        for name in EXPECTED:
            root = ROOT / 'addons' / name
            verify(root, name)
            for file in root.rglob('*'):
                if file.is_file():
                    relative = str(file.relative_to(ROOT))
                    self.assertIn(relative, selected)
                    self.assertEqual(selected[relative].read_bytes(), file.read_bytes())

    def test_missing_or_altered_companion_cannot_claim_complete_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'addon'; shutil.copytree(ROOT / 'addons/ai-scientist', root)
            target = root / 'methods/src/agents/skills/scientific-evidence/scripts/scientific_evidence.py'
            raw = target.read_bytes(); target.unlink()
            with self.assertRaises(AssertionError): verify(root, 'ai-scientist')
            target.write_bytes(raw + b'\n# unreviewed change\n')
            with self.assertRaises(AssertionError): verify(root, 'ai-scientist')


if __name__ == '__main__': unittest.main()
