import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base/'project'
        self.project.mkdir()
        self.env = dict(os.environ, HOME=str(self.base/'home'), CODEX_HOME=str(self.base/'profile'),
                        NSTACK_STATE=str(self.base/'state'), PYTHONDONTWRITEBYTECODE='1')
        self.cli = ROOT/'stack+'

    def invoke(self, *args, ok=True):
        result = subprocess.run([str(self.cli),*args],cwd=self.project,env=self.env,
                                text=True,capture_output=True,timeout=60)
        self.assertEqual(result.returncode==0, ok, (result.stdout,result.stderr))
        return result.stdout

    def stub_opencode(self):
        bin_dir=self.base/'bin'
        bin_dir.mkdir(exist_ok=True)
        path=bin_dir/'opencode'
        (self.base/'home/.config/opencode').mkdir(parents=True,exist_ok=True)
        path.write_text('#!'+sys.executable+'\n'+'''import json,os,sys
from pathlib import Path
home=Path(os.environ["HOME"])
if sys.argv[1:]==["debug","paths"]:
    print("home",home)
    print("config",home/".config/opencode")
else:
    action=sys.argv[2]
    agents=[{"id":"build","mode":"primary","permissions":[]}]
    values={"config.get":[{"info":{}}],"agent.list":agents,"agent.get":agents[0],"skill.list":[]}
    print(json.dumps({"data":values[action]}))
''')
        path.chmod(0o755)
        self.env['PATH']=str(bin_dir)+os.pathsep+self.env['PATH']

    def test_project_support_and_explicit_gate(self):
        self.stub_opencode()
        root = self.project/'.agents/skills'
        skill = root/'opal'
        (skill/'references').mkdir(parents=True)
        (skill/'SKILL.md').write_text('---\nname: opal\ndescription: Analyse a table.\n---\nApply the selected method.\n')
        ref = skill/'references/measurement.md'
        ref.write_text('Use the coherence interval to validate these measurements.\n')
        secret = self.base/'outside.md'
        secret.write_text('externalguardword')
        (skill/'references/private-link.md').symlink_to(secret)
        args = ['find','--host','opencode','--eligible',str(skill/'SKILL.md')]
        found, = json.loads(self.invoke(*args,'--json','coherence'))
        self.assertEqual(Path(found['path']), ref)
        self.assertIn('Apply the selected method.',self.invoke(*args,'--read',found['match_id']))
        self.assertEqual(json.loads(self.invoke(*args,'--json','externalguardword')),[])
        ref.write_text('A different coherence interval.\n')
        self.invoke(*args,'--read',found['match_id'],ok=False)
        (skill/'agents').mkdir()
        (skill/'agents/openai.yaml').write_text('policy:\n  allow_implicit_invocation: false\n')
        self.assertEqual(json.loads(self.invoke(*args,'--json','coherence')),[])
        self.assertTrue(json.loads(self.invoke(*args,'--bundle','opal','--explicit','--json','coherence')))

    @unittest.skipUnless(os.environ.get('STACKPLUS_NATIVE_CHECKS')=='1' and shutil.which('codex'),
                         'set STACKPLUS_NATIVE_CHECKS=1 to query a native Codex test profile')
    def test_native_library_policy_and_override(self):
        name = 'design-specification-workflow'
        self.env['XDG_DATA_HOME'] = str(self.base/'data')
        home, profile = Path(self.env['HOME']), Path(self.env['CODEX_HOME'])
        home.mkdir()
        profile.mkdir()
        config = profile/'config.toml'
        trust = f'[projects.{json.dumps(str(self.project))}]\ntrust_level="trusted"\n'
        config.write_text(trust)
        subprocess.run(['git','init','-q',self.project],check=True)
        local_config = self.project/'.codex/config.toml'
        local_config.parent.mkdir()
        local_config.write_text('[[skills.config]]\nname="some-other-skill"\nenabled=false\n')
        shelf = self.base/'data/stackplus/library'
        shelf.mkdir(parents=True)
        self.invoke('selections','--stage',name,str(shelf/name))
        options = ['find','--bundle',name]
        rows = json.loads(self.invoke(*options,'--json','drift'))
        self.assertTrue(rows)
        hit = rows[0]
        self.assertEqual(hit['scope'],'on-demand')
        self.assertIn('design-specification-workflow',self.invoke(*options,'--read',hit['match_id']))
        denied = f'[[skills.config]]\nname="{name}"\nenabled=false\n'
        config.write_text(trust+denied)
        self.assertEqual(json.loads(self.invoke(*options,'--json','drift')),[])
        self.invoke(*options,'--read',hit['match_id'],ok=False)
        config.write_text(trust)
        local_config.write_text(denied)
        self.assertEqual(json.loads(self.invoke(*options,'--json','drift')),[])
        local_config.write_text('')
        override=self.project/'.agents/skills'/name
        override.mkdir(parents=True)
        (override/'SKILL.md').write_text(f'---\nname: {name}\ndescription: local override\n---\nnewword\n')
        self.assertEqual(json.loads(self.invoke(*options,'--json','drift')),[])
        self.assertEqual(json.loads(self.invoke(*options,'--json','newword'))[0]['scope'],'project')

    @unittest.skipUnless(os.environ.get('STACKPLUS_PCBA_CHECKOUT'), 'supply the pinned public plugin checkout')
    def test_staged_pcba_referenced_support(self):
        self.stub_opencode()
        name='review-pcba-package'
        parent=self.project/'selected-pcba'
        self.invoke('selections','--stage',name,str(parent),'--source-checkout',os.environ['STACKPLUS_PCBA_CHECKOUT'])
        alias=self.project/'.agents/skills'/name
        alias.parent.mkdir(parents=True)
        alias.symlink_to(parent/'bundle/skills'/name,target_is_directory=True)
        allowed=(alias/'SKILL.md').resolve()
        with_scope=['find','--host','opencode','--eligible',str(allowed)]
        hit,=json.loads(self.invoke(*with_scope,'--json','authoritativePlacements'))
        self.assertTrue(hit['path'].endswith('/pcba-engineering/references/workflow.md'))
        self.assertEqual(hit['scope'],'project')
        detail=self.invoke(*with_scope,'--read',hit['match_id'])
        self.assertIn('Review a PCBA package',detail)
        self.assertIn('authoritativePlacements',detail)
        Path(hit['path']).write_text('changed technique')
        self.invoke(*with_scope,'--read',hit['match_id'],ok=False)

    def test_pinned_inputs_and_drift(self):
        artifact=self.project/'result.txt'
        artifact.write_text('first\n')
        p=self.invoke('review','pack','--artifact','result.txt').strip()
        self.assertEqual(self.invoke('review','show',p,'--file','result.txt'),'first\n')
        self.invoke('review','verify',p,'--current')
        artifact.write_text('second\n')
        self.invoke('review','verify',p,'--current',ok=False)
        self.assertEqual(self.invoke('review','show',p,'--file','result.txt'),'first\n')
        outside=self.base/'outside'
        outside.write_text('excluded')
        (self.project/'external').symlink_to(outside)
        self.invoke('review','pack','--artifact','external',ok=False)
        child=self.invoke('review','pack','--parent',p,'--artifact','result.txt').strip()
        self.assertEqual(json.loads(self.invoke('review','verify',child))['ancestors'],1)

    def test_only_01_native_install(self):
        home=self.base/'home'
        result=subprocess.run([sys.executable,'-B',str(ROOT/'native_setup.py'),'install','--only','01',
                               '--home',str(home),'--codex-home',str(home/'.codex'),'--state',str(self.base/'state')],
                              cwd=self.base,env=self.env,text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        skills=home/'.agents/skills'
        self.assertEqual([p.name for p in skills.iterdir()],['01'])
        self.assertIn('Stack+', (skills/'01/SKILL.md').read_text())
        self.assertTrue((skills/'01/scripts/project_find.py').is_file())


if __name__ == '__main__':
    unittest.main()
