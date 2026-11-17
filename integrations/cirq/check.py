"""Repeat the bounded Cirq CPU checks with an explicit isolated interpreter."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python',required=True,help='Absolute Python in the reviewed Cirq environment')
    parser.add_argument('--out',required=True,help='New owned evidence directory; must not already exist')
    args=parser.parse_args()
    interpreter=Path(args.python).expanduser().absolute()
    out=Path(args.out).expanduser().absolute()
    if out != out.resolve():
        parser.error('Select the explicit canonical output path; linked paths are preserved')
    if not interpreter.is_file() or not os.access(interpreter,os.X_OK):
        parser.error('An existing executable Cirq Python is required')
    if not Path('/usr/bin/sandbox-exec').is_file():
        parser.error('This checked operation requires the macOS network-denial boundary')
    if out.exists() or out.is_symlink():
        parser.error('Preserve existing evidence; choose a new output directory')
    base=subprocess.check_output([str(interpreter),'-I','-B','-c','import sys; print(sys.base_prefix)'],text=True).strip()
    out.mkdir(parents=True,mode=0o700)
    for name in ('home','tmp','config','cache','mpl'):
        (out/name).mkdir(mode=0o700)
    source=Path(__file__).with_name('acceptance.py')
    shutil.copyfile(source,out/'acceptance.py')
    readable=(interpreter.parent.parent,Path(base),out)
    exclusions=' '.join('(require-not (subpath '+json.dumps(str(p))+'))' for p in readable)
    rules=('(version 1)\n(allow default)\n(deny network*)\n'
           '(deny file-write* (require-all (require-not (subpath '+json.dumps(str(out))+')) '
           '(require-not (literal "/dev/null"))))\n'
           '(deny file-read-data file-read-xattr (require-all (subpath "/Users") '+exclusions+'))\n')
    (out/'sandbox.sb').write_text(rules)
    env={'HOME':str(out/'home'),'TMPDIR':str(out/'tmp'),'XDG_CONFIG_HOME':str(out/'config'),
         'XDG_CACHE_HOME':str(out/'cache'),'MPLCONFIGDIR':str(out/'mpl'),
         'PATH':str(interpreter.parent)+':/usr/bin:/bin','LANG':'en_US.UTF-8',
         'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
         'MKL_NUM_THREADS':'1','RAYON_NUM_THREADS':'1'}
    argv=['/usr/bin/sandbox-exec','-p',rules,str(interpreter),'-I','-B',str(out/'acceptance.py')]
    try:
        result=subprocess.run(argv,cwd=out,env=env,capture_output=True,text=True,timeout=180)
        record={'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    except subprocess.TimeoutExpired as error:
        def decoded(value):
            return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or ''
        record={'exit_code':124,'timed_out':True,'stdout':decoded(error.stdout),
                'stderr':decoded(error.stderr)+'\nCirq check exceeded 180 seconds.'}
    (out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'exit_code':record['exit_code'],'evidence':str(out)},indent=2))
    return record['exit_code']


if __name__=='__main__':
    raise SystemExit(main())
