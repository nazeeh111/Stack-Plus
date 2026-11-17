#!/usr/bin/env python3
"""Trusted original prepared-dispatch seam; no model/API/client auth here."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

_spec = importlib.util.spec_from_file_location('nstack_private_queue', Path(__file__).with_name('request_queue.py'))
queue = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(queue)
_guard_spec = importlib.util.spec_from_file_location('nstack_controller_guard', Path(__file__).with_name('docker_guard.py'))
guard_module = importlib.util.module_from_spec(_guard_spec); _guard_spec.loader.exec_module(guard_module)


def native_role(value: str) -> str:
    permitted = {'task.sh', 'idea.sh', 'run.sh', 'variant_agent.sh',
                 'posthoc_agent.sh', 'paper.sh', 'paper_edit.sh'}
    if value not in permitted:
        raise ValueError('original scientific role is unsupported')
    return value


def emit(response):
    if not response.get('success'):
        raise ValueError('native dispatch failed or uncertain; retain trusted receipt')
    print(response['answer'])
    print(json.dumps({'usage': response['usage']}))


def dispatch(container, cwd, role, arguments):
    emit(queue.submit(Path(os.environ['NSTACK_NATIVE_QUEUE']), container, cwd,
                      arguments, role=native_role(role)))


def masks(source: str, destination: str, role: str):
    """Cover sealed-data copies in the original drafting/reviewer workspaces.

    Original task-source masks remain active. These extra workspace masks are
    necessary because staging/alignment copies may sit below /workspace too.
    No model can receive the raw master dataset or private control directory.
    """
    role = native_role(role)
    policy = json.loads(Path(os.environ['NSTACK_DOCKER_GUARD_POLICY']).read_text())
    guard = guard_module.DockerGuard(policy)
    guard.check_bind('--mount', f'type=bind,src={source},dst={destination},readonly')
    root = Path(source).resolve(strict=True)
    if not root.is_dir() or (root.name == 'final' and root.parent.name == 'resources'):
        raise ValueError('workspace cannot be the sealed data root')
    empty = Path(os.environ['NSTACK_NATIVE_EMPTY_MASK'])
    if empty.is_symlink() or not empty.is_dir() or any(empty.iterdir()):
        raise ValueError('sealed mask directory is not empty and canonical')
    entries = {}
    ignored = {'.venv', '.git', '.agent_home', '__pycache__', 'node_modules',
               '.codex', '.ssh', '.aws', '.docker'}
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name not in ignored]
        here = Path(current)
        if here.name == 'resources' and ((here/'final').exists() or (here/'final').is_symlink()):
            final = here/'final'
            if final.is_symlink() or not final.is_dir():
                raise ValueError('sealed final directory must be a real directory')
            target = destination.rstrip('/') + '/' + final.relative_to(root).as_posix()
            entries[target] = f'{empty}:{target}:ro'
            directories.remove('final')
        if role != 'task.sh' and 'evaluate_final.py' in files:
            target = destination.rstrip('/') + '/' + (here/'evaluate_final.py').relative_to(root).as_posix()
            entries[target] = f'/dev/null:{target}:ro'
    for target in sorted(entries):
        sys.stdout.buffer.write(b'-v\0' + entries[target].encode() + b'\0')


def oneshot(role, cwd, inner_count, command):
    if (command[:2] != ['docker', 'run'] or type(inner_count) is not int
            or not 1 <= inner_count < len(command)-2):
        raise ValueError('original one-shot Docker command differs')
    inner = command[-inner_count:]
    prepared = command[:-inner_count]
    if prepared.count('--name') > 1:
        raise ValueError('ambiguous original role name')
    if '--name' in prepared:
        name = prepared[prepared.index('--name') + 1]
        name_arguments = []
    else:
        name = 'nstack-native-role-' + secrets.token_hex(8)
        name_arguments = ['--name', name]
    ident = None
    # Keep all original prepared mounts/modes/masks/limits. Only replace its
    # inner model CLI with a lifetime holder for the official remote executor.
    prepared = [*prepared[:2], '--detach', *name_arguments, *prepared[2:],
                '/bin/sh', '-c', 'exec sleep 900']
    try:
        result = subprocess.run(prepared, capture_output=True, text=True, timeout=30, check=True)
        ident = result.stdout.strip()
        if len(ident) != 64 or any(c not in '0123456789abcdef' for c in ident):
            raise ValueError('owned role container identity was not returned')
        dispatch(ident, cwd, role, inner)
    finally:
        # Guard inspects owner+private launch identity and removes immutable ID.
        subprocess.run(['docker', 'rm', '-f', ident or name], capture_output=True, text=True,
                       timeout=20, check=True)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['dispatch', 'oneshot', 'masks'], required=True)
    parser.add_argument('--role', required=True)
    parser.add_argument('--cwd')
    parser.add_argument('--source'); parser.add_argument('--destination')
    parser.add_argument('--container')
    parser.add_argument('--inner-count', type=int)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if os.environ.get('NSTACK_NATIVE_BRIDGE') != '1':
            raise ValueError('explicit native bridge mode is required')
        arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
        if args.mode == 'masks':
            masks(args.source, args.destination, args.role)
        elif args.mode == 'dispatch':
            if not args.container: raise ValueError('prepared role container required')
            dispatch(args.container, args.cwd, args.role, arguments)
        else:
            oneshot(args.role, args.cwd, args.inner_count, arguments)
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError):
        print('original prepared native dispatch refused or uncertain', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
