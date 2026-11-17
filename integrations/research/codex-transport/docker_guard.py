#!/usr/bin/env python3
"""Controller-only Docker ownership guard; never present in a model executor.

The ordinary original engine keeps its Docker commands. Launch labels and a
private ledger make cleanup depend on trusted launch identity, not writable
CID/name metadata. No daemon, proxy, credential loading or scientific logic.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import subprocess
import sys

OWNER = 'nstack.research.owner'
LAUNCH = 'nstack.research.launch'
ID = re.compile(r'[0-9a-f]{64}\Z')
IMAGE = re.compile(r'sha256:[0-9a-f]{64}\Z')
VALUE_OPTIONS = {'--cidfile', '--name', '--network', '--user', '--pids-limit',
                 '--cpus', '--memory', '--memory-swap', '--tmpfs', '--env', '-e',
                 '--volume', '-v', '--mount', '--workdir', '-w', '--label',
                 '--hostname', '--add-host', '--security-opt', '--cap-drop',
                 '--entrypoint', '--env-file', '--pull'}
FLAG_OPTIONS = {'--rm', '-i', '-t', '-d', '--detach', '--init', '--read-only',
                '--interactive', '--tty'}


class GuardRefusal(ValueError):
    pass


def atomic_json(path: Path, value: dict):
    temp = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def memory_bytes(value: str) -> int:
    match = re.fullmatch(r'([1-9][0-9]*)([kmgt]?)b?', value.lower())
    if not match:
        raise GuardRefusal('unsupported Docker memory bound')
    return int(match[1]) * 1024 ** ('kmgt'.find(match[2]) + 1 if match[2] else 0)


class DockerGuard:
    def __init__(self, policy: dict, *, capture=subprocess.run):
        self.policy = policy
        self.capture = capture
        self.binary = policy['real_docker']
        self.owner = policy['owner']
        self.ledger = Path(policy['ledger'])
        if (not Path(self.binary).is_absolute() or not re.fullmatch(r'[0-9a-f]{32}', self.owner)
                or not self.ledger.is_dir() or self.ledger.is_symlink()
                or self.ledger.resolve() != self.ledger):
            raise GuardRefusal('invalid trusted Docker guard policy')
        for rule in policy.get('bind_roots', []):
            root = rule.get('root')
            if (not isinstance(root, str) or not root.startswith('/') or root == '/'
                    or type(rule.get('writable')) is not bool
                    or str(self.ledger) == root or str(self.ledger).startswith(root.rstrip('/') + '/')
                    or root.startswith(str(self.ledger).rstrip('/') + '/')):
                raise GuardRefusal('private ownership ledger must be disjoint from child bind roots')
        # Only this controller owns this environment; no user Docker home or keys.
        self.env = {'PATH': '/opt/docker/bin:/usr/local/bin:/usr/bin:/bin',
                    'HOME': policy['empty_home'], 'DOCKER_CONFIG': policy['empty_config'],
                    'DOCKER_HOST': 'unix:///var/run/docker.sock', 'LANG': 'C'}

    def check_bind(self, key: str, value: str) -> str:
        # Accept only the exact grammar used by the frozen original builders.
        # Docker's full CSV/alias/boolean grammar is intentionally unsupported.
        if any(character in value for character in ('"', "'", "\\", "\n", "\r", "\0")):
            raise GuardRefusal('quoted or escaped child bind syntax is unsupported')
        if key == '--mount':
            parts = {}
            for piece in value.split(','):
                name, separator, setting = piece.partition('=')
                if name not in {'type', 'src', 'dst', 'readonly'} or name in parts:
                    raise GuardRefusal('duplicate, aliased or unsupported child mount field')
                if name == 'readonly':
                    if separator:
                        raise GuardRefusal('only bare readonly is supported')
                    parts[name] = True
                else:
                    if not separator or not setting:
                        raise GuardRefusal('incomplete child mount field')
                    parts[name] = setting
            if parts.get('type') != 'bind' or 'src' not in parts or 'dst' not in parts:
                raise GuardRefusal('child mount is not a complete reviewed bind')
            source, destination = parts['src'], parts['dst']
            writable = 'readonly' not in parts
        else:
            pieces = value.split(':')
            if len(pieces) not in (2, 3):
                raise GuardRefusal('unsupported child bind syntax')
            source, destination = pieces[:2]
            mode = pieces[2] if len(pieces) == 3 else 'rw'
            if mode not in ('rw', 'ro'):
                raise GuardRefusal('unsupported child bind mode')
            writable = mode == 'rw'
        if (not source.startswith('/') or not destination.startswith('/')
                or '..' in PurePosixPath(destination).parts):
            raise GuardRefusal('relative or escaping child bind is unsupported')
        destination = str(PurePosixPath(destination))
        actual = str(Path(source).resolve(strict=True))
        if any(character in actual or character in destination
               for character in (',', ':', '"', "'", '\\', '\n', '\r', '\0')):
            raise GuardRefusal('canonical child bind contains reserved mount syntax')
        if any(fragment in actual or fragment in destination
               for fragment in self.policy['forbidden_mount_fragments']):
            raise GuardRefusal('canonical child mount exposes forbidden control data')
        if actual != '/dev/null' or writable:
            allowed = [rule for rule in self.policy.get('bind_roots', [])
                       if actual == rule['root'] or actual.startswith(rule['root'].rstrip('/') + '/')]
            if not allowed or (writable and not any(rule['writable'] for rule in allowed)):
                raise GuardRefusal('child host bind is outside reviewed run roots')
        # Forward exactly the checked interpretation, never the original CSV
        # spelling or a symlink alias that the daemon could interpret differently.
        if key == '--mount':
            return 'type=bind,src=' + actual + ',dst=' + destination + (',readonly' if not writable else '')
        return actual + ':' + destination + (':rw' if writable else ':ro')

    def inspect_owned(self, name: str, *, require_agent=False) -> str | None:
        if not name or name.startswith('-') or any(c in name for c in '\n\r\0'):
            raise GuardRefusal('unsafe Docker cleanup reference')
        result = self.capture([self.binary, 'inspect', '--type', 'container',
                               '--format', '{{json .Id}} {{json .Config.Labels}}', name],
                              env=self.env, capture_output=True, text=True, timeout=10)
        if result.returncode:
            # Recognize only the native exact missing-object diagnostic. All
            # daemon/permission/parse failures retain recovery state.
            missing = ('Error: No such container: ' + name, 'Error: No such object: ' + name,
                       'Error response from daemon: No such container: ' + name)
            if result.stderr.strip() in missing:
                return None
            raise GuardRefusal('Docker ownership inspection failed')
        raw_id, separator, raw_labels = result.stdout.strip().partition(' ')
        try:
            ident = json.loads(raw_id)
            labels = json.loads(raw_labels) if separator else None
        except (TypeError, ValueError):
            raise GuardRefusal('invalid Docker ownership response') from None
        if (not isinstance(ident, str) or not ID.fullmatch(ident)
                or not isinstance(labels, dict) or labels.get(OWNER) != self.owner
                or not re.fullmatch(r'[0-9a-f]{32}', labels.get(LAUNCH, ''))):
            raise GuardRefusal('Docker object is outside this trusted run')
        record_path = self.ledger / (labels[LAUNCH] + '.json')
        if not record_path.is_file() or record_path.is_symlink():
            raise GuardRefusal('Docker launch has no private ownership record')
        record = json.loads(record_path.read_text())
        if record.get('owner') != self.owner or record.get('launch') != labels[LAUNCH]:
            raise GuardRefusal('Docker launch ownership record differs')
        if require_agent and record.get('agent') is not True:
            raise GuardRefusal('exec target is not a prepared model-role child')
        return ident

    def prepare_run(self, arguments: list[str]) -> list[str]:
        options = []; index = 0
        values = {}
        while index < len(arguments) and arguments[index].startswith('-'):
            token = arguments[index]
            if '=' in token:
                key, value = token.split('=', 1)
                if key not in VALUE_OPTIONS:
                    raise GuardRefusal('unreviewed Docker run option')
                index += 1
            elif token in VALUE_OPTIONS:
                if index + 1 >= len(arguments):
                    raise GuardRefusal('incomplete Docker run option')
                key, value = token, arguments[index + 1]; index += 2
            elif token in FLAG_OPTIONS:
                options.append((token, None)); index += 1; continue
            else:
                raise GuardRefusal('unreviewed Docker run option')
            if key == '--label' and value.split('=', 1)[0] in {OWNER, LAUNCH}:
                raise GuardRefusal('original command cannot supply trusted ownership')
            if key in {'--volume', '-v', '--mount'}:
                # The trusted original controller's children never need a
                # daemon socket, native auth home, private queue or ledger.
                if any(x in value for x in self.policy['forbidden_mount_fragments']):
                    raise GuardRefusal('forbidden child Docker mount')
                value = self.check_bind(key, value)
            if key == '--pull' and value != 'never':
                raise GuardRefusal('child image pulling is forbidden')
            profile = self.policy.get('agent_seccomp_path')
            if (key == '--security-opt' and value != 'no-new-privileges'
                    and not (profile and value == 'seccomp=' + profile)):
                raise GuardRefusal('unreviewed child security option')
            if key == '--cap-drop' and value != 'ALL':
                raise GuardRefusal('child capability set differs')
            if key == '--env-file' and value != self.policy['empty_env_file']:
                raise GuardRefusal('unreviewed child environment file')
            options.append((key, value)); values.setdefault(key, []).append(value)
        if index >= len(arguments) or arguments[index] not in self.policy['images']:
            raise GuardRefusal('child image is not an immutable reviewed image')
        if not IMAGE.fullmatch(arguments[index]):
            raise GuardRefusal('child image identity is not exact')
        if values.get('--network') != ['none']:
            raise GuardRefusal('child networking is outside the reviewed route')
        for key, maximum in [('--cpus', self.policy['max_cpus']),
                             ('--pids-limit', self.policy['max_pids'])]:
            if key in values and (len(values[key]) != 1 or not 0 < float(values[key][0]) <= maximum):
                raise GuardRefusal('child resource limit is outside campaign bounds')
        for key in ('--memory', '--memory-swap'):
            if key in values and (len(values[key]) != 1 or memory_bytes(values[key][0]) > self.policy['max_memory_bytes']):
                raise GuardRefusal('child memory is outside campaign bounds')
        additions = ['--label', OWNER + '=' + self.owner]
        launch = secrets.token_hex(16)
        additions += ['--label', LAUNCH + '=' + launch]
        present = {key for key, value in options}
        for key, value in [('--cpus', str(self.policy['max_cpus'])),
                           ('--pids-limit', str(self.policy['max_pids'])),
                           ('--memory', str(self.policy['max_memory_bytes'])),
                           ('--memory-swap', str(self.policy['max_memory_bytes'])),
                           ('--cap-drop', 'ALL'),
                           ('--pull', 'never')]:
            if key not in present:
                additions += [key, value]
        if 'no-new-privileges' not in values.get('--security-opt', []):
            additions += ['--security-opt', 'no-new-privileges']
        if '--read-only' not in present:
            additions.append('--read-only')
        atomic_json(self.ledger / (launch + '.json'), {
            'owner': self.owner, 'launch': launch,
            'agent': 'nstack.research.agent=true' in values.get('--label', []),
            'argv_sha256': hashlib.sha256(json.dumps(arguments).encode()).hexdigest(),
            'state': 'launch_prepared'})
        normalized = []
        for key, value in options:
            normalized.append(key)
            if value is not None: normalized.append(value)
        return ['run', *additions, *normalized, *arguments[index:]]

    def prepare(self, arguments: list[str]) -> list[str]:
        if not arguments:
            raise GuardRefusal('empty Docker command')
        if arguments[0] == 'run':
            return self.prepare_run(arguments[1:])
        if arguments[0] in {'rm', 'stop', 'kill'}:
            flags = [v for v in arguments[1:] if v.startswith('-')]
            if any(v not in {'-f', '--force'} for v in flags):
                raise GuardRefusal('unreviewed cleanup flag')
            refs = [v for v in arguments[1:] if not v.startswith('-')]
            ids = [ident for ref in refs if (ident := self.inspect_owned(ref)) is not None]
            return [arguments[0], *flags, *ids] if ids else []
        if arguments[0] == 'exec':
            # Actual original exec site: container_agent.sh prepared session
            # commands. Never allow it to target the socket-bearing controller,
            # a final evaluator, or an unrelated named container.
            index = 1
            while index < len(arguments) and arguments[index].startswith('-'):
                option = arguments[index]
                if option in {'-i', '-t', '--interactive', '--tty'}:
                    index += 1
                elif option in {'-w', '--workdir', '-e', '--env'} and index + 1 < len(arguments):
                    index += 2
                else:
                    raise GuardRefusal('unreviewed prepared exec option')
            if index >= len(arguments):
                raise GuardRefusal('prepared exec target is absent')
            ident = self.inspect_owned(arguments[index], require_agent=True)
            if ident is None:
                raise GuardRefusal('prepared exec target no longer exists')
            return [*arguments[:index], ident, *arguments[index + 1:]]
        if arguments[0] not in {'inspect', 'ps', 'info', 'version',
                                 'image', 'logs', 'wait'}:
            raise GuardRefusal('unreviewed controller Docker command')
        return arguments

    def execute(self, arguments: list[str]) -> int:
        command = self.prepare(arguments)
        if not command:
            return 0
        # Preserve original candidate stdio, session IDs and exit status.
        return subprocess.call([self.binary, *command], env=self.env)


def main():
    os.umask(0o077)
    try:
        policy_path = Path(os.environ['NSTACK_DOCKER_GUARD_POLICY'])
        if not policy_path.is_absolute() or policy_path.is_symlink():
            raise GuardRefusal('trusted Docker policy path required')
        guard = DockerGuard(json.loads(policy_path.read_text()))
        return guard.execute(sys.argv[1:])
    except GuardRefusal as error:
        if 'guard' in locals():
            atomic_json(guard.ledger / ('refusal-' + secrets.token_hex(8) + '.json'), {
                'reason': str(error),
                'argv_sha256': hashlib.sha256(json.dumps(sys.argv[1:]).encode()).hexdigest()})
        print('research Docker guard refused: ' + str(error), file=sys.stderr)
        return 125
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print('research Docker guard refused an unowned or unsupported operation', file=sys.stderr)
        return 125


if __name__ == '__main__':
    raise SystemExit(main())
