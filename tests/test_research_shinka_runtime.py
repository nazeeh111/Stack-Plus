"""No-model contract checks for the original Shinka CLI binding."""
import argparse
import importlib.util
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/'integrations/research'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class ShinkaBindingTests(unittest.TestCase):
    def test_evaluator_refuses_duplicate_and_symlink_escape(self):
        evaluator=load('research_shinka_evaluator',ROOT/'shinka_evaluator.py')
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw).resolve();results=root/'results';results.mkdir()
            script=root/'evaluate.py';script.write_text('# unchanged evaluator')
            program=results/'program.py';program.write_text('# candidate')
            m={'results':str(results),'evaluator':str(script)}
            argv=[str(script),'--program_path',str(program),'--results_dir',str(results/'gen0')]
            self.assertEqual(evaluator.targets(argv,m)[1],program)
            with self.assertRaises(ValueError):evaluator.targets(argv+['--program_path',str(program)],m)
            outside=root/'outside.py';outside.write_text('# private')
            program.unlink();program.symlink_to(outside)
            with self.assertRaises(ValueError):evaluator.targets(argv,m)

    def test_original_cli_authority_overrides_and_private_control(self):
        launch=load('research_shinka_launch',ROOT/'shinka.py')
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw).resolve();task=root/'task';task.mkdir();(task/'evaluate.py').write_text('# evaluator')
            source=root/'source';source.mkdir();receipts=root/'receipts';receipts.mkdir()
            python=root/'venv/bin/python';python.parent.mkdir(parents=True);python.touch()
            client=root/'codex';client.touch()
            manifest={'workspace':task,'read_roots':[task],'write_roots':[],
                      'deny_roots':[],'receipt_dir':receipts,'context_reference':root/'context.json',
                      '_manifest_path':root/'manifest.json'}
            modules={'nstack_shinka_source':types.SimpleNamespace(verify_source=lambda *_:source),
                     'nstack_shinka_client':types.SimpleNamespace(discover=lambda *_:client),
                     'nstack_shinka_transport':types.SimpleNamespace(load_manifest=lambda *_:manifest,
                         current_context=lambda *_:{},clean_environment=lambda:{'PATH':'/usr/bin:/bin'})}
            args=argparse.Namespace(source_state=root,python=python,codex=str(client),manifest=root/'manifest.json',
                task_dir=task,results_dir=task/'results',state=root/'private',num_generations=3,eval_time='00:01:30',
                set=['evo.llm_models=["paid-provider"]','job.python_executable=/unsafe'])
            with patch.object(launch,'module',side_effect=lambda name,_:modules[name]),patch.object(launch.subprocess,'run') as run:
                argv,env,evaluation,_,_=launch.command(args)
                settings=[argv[i+1] for i,x in enumerate(argv[:-1]) if x=='--set']
                self.assertEqual([x for x in settings if x.startswith('evo.llm_models=')][-1],'evo.llm_models=["headless/codex"]')
                self.assertIn('job.python_executable="'+str(root/'private/evaluate')+'"',settings)
                self.assertIn('runpy.run_module(\'shinka.cli.run\'',argv[4])
                self.assertIn(str(root/'manifest.json'),evaluation['deny_roots'])
                self.assertEqual(run.call_count,1) # metadata version probe only
                args.results_dir=root/'outside-results'
                with self.assertRaises(ValueError):launch.command(args)
                args.results_dir=task/'results'
                args.state.symlink_to(root/'missing-private',target_is_directory=True)
                with self.assertRaises(ValueError):launch.command(args)
                args.state.unlink()
                args.state=task/'private'
                with self.assertRaises(ValueError):launch.command(args)
                args.state=root/'private';(task/'.env').touch()
                with self.assertRaises(ValueError):launch.command(args)

if __name__=='__main__':unittest.main()
