"""Resolve a selected project or shelf package using its public catalog and receipt."""
import json
import os
from pathlib import Path
import re


MENTION = re.compile(r"(?:^|[\s`'\x22(])((?:\.\./)+(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+)(?=$|[\s`'\x22#),;:])")


def library():
    location = Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share').expanduser()
    return location/'stackplus/library'


def catalog(api):
    if api is None:
        return {}, {}
    data = json.loads((api.ROOT/'registry/stackplus-selections.json').read_text())
    return {row['name']:row for row in data['methods']}, data['shared_support']


def staged(bundle, row, read):
    """Return only the exact selected canonical entry and package manifest."""
    if bundle.resolve() != bundle or bundle.name != 'bundle':
        return None
    try:
        rec = json.loads(read(bundle/'bundle.json',limit=8*1024*1024))
        if (rec['name'] != row['name'] or rec['scope'] != row['scope']
                or rec['source'] != row.get('source',row.get('checkout_bundle'))):
            return None
        entry = Path(rec['entry'])
        if (entry.is_absolute() or '..' in entry.parts or entry.parts[0]!='package'
                or entry.name!='SKILL.md' or not isinstance(rec['document_sha256'],dict)):
            return None
        if row.get('leaf') and entry != Path('package')/row['leaf']/'SKILL.md':
            return None
        target = bundle/entry
        alias = bundle/'skills'/row['name']
        if target.resolve(strict=True)!=target or alias.parent.resolve()!=alias.parent or not alias.is_symlink():
            return None
        if alias.resolve(strict=True)!=target.parent:
            return None
        return target.parent, bundle/'package', rec['document_sha256'], rec['package_sha256']
    except (IndexError, KeyError, OSError, ValueError, TypeError):
        return None


def package_for_entry(target, name, project_root, shelf, row, read):
    if not row:
        return None
    for package in (target, *target.parents):
        if package.name!='package' or package.parent.name!='bundle':
            continue
        base = package.parent
        if not (base.is_relative_to(project_root) or base == shelf/name/'bundle'):
            return None
        result = staged(base,row,read)
        if result and result[0]==target:
            return result
    return None


def shared_files(folder, text, receipt, row, groups):
    if not receipt or not row.get('shared'):
        return
    _, package, hashes, _ = receipt
    allowed = set(groups.get(row['shared'],[]))
    for ref in sorted(set(MENTION.findall(text))):
        # Resolve .. lexically, then refuse any symlink component of the resulting file.
        path = Path(os.path.normpath(folder/ref))
        if not path.is_relative_to(package) or path.resolve()!=path or path.is_relative_to(folder):
            continue
        rel = path.relative_to(package).as_posix()
        if rel in allowed and rel in hashes:
            yield ref, path


def permits(scope, project, named, explicit):
    scope = scope.casefold()
    if scope=='explicit selection required':
        return named and explicit
    if 'match by name' in scope:
        return named
    if scope=='on demand' or scope in ('external discovery','input discovery'):
        return True
    if project and scope.startswith(('project', 'selected leaves')):
        return True
    return project and named and explicit
