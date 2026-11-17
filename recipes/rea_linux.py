#!/usr/bin/env python3
"""Pinned, offline, on-demand Linux REA + Ghidra; enforced static MCP policy."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import urllib.request
import uuid
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'lib'))
from docker_client import LocalDocker, docker_binary
ASSETS = HERE / 'integrations/rea/linux'
PINS = json.loads((ASSETS / 'PINS.json').read_text())
STATIC_TOOLS = frozenset(json.loads((ASSETS / 'static-tools.json').read_text()))
DEFAULT_STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack')) / 'native-tools/rea-linux/6.9.0'
MAX_INPUT = 128 * 1024 * 1024
MAX_MESSAGE = 128 * 1024 * 1024
FORBIDDEN = {'.ssh', '.codex', '.claude', '.config', '.aws', '.gnupg', '.docker', '.git', '.obsidian', 'knowledge', 'credentials', 'secrets', 'passwords', 'keychains', '.env', '.netrc', '.npmrc', '.pypirc', '.git-credentials'}


def sensitive(name):
    name = name.casefold()
    return name in FORBIDDEN or name.startswith('.env.')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024): h.update(block)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')
    Path(path).chmod(0o600)


def concrete(path):
    if any(c in str(path) for c in (',', '\n', '\r', '\0')): raise ValueError('Unsafe mount-path separator')
    result = Path(os.path.abspath(path))
    if result != result.resolve(): raise ValueError('Linked path preserved; select its explicit canonical target')
    return result


def identity():
    return hashlib.sha256(b''.join((ASSETS / name).read_bytes() for name in ('PINS.json', 'Dockerfile', 'runner.mjs', 'static-tools.json'))).hexdigest()


def capture(client, argv, timeout=120, stdout=None, stderr=None):
    result = subprocess.run([str(x) for x in argv], env=client.env, text=True, stdout=stdout or subprocess.PIPE, stderr=stderr or subprocess.PIPE, timeout=timeout)
    if result.returncode: raise ValueError('Operation failed; no permission fallback: ' + (result.stderr or str(argv))[-6000:])
    return result.stdout


def tree(root):
    result = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink(): result[str(p.relative_to(root))] = {'link': os.readlink(p)}
        elif p.is_file(): result[str(p.relative_to(root))] = {'sha256': digest(p), 'mode': p.stat().st_mode & 0o777}
        elif not p.is_dir(): raise ValueError('Special file preserved')
    return result


def tree_hash(root):
    return hashlib.sha256(json.dumps(tree(root), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def archive_files():
    return [{'filename': 'rea.tgz', 'url': PINS['rea_url'], 'sha256': PINS['rea_sha256']},
            {'filename': 'ghidra.zip', 'url': PINS['ghidra_url'], 'sha256': PINS['ghidra_sha256']},
            {'filename': 'InRelease', 'url': PINS['debian_inrelease_url'], 'sha256': PINS['debian_inrelease_sha256']},
            {'filename': 'Packages.xz', 'url': PINS['debian_packages_url'], 'sha256': PINS['debian_packages_sha256']}, *PINS['debian_packages']]


def acquire(row, destination, supplied=None):
    if supplied:
        source = concrete(supplied)
        if not source.is_file() or digest(source) != row['sha256']: raise ValueError('Acquired artifact hash mismatch; not used')
        shutil.copyfile(source, destination)
    else:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(row['url'], timeout=120) as response, destination.open('xb') as output: shutil.copyfileobj(response, output)
    if digest(destination) != row['sha256']: raise ValueError('Official artifact hash mismatch; preserved without execution')


def safe_tar(source, output):
    output.mkdir()
    with tarfile.open(source) as archive:
        members = archive.getmembers()
        if len(members) > 30000 or sum(x.size for x in members) > 1024 ** 3: raise ValueError('Archive size budget exceeded')
        seen = set(); links = set()
        for m in members:
            parts = PurePosixPath(m.name).parts
            if not parts or parts[0] != 'package' or '..' in parts or m.name.startswith('/'): raise ValueError('Unsafe package archive path')
            rel = Path(*parts[1:])
            if not rel.parts:
                if m.isdir(): continue
                raise ValueError('Invalid archive root')
            if str(rel) in seen or not (m.isdir() or m.isfile() or m.issym()): raise ValueError('Duplicate/special archive entry')
            seen.add(str(rel))
            if m.issym():
                if not (output / rel.parent / m.linkname).resolve().is_relative_to(output): raise ValueError('Escaping archive link')
                links.add(rel)
        for m in members:
            rel = Path(*PurePosixPath(m.name).parts[1:])
            if not rel.parts: continue
            if any(p in links for p in rel.parents): raise ValueError('Archive writes through link')
            dst = output / rel; dst.parent.mkdir(parents=True, exist_ok=True)
            if m.isdir(): dst.mkdir(exist_ok=True)
            elif m.isfile():
                with archive.extractfile(m) as src, dst.open('xb') as target: shutil.copyfileobj(src, target)
                dst.chmod(m.mode & 0o777)
        for m in members:
            if m.issym(): (output / Path(*PurePosixPath(m.name).parts[1:])).symlink_to(m.linkname)


def safe_zip(source, output):
    output.mkdir()
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist(); seen = set()
        if len(entries) > 20000 or sum(x.file_size for x in entries) > 2 * 1024 ** 3: raise ValueError('Ghidra archive budget exceeded')
        for member in entries:
            parts = PurePosixPath(member.filename).parts
            if not parts or parts[0] != 'ghidra_12.1.4_PUBLIC' or '..' in parts or member.filename.startswith('/'): raise ValueError('Unsafe Ghidra path')
            rel = Path(*parts[1:])
            if not rel.parts: continue
            if str(rel) in seen or ((member.external_attr >> 16) & 0o170000) not in (0, 0o040000, 0o100000): raise ValueError('Duplicate/special Ghidra entry')
            seen.add(str(rel)); dst = output / rel; dst.parent.mkdir(parents=True, exist_ok=True)
            if member.is_dir(): dst.mkdir(exist_ok=True)
            else:
                with archive.open(member) as src, dst.open('xb') as target: shutil.copyfileobj(src, target)
                dst.chmod((member.external_attr >> 16) & 0o777 or 0o644)


def prepare(state, acquired=None):
    state = concrete(state)
    if state.exists(): return verify(state)
    state.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.rea-linux-prepare-', dir=state.parent))
    archives = stage / 'archives'; archives.mkdir()
    for row in archive_files():
        supplied = Path(acquired) / row['filename'] if acquired else None
        acquire(row, archives / row['filename'], supplied)
    context = stage / 'context'; context.mkdir(); (context / 'debs').mkdir(); (context / 'metadata').mkdir()
    for row in PINS['debian_packages']: shutil.copyfile(archives / row['filename'], context / 'debs' / row['filename'])
    for name in ('InRelease', 'Packages.xz'): shutil.copyfile(archives / name, context / 'metadata' / name)
    safe_tar(archives / 'rea.tgz', context / 'rea'); safe_zip(archives / 'ghidra.zip', context / 'ghidra')
    native = context / 'ghidra/Ghidra/Features/Decompiler/os/linux_x86_64/decompile'
    if digest(native) != PINS['ghidra_native_sha256']: raise ValueError('Ghidra native identity differs')
    for name in ('Dockerfile', 'runner.mjs'): shutil.copyfile(ASSETS / name, context / name)
    # Metadata is not sent to image build; only fixed public payloads are copied.
    (context / '.dockerignore').write_text('metadata\n')
    catalog = json.loads((context / 'rea/dist/mcp-catalog-full.json').read_text())
    names = {x['name'] for x in catalog['tools']}
    if len(names) != 255 or not STATIC_TOOLS.issubset(names): raise ValueError('Original catalog/static policy mismatch')
    save(stage / 'PREPARED.json', {'identity': identity(), 'context_sha256': tree_hash(context), 'original_catalog_tools': len(names), 'version': PINS['rea_version'], 'activation': 'Prepared payload only; metadata gate/build/acceptance separate'})
    os.rename(stage, state)
    return verify(state)


def verify(state, built=False, client=None):
    state = concrete(state)
    receipt = json.loads((state / 'PREPARED.json').read_text())
    if receipt['identity'] != identity() or receipt['context_sha256'] != tree_hash(state / 'context'): raise ValueError('Prepared source differs; preserved')
    for row in archive_files():
        if digest(state / 'archives' / row['filename']) != row['sha256']: raise ValueError('Sealed archive differs')
    if built:
        if client is None: raise ValueError('Built image verification requires a private local Docker client')
        build = json.loads((state / 'BUILD.json').read_text())
        if build['identity'] != identity() or build['context_sha256'] != receipt['context_sha256']: raise ValueError('Build receipt source mismatch')
        actual = json.loads(capture(client, [client.binary, 'image', 'inspect', build['image_id']]))[0]
        if actual['Id'] != build['image_id'] or actual['Config']['Labels'].get('nstack.rea.identity') != identity(): raise ValueError('Owned built image differs')
        return build
    return receipt


def metadata_args(state, name, command, client):
    return [client.binary, 'run', '--rm', '--name', name, '--pull=never', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '512m', '--cpus', '1', '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m,mode=1777', '--mount', 'type=bind,src=' + str(state / 'context') + ',dst=/metadata,readonly', '--entrypoint', '/bin/sh', PINS['base'], '-c', command]


def metadata_gate(state, client):
    verify(state)
    base = json.loads(capture(client, [client.binary, 'image', 'inspect', PINS['base']]))[0]
    if base['Id'] != PINS['base_config_sha256'] or base['Architecture'] != 'amd64': raise ValueError('Pinned base image missing/mismatched; acquire exact reviewed digest explicitly')
    unique = uuid.uuid4().hex
    signed = capture(client, metadata_args(state, 'nstack-rea-signature-' + unique, '/usr/bin/sqv --keyring /usr/share/keyrings/debian-archive-keyring.pgp --cleartext --output /tmp/authenticated /metadata/metadata/InRelease && cat /tmp/authenticated', client))
    if PINS['debian_packages_sha256'] not in signed: raise ValueError('Package index not authenticated by signed release')
    simulated = capture(client, metadata_args(state, 'nstack-rea-simulate-' + unique, 'apt-get --simulate --no-download --no-install-recommends -o Debug::NoLocking=1 install /metadata/debs/*.deb', client))
    actual = {}
    for line in simulated.splitlines():
        if line.startswith('Inst '):
            match = re.match(r'Inst ([^ ]+)(?: \[[^]]+\])? \(([^ ]+)', line)
            if not match: raise ValueError('Unrecognized apt install simulation')
            actual[match[1]] = match[2]
    if actual != {x['name']: x['version'] for x in PINS['debian_packages']}: raise ValueError('New dependency set; stop for source review')
    result = {'passed': True, 'identity': identity(), 'signed_release_sha256': PINS['debian_inrelease_sha256'], 'authenticated_packages_sha256': PINS['debian_packages_sha256'], 'exact_install_set': actual, 'signature_policy': 'Official pinned base sqv/default policy and built-in Debian archive keyring'}
    save(state / 'METADATA.json', result)
    (state / 'apt-simulation.log').write_text(simulated)
    return result


def build(state, client):
    state = concrete(state); prepared = verify(state); metadata_gate(state, client)
    if (state / 'BUILD.json').exists(): return verify(state, built=True, client=client)
    tag = 'nstack-rea-linux:' + identity()[:16]
    # Build context contains only pinned public artifacts. No network, secret or host mounts.
    with (state / 'build.log').open('w') as log:
        capture(client, [client.binary, 'build', '--platform', 'linux/amd64', '--network=none', '--pull=false', '--label', 'nstack.rea.identity=' + identity(), '--tag', tag, '--file', state / 'context/Dockerfile', state / 'context'], timeout=1200, stdout=log, stderr=log)
    actual = json.loads(capture(client, [client.binary, 'image', 'inspect', tag]))[0]
    result = {'identity': identity(), 'context_sha256': prepared['context_sha256'], 'image_id': actual['Id'], 'tag': tag, 'platform': 'linux/amd64', 'base': PINS['base'], 'readiness': 'Built original payload; real JS/native/MCP acceptance separate'}
    save(state / 'BUILD.json', result)
    return verify(state, built=True, client=client)


def snapshot(source, destination):
    source = concrete(source)
    if any(sensitive(x) for x in source.parts): raise ValueError('Sensitive source/config/vault excluded')
    if not source.is_dir() or source in {Path('/'), Path('/Users'), Path.home(), Path('/private/tmp'), Path('/Applications')}: raise ValueError('Select an explicit artifact directory')
    def inventory(destination=None):
        result = {}; size = count = 0
        rootfd = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if destination is not None: destination.mkdir()
            for directory, directories, files, dirfd in os.fwalk('.', dir_fd=rootfd, follow_symlinks=False):
                relative = Path(directory)
                if destination is not None: (destination / relative).mkdir(exist_ok=True)
                for name in [*directories, *files]:
                    info = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
                    if sensitive(name) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                        raise ValueError('Linked/sensitive/special input preserved')
                    count += 1
                    if count > 10000: raise ValueError('Input exceeds10000entries')
                for name in files:
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
                    with os.fdopen(fd, 'rb') as stream:
                        info = os.fstat(stream.fileno())
                        if not stat.S_ISREG(info.st_mode): raise ValueError('Changed non-regular source refused')
                        h = hashlib.sha256(); target = (destination / relative / name).open('xb') if destination is not None else None
                        try:
                            while block := stream.read(1024 * 1024):
                                size += len(block)
                                if size > MAX_INPUT: raise ValueError('Input exceeds128MiB')
                                h.update(block)
                                if target is not None: target.write(block)
                        finally:
                            if target is not None: target.close()
                        result[str(relative / name)] = {'sha256': h.hexdigest(), 'mode': info.st_mode & 0o777}
                        if destination is not None: (destination / relative / name).chmod(info.st_mode & 0o777)
        finally: os.close(rootfd)
        return hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if destination is None: return inventory()
    original = inventory()
    if inventory(destination) != original or inventory() != original: raise ValueError('Input changed while freezing snapshot')
    return original


def owned_task(state, source, out):
    state, source, out = concrete(state), concrete(source), concrete(out)
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out) or out.is_relative_to(state) or state.is_relative_to(out): raise ValueError('Select new disjoint task output; existing work preserved')
    out.mkdir(parents=True, mode=0o700)
    original = snapshot(source, out / 'input')
    (out / 'output').mkdir()
    save(out / 'OWNERSHIP.json', {'source': str(source), 'source_sha256': original, 'identity': identity()})
    return out


def container_args(image, task, name, arguments, binary=None):
    return [binary or docker_binary(), 'run', '--name', name, '--init', '--pull=never', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '256', '--memory', '4g', '--cpus', '2', '--tmpfs', '/tmp:rw,nosuid,nodev,size=512m,mode=1777', '--mount', 'type=bind,src=' + str(task / 'input') + ',dst=/input,readonly', '--mount', 'type=bind,src=' + str(task / 'output') + ',dst=/output', '--interactive', image, *arguments]


def validate_call(name, arguments):
    if name not in STATIC_TOOLS: raise ValueError('Tool is outside the enforced static policy')
    if not isinstance(arguments, dict): raise ValueError('Tool arguments must be an object')
    if name == 'open_binary' and arguments.get('provider_id', 'ghidra') != 'ghidra': raise ValueError('Only reviewed Ghidra binding is selected')
    if name == 'open_binary': arguments = {**arguments, 'provider_id': 'ghidra'}
    return arguments


def map_paths(value, source, task, key=None):
    if isinstance(value, dict): return {k: map_paths(v, source, task, k) for k, v in value.items()}
    if isinstance(value, list): return [map_paths(v, source, task, key) for v in value]
    if isinstance(value, str) and key in {'path', 'input_path', 'binary_path', 'left_path', 'right_path', 'save_path', 'output_path', 'output_dir', 'snapshot_path'} and value.startswith('/'):
        p = Path(os.path.normpath(value))
        if p.is_relative_to(source): return '/input/' + str(p.relative_to(source))
        if p.is_relative_to(task / 'output'): return '/output/' + str(p.relative_to(task / 'output'))
        # Normalize traversal before admitting guest paths.
        normalized = Path(os.path.normpath(value))
        if normalized.is_relative_to('/input') or normalized.is_relative_to('/output'): return str(normalized)
        raise ValueError('Path is outside explicit task input/output')
    return value


def cleanup_container(name, task, client):
    observed = json.loads(capture(client, [client.binary, 'inspect', name]))[0]
    save(task / 'container-final.json', {'Id': observed['Id'], 'State': observed['State'], 'Mounts': observed['Mounts'], 'HostConfig': {k: observed['HostConfig'].get(k) for k in ('NetworkMode', 'PidMode', 'Init', 'Privileged', 'CapDrop', 'SecurityOpt', 'ReadonlyRootfs', 'PidsLimit', 'Memory', 'NanoCpus', 'Tmpfs')}})
    if observed['State']['Running']:
        # Own container only, native Docker lifecycle. A timeout never starts replacement work.
        capture(client, [client.binary, 'stop', '--time', '20', name], timeout=40)
        raise ValueError('Upstream did not stop normally; owned container stopped, acceptance failed')
    capture(client, [client.binary, 'rm', name])
    return observed['State']['ExitCode']


def mcp(state, source, out, client):
    built = verify(state, built=True, client=client); task = owned_task(state, source, out)
    name = 'nstack-rea-' + uuid.uuid4().hex
    argv = container_args(built['image_id'], task, name, ['mcp'], client.binary)
    pending = {}; lock = threading.Lock(); emit_lock = threading.Lock(); errors = []; calls = []; rejected = []
    with (task / 'upstream.stderr').open('w') as stderr:
        process = subprocess.Popen(argv, env=client.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        def emit(document):
            with emit_lock:
                sys.stdout.write(json.dumps(document, separators=(',', ':')) + '\n'); sys.stdout.flush()
        def reply_error(id, text): emit({'jsonrpc': '2.0', 'id': id, 'error': {'code': -32602, 'message': text}})
        def responses():
            try:
                while line := process.stdout.readline(MAX_MESSAGE + 1):
                    if len(line) > MAX_MESSAGE or not line.endswith(b'\n'): raise ValueError('Oversized/malformed upstream frame')
                    message = json.loads(line)
                    if 'method' in message and 'id' in message:
                        # No model sampling, elicitation, host roots or other server-to-client execution.
                        with lock:
                            process.stdin.write((json.dumps({'jsonrpc':'2.0','id':message['id'],'error':{'code':-32601,'message':'Client-side requests disabled by static controller'}})+'\n').encode()); process.stdin.flush()
                        continue
                    method = pending.pop(message.get('id'), None)
                    if method == 'tools/list' and 'result' in message:
                        message['result']['tools'] = [t for t in message['result'].get('tools', []) if t.get('name') in STATIC_TOOLS]
                    emit(message)
            except BaseException as error: errors.append(str(error))
        reader = threading.Thread(target=responses, daemon=True); reader.start()
        try:
            for line in sys.stdin.buffer:
                if len(line) > 16 * 1024 * 1024: raise ValueError('Oversized client request')
                message = json.loads(line); method = message.get('method'); id = message.get('id')
                try:
                    if method == 'tools/call':
                        params = message.get('params', {}); tool = params.get('name')
                        arguments = validate_call(tool, params.get('arguments', {}))
                        message['params']['arguments'] = map_paths(arguments, concrete(source), task)
                        calls.append(tool)
                    elif method not in {'initialize','ping','tools/list','prompts/list','prompts/get','completion/complete','notifications/initialized','notifications/cancelled','logging/setLevel'}:
                        raise ValueError('Method is outside the static controller protocol')
                    if id is not None:
                        if id in pending: raise ValueError('Duplicate pending request id')
                        pending[id] = method
                    with lock: process.stdin.write((json.dumps(message,separators=(',',':'))+'\n').encode()); process.stdin.flush()
                except ValueError as error:
                    rejected.append({'method': method, 'tool': message.get('params', {}).get('name'), 'reason': str(error)})
                    if id is not None: reply_error(id, str(error))
            process.stdin.close(); process.wait(timeout=120); reader.join(timeout=5)
        finally:
            if process.poll() is None:
                capture(client, [client.binary, 'stop', '--time', '20', name], timeout=40)
                process.wait(timeout=30)
            exit_code = cleanup_container(name, task, client)
            save(task / 'CONTROLLER.json', {'image_id': built['image_id'], 'identity': identity(), 'calls': calls, 'rejected': rejected, 'errors': errors, 'container_exit': exit_code, 'static_tools': sorted(STATIC_TOOLS), 'input_unchanged': snapshot(concrete(source), None) == json.loads((task / 'OWNERSHIP.json').read_text())['source_sha256']})
    if errors or exit_code: raise ValueError('MCP upstream/cleanup failed; retained task evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--docker-host', help='Existing local unix:///absolute/socket; inherited Docker settings are ignored')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--acquired', type=Path)
    sub.add_parser('verify'); sub.add_parser('metadata'); sub.add_parser('build')
    p = sub.add_parser('mcp'); p.add_argument('--input', required=True, type=Path); p.add_argument('--outdir', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'prepare': result = prepare(args.state, args.acquired)
        elif args.command == 'verify' and not (args.state / 'BUILD.json').exists(): result = verify(args.state)
        else:
            with LocalDocker(args.docker_host) as client:
                if args.command == 'verify': result = verify(args.state, built=True, client=client)
                elif args.command == 'metadata': result = metadata_gate(concrete(args.state), client)
                elif args.command == 'build': result = build(args.state, client)
                else: mcp(args.state, args.input, args.outdir, client); return
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError, tarfile.TarError, zipfile.BadZipFile) as error: parser.exit(1, str(error) + '\n')


if __name__ == '__main__': main()
