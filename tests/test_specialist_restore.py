"""Restore the new specialist sources without the author's home or runtimes."""
from pathlib import Path
import contextlib, io, json, sys, tempfile, unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
import native_setup as native
import install

NAMES=('ui-design-hallmark','pixel-art-effects','design-specification-workflow',
       'presentation-visual-design','iphone-mirroring-automation',
       'agent-ui-streaming','typed-graph-workflows',
       'causal-and-temporal-validation','computational-photonics-verification','production-observability-release','quantum-error-correction','signal-and-control-verification')

class SpecialistRestore(unittest.TestCase):
    def test_staged_source_restores_all_specialist_files_and_methods(self):
        with tempfile.TemporaryDirectory(prefix='nstack-source-restore-') as tmp:
            state=Path(tmp)/'state'
            with patch.object(native.nstack,'STATE',state):
                code=install.stage(state)
                release,index=native.prepare(state,[],list(NAMES))
            self.assertEqual({r['name'] for r in index},set(NAMES))
            for name in NAMES:
                original=ROOT/'addons'/name
                for p in original.rglob('*'):
                    if not p.is_file() or '__pycache__' in p.parts:continue
                    rel=p.relative_to(original)
                    self.assertEqual((code/'addons'/name/rel).read_bytes(),p.read_bytes(),str(rel))
                row=next(r for r in index if r['name']==name)
                self.assertEqual(Path(row['skill_path']).read_bytes(),(original/'SKILL.md').read_bytes())
                self.assertEqual(len(list((release/'bundles'/name).rglob('SKILL.md'))),1)
            self.assertEqual(native.tree(release),json.loads((release/'NATIVE-MANIFEST.json').read_text())['files'])

    def test_cli_duplicate_user_owned_skill_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix='nstack-duplicate-') as tmp:
            home=Path(tmp)/'home';state=Path(tmp)/'state'
            user=home/'.codex/skills'/NAMES[0];user.mkdir(parents=True)
            body=b'user-owned original\n';(user/'SKILL.md').write_bytes(body)
            argv=['native_setup.py','install','--home',str(home),'--state',str(state),
                  '--extra-skill',NAMES[0]]
            with patch.object(sys,'argv',argv),patch.object(native,'selection',return_value=[]),patch.object(native.nstack,'STATE',state):
                err=io.StringIO()
                with self.assertRaises(SystemExit) as raised:
                    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(err):native.main()
                self.assertEqual(raised.exception.code,1)
                self.assertIn('already exists',err.getvalue())
            self.assertEqual((user/'SKILL.md').read_bytes(),body)
            self.assertFalse((home/'.agents/skills').exists())

if __name__=='__main__':unittest.main()
