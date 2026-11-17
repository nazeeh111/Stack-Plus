#!/usr/bin/env python3
"""Prepare exact offline dependencies, explicitly build them, or check prerequisites.

No download, dependency resolution, daemon startup, account access or inference.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'lib'))
from docker_client import LocalDocker


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256')
    return digest.hexdigest()


def save(path, value):
    # Reports are append-only: an earlier failed attempt stays inspectable.
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def inventory(root):
    result = {}
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Expected a real directory')
    for entry in root.rglob('*'):
        if entry.is_symlink():
            raise ValueError('Symlinks are not accepted: ' + str(entry.relative_to(root)))
        if entry.is_file():
            result[str(entry.relative_to(root))] = sha(entry)
        elif not entry.is_dir():
            raise ValueError('Only directories and ordinary files are accepted')
    return result


def exact(root, expected):
    observed = inventory(root)
    if observed != expected:
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        drift = sorted(k for k in set(observed) & set(expected) if observed[k] != expected[k])
        raise ValueError(f'Frozen input differs; missing={missing}, extra={extra}, changed={drift}')


def verify_recipe():
    manifest = read(HERE / 'RECIPE.json')
    exact(HERE, {**manifest['files'], 'RECIPE.json': sha(HERE / 'RECIPE.json')})
    context = read(HERE / 'manifests/context.json')
    expected = hashlib.sha256(json.dumps(context['files'], sort_keys=True,
                              separators=(',', ':')).encode()).hexdigest()
    if expected != context['sha256'] or expected != read(HERE / 'PINS.json')['portable_context_sha256']:
        raise ValueError('Context manifest hash differs')
    return read(HERE / 'PINS.json'), context


def canonical(path):
    path = Path(path).expanduser().absolute()
    if path.parent.resolve() != path.parent or path.is_symlink():
        raise ValueError('Use a canonical directory without symlink ancestors')
    if any(x in str(path) for x in (',', '\n', '\r', '\0')):
        raise ValueError('Directory cannot contain Docker mount separators or control characters')
    return path


def prepare(artifacts, state):
    pins, context = verify_recipe()
    artifacts, state = canonical(artifacts), canonical(state)
    if state.exists():
        raise ValueError('Preserve existing state; select a fresh private directory')
    inputs = read(HERE / 'manifests/inputs.json')
    # No recursive search across home/account folders. Artifacts are supplied in
    # the frozen relative layout; unrelated source files are never copied.
    for rel, digest in {**inputs['artifacts'], **{
            'metadata/' + k: v['sha256'] for k, v in inputs['metadata'].items()}}.items():
        file = artifacts / rel
        if any(p.is_symlink() for p in [file, *file.parents]) or not file.is_file() or sha(file) != digest:
            raise ValueError('Missing or changed reviewed artifact: ' + rel)
    state.mkdir(mode=0o700)
    context_dir = state / 'context'
    shutil.copytree(HERE / 'context', context_dir)
    for rel in inputs['artifacts']:
        target = context_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(artifacts / rel, target)
        if rel.startswith('runtime/'):
            target.chmod(0o755)
    shutil.copytree(artifacts / 'metadata', state / 'metadata',
                    ignore=lambda directory, names: [n for n in names if n not in inputs['metadata']])
    exact(context_dir, context['files'])
    exact(state / 'metadata', {k: v['sha256'] for k, v in inputs['metadata'].items()})
    shutil.copytree(HERE / 'fixtures', state / 'fixtures')
    save(state / 'OWNER.json', {'owner': 'nstack-scientific-image',
         'context_sha256': context['sha256'], 'recipe_sha256': sha(HERE / 'RECIPE.json')})
    return {'state': 'prepared-inert', 'context_sha256': context['sha256'],
            'scope': 'Exact file assembly only; no installation, build, Docker or readiness claim'}


def verify_state(state):
    pins, context = verify_recipe()
    state = canonical(state)
    owner = read(state / 'OWNER.json')
    if owner != {'owner': 'nstack-scientific-image', 'context_sha256': context['sha256'],
                 'recipe_sha256': sha(HERE / 'RECIPE.json')}:
        raise ValueError('State belongs to another recipe or generation')
    exact(state / 'context', context['files'])
    inputs = read(HERE / 'manifests/inputs.json')
    exact(state / 'metadata', {k: v['sha256'] for k, v in inputs['metadata'].items()})
    exact(state / 'fixtures', inventory(HERE / 'fixtures'))
    return state, pins, context


def capture(client, arguments, timeout=30):
    return subprocess.run([client.binary, *arguments], env=client.env,
                          capture_output=True, text=True, timeout=timeout)


def inspect(client, image):
    result = capture(client, ['image', 'inspect', image])
    if result.returncode:
        raise ValueError('Exact existing local image required; no pull or tag fallback')
    return json.loads(result.stdout)[0]


def assert_base(row, base):
    for key in ('Id', 'Architecture', 'Os', 'RootFS'):
        if row.get(key) != base[key]:
            raise ValueError('Original base identity differs: ' + key)
    if not set(base['RepoDigests']).issubset(row.get('RepoDigests', [])):
        raise ValueError('Original official base RepoDigest missing')


def remove_owned(client, name, token):
    result = capture(client, ['container', 'inspect', name])
    if result.returncode == 0:
        row = json.loads(result.stdout)[0]
        if row['Config']['Labels'].get('org.nstack.scientific-check') != token:
            raise ValueError('Refusing cleanup of an unowned container')
        result = capture(client, ['container', 'rm', '-f', row['Id']])
        if result.returncode:
            raise ValueError('Owned container cleanup failed')
    elif not (result.returncode == 1 and result.stdout.strip() == '[]'
              and result.stderr.strip().casefold() == 'error: no such container: ' + name):
        raise ValueError('Container inspection failed; absence not established')
    result = capture(client, ['container', 'inspect', name])
    if not (result.returncode == 1 and result.stdout.strip() == '[]'
            and result.stderr.strip().casefold() == 'error: no such container: ' + name):
        raise ValueError('Owned container absence not established')


def owned_run(client, image, mounts, command, log, timeout=180):
    if os.getuid() == 0:
        raise ValueError('Run prerequisite containers from an ordinary non-root account')
    name = 'nstack-scientific-check-' + uuid.uuid4().hex
    token = uuid.uuid4().hex
    argv = ['run', '--rm', '--init', '--name', name, '--label',
        'org.nstack.scientific-check=' + token, '--pull=never', '--network=none',
        '--read-only', '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
        '--security-opt=no-new-privileges', '--memory=1g', '--cpus=1', '--pids-limit=128',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m,mode=1777']
    for key, value in {'HOME': '/tmp/verification-home', 'TMPDIR': '/tmp',
            'MPLCONFIGDIR': '/tmp/mpl', 'MPLBACKEND': 'Agg', 'OPENBLAS_NUM_THREADS': '1',
            'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'PYTHONNOUSERSITE': '1'}.items():
        argv += ['-e', key + '=' + value]
    for source, destination, readonly in mounts:
        argv += ['--mount', f'type=bind,src={source},dst={destination}' + (',readonly' if readonly else '')]
    argv += ['--entrypoint', '/bin/sh', image, '-c', command]
    try:
        result = capture(client, argv, timeout=timeout)
        save(log, {'returncode': result.returncode, 'stdout': result.stdout,
                   'stderr': result.stderr, 'image': image, 'scope': 'dependency prerequisite only'})
    except subprocess.TimeoutExpired as error:
        save(log, {'state': 'timeout', 'timeout_seconds': timeout,
                   'stdout': (error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                   'stderr': (error.stderr or b'').decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr})
        raise
    finally:
        remove_owned(client, name, token)
    if result.returncode:
        raise ValueError('Dependency verification failed; raw logs retained')
    return result.stdout


def closure_versions(text):
    # APT's local-package simulation must select exactly the reviewed115.
    if any(line.startswith('Remv ') for line in text.splitlines()):
        raise ValueError('Unexpected package removal in original-base simulation')
    result = {}
    for line in text.splitlines():
        if line.startswith('Inst '):
            match = re.match(r'Inst ([^ :]+)(?::[^ ]+)?(?: \[[^]]+\])? \(([^ ]+)', line)
            if not match or match[1] in result:
                raise ValueError('Unexpected or repeated APT install record')
            result[match[1]] = match[2]
    return result


def verify_base_closure(client, state, pins, evidence):
    base = pins['base']
    assert_base(inspect(client, base['tag']), base)
    command = ('set -eu; python -I -B /input/base.py; '
        "sha256sum /var/lib/dpkg/status; "
        "apt-get --simulate --no-download --no-install-recommends -o Debug::NoLocking=1 install /packages/debs/*.deb")
    text = owned_run(client, base['Id'], [(state/'context', '/packages', True),
        (state/'fixtures', '/input', True), (state/'metadata', '/metadata', True)],
        command, evidence/'base-closure.json')
    if base['dpkg_status_sha256'] + '  /var/lib/dpkg/status' not in text:
        raise ValueError('Original base dpkg state differs')
    expected = {r['name']: r['version'] for r in read(HERE/'manifests/debian.json')['packages']}
    if closure_versions(text) != expected:
        raise ValueError('Original-base offline Debian closure differs')


def image_identity(row, pins, context):
    base = pins['base']
    if row.get('Os') != 'linux' or row.get('Architecture') != 'arm64':
        raise ValueError('Only the reviewed Linux arm64 image is supported')
    if row.get('RootFS', {}).get('Layers', [])[:len(base['RootFS']['Layers'])] != base['RootFS']['Layers']:
        raise ValueError('Original base RootFS prefix differs')
    accepted = pins['historical_acceptance']
    expected_context = accepted['context_sha256'] if row['Id'] == accepted['image_id'] else context['sha256']
    labels = row.get('Config', {}).get('Labels') or {}
    if labels.get('org.nstack.owner') != 'research' or labels.get('org.nstack.inputs') != expected_context:
        raise ValueError('Image owner or frozen input label differs')


def build(state, endpoint):
    state, pins, context = verify_state(state)
    evidence = state / ('build-' + uuid.uuid4().hex)
    evidence.mkdir(mode=0o700)
    with LocalDocker(endpoint) as client:
        verify_base_closure(client, state, pins, evidence)
        image_file = evidence/'image.id'
        try:
            result = capture(client, ['build', '--network=none', '--pull=false', '--label',
                'org.nstack.owner=research', '--label', 'org.nstack.inputs=' + context['sha256'],
                '--iidfile', str(image_file), str(state/'context')], timeout=1200)
        except subprocess.TimeoutExpired as error:
            save(evidence/'build-timeout.json', {'state': 'timeout', 'timeout_seconds': 1200,
                'stdout': error.stdout.decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                'stderr': error.stderr.decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr})
            raise
        save(evidence/'build.json', {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            raise ValueError('Offline build failed; frozen inputs and failure logs retained')
        image = image_file.read_text().strip()
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
            raise ValueError('Builder did not return an immutable image ID')
        image_identity(inspect(client, image), pins, context)
    verify_state(state)
    return {'state': 'built-unchecked-prerequisite', 'image_id': image, 'context_sha256': context['sha256']}


def check(state, image, endpoint):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
        raise ValueError('Select an exact immutable image ID')
    state, pins, context = verify_state(state)
    evidence = state / ('check-' + uuid.uuid4().hex)
    evidence.mkdir(mode=0o700)
    output = evidence / 'outputs'; output.mkdir(mode=0o700)
    with LocalDocker(endpoint) as client:
        verify_base_closure(client, state, pins, evidence)
        image_identity(inspect(client, image), pins, context)
        mounts = [(state/'fixtures', '/input', True), (output, '/output', False)]
        owned_run(client, image, mounts, 'mkdir -p /tmp/verification-home && exec python -I -B /input/core.py', evidence/'core.json')
        owned_run(client, image, mounts, 'mkdir -p /tmp/verification-home && exec /bin/sh /input/compile.sh', evidence/'compile.json')
    verify_state(state)
    result = {'state': 'dependency-prerequisite-checked', 'image_id': image,
        'context_sha256': context['sha256'], 'model_calls': 0,
        'scope': 'Imports/native numerical and plot fixture/original ICLR compilation only; no engine, research, scientific claims or publication acceptance',
        'core': read(output/'CORE.json'), 'compile': read(output/'COMPILE.json')}
    save(evidence/'CHECK.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'build', 'check'])
    parser.add_argument('--state', required=True, help='Canonical private state directory; fresh for prepare')
    parser.add_argument('--artifacts', help='Caller-supplied inert artifacts in the frozen relative layout')
    parser.add_argument('--image', help='Immutable existing image ID for check')
    parser.add_argument('--docker-host', help='Existing local Unix socket; never starts or configures Docker')
    args = parser.parse_args()
    try:
        if args.operation == 'prepare':
            if not args.artifacts: raise ValueError('prepare requires --artifacts')
            result = prepare(args.artifacts, args.state)
        elif args.operation == 'build':
            result = build(args.state, args.docker_host)
        else:
            if not args.image: raise ValueError('check requires --image')
            result = check(args.state, args.image, args.docker_host)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
