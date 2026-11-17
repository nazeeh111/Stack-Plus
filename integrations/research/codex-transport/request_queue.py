#!/usr/bin/env python3
"""Task-owned regular-file transport between trusted controller and host.

This directory is outside every model/evaluator/candidate mount. It carries
only prepared agent dispatch, not a generic command-execution service.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time

_spec = importlib.util.spec_from_file_location(
    'nstack_private_atomic', Path(__file__).with_name('docker_guard.py'))
_atomic = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_atomic)
MAX_BYTES = 4 * 1024 * 1024


class QueueRefusal(ValueError):
    pass


def read_object(path: Path) -> dict:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > MAX_BYTES:
            raise QueueRefusal('queue entry is not a bounded owner-controlled regular file')
        with os.fdopen(descriptor, 'r', closefd=False) as stream:
            value = json.load(stream)
    finally:
        os.close(descriptor)
    if not isinstance(value, dict):
        raise QueueRefusal('queue entry has an invalid shape')
    return value


def queue_settings(root: Path) -> dict:
    if (not root.is_absolute() or root.resolve() != root or root.is_symlink()
            or not root.is_dir() or root.stat().st_uid != os.getuid()
            or root.stat().st_mode & 0o077):
        raise QueueRefusal('queue root must be canonical private owner-controlled directory')
    value = read_object(root / 'queue.json')
    if (not re.fullmatch(r'[0-9a-f]{32}', value.get('owner', ''))
            or not 1 <= value.get('request_timeout_seconds', 0) <= 600):
        raise QueueRefusal('queue policy is absent or invalid')
    for name in ('requests', 'responses'):
        path = root / name
        if path.is_symlink() or not path.is_dir() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
            raise QueueRefusal('queue subdirectory is not private and owner-controlled')
    return value


def submit(root: Path, container: str, cwd: str, arguments: list[str], *, role: str) -> dict:
    settings = queue_settings(root)
    if (not container or not cwd.startswith('/') or not arguments
            or not re.fullmatch(r'[a-z_]+\.sh', role)
            or not all(isinstance(x, str) and '\0' not in x for x in arguments)):
        raise QueueRefusal('invalid prepared agent dispatch')
    nonce = secrets.token_hex(16)
    created = time.time(); timeout = settings['request_timeout_seconds']
    request = {'schema_version': 1, 'owner': settings['owner'], 'request_id': nonce,
               'created_at': created, 'expires_at': created + timeout + 30,
               'container': container, 'cwd': cwd, 'role': role, 'arguments': arguments}
    if len(json.dumps(request).encode()) > MAX_BYTES:
        raise QueueRefusal('prepared request exceeds bound')
    _atomic.atomic_json(root / 'requests' / (nonce + '.json'), request)
    response_path = root / 'responses' / (nonce + '.json')
    deadline = time.monotonic() + timeout + 35
    while time.monotonic() < deadline:
        if response_path.exists():
            response = read_object(response_path)
            if response.get('request_id') != nonce or response.get('owner') != settings['owner']:
                raise QueueRefusal('response identity differs')
            return response
        time.sleep(0.1)
    # Request remains for host reconciliation. Never infer zero model use or
    # submit it again after this timeout.
    raise QueueRefusal('prepared dispatch timed out; inference state requires reconciliation')


def pending(root: Path, completed: set[str]):
    settings = queue_settings(root)
    for path in sorted((root / 'requests').glob('*.json')):
        if path.stem in completed:
            continue
        if not re.fullmatch(r'[0-9a-f]{32}', path.stem):
            raise QueueRefusal('unexpected queue request name')
        value = read_object(path)
        if (value.get('schema_version') != 1 or value.get('owner') != settings['owner']
                or value.get('request_id') != path.stem
                or not isinstance(value.get('expires_at'), (int, float))
                or value['expires_at'] < time.time()):
            raise QueueRefusal('prepared request identity or deadline is invalid')
        yield value


def finish(root: Path, request: dict, *, success: bool, answer: str = '', usage=None):
    response = {'schema_version': 1, 'owner': queue_settings(root)['owner'],
                'request_id': request['request_id'], 'success': success,
                'answer': answer, 'usage': usage}
    if len(json.dumps(response).encode()) > MAX_BYTES:
        raise QueueRefusal('native response exceeds queue bound')
    _atomic.atomic_json(root / 'responses' / (request['request_id'] + '.json'), response)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container', required=True)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--role', required=True)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
        response = submit(Path(os.environ['NSTACK_NATIVE_QUEUE']), args.container, args.cwd,
                          arguments, role=args.role)
        if not response.get('success'):
            raise QueueRefusal('native prepared dispatch failed; inspect trusted receipt')
        print(response['answer'])
        print(json.dumps({'usage': response['usage']}))
        return 0
    except (QueueRefusal, OSError, KeyError, ValueError):
        print('research prepared dispatch refused or uncertain; inspect trusted receipt', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
