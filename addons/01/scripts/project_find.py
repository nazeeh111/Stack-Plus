#!/usr/bin/env python3
"""Find a contribution in the current project's skill instructions and supporting files."""
import argparse
import itertools
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import queue
import shutil
import sqlite3
import subprocess
import sys
import threading
import time

import capabilities as cap
import staged_shelf
import opencode_eligibility


TEXT = {'.md', '.mdx', '.rst', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.ts', '.sh', '.sql'}
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z')
MAX_FILE = 512 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_FILES = 2048


def read(path, limit=MAX_FILE, expected=None):
    with cap.regular_file(path) as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or b'\0' in raw:
        raise ValueError('Expected bounded UTF-8 text')
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Staged file differs from its receipt')
    return raw.decode('utf-8-sig')


def project_dirs(start):
    if start == Path.home() or start.parent == start:
        raise ValueError('Choose a project directory')
    dirs = []
    for path in (start, *start.parents):
        if path == Path.home() or path.parent == path:
            break
        dirs.append(path)
        if (path / '.git').exists():
            return dirs
    return [start]


def config_permits(name, path, rules):
    """Apply the effective native rule array in order to the exact skill entry."""
    enabled = True
    for rule in rules:
        if not isinstance(rule,dict) or not isinstance(rule.get('enabled'),bool):
            continue
        by_name, by_path = rule.get('name'), rule.get('path')
        if isinstance(by_name,str) and by_path is None:
            matches = by_name == name
        elif isinstance(by_path,str) and by_name is None:
            selector = Path(by_path).expanduser()
            matches = selector.is_absolute() and selector.resolve() == path
        else:
            continue
        if matches:
            enabled = rule['enabled']
    return enabled


def codex_eligible(project):
    """Delegate profile layering, project trust, name/path rules and user disables to Codex."""
    binary = shutil.which('codex')
    if not binary:
        raise ValueError('The Codex CLI is required to read effective project skill eligibility')
    child = subprocess.Popen([binary, 'app-server', '--stdio'], cwd=project, text=True,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    replies = queue.Queue()

    def collect():
        try:
            for line in child.stdout:
                replies.put(json.loads(line))
        finally:
            replies.put(None)

    def send(obj):
        child.stdin.write(json.dumps(obj) + '\n')
        child.stdin.flush()

    def request(number, method, params):
        send(dict(id=number, method=method, params=params))
        deadline = time.monotonic() + 20
        while True:
            try:
                msg = replies.get(timeout=max(0,deadline-time.monotonic()))
            except queue.Empty as exc:
                raise ValueError('Codex did not return effective skill eligibility') from exc
            if msg is None or ('error' in msg and msg.get('id') == number):
                raise ValueError('Codex did not return effective skill eligibility')
            if msg.get('id') == number:
                return msg['result']

    threading.Thread(target=collect, daemon=True).start()
    try:
        request(1,'initialize',{'clientInfo':{'name':'stackplus-project-find','version':'1'}})
        send({'method':'initialized','params':{}})
        rows = request(2,'skills/list',{'cwds':[str(project)],'forceReload':True})['data']
        if len(rows)!=1 or Path(rows[0]['cwd']).resolve()!=project or rows[0].get('errors'):
            raise ValueError('The native loader could not verify this project')
        config = request(3,'config/read',{'cwd':str(project),'includeLayers':False})
        rules = (config['config'].get('skills') or {}).get('config') or []
        if not isinstance(rules,list):
            raise ValueError('Invalid effective skill rule list')
        permitted = {}
        for skill in rows[0]['skills']:
            if skill.get('enabled') is True and skill.get('scope') == 'repo':
                name, path = skill['name'], Path(skill['path']).resolve()
                if config_permits(name,path,rules):
                    permitted[path] = name
        # A project rule array can replace the entire user array. The loader checks
        # user selection separately for native skills; dormant packages have no row.
        user_config = request(4,'config/read',{'cwd':str(Path.home()),'includeLayers':False})
        user_rules = (user_config['config'].get('skills') or {}).get('config') or []
        if not isinstance(user_rules,list):
            raise ValueError('Invalid user skill rule list')
        return permitted, (rules,user_rules), {entry['name'] for entry in rows[0]['skills']}
    finally:
        child.terminate()
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def explicit_only(bundle, meta, receipt=None):
    if (str(meta.get('disable-model-invocation', '')).casefold() == 'true'
            or str(meta.get('opencode/autoinvoke', '')).casefold() == 'false'):
        return True
    policy = bundle/'agents/openai.yaml'
    expected = None
    if receipt:
        expected = receipt[2].get(policy.relative_to(receipt[1]).as_posix())
    try:
        text = read(policy,expected=expected)
    except FileNotFoundError:
        if expected:
            raise ValueError('The staged invocation policy is missing')
        return False
    return bool(re.search(r'''(?im)^\s*['"]?allow_implicit_invocation['"]?\s*:\s*['"]?false\b''',text))


def bundles(args, dirs, api):
    catalog, shared = staged_shelf.catalog(api)
    if args.host == 'codex':
        native, rules, host_names = codex_eligible(dirs[0])
    else:
        try:
            projection = opencode_eligibility.eligibility(dirs[0],args.agent,args.session,catalog)
            native = {Path(item['path']): item['name'] for item in projection['eligible'] if item['scope']=='project'}
            host_names = set(catalog) - set(projection['on_demand'])
            rules = ()
        except (KeyError, TypeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
            raise ValueError('OpenCode could not verify effective project skill access. Check the active location and agent.') from error
    shelf_root = staged_shelf.library()
    selected_paths = {Path(p).resolve() for p in args.eligible or []}
    seen_folders = set()
    seen_names = set()
    for project in dirs:
        roots = ['.opencode/skills', '.opencode/skill', '.agents/skills', '.claude/skills'] if args.host == 'opencode' else ['.agents/skills', '.codex/skills']
        for rel in roots:
            shelf = project / rel
            if not shelf.is_dir() or shelf.resolve() != shelf:
                continue
            for entry in sorted(shelf.iterdir()):
                folder_name = entry.name
                if not NAME.fullmatch(folder_name) or (args.host=='codex' and folder_name in seen_folders):
                    continue
                seen_folders.add(folder_name)
                target = entry.resolve()
                instructions = target / 'SKILL.md'
                if native is not None and instructions not in native:
                    continue
                if selected_paths and instructions not in selected_paths:
                    continue
                receipt = staged_shelf.package_for_entry(target,folder_name,dirs[-1],shelf_root,
                                                         catalog.get(folder_name),read)
                if entry.is_symlink() and not receipt:
                    # The publisher's authoritative journal binds a project link to a sealed build.
                    owner = api.activation_rows(project).get(folder_name, {}) if api and rel == '.agents/skills' else {}
                    if owner.get('phase') != 'active' or str(target) != owner.get('target'):
                        continue
                    release = Path(owner['release'])
                    receipt, _, _ = api.registered_release(release)
                    if (receipt.get('name') != folder_name or receipt.get('content_sha256') != owner.get('content_sha256')
                            or target != (release/receipt.get('entry_dir', '.')).resolve()):
                        continue
                if (target/'.disabled').exists():
                    continue
                try:
                    meta, _ = cap.frontmatter(instructions)
                    name = meta.get('name', '')
                    if (not NAME.fullmatch(name) or name in seen_names or (args.bundle and name != args.bundle)
                            or (native is not None and native[instructions] != name)):
                        continue
                    seen_names.add(name)
                    if explicit_only(target,meta,receipt) and not args.explicit:
                        continue
                    if receipt:
                        if not staged_shelf.permits(catalog[folder_name]['scope'],True,bool(args.bundle),args.explicit):
                            continue
                        checksum = receipt[2].get(instructions.relative_to(receipt[1]).as_posix())
                        if not checksum:
                            continue
                        skill = read(instructions,expected=checksum)
                    else:
                        skill = read(instructions)
                except (OSError, ValueError, TypeError):
                    continue
                yield name, target, skill, receipt, catalog.get(folder_name,{}), shared, 'project'

    for name, row in catalog.items():
        if name in seen_folders or name in seen_names or name in host_names or (args.bundle and args.bundle!=name):
            continue
        if not staged_shelf.permits(row['scope'],False,bool(args.bundle),args.explicit):
            continue
        receipt = staged_shelf.staged(shelf_root/name/'bundle',row,read)
        if not receipt:
            continue
        folder, package, hashes, _ = receipt
        entry = folder/'SKILL.md'
        if selected_paths and entry not in selected_paths:
            continue
        if any(not config_permits(name,entry,layer) for layer in rules) or (folder/'.disabled').exists():
            continue
        try:
            key = entry.relative_to(package).as_posix()
            skill = read(entry,expected=hashes[key])
            meta, _ = cap.frontmatter(entry)
            if meta.get('name')!=name or (explicit_only(folder,meta,receipt) and not args.explicit):
                continue
        except (KeyError,OSError,ValueError,TypeError):
            continue
        yield name, folder, skill, receipt, row, shared, 'on-demand'


def public_component(name):
    return (name.isprintable() and not name.startswith('.')
            and name.casefold().split('.')[0] not in cap.PRIVATE | {'tokens', 'auth'})


def documents(folder):
    yield 'SKILL.md'
    for subdir in ('references', 'scripts', 'assets'):
        base = folder/subdir
        if base.is_symlink():
            continue
        for dirname, dirs, files in os.walk(base, followlinks=False):
            here = Path(dirname)
            dirs[:] = sorted(d for d in dirs if public_component(d) and cap.safe(here/d)
                             and not (here/d).is_symlink() and not (here/d/'SKILL.md').is_file()
                             and len((here/d).relative_to(base).parts) <= 5)
            for name in sorted(files):
                path = here/name
                if (public_component(name) and path.suffix.casefold() in TEXT
                        and cap.safe(path) and not path.is_symlink()):
                    yield str(path.relative_to(folder))


def token(name, path, rel, instructions, text, package_digest):
    identity = json.dumps([str(path), name, rel, instructions, text, package_digest],ensure_ascii=False).encode()
    stamp = hashlib.sha256(identity).hexdigest()
    return base64.urlsafe_b64encode(json.dumps([name, rel, stamp]).encode()).decode()


def decode(token_value):
    if len(token_value) > 4096:
        raise ValueError('Invalid match ID')
    try:
        data = json.loads(base64.b64decode(token_value, altchars=b'-_', validate=True))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Invalid match ID') from exc
    if (not isinstance(data,list) or len(data)!=3 or not all(isinstance(v,str) for v in data)
            or not NAME.fullmatch(data[0]) or not re.fullmatch('[0-9a-f]{64}',data[2])):
        raise ValueError('Invalid match ID')
    return data


def run(args, api=None):
    project = args.project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError('Choose a project directory')
    dirs = project_dirs(project)
    if args.host != 'opencode' and (args.agent or args.session):
        raise ValueError('--agent and --session apply to OpenCode')
    if any(not Path(p).is_absolute() or Path(p).name != 'SKILL.md' for p in args.eligible or []):
        raise ValueError('--eligible needs the exact absolute project SKILL.md path from the active host')
    if args.explicit and not args.bundle:
        raise ValueError('--explicit requires the individually selected --bundle NAME')
    if args.method and not args.read:
        raise ValueError('--method requires --read MATCH_ID')
    wanted = decode(args.read) if args.read else None
    if wanted:
        if args.query or (args.bundle and args.bundle != wanted[0]):
            raise ValueError('Read the selected match using its original scope')
        args.bundle = wanted[0]
    words = sorted(set(re.findall(r'[^\W_]+', ' '.join(args.query).casefold())))
    if not wanted and not (1 <= len(words) <= 32):
        raise ValueError('Use one to 32 distinct query terms')
    records = []
    size = 0
    with sqlite3.connect(':memory:') as db:
        db.execute("CREATE VIRTUAL TABLE docs USING fts5(name, path, text, tokenize='porter unicode61')")
        for name, folder, skill, receipt, row, shared, scope in bundles(args, dirs, api):
            local = ((rel, folder/rel) for rel in documents(folder))
            support = staged_shelf.shared_files(folder,skill,receipt,row,shared)
            for rel, candidate in itertools.chain(local,support):
                if wanted and rel != wanted[1]:
                    continue
                try:
                    if rel=='SKILL.md':
                        body = skill
                    elif receipt:
                        key = candidate.relative_to(receipt[1]).as_posix()
                        if key not in receipt[2]:
                            continue
                        body = read(candidate,expected=receipt[2][key])
                    else:
                        body = read(candidate)
                except (OSError, ValueError):
                    continue
                match = token(name, folder, rel, skill, body, receipt[3] if receipt else None)
                if wanted:
                    if match != args.read:
                        raise ValueError('Changed match. Search again.')
                    print(skill, end='' if skill.endswith('\n') else '\n')
                    if rel != 'SKILL.md':
                        print(f'\n--- {name}/{rel} ---')
                        print(body,end='' if body.endswith('\n') else '\n')
                    return
                size += len(body.encode())
                if len(records) >= MAX_FILES or size > MAX_TOTAL:
                    raise ValueError('Project search budget exceeded. Limit the search to one --bundle.')
                db.execute('INSERT INTO docs VALUES (?,?,?)',(name,rel,body))
                records.append((name,candidate,rel,body,match,scope,row.get("source") if receipt else None))
        if wanted:
            raise ValueError('Match unavailable or disabled. Search again.')
        query = ' OR '.join(f'"{w}"' for w in words)
        ranked = db.execute('SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs,3,1,1),rowid LIMIT ?', (query,args.limit))
        output = []
        for (rowid,) in ranked:
            name, candidate, rel, body, match, scope, source = records[rowid-1]
            lines = body.splitlines() or ['']
            line = max(range(len(lines)),key=lambda i:sum(w in lines[i].casefold() for w in words))
            output.append(dict(name=name,scope=scope,source=source,path=str(candidate),line=line+1,excerpt=lines[line].strip()[:240],match_id=match))
    if args.json:
        print(json.dumps(output,ensure_ascii=False))
    else:
        for item in output:
            print('{name}\n  {path}:{line}  {excerpt}\n  {match_id}'.format(**item))


def arguments(cli):
    cli.add_argument('query',nargs='*')
    cli.add_argument('--project',type=Path,default=Path.cwd())
    cli.add_argument('--host',choices=('codex','opencode'),default='codex')
    cli.add_argument('--agent',help='active OpenCode agent for the current location')
    cli.add_argument('--session',help='OpenCode session whose selected agent and permissions apply')
    cli.add_argument('--eligible',action='append',metavar='SKILL_PATH',help='exact current host-permitted project SKILL.md path; repeat as needed')
    cli.add_argument('--bundle',help='restrict discovery to one named project method')
    cli.add_argument('--explicit',action='store_true',help='the user individually selected this exact bundle')
    cli.add_argument('--method',action='store_true',help='with --read, return the complete method and matched support')
    cli.add_argument('--read',metavar='MATCH_ID',help='revalidate and read the full method and matching support file')
    cli.add_argument('--limit',choices=range(1,51),type=int,default=5,metavar='1..50')
    cli.add_argument('--json',action='store_true')
    return cli


if __name__ == '__main__':
    try:
        run(arguments(argparse.ArgumentParser(description=__doc__)).parse_args())
    except (OSError, ValueError, sqlite3.Error) as error:
        sys.exit(str(error))
