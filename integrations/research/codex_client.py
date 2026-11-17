#!/usr/bin/env python3
"""Discover the reviewed client first, or explicitly acquire it privately.

No global installation, config/profile edit, account setup, or auth-store access.
Only --version is executed; normal subscription preflight belongs to dispatch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
PIN = json.loads((HERE/'CODEX-CLIENT.json').read_text())


def compatible(path):
    if not path: return None
    candidate = Path(path).expanduser().resolve(strict=True)
    if not candidate.is_file() or not os.access(candidate, os.X_OK): return None
    result = subprocess.run([str(candidate), '--version'], capture_output=True, text=True,
                            timeout=10, env={'PATH': '/usr/bin:/bin'})
    return candidate if result.returncode == 0 and result.stdout.strip() == PIN['version'] else None


def discover(explicit=None, state=None):
    choices = [explicit] if explicit else [
        shutil.which('codex'),
        Path.home()/'Library/Application Support/nstack/bin/0.169.0/codex',
        Path(state)/'codex' if state else None]
    for path in choices:
        if not path: continue
        try: found = compatible(path)
        except (OSError, subprocess.SubprocessError): found = None
        if found: return found
    return None


def acquire(state):
    if (platform.system(), platform.machine()) != ('Darwin', 'arm64'):
        raise ValueError('This exact private client pin is only reviewed for Darwin arm64')
    state = Path(state).expanduser().absolute()
    if state.exists() or state.is_symlink():
        raise ValueError('Preserve existing state; choose a fresh private client directory')
    if state.parent.resolve() != state.parent:
        raise ValueError('Private client parent must be canonical')
    # Disposable downloads/extraction stay off synced folders. Only the verified
    # executable, first-party notices and acquisition receipt become durable.
    with tempfile.TemporaryDirectory(prefix='nstack-research-client-', dir='/private/tmp') as temporary:
        archive = Path(temporary)/'client.tar.gz'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(PIN['asset']['browser_download_url'], timeout=120) as response, archive.open('wb') as output:
            size = 0
            while chunk := response.read(1024*1024):
                size += len(chunk)
                if size > PIN['asset']['size']: raise ValueError('Client artifact exceeds frozen size')
                output.write(chunk)
        if (size != PIN['asset']['size'] or 'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest() != PIN['asset']['digest']):
            raise ValueError('Official client archive digest/size differs')
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            if len(members) != 1 or members[0].name != PIN['archive_member'] or not members[0].isfile():
                raise ValueError('Official client archive member differs')
            raw = bundle.extractfile(members[0]).read()
        executable = Path(temporary)/'codex'; executable.write_bytes(raw); executable.chmod(0o500)
        if compatible(executable) is None: raise ValueError('Official client version differs')
        state.mkdir(mode=0o700)
        shutil.copyfile(executable, state/'codex'); (state/'codex').chmod(0o500)
        for name in ('Codex-LICENSE', 'Codex-NOTICE'):
            shutil.copyfile(HERE/'licenses'/name, state/name)
        (state/'ACQUISITION.json').write_text(json.dumps({
            'pin': PIN, 'binary_sha256': hashlib.sha256(raw).hexdigest(),
            'scope': 'Private client prerequisite only; no model, login or research acceptance'}, indent=2)+'\n')
        return state/'codex'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', help='Existing caller-selected compatible client')
    parser.add_argument('--state', help='Fresh durable private directory, used only when acquisition is necessary')
    parser.add_argument('--acquire', action='store_true', help='Allow exact free official acquisition if discovery fails')
    args = parser.parse_args()
    try:
        client = discover(args.client, args.state)
        if client is None:
            if not args.acquire or not args.state: raise ValueError('Reviewed Codex0.169.0 required; select compatible existing client or explicit private acquisition')
            client = acquire(args.state)
        print(json.dumps({'client': str(client), 'version': PIN['version'],
                          'scope': 'Compatible prerequisite only; no inference/auth/setup/config change'}))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
