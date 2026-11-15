#!/usr/bin/env python3
"""Pinned private REA runtime and guarded static artifact evidence."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import signal
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid

VERSION = '6.9.0'
REVISION = 'd74549e495c58eb4a560279fd9f05508401ea0a0'
PACKAGE_URL = 'https://registry.npmjs.org/rea-agents/-/rea-agents-6.9.0.tgz'
PACKAGE_SHA256 = '322338a1505e2557702a16012e7d46abdb5729641d98938662762dfbfb79262a'
PACKAGE_MANIFEST = '9183f7a83516548cff22f3ad9299d0578e653f04bf8b2b456d3a7b404d85c269'
NODE_VERSION = '24.22.1'
NODE_URL = 'https://nodejs.org/dist/v24.22.1/node-v24.22.1-darwin-arm64.tar.gz'
NODE_SHA256 = '89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7'
NODE_MANIFEST = '0541bb8d932eebfad2d43096cab4bd02486d90b9e4e838fb38e3be5a4797300d'
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
MAX_BYTES = 128 * 1024 * 1024
MAX_FILES = 10000


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def concrete(path):
    path = Path(os.path.abspath(path))
    if path.resolve() != path:
        raise ValueError('Linked path preserved; select its explicit canonical target')
    return path


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')
    Path(path).chmod(0o600)


def manifest(root):
    rows = {}
    for p in sorted(Path(root).rglob('*')):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            rows[rel] = {'link': os.readlink(p)}
        elif p.is_file():
            rows[rel] = {'sha256': digest(p), 'mode': p.stat().st_mode & 0o777}
        elif not p.is_dir():
            raise ValueError('Special file preserved: ' + str(p))
    return rows


def manifest_hash(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def runtime_root(state=STATE):
    return concrete(concrete(state) / 'native-tools/rea' / VERSION)


def host():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('This pinned route requires Apple Silicon macOS')
    if not Path('/usr/bin/sandbox-exec').is_file():
        raise ValueError('Required OS sandbox unavailable; no unrestricted fallback')


@contextmanager
def writer(parent):
    parent = concrete(parent)
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = parent / '.writer.lock'
    if lock.is_symlink():
        raise ValueError('Linked writer lock preserved')
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def capture(argv, cwd=None, env=None, timeout=120):
    process = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    return {'argv': [str(x) for x in argv], 'exit_code': process.returncode,
            'stdout': stdout, 'stderr': stderr}


def checked(argv, **kwargs):
    result = capture(argv, **kwargs)
    if result['exit_code']:
        raise ValueError('Native operation failed or rejected: ' + json.dumps(result))
    return result


def safe_extract(archive, destination, prefix):
    """Extract only regular files/directories and internal symbolic links, never hooks."""
    destination = concrete(destination)
    destination.mkdir(mode=0o700)
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        if len(members) > 30000 or sum(m.size for m in members) > 1024 * 1024 * 1024:
            raise ValueError('Archive exceeds pinned distribution limits')
        entries = []
        seen = set()
        for member in members:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != prefix or '..' in parts or member.name.startswith('/'):
                raise ValueError('Unsafe archive member: ' + member.name)
            relative = Path(*parts[1:])
            if not relative.parts:
                if member.isdir():
                    continue
                raise ValueError('Archive root is not a directory')
            if str(relative) in seen or not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError('Duplicate or special archive member: ' + member.name)
            seen.add(str(relative))
            if member.issym():
                target = PurePosixPath(member.linkname)
                resolved = (destination / relative.parent / member.linkname).resolve()
                if target.is_absolute() or not resolved.is_relative_to(destination):
                    raise ValueError('Archive link escapes distribution: ' + member.name)
            entries.append((member, destination / relative))
        link_paths = {path for member, path in entries if member.issym()}
        for member, path in entries:
            if any(parent in link_paths for parent in path.parents):
                raise ValueError('Archive member descends through a symbolic link')
            path.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                path.mkdir(exist_ok=True)
            elif member.isfile():
                with stream.extractfile(member) as source, path.open('xb') as output:
                    shutil.copyfileobj(source, output)
                path.chmod(member.mode & 0o777)
        for member, path in entries:
            if member.issym():
                path.symlink_to(member.linkname)


def download(url, path, expected):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=120) as response, Path(path).open('xb') as output:
        shutil.copyfileobj(response, output)
    if digest(path) != expected:
        raise ValueError('Distribution checksum differs; not extracted or executed')


def assess_node(node):
    # A standalone CLI is not an application bundle. Check its actual signature;
    # do not run an unsupported app-only assessment or weaken native execution controls.
    return checked(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', node])


def verify(state=STATE):
    host()
    root = runtime_root(state)
    receipt = root / 'SOURCE.json'
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError('No owned pinned REA runtime')
    saved = json.loads(receipt.read_text())
    expected = {'version': VERSION, 'revision': REVISION, 'package_sha256': PACKAGE_SHA256,
                'node_version': NODE_VERSION, 'node_sha256': NODE_SHA256}
    if any(saved.get(k) != value for k, value in expected.items()):
        raise ValueError('Runtime identity differs; preserved')
    for name, expected_hash in [('package', PACKAGE_MANIFEST), ('node', NODE_MANIFEST)]:
        directory = root / name
        if directory.is_symlink() or not directory.is_dir() or manifest_hash(manifest(directory)) != expected_hash:
            raise ValueError('Pinned runtime tree differs: ' + name + '; preserved')
    node = root / 'node/bin/node'
    assess_node(node)
    return node, root / 'package/scripts/rea.mjs'


def install(state=STATE, package_tarball=None, node_tarball=None):
    host()
    root = runtime_root(state)
    with writer(root.parent):
        if root.exists() or root.is_symlink():
            return verify(state)
        with tempfile.TemporaryDirectory(prefix='nstack-rea-install-', dir='/private/tmp') as temporary:
            acquired = []
            for name, supplied, url, checksum in [
                ('package', package_tarball, PACKAGE_URL, PACKAGE_SHA256),
                ('node', node_tarball, NODE_URL, NODE_SHA256),
            ]:
                archive = concrete(supplied) if supplied else Path(temporary) / (name + '.tgz')
                if supplied is None:
                    download(url, archive, checksum)
                if not archive.is_file() or digest(archive) != checksum:
                    raise ValueError('Distribution checksum differs; not extracted or executed')
                acquired.append(archive)
            stage = Path(tempfile.mkdtemp(prefix='.prepare-', dir=root.parent))
            # A failed stage is retained for diagnosis. Never overwrite an installed copy.
            safe_extract(acquired[0], stage / 'package', 'package')
            safe_extract(acquired[1], stage / 'node', 'node-v' + NODE_VERSION + '-darwin-arm64')
            for name, expected_hash in [('package', PACKAGE_MANIFEST), ('node', NODE_MANIFEST)]:
                if manifest_hash(manifest(stage / name)) != expected_hash:
                    raise ValueError('Extracted distribution differs; retained stage: ' + str(stage))
            assessment = assess_node(stage / 'node/bin/node')
            write(stage / 'SOURCE.json', {'version': VERSION, 'revision': REVISION,
                  'package_url': PACKAGE_URL, 'package_sha256': PACKAGE_SHA256,
                  'package_manifest_sha256': PACKAGE_MANIFEST,
                  'node_version': NODE_VERSION, 'node_url': NODE_URL,
                  'node_sha256': NODE_SHA256, 'node_manifest_sha256': NODE_MANIFEST,
                  'node_codesign': assessment,
                  'identity_limit': 'Official archive identity; no reproducible source-to-binary attestation',
                  'activation': 'Dormant private CLI; no npm lifecycle, PATH edit, MCP registration or provider',
                  'readiness': 'Payload verified; static fixture acceptance remains separate'})
            os.rename(stage, root)
    return verify(state)


def guard_python():
    native = Path(sys.base_prefix) / 'Resources/Python.app/Contents/MacOS/Python'
    return native.resolve() if native.is_file() else Path(sys.executable).resolve()


def environment(run):
    run = Path(run)
    return {'HOME': str(run / 'home'), 'PATH': '/usr/bin:/bin',
            'XDG_CONFIG_HOME': str(run / 'config'), 'XDG_CACHE_HOME': str(run / 'cache'),
            'TMPDIR': str(run / 'tmp'), 'LANG': 'en_US.UTF-8', 'TZ': 'UTC',
            'CI': '1', 'NO_UPDATE_NOTIFIER': '1',
            'REA_DARWIN_MODULE_CACHE_PATH': str(run / 'module-cache')}


def profile(runtime, source, out):
    readable = [Path(runtime), Path(source), Path(out), Path(sys.base_prefix)]
    excluded = ' '.join('(require-not (subpath ' + json.dumps(str(p)) + '))' for p in readable)
    executable = [Path(runtime) / 'node/bin/node', guard_python()]
    permitted_exec = ['(require-not (literal ' + json.dumps(str(p)) + '))' for p in executable]
    # System compiler tools build REA's reviewed process-ownership helper inside
    # the owned task. The supplied target is never an executable allowlist root.
    permitted_exec += ['(require-not (subpath ' + json.dumps(str(p)) + '))' for p in
                       ['/usr/bin', '/bin', '/Library/Developer',
                        '/Applications/Xcode.app/Contents/Developer', Path(out)]]
    return ('(version 1)\n(allow default)\n(deny network*)\n'
            '(deny file-read-data file-read-xattr (require-all (require-any (subpath "/Users") (subpath "/private/tmp")) ' + excluded + '))\n'
            '(deny file-write* (require-all (require-not (subpath ' + json.dumps(str(out)) + '))'
            ' (require-not (literal "/dev/null"))))\n'
            '(deny process-exec (require-all ' + ' '.join(permitted_exec) + '))\n')


def approved_source(source, evidence=False, native=False):
    source = concrete(source)
    forbidden = {'.ssh', '.codex', '.claude', '.config', '.aws', '.gnupg', '.docker',
                 'keychains', 'credentials', 'secrets', 'passwords', '.obsidian', 'knowledge'}
    if forbidden.intersection(part.casefold() for part in source.parts):
        raise ValueError('Credential/configuration/vault input is outside this static route')
    if source.is_file():
        if source.stat().st_size > MAX_BYTES or (not (evidence or native) and source.suffix.lower() != '.asar'):
            raise ValueError('Select a directory or regular ASAR at most128MiB')
        return source, digest(source)
    if evidence or native or not source.is_dir():
        raise ValueError('Select a regular input file' if evidence or native else 'Select a directory or regular ASAR')
    if source in {Path('/'), Path('/Users'), Path('/private'), Path('/private/tmp'), Path('/Applications'), Path.home()}:
        raise ValueError('Select one explicit artifact directory, not a host root')
    count = size = 0
    for directory, directories, files in os.walk(source, followlinks=False):
        for name in [*directories, *files]:
            path = Path(directory) / name
            # Refuse before descending into or hashing a nested credential store.
            if name.casefold() in forbidden:
                raise ValueError('Sensitive nested target content preserved')
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError('Linked or special target content preserved')
            count += 1
            if path.is_file():
                size += path.stat().st_size
            if count > MAX_FILES or size > MAX_BYTES:
                raise ValueError('Static target exceeds10000entries/128MiB')
    return source, manifest_hash(manifest(source))


def source_hash(source):
    return manifest_hash(manifest(source)) if Path(source).is_dir() else digest(source)


def own_output(out, source, identity, state, operation):
    out = concrete(out)
    root = runtime_root(state)
    if out == source or out.is_relative_to(source) or source.is_relative_to(out) or out.is_relative_to(root) or root.is_relative_to(out):
        raise ValueError('Select disjoint input/output outside the sealed runtime')
    ownership = {'revision': REVISION, 'source': str(source), 'sha256': identity, 'operation': operation}
    if out.exists():
        receipt = out / 'OWNERSHIP.json'
        if receipt.is_symlink() or not receipt.is_file() or json.loads(receipt.read_text()) != ownership:
            raise ValueError('Foreign or changed-input output preserved')
    else:
        out.mkdir(parents=True, mode=0o700)
        write(out / 'OWNERSHIP.json', ownership)
    return out, ownership


def prepare_run(out):
    run = concrete(out / 'runs' / uuid.uuid4().hex)
    run.mkdir(parents=True, mode=0o700)
    for name in ('home', 'config', 'cache', 'tmp', 'module-cache'):
        (run / name).mkdir(mode=0o700)
    return run


def containment_probe(rules, run, state):
    with tempfile.TemporaryDirectory(prefix='guard-', dir=runtime_root(state).parent) as temporary:
        sentinel = Path(temporary) / 'synthetic-private.txt'
        sentinel.write_text('synthetic private-file probe only')
        probe = ('import errno,json,socket,sys\nchecks={}\n'
                 'try:\n open(sys.argv[1]).read()\n checks["read_denied"]=False\n'
                 'except OSError as e:\n checks["read_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                 'try:\n socket.create_connection(("127.0.0.1",9),timeout=1)\n checks["network_denied"]=False\n'
                 'except OSError as e:\n checks["network_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                 'print(json.dumps(checks))\nsys.exit(0 if all(checks.values()) else 1)')
        result = capture(['/usr/bin/sandbox-exec', '-p', rules, guard_python(), '-I', '-B', '-S', '-c', probe, sentinel],
                         cwd=run, env=environment(run), timeout=30)
        write(run / 'guard.json', result)
        if result['exit_code']:
            raise ValueError('OS containment probe failed; target not opened: ' + str(run))


def run_static(node, script, arguments, rules, run):
    argv = ['/usr/bin/sandbox-exec', '-p', rules, node, script, *arguments, '--json']
    stdout = run / 'evidence.json'
    stderr = run / 'stderr.log'
    with stdout.open('xb') as output, stderr.open('xb') as errors:
        process = subprocess.Popen([str(x) for x in argv], cwd=run, env=environment(run),
                                   stdout=output, stderr=errors, start_new_session=True)
        start = time.monotonic()
        try:
            while process.poll() is None:
                if time.monotonic() - start > 180 or stdout.stat().st_size + stderr.stat().st_size > MAX_BYTES:
                    raise ValueError('Static command exceeded180seconds/128MiB output; retained ' + str(run))
                time.sleep(0.1)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
    write(run / 'execution.json', {'argv': [str(x) for x in argv], 'exit_code': process.returncode,
          'stdout': str(stdout), 'stderr': str(stderr)})
    if process.returncode:
        raise ValueError('Static command failed or native execution denied; retained ' + str(run))
    if stdout.stat().st_size > MAX_BYTES:
        raise ValueError('Oversized result preserved')
    document = json.loads(stdout.read_text())
    if not isinstance(document, dict) or not isinstance(document.get('normalized_result'), dict) or not str(document.get('evidence_id', '')).startswith('ev_'):
        raise ValueError('Missing successful structured Evidence; retained ' + str(run))
    return stdout, document


def execute(state, source, out, operation='inspect'):
    if operation not in {'inspect', 'summary', 'native-exports'}:
        raise ValueError('Only static inspect, native-exports and summary operations are admitted')
    source, identity = approved_source(source, evidence=operation == 'summary', native=operation == 'native-exports')
    node, script = verify(state)
    out, ownership = own_output(out, source, identity, state, operation)
    with writer(out):
        run = prepare_run(out)
        rules = profile(runtime_root(state), source, out)
        (run / 'sandbox.sb').write_text(rules)
        containment_probe(rules, run, state)
        if operation == 'inspect':
            arguments = ['analyze-javascript-application', source]
        elif operation == 'native-exports':
            arguments = ['inspect-native-exports', source]
        else:
            request = run / 'summary-request.json'
            write(request, {'source': {'kind': 'evidence-file', 'path': str(source)}, 'view': {'kind': 'summary'}})
            arguments = ['inspect-analysis-view', request]
        evidence, document = run_static(node, script, arguments, rules, run)
        if source_hash(source) != identity:
            raise ValueError('Input changed during analysis; result is stale')
        receipt = {'revision': REVISION, 'version': VERSION, 'operation': operation,
                   'input': ownership, 'evidence': str(evidence), 'evidence_id': document['evidence_id'],
                   'sha256': digest(evidence), 'network': 'OS denied', 'target_execution': False,
                   'limits': 'Static artifact evidence; no runtime behavior/all-format acceptance'}
        write(run / 'receipt.json', receipt)
        return receipt


def native_fixture(format, positive=True):
    """Data-only PE64/ELF64 tables with known facts, never machine instructions."""
    if format == 'elf':
        data = bytearray(0x300)
        data[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<HHI', data, 16, 3, 62, 1)  # ET_DYN, EM_X86_64, version1
        struct.pack_into('<Q', data, 40, 0x200)  # section-header offset
        struct.pack_into('<HHHHHH', data, 52, 64, 56, 0, 64, 4, 3)
        strings = b'\0nstack_answer\0nstack_absent\0'
        data[0x140:0x140 + len(strings)] = strings
        section_names = b'\0.dynsym\0.dynstr\0.shstrtab\0'
        data[0x180:0x180 + len(section_names)] = section_names
        # Null dynamic symbol followed by one defined global/function, or local
        # function in the negative image. Raw name bytes exist in both images.
        struct.pack_into('<IBBHQQ', data, 0x118, 1, 0x12 if positive else 0x02, 0, 1, 0x1020, 16)
        for index, (name, kind, offset, size, link, entry_size) in enumerate([
            (0, 0, 0, 0, 0, 0), (1, 11, 0x100, 48, 2, 24),
            (9, 3, 0x140, len(strings), 0, 0), (17, 3, 0x180, len(section_names), 0, 0),
        ]):
            struct.pack_into('<IIQQQQIIQQ', data, 0x200 + index * 64,
                             name, kind, 0, 0, offset, size, link, 0, 1, entry_size)
        return bytes(data)
    if format == 'pe':
        data = bytearray(0x800)
        data[:2] = b'MZ'
        struct.pack_into('<I', data, 60, 0x80)
        data[0x80:0x84] = b'PE\0\0'
        struct.pack_into('<HH', data, 132, 0x8664, 1)
        struct.pack_into('<H', data, 148, 240)
        optional = 152
        struct.pack_into('<H', data, optional, 0x20b)
        struct.pack_into('<Q', data, optional + 24, 0x180000000)
        struct.pack_into('<I', data, optional + 60, 0x400)
        struct.pack_into('<I', data, optional + 108, 16)
        if positive:
            struct.pack_into('<II', data, optional + 112, 0x1000, 0x200)
        section = optional + 240
        data[section:section + 6] = b'.edata'
        struct.pack_into('<IIII', data, section + 8, 0x400, 0x1000, 0x400, 0x400)
        struct.pack_into('<I', data, section + 36, 0x40000040)
        struct.pack_into('<IIIIIII', data, 0x400 + 12, 0x1200, 1, 1, 1, 0x1040, 0x1080, 0x10c0)
        struct.pack_into('<I', data, 0x440, 0x2000)
        struct.pack_into('<I', data, 0x480, 0x1220)
        struct.pack_into('<H', data, 0x4c0, 0)
        data[0x600:0x60c] = b'fixture.dll\0'
        data[0x620:0x62e] = b'nstack_answer\0'
        data[0x670:0x67e] = b'nstack_absent\0'
        return bytes(data)
    raise ValueError('Fixture format must be pe or elf')


def assert_native_fixture(document, format, expected_hash, positive=True):
    result = document.get('normalized_result', {})
    expected_count = 1 if positive else 0
    if (document.get('operation') != 'inspect_native_exports' or result.get('format') != format or
            result.get('artifact', {}).get('sha256') != expected_hash or
            result.get('coverage', {}).get('status') != 'complete' or
            result['coverage'].get('exports') != expected_count or result.get('issues') != [] or
            len(result.get('exports', [])) != expected_count):
        raise ValueError('Native export artifact identity/table coverage did not match fixture')
    if positive:
        row = result['exports'][0]
        if row.get('name') != 'nstack_answer':
            raise ValueError('Known export absent from parsed export rows')
        if format == 'elf':
            if row.get('value') != '0x1020' or row.get('binding') != 'global' or row.get('type') != 'function':
                raise ValueError('ELF symbol value/binding/type differ from table bytes')
        elif row.get('address') != '0x180002000' or row.get('ordinal') != 1 or row.get('forwarder') is not None:
            raise ValueError('PE address/ordinal differ from table bytes')
    if any(row.get('name') == 'nstack_absent' for row in result.get('exports', [])):
        raise ValueError('Inert absent name manufactured an export')


def check(state=STATE):
    """Accept the separate providerless export-table lane, never the blocked JS lane."""
    node, script = verify(state)
    root = runtime_root(state).parent / ('check-native-exports-' + uuid.uuid4().hex)
    root.mkdir(mode=0o700)
    fixtures = root / 'fixtures'
    fixtures.mkdir()
    metadata = prepare_run(root / 'metadata')
    rules = profile(runtime_root(state), fixtures, root)
    version = checked(['/usr/bin/sandbox-exec', '-p', rules, node, script, '--version'],
                      cwd=metadata, env=environment(metadata), timeout=30)
    write(metadata / 'version.json', version)
    if version['stdout'].strip() != VERSION:
        raise ValueError('Runtime version differs from pinned release')
    receipts = []
    ids = set()
    for format in ('elf', 'pe'):
        for positive in (True, False):
            label = format + ('-known' if positive else '-empty')
            source = fixtures / label
            source.write_bytes(native_fixture(format, positive))
            original = digest(source)
            receipt = execute(state, source, root / (label + '-evidence'), 'native-exports')
            document = json.loads(Path(receipt['evidence']).read_text())
            assert_native_fixture(document, format, original, positive)
            summary = execute(state, receipt['evidence'], root / (label + '-summary'), 'summary')
            projected = json.loads(Path(summary['evidence']).read_text())
            view = projected['normalized_result']
            if (view.get('parent_evidence_id') != document['evidence_id'] or
                    view.get('parent_operation') != 'inspect_native_exports' or
                    view.get('summary', {}).get('format') != format or
                    view['summary'].get('export_count') != (1 if positive else 0) or
                    view['summary'].get('coverage') != document['normalized_result']['coverage']):
                raise ValueError('Export summary does not match retained parent Evidence')
            if digest(source) != original or source.stat().st_mode & 0o111:
                raise ValueError('Data-only target changed or became executable')
            ids.update([document['evidence_id'], projected['evidence_id']])
            receipts.append({'format': format, 'positive': positive, 'input_sha256': original,
                             'inspection': receipt, 'summary': summary})
    if len(ids) != 8:
        raise ValueError('Export fixture/summary Evidence IDs repeated')
    accepted = {'passed': True, 'lane': 'native-exports', 'checks': receipts,
                'fixture': str(fixtures), 'input_unchanged': True,
                'target_executed': False, 'target_kind': 'Data-only binary tables without instructions',
                'negative_controls': 'Inert nstack_absent bytes are never exported; local ELF symbol and PE absent directory each return zero exports',
                'javascript_lane': 'Not accepted: earlier native ps spawn EPERM during cleanup; not retried',
                'qualification': 'Tiny PE64/ELF64 export tables and saved-Evidence summaries only'}
    write(root / 'CHECK.json', accepted)
    return accepted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('install'); p.add_argument('--package-tarball'); p.add_argument('--node-tarball')
    sub.add_parser('verify'); sub.add_parser('check')
    p = sub.add_parser('inspect'); p.add_argument('--source', required=True); p.add_argument('--outdir', required=True)
    p = sub.add_parser('summary'); p.add_argument('--evidence', required=True); p.add_argument('--outdir', required=True)
    p = sub.add_parser('native-exports'); p.add_argument('--source', required=True); p.add_argument('--outdir', required=True)
    args = parser.parse_args()
    try:
        if args.command in {'install', 'verify'}:
            node, script = install(args.state, args.package_tarball, args.node_tarball) if args.command == 'install' else verify(args.state)
            result = {'node': str(node), 'script': str(script), 'command': [str(node), str(script)],
                      'version': VERSION, 'revision': REVISION, 'readiness': 'Payload verification; check is separate'}
        elif args.command == 'check':
            result = check(args.state)
        else:
            result = execute(args.state, args.evidence if args.command == 'summary' else args.source, args.outdir, args.command)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError, tarfile.TarError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
