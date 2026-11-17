"""Agent Desktop source fidelity and inert native packaging; never run its CLI."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native
import skill_names

ADDON = ROOT / 'addons/agent-desktop'
PIN = 'b0b7277bea09b770ef9d1fb45aad667bc432cd57'
UPSTREAM_IDENTITY = 'dcf9cde54a766b823a914d90931a30510a7087d59972c48e3773e88f193ea9e4'
PREFACE = (
    '> Native adaptation, 2026-11-15: scope and invocation guidance adapted for the shared toolkit. '
    'Read [native bindings](NATIVE-BINDINGS.md) first, then the complete upstream method below. '
    'Original source, unchanged support and replayable diff are recorded in [SOURCE.json](SOURCE.json).\n\n'
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class AgentDesktopAddon(unittest.TestCase):
    def test_complete_pinned_source_closure_and_notice(self):
        receipt = json.loads((ADDON / 'SOURCE.json').read_text())
        self.assertEqual(receipt['repository'], 'vercel-labs/agent-desktop')
        self.assertEqual(receipt['revision'], PIN)
        self.assertEqual(receipt['release'], 'v1.3.1')
        self.assertEqual(receipt['license'], 'Apache-2.0')
        upstream = receipt['upstream_files']
        self.assertEqual(len(upstream), 20)
        source_identity = {row['source_path']: row['sha256'] for row in upstream.values()}
        self.assertEqual(sha(json.dumps(source_identity, sort_keys=True, separators=(',', ':')).encode()),
                         UPSTREAM_IDENTITY)
        for relative, row in upstream.items():
            self.assertEqual(sha((ADDON / relative).read_bytes()), row['sha256'], relative)
        expected_counts = {'references': 4, 'platforms/macos': 2,
                           'platforms/linux': 7, 'platforms/windows': 5}
        for relative, count in expected_counts.items():
            self.assertEqual(len(list((ADDON / relative).rglob('*.md'))), count, relative)
        self.assertIn('Apache License\n', (ADDON / 'upstream/LICENSE').read_text())
        self.assertIn('Version 2.0, January 2004', (ADDON / 'upstream/LICENSE').read_text())
        self.assertIn('Native adaptation, 2026-11-15', (ADDON / 'SKILL.md').read_text())
        self.assertNotIn('/Users/', json.dumps(receipt))
        self.assertNotIn('/private/tmp/', json.dumps(receipt))

    def test_upstream_method_and_exact_adaptation_replay(self):
        original = (ADDON / 'upstream/ORIGINAL-SKILL.md').read_text()
        active = (ADDON / 'SKILL.md').read_text()
        self.assertEqual(original.split('\n# agent-desktop\n', 1)[1],
                         active.split('\n# agent-desktop\n', 1)[1].replace('\n' + PREFACE, '\n', 1))
        self.assertTrue(active.startswith('---\nname: agent-desktop\n'))
        self.assertIn('when the user selects\n  this CLI', active)
        self.assertIn('Read its native\n  admission and platform guide first', active)
        expected = ''.join(difflib.unified_diff(original.splitlines(keepends=True),
                                               active.splitlines(keepends=True),
                                               fromfile='a/SKILL.md', tofile='b/SKILL.md'))
        self.assertEqual((ADDON / 'adaptations/SKILL.md.diff').read_text(), expected)
        row = json.loads((ADDON / 'SOURCE.json').read_text())['adapted_files'][0]
        self.assertEqual(row['source_sha256'], sha(original.encode()))
        self.assertEqual(row['active_sha256'], sha(active.encode()))
        with tempfile.TemporaryDirectory(prefix='agent-desktop-source-replay-', dir='/private/tmp') as tmp:
            (Path(tmp) / 'SKILL.md').write_text(original)
            result = subprocess.run(['git', 'apply', '--check', str(ADDON / row['diff'])],
                                    cwd=tmp, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run(['git', 'apply', str(ADDON / row['diff'])], cwd=tmp,
                           check=True, capture_output=True, timeout=10)
            self.assertEqual((Path(tmp) / 'SKILL.md').read_bytes(), (ADDON / 'SKILL.md').read_bytes())

    def test_one_entry_name_and_supported_local_references(self):
        self.assertEqual({str(p.relative_to(ADDON)) for p in ADDON.rglob('SKILL.md')}, {'SKILL.md'})
        self.assertFalse(any(p.is_symlink() for p in ADDON.rglob('*')))
        self.assertEqual(skill_names.canonical('agent-desktop'), 'agent-desktop')
        self.assertNotIn('agent-desktop', {name for name, _ in native.selection()})
        for path in ADDON.rglob('*.md'):
            if path.is_relative_to(ADDON / 'upstream'):
                continue
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                resolved = (path.parent / unquote(target.split('#', 1)[0])).resolve()
                self.assertTrue(resolved.is_relative_to(ADDON.resolve()), (path, target))
                self.assertTrue(resolved.is_file(), (path, target))

    def test_native_packaging_preserves_bytes_without_installing_runtime(self):
        spec = native.addon_definition('agent-desktop')
        frozen = native.addon_files(spec)
        expected = {str(p.relative_to(ADDON)): p.read_bytes()
                    for p in ADDON.rglob('*') if p.is_file()}
        self.assertEqual(set(frozen), set(expected))
        for path, raw in expected.items():
            self.assertEqual(frozen[path], (raw, 0o444), path)
        rows = native.index_rows([], {'agent-desktop': spec}, Path('/detached/native-generation'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'agent-desktop')
        self.assertEqual(rows[0]['revision'], PIN)
        self.assertEqual(rows[0]['skill_path'],
                         '/detached/native-generation/bundles/agent-desktop/SKILL.md')
        # Documentation discovery does not create an executable invocation or claim readiness.
        for key in ['command', 'entrypoint', 'runtime_recipe', 'readiness']:
            self.assertNotIn(key, rows[0])

    def test_actual_detached_native_prepare_accepts_root_license_and_seals_method_only(self):
        # Exercise the real license gate and tree verifier in disposable state.
        # This never changes a shared profile or executes Agent Desktop.
        self.assertEqual((ADDON / 'LICENSE').read_bytes(), (ADDON / 'upstream/LICENSE').read_bytes())
        with tempfile.TemporaryDirectory(prefix='agent-desktop-native-prepare-', dir='/private/tmp') as tmp:
            state = Path(tmp)
            release, index = native.prepare(state, [], ['agent-desktop'])
            self.assertEqual([row['name'] for row in index], ['agent-desktop'])
            self.assertEqual((release / 'bundles/agent-desktop/LICENSE').read_bytes(),
                             (ADDON / 'upstream/LICENSE').read_bytes())
            self.assertTrue((release / 'NATIVE-MANIFEST.json').is_file())
            self.assertFalse((state / 'native-profile.json').exists())
            self.assertFalse((state / 'native-tools').exists())

    def test_binding_controls_before_unadmitted_upstream_invocations(self):
        active = (ADDON / 'SKILL.md').read_text()
        self.assertLess(active.index('Read [native bindings]'), active.index('## First run'))
        binding = (ADDON / 'NATIVE-BINDINGS.md').read_text()
        for required in ['Gatekeeper assessment', 'rejects each with exit 3',
                         'Neither was executed', 'before parsing even `version`, `--help` or',
                         'environment buffers', 'SIGKILL', 'Do not run them while runtime admission is',
                         'Do not patch, rebuild, re-sign, remove quarantine',
                         'a grant or successful test from another host does not transfer',
                         'observe before repeating or substituting an action']:
            self.assertIn(required, binding)
        for forbidden in ['xattr -d', 'spctl --add', 'codesign --force', 'tccutil reset']:
            self.assertNotIn(forbidden, binding)
        self.assertIn('No runtime, grant or profile activation.',
                      json.loads((ADDON / 'SOURCE.json').read_text())['adaptation'])


if __name__ == '__main__':
    unittest.main()
