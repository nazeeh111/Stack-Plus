"""Prepare/build an exact offline EDA image or run bounded, isolated CPU checks."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'lib'))
from docker_client import LocalDocker
PINS = json.loads((HERE/'PINS.json').read_text())


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def identity():
    return hashlib.sha256((HERE/'PINS.json').read_bytes()+(HERE/'Dockerfile').read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n')


def capture(client, argv, timeout=180):
    result = subprocess.run([str(x) for x in argv], env=client.env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError('Operation failed; no permission fallback: '+result.stderr[-4000:])
    return result.stdout


def canonical(value):
    path = Path(value).expanduser().absolute()
    if path != path.resolve() or any(x in str(path) for x in (',', '\n', '\r', '\0')):
        raise ValueError('Select a canonical path without mount separators; links are preserved')
    return path


def verify(state):
    receipt = json.loads((state/'PREPARED.json').read_text())
    if receipt['identity'] != identity():
        raise ValueError('Prepared definition differs; preserve it and choose a new state')
    for row in PINS['packages']:
        if digest(state/'context/debs'/row['filename']) != row['sha256']:
            raise ValueError('Frozen package hash mismatch: '+row['name'])
    if digest(state/'context/metadata/InRelease') != PINS['inrelease_sha256']:
        raise ValueError('Frozen signed release mismatch')
    if (state/'context/Dockerfile').read_bytes() != (HERE/'Dockerfile').read_bytes():
        raise ValueError('Prepared Dockerfile differs')


def prepare(state, supplied):
    if state.exists():
        raise ValueError('Preserve existing state; choose a new directory')
    supplied = canonical(supplied)
    state.mkdir(parents=True)
    context = state/'context';(context/'debs').mkdir(parents=True);(context/'metadata').mkdir()
    for row in PINS['packages']:
        source = supplied/row['filename']
        if source.is_symlink() or not source.is_file() or digest(source) != row['sha256']:
            raise ValueError('Acquired package mismatch; not installed: '+row['name'])
        shutil.copyfile(source, context/'debs'/row['filename'])
    release = supplied/'InRelease'
    if release.is_symlink() or digest(release) != PINS['inrelease_sha256']:
        raise ValueError('Supplied signed release mismatch')
    shutil.copyfile(release, context/'metadata/InRelease')
    shutil.copyfile(HERE/'Dockerfile', context/'Dockerfile')
    (context/'.dockerignore').write_text('metadata\n')
    save(state/'PREPARED.json', {'identity': identity(), 'activation': 'Prepared exact packages, not built or accepted'})
    verify(state)


def gate(state, client):
    docker = client.binary
    verify(state)
    argv = [docker, 'run', '--rm', '--name', 'nstack-fpga-metadata-'+uuid.uuid4().hex[:12],
        '--pull=never', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--user', '1000:1000',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '512m', '--cpus', '1',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m,mode=1777', '--mount',
        'type=bind,src='+str(state/'context')+',dst=/metadata,readonly', '--entrypoint', '/bin/sh', PINS['base'], '-c',
        '/usr/bin/sqv --keyring /usr/share/keyrings/debian-archive-keyring.pgp --cleartext --output /tmp/authenticated /metadata/metadata/InRelease && cat /tmp/authenticated && apt-get --simulate --no-download --no-install-recommends -o Debug::NoLocking=1 install /metadata/debs/*.deb']
    text = capture(client, argv)
    actual = {}
    for line in text.splitlines():
        if line.startswith('Inst '):
            match = re.match(r'Inst ([^ ]+)(?: \[[^]]+\])? \(([^ ]+)', line)
            if not match:
                raise ValueError('Unrecognized exact closure simulation')
            actual[match[1]] = match[2]
    if PINS['index_sha256'] not in text or actual != {x['name']: x['version'] for x in PINS['packages']}:
        raise ValueError('Signed index or exact dependency closure differs')
    (state/'metadata.log').write_text(text)
    save(state/'METADATA.json', {'passed': True, 'identity': identity(), 'exact_packages': actual,
                                'signature': 'sqv default policy with official base Debian keyring'})


def build(state, client):
    docker = client.binary
    gate(state, client)
    tag = 'nstack-fpga-linux:'+identity()[:16]
    try:
        text = capture(client, [docker, 'build', '--platform', 'linux/amd64', '--network=none', '--pull=false',
            '--label', 'nstack.fpga.identity='+identity(), '--tag', tag, '--file', state/'context/Dockerfile', state/'context'], timeout=600)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Image build exceeded 600 seconds; no runtime readiness claim') from error
    (state/'build.log').write_text(text)
    image = json.loads(capture(client, [docker, 'image', 'inspect', tag]))[0]
    save(state/'BUILD.json', {'identity': identity(), 'image_id': image['Id'], 'tag': tag,
                             'readiness': 'Built tools only; actual acceptance separate'})


def check(state, output, client):
    docker = client.binary
    verify(state)
    built = json.loads((state/'BUILD.json').read_text())
    image = json.loads(capture(client, [docker, 'image', 'inspect', built['image_id']]))[0]
    if built['identity'] != identity() or image['Config']['Labels'].get('nstack.fpga.identity') != identity():
        raise ValueError('Owned EDA image differs')
    if output.exists() or output.is_symlink():
        raise ValueError('Preserve existing evidence; choose a new output directory')
    output.mkdir(parents=True, mode=0o700)
    skill = HERE.parents[1]/'addons/fpga-development'
    name = 'nstack-fpga-check-'+uuid.uuid4().hex[:12]
    argv = [docker, 'run', '--rm', '--name', name, '--pull=never', '--platform', 'linux/amd64',
        '--network', 'none', '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--pids-limit', '64', '--memory', '512m', '--cpus', '1',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777',
        '--mount', 'type=bind,src='+str(HERE)+',dst=/fixture,readonly',
        '--mount', 'type=bind,src='+str(skill)+',dst=/skill,readonly',
        '--mount', 'type=bind,src='+str(output)+',dst=/output', built['image_id']]
    try:
        result = subprocess.run(argv, env=client.env, capture_output=True, text=True, timeout=180)
        record = {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        # Stop only this invocation's unique owned container. Never alter the daemon.
        subprocess.run([docker, 'rm', '-f', name], env=client.env, capture_output=True, timeout=30)
        record = {'exit_code': 124, 'timed_out': True, 'stdout': str(error.stdout or ''),
                  'stderr': str(error.stderr or '')}
    save(output/'execution.json', record)
    save(output/'RUNTIME.json', {'identity': identity(), 'image_id': built['image_id'],
        'acceptance_sha256': digest(HERE/'acceptance.py'), 'skill_source_receipt_sha256': digest(skill/'SOURCE.json')})
    print(json.dumps({'exit_code': record['exit_code'], 'evidence': str(output)}, indent=2))
    return record['exit_code']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'build', 'check'))
    parser.add_argument('--state', required=True)
    parser.add_argument('--docker-host', help='Existing local unix:///absolute/socket; inherited Docker settings are ignored')
    parser.add_argument('--debs', help='Existing exact reviewed .deb directory plus signed InRelease')
    parser.add_argument('--out', help='New owned acceptance evidence directory')
    args = parser.parse_args()
    state = canonical(args.state)
    try:
        if args.operation == 'prepare':
            if not args.debs: parser.error('--debs is required for prepare')
            prepare(state, args.debs)
        else:
            with LocalDocker(args.docker_host) as client:
                if args.operation == 'build': build(state, client)
                else:
                    if not args.out: parser.error('--out is required for check')
                    return check(state, canonical(args.out), client)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
