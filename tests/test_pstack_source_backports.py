"""Source-backed statechart diagnostic/layout regression checks, without acquisition."""
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
from patch_native34 import materialize
from patch_pstack import STATECHART_BACKPORTS, statechart_backport


class PstackSourceBackports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT / 'registry/manifest.json').read_text())
        cls.component = next(c for c in manifest['components'] if c['id'] == 'P028')
        cls.spec = next(s for s in manifest['skills'] if s.get('native_name') == 'pstack-statechart')
        cls.source = Path.home() / 'Library/Application Support/nstack/sources/cursor--plugins' / cls.spec['revision']
        cls.scripts = cls.source / 'harness/pstack/claude-code/skills/statechart/scripts'
        if not cls.scripts.is_dir():
            raise unittest.SkipTest('Pinned offline source absent; no acquisition')
        cls.node = shutil.which('node')
        if cls.node is None:
            raise unittest.SkipTest('Existing TypeScript-capable Node absent; no acquisition')
        cls.temporary = tempfile.TemporaryDirectory(prefix='pstack-backport-')
        cls.out = Path(cls.temporary.name) / 'materialized'
        cls.entry = cls.out / materialize(cls.source, cls.out, cls.spec, cls.component)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_exact_backport_refuses_source_drift_and_matches_reviewed_target(self):
        for relative, receipt in STATECHART_BACKPORTS.items():
            raw = (self.scripts / relative).read_text()
            with self.subTest(relative=relative):
                self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), receipt['before_sha256'])
                changed = statechart_backport(raw, relative)
                self.assertEqual(hashlib.sha256(changed.encode()).hexdigest(), receipt['after_sha256'])
                with self.assertRaisesRegex(ValueError, 'statechart preimage changed'):
                    statechart_backport(raw + '// unreviewed source drift\n', relative)
                with self.assertRaisesRegex(ValueError, 'statechart preimage changed'):
                    statechart_backport(changed, relative)

    def test_three_operative_copies_agree_and_all_originals_and_diffs_replay(self):
        # This is output/provenance equivalence, not a test of generated wording.
        bases = [self.entry]
        for kind in ('create', 'maintain'):
            addon = ROOT / 'addons' / ('pstack-' + kind + '-formal-verification')
            bases.append(addon / 'support/statechart')
            receipt = json.loads((addon / 'SOURCE.json').read_text())
            for rel in ('run.ts', 'backends/mermaid.ts'):
                active = 'support/statechart/scripts/' + rel
                item = next(x for x in receipt['adapted_files'] if x['active_path'] == active)
                raw = (addon / item['original_path']).read_bytes()
                self.assertEqual(raw, (self.scripts / rel).read_bytes())
                with tempfile.TemporaryDirectory(prefix='pstack-replay-') as temp:
                    target = Path(temp) / active
                    target.parent.mkdir(parents=True)
                    target.write_bytes(raw)
                    subprocess.run(['git', 'apply', '--check', str(addon / item['diff'])], cwd=temp, check=True, capture_output=True)
                    subprocess.run(['git', 'apply', str(addon / item['diff'])], cwd=temp, check=True, capture_output=True)
                    self.assertEqual(target.read_bytes(), (addon / active).read_bytes())
        for relative in ('run.ts', 'backends/mermaid.ts'):
            contents = [(base / 'scripts' / relative).read_bytes() for base in bases]
            self.assertTrue(all(data == contents[0] for data in contents))
        # Bootstrap and the TLC search flags remain the existing native choices.
        active = (self.entry / 'scripts/run.ts').read_text()
        self.assertNotIn('const mise =', active)
        self.assertIn('["-workers", "1", "-fp", "0", "-lncheck", "final"]', active)
        self.assertNotIn('"-dfid"', active)

    def node_json(self, code):
        result = subprocess.run([self.node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True, timeout=20)
        return json.loads(result.stdout)

    def test_parent_entry_preserves_branch_labels_without_false_merge(self):
        module = (self.entry / 'scripts/backends/mermaid.ts').as_uri()
        payload = self.node_json('import { drawnEdges } from ' + json.dumps(module) + ';' + r"""
const state = (path, start=false) => ({path, start, breaks: [], works: true});
const step = (from,to,label) => ({from,to,label});
const single = {name:'Flow',states:[state(['Ask'],true),state(['Layout','Flat']),state(['Layout','Parents'])],steps:[step(['Ask'],['Layout','Flat'],'String'),step(['Ask'],['Layout','Parents'],'Array')]};
const multiple = {name:'Flow',states:[state(['A'],true),state(['B']),state(['P','p']),state(['P','q'])],steps:[step(['A'],['P','p'],'Left'),step(['B'],['P','q'],'Right')]};
console.log(JSON.stringify({single:drawnEdges(single),multiple:drawnEdges(multiple)}));
""")
        self.assertIn({'from':['Ask'],'start':False,'to':['Layout']}, payload['single'])
        self.assertIn({'from':['Layout'],'start':True,'to':['Layout','Flat'],'label':'String'}, payload['single'])
        self.assertIn({'from':['Layout'],'start':True,'to':['Layout','Parents'],'label':'Array'}, payload['single'])
        self.assertIn({'from':['A'],'start':False,'to':['P','p'],'label':'Left'}, payload['multiple'])
        self.assertIn({'from':['B'],'start':False,'to':['P','q'],'label':'Right'}, payload['multiple'])
        self.assertFalse(any(e['to'] == ['P'] for e in payload['multiple']))

    def test_real_sany_failure_names_the_unknown_operator_and_remains_error(self):
        jar = Path(os.environ.get('TLA2TOOLS', str(Path.home() / 'Library/Application Support/nstack/native-tools/tlc/1.7.4/tla2tools.jar')))
        java = os.environ.get('JAVA') or shutil.which('java')
        if not jar.is_file() or java is None:
            self.skipTest('Existing Java/TLC absent; no acquisition')
        with tempfile.TemporaryDirectory(prefix='pstack-sany-') as temp:
            folder = Path(temp)
            spec = folder / 'Bad.tla'
            spec.write_text("---- MODULE Bad ----\nEXTENDS Naturals\nVARIABLE x\nInit == x = 0\nNext == x' = x + 1\nBroken == MissingIdentifier\n====\n")
            spec.with_suffix('.cfg').write_text('INIT Init\nNEXT Next\nINVARIANT Broken\n')
            result = subprocess.run([self.node, str(self.entry / 'scripts/statechart.ts'), str(spec), '--out', str(folder / 'result')], env=dict(os.environ, JAVA=java, TLA2TOOLS=str(jar)), capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Unknown operator', result.stderr)
            self.assertIn('MissingIdentifier', result.stderr)
            self.assertIn('line 6', result.stderr)
            self.assertFalse((folder / 'result/chart.mmd').exists())


if __name__ == '__main__':
    unittest.main()
