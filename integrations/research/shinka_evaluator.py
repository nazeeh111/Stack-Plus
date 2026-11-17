#!/usr/bin/env python3
"""Scoped per-job native sandbox for the unchanged original Shinka evaluator."""
import argparse,json,os,subprocess,sys
from pathlib import Path

def toml(value):
    if isinstance(value,dict):return '{'+','.join(json.dumps(k)+'='+toml(v) for k,v in value.items())+'}'
    return json.dumps(value)

def targets(arguments,m):
    if not arguments or any(arguments.count(key)!=1 for key in ('--program_path','--results_dir')):
        raise ValueError('Original evaluation requires exactly one program and results target')
    evaluator=Path(arguments[0]).resolve(strict=True)
    program=Path(arguments[arguments.index('--program_path')+1]).resolve(strict=True)
    result=Path(arguments[arguments.index('--results_dir')+1]).resolve()
    root=Path(m['results']).resolve()
    if evaluator!=Path(m['evaluator']).resolve() or not program.is_relative_to(root) or not result.is_relative_to(root):
        raise ValueError('Original evaluation target is outside declared run')
    return evaluator,program,result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True)
    args,arguments=parser.parse_known_args();m=json.loads(args.manifest.read_text())
    evaluator,program,result=targets(arguments,m)
    result.mkdir(parents=True,exist_ok=True)
    fs={':minimal':'read',m['source']:'read',str(Path(m['python']).parent.parent):'read',m['python_base']:'read',
        str(evaluator):'read',str(program):'read',str(result):'write'}
    for path in m['read_roots']:fs[path]='read'
    for path in m['deny_roots']:fs[path]='deny'
    policy={'filesystem':fs,'network':{'enabled':False,'dangerously_allow_all_unix_sockets':False}}
    command=[m['codex'],'sandbox','-P','research_eval','-c','permissions.research_eval='+toml(policy),
             '-C',str(result),'--',m['python'],*arguments]
    environment={k:os.environ[k] for k in ['PATH','HOME','LANG'] if k in os.environ}
    environment.update(PYTHONPATH=m['source'],PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(result/'mpl-cache'),
                       TMPDIR=str(result),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
    with Path(m['receipt']).open('a') as out:out.write(json.dumps({'command':command,'policy':policy,'program':str(program),'results':str(result)})+'\n')
    return subprocess.run(command,env=environment).returncode
if __name__=='__main__':raise SystemExit(main())
