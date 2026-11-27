"""Audit absolute local runtime paths. Optionally propose receipt-backed replacements.

Run from the nstack source with python3 -m lib.runtime_paths --help.
Reports filesystem observations only. This module never launches a runtime or
writes an index. Historical checks, access restrictions and notes stay intact.
"""
import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from .transaction_paths import open_parent


# Only inspect operational fields. An archived run, a URL or an instruction
# mentioning a path is not an invocation. Relative commands depend on host PATH.
OPERATION_FIELDS = {
    'entrypoint', 'command', 'invoke', 'invocation', 'commands', 'syntax',
    'python', 'node', 'binary', 'script', 'ffprobe_command', 'adapter',
    'recipe', 'helper', 'plugin_source', 'host_client_helper', 'docker_cli',
    'native_client', 'controller_cli', 'host_python', 'compose_file', 'model',
    'config_inspection_invoke', 'start_invoke', 'check_invoke', 'check_template',
    'acceptance_invoke', 'verify_invoke', 'report_template', 'node_info_example',
    'workflow_validation', 'mcp_arguments', 'args', 'arguments', 'environment',
}
NESTED_FIELDS = {
    'mcp': ('invoke', 'browser_executable'),
    'linux_backend': ('tlc_jar', 'host_client_helper', 'support'),
}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular_bytes(path):
    """Read only a bounded regular file, without following parent or leaf links."""
    path = Path(path).absolute()
    with open_parent(path) as parent:
        if parent.path != path.parent:
            raise FileNotFoundError(path)
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent.fd)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('Expected a regular file: ' + str(path))
            raw = stream.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError('Oversized metadata or wrapper: ' + str(path))
            return raw


def index_rows(raw):
    def unique_keys(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError('Duplicate runtime-index field')
        return result

    rows = json.loads(raw, object_pairs_hook=unique_keys)
    if not isinstance(rows, list):
        raise ValueError('Runtime index must be an array')
    names = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str):
            raise ValueError('Runtime record lacks its name')
        if not row['name'] or row['name'] in names:
            raise ValueError('Empty or duplicate runtime name')
        names.add(row['name'])
    return rows


def absolute_components(value, location):
    if isinstance(value, str):
        if value.startswith('/') and '\x00' not in value:
            yield value, location
    elif isinstance(value, list):
        for i, part in enumerate(value):
            yield from absolute_components(part, [*location, i])
    elif isinstance(value, dict):
        for key, part in value.items():
            yield from absolute_components(part, [*location, key])


def invocation_paths(row):
    locations = {}
    for key in OPERATION_FIELDS.intersection(row):
        for path, parts in absolute_components(row[key], [key]):
            locations.setdefault(path, []).append(parts)
    for key, fields in NESTED_FIELDS.items():
        group = row.get(key)
        if isinstance(group, dict):
            for field in fields:
                for path, parts in absolute_components(group.get(field), [key, field]):
                    locations.setdefault(path, []).append(parts)
    return locations


def original_relative(path, releases):
    if not path.is_relative_to(releases):
        return None
    parts = path.relative_to(releases).parts
    if len(parts) < 2 or '..' in parts or not re.fullmatch('[a-f0-9]{64}', parts[0]):
        return None
    return '/'.join(parts[1:])


def proposed_bindings(row, missing, original, release, manifest):
    # Normal Python equality considers 0 and False equal. Authority fields
    # and the exact original record must retain their JSON value types.
    if (original is None
            or json.dumps(row, sort_keys=True) != json.dumps(original, sort_keys=True)
            or row.get('callable') is False or row.get('runtime_accepted') is False):
        return []
    proposals = []
    for item in missing:
        old = Path(item['path'])
        relative = original_relative(old, release.parent)
        if not relative or old.is_symlink() or old.resolve(strict=False) != old:
            continue
        hash_fields = sorted(key + '_sha256' for key, value in row.items()
                             if key in OPERATION_FIELDS and value == str(old)
                             and key + '_sha256' in row)
        if not hash_fields:
            continue
        hash_field = hash_fields[0]
        expected = original[hash_field]
        if (not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected)
                or any(original[key] != expected for key in hash_fields)
                or manifest.get(relative) != expected):
            continue
        target = release / relative
        try:
            actual = digest(regular_bytes(target))
        except (OSError, ValueError):
            continue
        if actual == expected:
            proposals.append({**item, 'target': str(target), 'sha256': expected,
                              'receipt_field': hash_field})
    return proposals


def audit(state, *, release_id=None, reference=None, reference_sha256=None, selected=()):
    """Produce a read-only report bound to the index bytes and optional evidence."""
    state = Path(state).absolute()
    index = state / 'native-tools/index.json'
    raw = regular_bytes(index)
    rows = index_rows(raw)
    selected = set(selected)
    if selected - {row['name'] for row in rows}:
        raise ValueError('Unrecognized runtime selected for footprint comparison')
    release = None
    historical = {}
    manifest = {}
    if any(x is not None for x in (release_id, reference, reference_sha256)):
        if (not isinstance(release_id, str) or not re.fullmatch('[a-f0-9]{64}', release_id)
                or not reference or not reference_sha256):
            raise ValueError('Proposals require a release ID, reference index and pinned reference SHA-256')
        reference = Path(reference)
        receipt = regular_bytes(reference)
        if reference.samefile(index) or digest(receipt) != reference_sha256:
            raise ValueError('Supply a separate reference index matching its retained digest')
        historical = {row['name']: row for row in index_rows(receipt)}
        release = state / 'releases' / release_id
        manifest = json.loads(regular_bytes(release / 'INSTALL-MANIFEST.json'))
        if not isinstance(manifest, dict):
            raise ValueError('Invalid install manifest')

    if selected and release is None:
        raise ValueError('Selected replacement candidates require a pinned release and reference')

    report = {'index_sha256': digest(raw), 'release_id': release_id,
              'reference_sha256': reference_sha256,
              'scope': 'Absolute invocation paths and local components only. Presence does not establish execution, permission or readiness.',
              'records': []}
    for i, row in enumerate(rows):
        paths = invocation_paths(row)
        missing = []
        inaccessible = []
        for value, fields in sorted(paths.items()):
            item = {'path': value, 'fields': sorted(fields, key=repr)}
            try:
                os.stat(value)
            except (FileNotFoundError, NotADirectoryError):
                missing.append(item)
            except OSError as error:
                inaccessible.append({**item, 'errno': error.errno})
        bindings = proposed_bindings(row, missing, historical.get(row['name']),
                                     release, manifest) if release and row['name'] in selected else []
        if missing or inaccessible:
            status = 'paths-missing-or-inaccessible'
        else:
            status = 'recorded-paths-present' if paths else 'no-absolute-paths-to-check'
        report['records'].append({'name': row['name'], 'row_index': i,
                                  'path_status': status, 'absolute_components': len(paths), 'missing': missing,
                                  'inaccessible': inaccessible, 'proposals': bindings})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--release-id', help='An installed nstack code release to compare')
    parser.add_argument('--reference', type=Path, help='Independently retained original runtime index')
    parser.add_argument('--reference-sha256', help='Digest from its commissioning or recovery receipt')
    parser.add_argument('--select', action='append', default=[],
                        help='Runtime name to compare for byte-identical replacements (repeatable)')
    args = parser.parse_args()
    print(json.dumps(audit(args.state, release_id=args.release_id, reference=args.reference,
                           reference_sha256=args.reference_sha256, selected=args.select), indent=2))


if __name__ == '__main__':
    main()
