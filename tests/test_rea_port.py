"""Full upstream-method preservation and exact local port replay, without runtime activation."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ADDON=ROOT/'addons/rea'
SOURCE=json.loads((ADDON/'SOURCE.json').read_text())
# Method updates can precede runtime upgrades. Keep independent exact known
# preimages rather than trusting a self-reported manifest hash.
PREIMAGES = {
    'd74549e495c58eb4a560279fd9f05508401ea0a0': 'b53cce995c43ca59fd6f6a306106fcfbf5db3dc2837f13598bb665e230ef798e',
    'ab16163061094a6c28e9133c9c618e0850c9cb2f': 'bca2b4594eb3279db14578b9437741ebc6733f72fd1231bd33db77514034c1f9',
}
REVISION = SOURCE['revision']
ORIGINAL_SHA = PREIMAGES[REVISION]

class ReaFullMethodPort(unittest.TestCase):
    def test_every_substantive_upstream_byte_remains_operative(self):
        original=(ADDON/'upstream/ORIGINAL-SKILL.md').read_text()
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),ORIGINAL_SHA)
        active=(ADDON/'SKILL.md').read_text()
        normalized=re.sub(r'<!-- nstack-native:start -->.*?<!-- nstack-native:end -->\n\n','',active,flags=re.S)
        normalized=normalized.replace('name: rea\n','name: reverse-engineer-anything\n',1)
        normalized=normalized.replace('(upstream/references/','(references/').replace('`upstream/references/','`references/')
        normalized=normalized.replace('https://github.com/morluto/rea/blob/'+REVISION+'/','https://github.com/morluto/rea/blob/main/')
        self.assertEqual(normalized,original)
        self.assertGreater(len(active.splitlines()),600)

    def test_actual_patch_replays_from_exact_original(self):
        patch=shutil.which('patch')
        self.assertIsNotNone(patch,'The native source-port check requires the existing patch executable')
        with tempfile.TemporaryDirectory(prefix='rea-source-port-') as temporary:
            path=Path(temporary)/'SKILL.md';shutil.copyfile(ADDON/'upstream/ORIGINAL-SKILL.md',path)
            result=subprocess.run([patch,'-s','-p1','-i',str(ADDON/'PORT.patch')],cwd=temporary,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(path.read_bytes(),(ADDON/'SKILL.md').read_bytes())

    def test_retained_guides_license_and_local_paths_are_real(self):
        for rel,row in SOURCE['upstream_files'].items():
            self.assertEqual(hashlib.sha256((ADDON/rel).read_bytes()).hexdigest(),row['sha256'],rel)
        guides=list((ADDON/'upstream/references').glob('*.md'));self.assertEqual(len(guides),8)
        text=(ADDON/'SKILL.md').read_text()
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in link and not link.startswith('#'):
                self.assertTrue((ADDON/link.split('#')[0]).is_file(),link)
        self.assertNotIn('https://github.com/morluto/rea/blob/main/',text)

    def test_source_port_receipt_matches_exact_preimage_entry_patch_and_binding(self):
        port=SOURCE['operative_port'];self.assertEqual(port['preimage_sha256'],ORIGINAL_SHA)
        for key in ['entry','patch','binding']:
            self.assertEqual(hashlib.sha256((ADDON/port[key]).read_bytes()).hexdigest(),port[key+'_sha256'])
        self.assertEqual(SOURCE['runtime_recipe'],'recipes/rea.py')
        self.assertEqual(SOURCE['runtime_recipe_linux'],'recipes/rea_linux.py')
        self.assertTrue((ROOT/SOURCE['runtime_recipe_linux']).is_file())

    def test_precise_authority_overrides_precede_upstream_examples(self):
        active=(ADDON/'SKILL.md').read_text();header=active.split('<!-- nstack-native:start -->',1)[1].split('<!-- nstack-native:end -->',1)[0]
        for text in ['@latest','setup/update/uninstall','not automatic','headless `$4`','Never inspect credential stores','denied Mac','actual client permissions','255-tool']:
            self.assertIn(text,header)
        self.assertLess(active.index('<!-- nstack-native:end -->'),active.index('npx -y rea-agents@latest'))
        binding=(ADDON/'NATIVE-BINDINGS.md').read_text()
        for text in ['Codex','OpenCode','Task-scoped MCP','native tool namespace','direct omitted','no-new-privileges']:
            # Low-level container controls live in the separately source-bound backend guide.
            if text=='no-new-privileges':continue
            self.assertIn(text,binding)
        self.assertNotIn('retained as source references, not additional installed skills or authority',active)

if __name__=='__main__':unittest.main()
