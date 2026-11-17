#!/usr/bin/env python3
"""Launch the original pinned Shinka CLI through scoped native transport."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:spec.loader.exec_module(value)
    finally:sys.dont_write_bytecode=old
    return value


def command(args):
    preparation=module('nstack_shinka_source',HERE/'source-runtime/runtime.py')
    source=preparation.verify_source(args.source_state,'shinka')
    transport=module('nstack_shinka_transport',HERE/'codex-transport/transport.py')
    client_module=module('nstack_shinka_client',HERE/'codex_client.py')
    client=client_module.discover(args.codex)
    if client is None:raise ValueError('Reviewed existing Codex0.169.0 required; private client acquisition is separate')
    manifest=transport.load_manifest(args.manifest);transport.current_context(manifest['context_reference'])
    task=args.task_dir.resolve(strict=True);results=args.results_dir.resolve();state=args.state.resolve()
    if (task/'.env').exists() or (task/'.env').is_symlink():
        raise ValueError('Upstream imports launch-directory dotenv; use a clean task view without .env')
    if (task!=manifest['workspace'] or results.exists() or state.exists()
            or args.results_dir.is_symlink() or args.state.is_symlink()):
        raise ValueError('Task must equal declared workspace; preserve prior results/state')
    if not results.is_relative_to(task) or results==task:
        raise ValueError('Fresh results must be a descendant of the declared task workspace')
    if any(state.is_relative_to(root) or root.is_relative_to(state)
           for root in manifest['read_roots']+manifest['write_roots']):
        raise ValueError('Private run control must be outside all model permission roots')
    if any((task/'evaluate.py').is_relative_to(root) for root in manifest['write_roots']):
        raise ValueError('Original evaluator must stay outside model-writable roots')
    if state==task or state.is_relative_to(task) or task.is_relative_to(state):
        raise ValueError('Private evaluator/control state must be outside task workspace')
    if args.python.is_symlink():python=args.python.resolve(strict=True)
    else:python=args.python.absolute()
    # Use the venv entrypoint (including its normal symlink) for execution;
    # resolving it here is only for explicit base-interpreter read authority.
    executable=args.python.absolute()
    expected=json.loads((HERE/'source-runtime/manifests/shinka-dependencies.json').read_text())
    versions={row['name']:row['version'] for row in expected['wheels']}
    probe='import importlib.metadata,json; e=json.loads('+repr(json.dumps(versions))+'); assert all(importlib.metadata.version(k)==v for k,v in e.items()); print("exact Shinka dependency versions")'
    subprocess.run([str(executable),'-I','-B','-c',probe],env={'PATH':'/usr/bin:/bin','PYTHONNOUSERSITE':'1'},check=True,capture_output=True,text=True,timeout=20)
    if not 1<=args.num_generations<=1000:raise ValueError('Declare finite1..1000 generations')
    if not re.fullmatch(r'[0-9]{2}:[0-5][0-9]:[0-5][0-9]',args.eval_time) or args.eval_time=='00:00:00':
        raise ValueError('Evaluation time must be finite positive HH:MM:SS')
    if not (task/'evaluate.py').is_file():raise ValueError('Original task contract requires evaluate.py')
    protected=['.codex','.ssh','.aws','.docker','.netrc','.config/opencode','Library/Keychains']
    deny=[str(Path.home()/name) for name in protected]+[str(state),str(manifest['receipt_dir']),
          str(manifest['context_reference']),str(manifest['_manifest_path']),
          '/var/run/docker.sock','/private/var/run/docker.sock',*[str(x) for x in manifest['deny_roots']]]
    evaluation={'python':str(executable),'python_base':str(python.parent.parent),
                'source':str(source),'task':str(task),'evaluator':str(task/'evaluate.py'),
                'results':str(results),'codex':str(client),'read_roots':[str(x) for x in manifest['read_roots']],
                'deny_roots':deny,'receipt':str(state/'eval-launches.jsonl')}
    wrapper=state/'evaluate';evaluation_path=state/'evaluation.json'
    native_command=shlex.join([str(executable),'-B',str(HERE/'codex-transport/transport.py'),'--manifest',str(args.manifest)])
    # Isolated module lookup prevents task-directory modules shadowing trusted
    # engine/stdlib imports. This still calls the original CLI main unchanged.
    bootstrap="import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('shinka.cli.run',run_name='__main__')"
    original=[str(executable),'-I','-B','-c',bootstrap,str(source),'--task-dir',str(task),'--results_dir',str(results),
              '--num_generations',str(args.num_generations),'--max-evaluation-jobs','1',
              '--max-proposal-jobs','1','--max-db-workers','1']
    for value in args.set:original+=['--set',value]
    fixed={'evo.job_type':'local','evo.llm_models':['headless/codex'],'evo.meta_llm_models':['headless/codex'],
           'evo.novelty_llm_models':['headless/codex'],'evo.prompt_llm_models':['headless/codex'],
           'evo.embedding_model':None,'evo.enable_wandb_logging':False,
           'evo.llm_kwargs':{'headless_work_dir':str(task)},'job.python_executable':str(wrapper),
           'job.eval_program_path':str(task/'evaluate.py'),
           'job.activate_script':None,'job.conda_env':None,'job.numeric_threads_per_job':1,
           'job.time':args.eval_time}
    for key,value in fixed.items():original+=['--set',key+'='+json.dumps(value)]
    environment=transport.clean_environment();environment.update(
        PATH=str(client.parent)+os.pathsep+environment.get('PATH','/usr/bin:/bin'),
        PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1',
        SHINKA_HEADLESS_COMMAND=native_command,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    return original,environment,evaluation,evaluation_path,wrapper


def main():
    os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['plan','run'])
    parser.add_argument('--source-state',type=Path,required=True);parser.add_argument('--python',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--codex')
    parser.add_argument('--task-dir',type=Path,required=True);parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--state',type=Path,required=True);parser.add_argument('--num-generations',type=int,required=True)
    parser.add_argument('--eval-time',default='00:01:30');parser.add_argument('--set',action='append',default=[])
    args=parser.parse_args()
    try:
        original,environment,evaluation,path,wrapper=command(args)
        if args.operation=='plan':
            print(json.dumps({'original_argv':original,'evaluation':evaluation,
                              'source_binding':environment['PYTHONPATH'],
                              'native_transport':environment['SHINKA_HEADLESS_COMMAND'],
                              'scope':'Plan only; version/metadata/dependency checks, no model/evaluator/engine run'},indent=2));return 0
        args.state.mkdir(mode=0o700)
        path.write_text(json.dumps(evaluation,indent=2)+'\n')
        wrapper.write_text('#!/bin/sh\nexec '+shlex.join([evaluation['python'],'-B',str(HERE/'shinka_evaluator.py'),'--manifest',str(path)])+' "$@"\n');wrapper.chmod(0o500)
        (args.state/'LAUNCH.json').write_text(json.dumps({'original_argv':original,'evaluation':evaluation,
          'native_transport':environment['SHINKA_HEADLESS_COMMAND'],'source_binding':environment['PYTHONPATH']},indent=2)+'\n')
        return subprocess.run(original,env=environment,cwd=args.task_dir).returncode
    except (ValueError,OSError,subprocess.SubprocessError) as error:parser.error(str(error))
    return 1
if __name__=='__main__':raise SystemExit(main())
