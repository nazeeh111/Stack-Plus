#!/usr/bin/env python3
"""Prepare pinned engine source and explicit offline Shinka dependencies only."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent


def read(path): return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def canonical(path):
    path = Path(path).expanduser().absolute()
    if path.resolve() != path or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Use a canonical path without symlinks')
    if any(c in str(path) for c in ('\n', '\r', '\0')):
        raise ValueError('Control characters are not accepted in paths')
    return path


def inventory(root):
    files = {}
    for path in root.rglob('*'):
        if path.is_symlink(): raise ValueError('Symlink in frozen source')
        if path.is_file(): files[str(path.relative_to(root))] = sha(path)
        elif not path.is_dir(): raise ValueError('Special file in frozen source')
    return files


def verify_recipe():
    manifest = read(HERE/'RECIPE.json')
    if inventory(HERE) != {**manifest['files'], 'RECIPE.json': sha(HERE/'RECIPE.json')}:
        raise ValueError('Portable preparation recipe changed')


def archive_entries(archive, spec):
    if sha(archive) != spec['archive_sha256'] or archive.stat().st_size != spec['archive_bytes']:
        raise ValueError('Exact reviewed git-archive bytes required')
    entries, payloads, seen = [], {}, set()
    with tarfile.open(archive, 'r:') as bundle:
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or str(path) != member.name.rstrip('/')
                or member.name.rstrip('/') in seen or not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe or duplicate source archive member')
            seen.add(member.name.rstrip('/'))
            row = {'path': member.name, 'type': 'file' if member.isfile() else 'directory',
                   'mode': member.mode, 'size': member.size}
            if member.mode & ~0o777 or (member.mode & 0o222 == 0 and member.isdir()):
                raise ValueError('Unexpected archive permissions')
            if member.isfile():
                expected = spec['files'].get(member.name)
                if expected is None or member.size != expected['size']:
                    raise ValueError('Unexpected source member or size')
                raw = bundle.extractfile(member).read()
                row['sha256'] = hashlib.sha256(raw).hexdigest()
                payloads[member.name] = raw
            entries.append(row)
    if entries != spec['members'] or set(payloads) != set(spec['files']):
        raise ValueError('Source archive member/content/mode inventory changed')
    return payloads


def patcher(bash):
    support = read(HERE/'manifests/patch-support.json')
    for relative, digest in support['files'].items():
        path = HERE.parent/relative
        if path.is_symlink() or not path.is_file() or sha(path) != digest:
            raise ValueError('Reviewed transport patch support changed')
    bash = canonical(bash)
    if not bash.is_file() or not os.access(bash, os.X_OK) or sha(bash) != support['bash']['sha256']:
        raise ValueError('Explicit existing reviewed GNU Bash5.3.20 required for syntax validation')
    path = HERE.parent/'codex-transport/apply_engine_patches.py'
    spec = importlib.util.spec_from_file_location('nstack_engine_source_patches', path)
    module = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode; sys.dont_write_bytecode = True
    try: spec.loader.exec_module(module)
    finally: sys.dont_write_bytecode = old
    return module, bash


def expected_source(engine):
    spec = read(HERE/'manifests'/f'{engine}.json')
    files = {path: {'sha256': row['sha256'], 'mode': 0o555 if row['mode'] & 0o111 else 0o444}
             for path, row in spec['files'].items()}
    if engine == 'ai-scientist':
        patches = read(HERE.parent/'codex-transport/patches/manifest.json')
        if patches['commit'] != spec['revision']: raise ValueError('Patch source revision differs')
        for row in patches['files']: files[row['path']]['sha256'] = row['patched_sha256']
    return files


def source_inventory(source):
    if not source.is_dir() or source.is_symlink(): raise ValueError('Missing real prepared source')
    result = {}
    for path in [source, *source.rglob('*')]:
        info = path.lstat()
        if info.st_uid != os.getuid() or stat.S_ISLNK(info.st_mode):
            raise ValueError('Prepared source must remain owner-controlled without symlinks')
        if stat.S_ISDIR(info.st_mode):
            if stat.S_IMODE(info.st_mode) != 0o555: raise ValueError('Prepared source directory is not read-only')
        elif stat.S_ISREG(info.st_mode):
            result[str(path.relative_to(source))] = {'sha256': sha(path), 'mode': stat.S_IMODE(info.st_mode)}
        else: raise ValueError('Unexpected prepared source special file')
    return result


def verify_source(state, engine=None):
    verify_recipe(); state = canonical(state)
    receipt = read(state/'SOURCE.json')
    selected = receipt['engine']
    if selected not in ('shinka', 'ai-scientist') or engine and selected != engine:
        raise ValueError('Prepared source is the wrong engine')
    pin = read(HERE/'PINS.json')[selected]
    if receipt['owner'] != 'nstack-research-source' or receipt['pin'] != pin:
        raise ValueError('Prepared source owner/revision differs')
    if receipt['recipe_sha256'] != sha(HERE/'RECIPE.json'):
        raise ValueError('Source belongs to a different preparation recipe')
    expected_directories = {row['path'].rstrip('/') for row in read(HERE/'manifests'/f'{selected}.json')['members'] if row['type']=='directory'}
    observed_directories = {str(p.relative_to(state/'source')) for p in (state/'source').rglob('*') if p.is_dir()}
    if observed_directories != expected_directories:
        raise ValueError('Prepared source directory set changed')
    if source_inventory(state/'source') != expected_source(selected):
        raise ValueError('Prepared source bytes or permissions changed')
    if sha(state/'original.tar') != pin['archive_sha256']:
        raise ValueError('Preserved original source archive changed')
    if selected == 'ai-scientist':
        support = read(HERE/'manifests/patch-support.json')
        for relative, digest in support['files'].items():
            if sha(HERE.parent/relative) != digest: raise ValueError('Patch support changed')
        if inventory(state/'patch-originals') != receipt['patch_original_hashes']:
            raise ValueError('Preserved patch originals/diffs changed')
    return state/'source'


def prepare_source(engine, archive, state, bash=None):
    verify_recipe()
    state, archive = canonical(state), canonical(archive)
    if state.exists(): raise ValueError('Preserve existing state; select a fresh source generation')
    specification = read(HERE/'manifests'/f'{engine}.json')
    payloads = archive_entries(archive, specification)
    module = None
    if engine == 'ai-scientist':
        if not bash: raise ValueError('AI Scientist source preparation requires --bash')
        module, bash = patcher(bash)
    state.mkdir(mode=0o700)
    source = state/'source'; source.mkdir(mode=0o700)
    shutil.copyfile(archive, state/'original.tar'); (state/'original.tar').chmod(0o400)
    for relative, raw in payloads.items():
        target = source/relative; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream: stream.write(raw)
        target.chmod(0o755 if specification['files'][relative]['mode'] & 0o111 else 0o644)
    if module:
        module.apply(source, state/'patch-originals', bash=bash)
    for path in source.rglob('*'):
        if path.is_file(): path.chmod(0o555 if specification['files'][str(path.relative_to(source))]['mode'] & 0o111 else 0o444)
    for path in sorted([p for p in source.rglob('*') if p.is_dir()], key=lambda p: len(p.parts), reverse=True): path.chmod(0o555)
    source.chmod(0o555)
    receipt = {'owner': 'nstack-research-source', 'engine': engine,
        'pin': read(HERE/'PINS.json')[engine], 'recipe_sha256': sha(HERE/'RECIPE.json'),
        'patch_original_hashes': inventory(state/'patch-originals') if module else {},
        'scope': 'Inert original engine source, with exact reviewed AIS patches; no engine execution or activation'}
    write(state/'SOURCE.json', receipt)
    verify_source(state, engine)
    return {'state': 'source-prepared-readonly', 'engine': engine, 'source': str(source),
            'source_state': str(state), 'revision': specification['revision'], 'model_calls': 0}


def native_profile(home):
    # Match the reviewed native preparation route: no network, inherited auth,
    # account files or keychain. This profile does not grant task execution.
    deny = [home/'.codex', home/'.claude', home/'.config/opencode', home/'.ssh',
            home/'.aws', home/'.docker', home/'Library/Keychains', home/'.netrc']
    return '(version 1)(allow default)(deny network*)' + ''.join(
        '(deny file-read* (subpath '+json.dumps(str(path))+'))' for path in deny)


def prepare_shinka(source_state, artifacts, python, state):
    source = verify_source(source_state, 'shinka')
    if (platform.system(), platform.machine()) != ('Darwin', 'arm64'):
        raise ValueError('Only the reviewed Darwin arm64 CPython3.11 Shinka closure is supported')
    state, artifacts, python = canonical(state), canonical(artifacts), canonical(python)
    if state.exists(): raise ValueError('Preserve existing dependency state; use a fresh private directory')
    if not python.is_file() or not os.access(python, os.X_OK): raise ValueError('Explicit reviewed existing Python executable required')
    sandbox = Path('/usr/bin/sandbox-exec')
    if not sandbox.is_file(): raise ValueError('Existing native execution controls required; no uncontained fallback')
    dependencies = read(HERE/'manifests/shinka-dependencies.json')
    for row in dependencies['wheels']:
        file = canonical(artifacts/row['input_path'])
        if not file.is_file() or sha(file) != row['sha256'] or file.stat().st_size != row['size']:
            raise ValueError('Missing/changed reviewed wheel: '+row['input_path'])
    # No state or tool process before complete artifact and platform checks.
    state.mkdir(mode=0o700)
    for name in ('home', 'tmp', 'wheelhouse', 'logs'): (state/name).mkdir(mode=0o700)
    for row in dependencies['wheels']: shutil.copyfile(artifacts/row['input_path'], state/'wheelhouse'/row['filename'])
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(state/'home'), 'TMPDIR': str(state/'tmp'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PIP_NO_INDEX': '1',
        'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PIP_CONFIG_FILE': '/dev/null',
        'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    profile = native_profile(Path.home())
    def run(name, argv, timeout=300):
        command = [str(sandbox), '-p', profile, *map(str, argv)]
        try: result = subprocess.run(command, env=env, cwd=state, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            write(state/'logs'/(name+'.json'), {'state':'timeout','timeout_seconds':timeout,
                'stdout':error.stdout.decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                'stderr':error.stderr.decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr})
            raise
        write(state/'logs'/(name+'.json'), {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode: raise ValueError('Offline dependency preparation failed at '+name+'; raw logs preserved')
        return result.stdout
    version = run('python-prerequisite', [python, '-I', '-B', '-c',
        "import json,platform,sys;assert sys.implementation.name=='cpython' and sys.version_info[:2]==(3,11) and platform.machine()=='arm64';print(json.dumps({'version':platform.python_version(),'implementation':sys.implementation.name}))"])
    run('venv', [python, '-I', '-B', '-m', 'venv', state/'venv'])
    executable = state/'venv/bin/python'
    base = [executable, '-I', '-B', '-m', 'pip', '--isolated', '--disable-pip-version-check', '--no-input', '--keyring-provider', 'disabled']
    for name, lock in [('bootstrap','bootstrap-exact.lock'),('runtime','runtime-exact.lock')]:
        run(name, [*base, 'install', '--no-index', '--no-deps', '--only-binary=:all:',
                   '--find-links='+str(state/'wheelhouse'), '--require-hashes', '-r', HERE/lock], timeout=600)
    run('pip-check', [*base, 'check'])
    expected = {r['name']:r['version'] for r in dependencies['wheels']}
    run('exact-versions', [executable, '-I', '-B', '-c',
        'import importlib.metadata,json; expected=json.loads('+repr(json.dumps(expected))+');assert all(importlib.metadata.version(k)==v for k,v in expected.items());print(json.dumps(expected,sort_keys=True))'])
    verify_source(source_state, 'shinka')
    receipt = {'owner':'nstack-shinka-dependencies','source_state':str(canonical(source_state)),
        'source_revision':read(HERE/'PINS.json')['shinka']['revision'],'python_prerequisite':json.loads(version),
        'python_binary_sha256':sha(python),'recipe_sha256':sha(HERE/'RECIPE.json'),
        'wheel_hashes':{r['filename']:r['sha256'] for r in dependencies['wheels']},
        'scope':'Offline native dependencies only; source remains PYTHONPATH binding; no provider login, model call or research acceptance'}
    write(state/'DEPENDENCIES.json', receipt)
    return {'state':'shinka-dependencies-prepared','python':str(executable),'source':str(source),
        'dependency_state':str(state),'mandatory_roots':26,'resolved_dependencies':101,'model_calls':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare-source','verify-source','prepare-shinka'])
    parser.add_argument('--engine', choices=['shinka','ai-scientist'])
    parser.add_argument('--archive'); parser.add_argument('--state', required=True)
    parser.add_argument('--bash'); parser.add_argument('--source-state'); parser.add_argument('--artifacts'); parser.add_argument('--python')
    args = parser.parse_args()
    try:
        if args.operation == 'prepare-source':
            if not args.engine or not args.archive: raise ValueError('prepare-source requires --engine and --archive')
            result = prepare_source(args.engine,args.archive,args.state,args.bash)
        elif args.operation == 'verify-source':
            result = {'state':'source-verified','source':str(verify_source(args.state,args.engine))}
        else:
            if not all((args.source_state,args.artifacts,args.python)):
                raise ValueError('prepare-shinka requires --source-state, --artifacts and explicit --python')
            result = prepare_shinka(args.source_state,args.artifacts,args.python,args.state)
        print(json.dumps(result,indent=2))
    except (ValueError,OSError,subprocess.SubprocessError,tarfile.TarError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__': raise SystemExit(main())
