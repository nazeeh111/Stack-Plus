#!/usr/bin/env python3
"""Apply only exact reviewed engine preimages, preserving originals and diff."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply(source: Path, archive: Path, *, bash: Path | None = None) -> dict:
    source = source.resolve(strict=True)
    if not source.is_dir() or source == Path('/'):
        raise ValueError('source must be a private reviewed engine directory')
    specification = Path(__file__).with_name('patches') / 'manifest.json'
    spec = json.loads(specification.read_text())
    prepared = []
    for item in spec['files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('patch path must stay inside reviewed source')
        path = source / relative
        info = path.lstat()
        if path.resolve() != path or not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('patch source must be canonical and owner-controlled')
        original = path.read_bytes()
        if digest(original) != item['original_sha256']:
            raise ValueError('engine preimage drift: ' + item['path'])
        text = original.decode()
        replacements = item.get('replacements') or [
            {'before': item['replace_before'], 'after': item['replace_after']}]
        for replacement in replacements:
            if text.count(replacement['before']) != 1:
                raise ValueError('ambiguous patch preimage')
            text = text.replace(replacement['before'], replacement['after'], 1)
        patched = text.encode()
        if digest(patched) != item['patched_sha256']:
            raise ValueError('reviewed patch result mismatch')
        if path.suffix == '.py':
            ast.parse(patched)
        elif path.suffix == '.sh' and bash is not None and bash.is_absolute():
            # Syntax only, empty environment: no source execution or BASH_ENV.
            subprocess.run([str(bash), '--noprofile', '--norc', '-n'], input=patched,
                           env={'PATH': '/usr/bin:/bin'}, capture_output=True, check=True)
        else:
            raise ValueError('reviewed absolute Bash required for shell patch syntax')
        prepared.append((path, relative, original, patched, item))
    # Refuse existing archives so an earlier original can never be overwritten.
    archive.mkdir(mode=0o700, parents=True, exist_ok=False)
    receipt = {'repository': spec['repository'], 'commit': spec['commit'], 'files': []}
    for path, relative, original, patched, item in prepared:
        saved = archive / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(original)
        patch_name = item['patch']
        (archive / patch_name).write_bytes((specification.parent / patch_name).read_bytes())
        path.write_bytes(patched)
        receipt['files'].append({k: item[k] for k in
                                 ('path', 'original_sha256', 'patched_sha256', 'patch')})
    (archive / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--bash', type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.archive, bash=args.bash), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
