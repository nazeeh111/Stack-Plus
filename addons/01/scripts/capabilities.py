#!/usr/bin/env python3
"""Bounded discovery from nstack indexes and current user/project skill metadata."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat

MAX_FRONTMATTER = 16384
MAX_INDEX_BYTES = 8 * 1024 * 1024
MAX_RUNTIME_FIELD_CHARS = 4096
MAX_RUNTIME_LIST_ITEMS = 32
MAX_PATHS = 8192
MAX_DEPTH = 6
MAX_BODY_BYTES = 131072
MAX_BODY_TOTAL_BYTES = 4194304
MAX_BODY_SNIPPETS = 4
MAX_SNIPPET_CHARS = 240
MAX_CATALOG_BYTES = 1024 * 1024
FACET_KEYS = ('work', 'domains', 'artifacts')
SKIP = {'.git', 'node_modules', '__pycache__', '.cache', 'cache', 'caches', '.venv'}
PRIVATE = {'.ssh', '.aws', '.gnupg', '.azure', '.kube', 'keychains',
           'credentials', 'secrets', 'passwords'}


def safe(path):
    """Inspect paths, never account/provider stores or plugin cache trees."""
    parts = [p.casefold() for p in path.parts]
    return not (PRIVATE.intersection(parts) or SKIP.intersection(parts)
                or any(a == 'plugins' and b == 'cache' for a, b in zip(parts, parts[1:])))


@contextmanager
def directory_fd(path):
    """Walk a validated absolute path without following any component symlink."""
    required = ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK')
    if (os.open not in os.supports_dir_fd or any(not hasattr(os, key) for key in required)
            or not path.is_absolute() or '..' in path.parts or not safe(path)):
        raise ValueError('Safe descriptor-relative discovery is unavailable for this path')
    descriptor = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
    try:
        descriptor = os.open(path.anchor, flags)
        for component in path.parts[1:]:
            following = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        yield descriptor
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def regular_file(path):
    """Nonblocking/no-follow open plus fstat before any content is read."""
    descriptor = None
    with directory_fd(path.parent) as parent:
        try:
            descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                                 | getattr(os, 'O_CLOEXEC', 0), dir_fd=parent)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError('Discovery input is not a regular file')
            stream = os.fdopen(descriptor, 'rb')
            descriptor = None
            with stream:
                yield stream
        finally:
            if descriptor is not None:
                os.close(descriptor)


def quoted_scalar(lines, index, value):
    """Extract bounded YAML flow strings, without evaluating tags or objects."""
    quote = value[0]
    pattern = (r"^'((?:[^']|'')*)'(?:\s+#.*)?$" if quote == "'" else
               r'^"((?:[^"\\]|\\.)*)"(?:\s+#.*)?$')
    candidate = value
    for following in [None, *lines[index + 1:]]:
        if following is not None:
            if following.strip() and not following[0].isspace():
                raise ValueError('Unclosed quoted frontmatter scalar')
            candidate += '\n' + following
        match = re.fullmatch(pattern, candidate, flags=re.DOTALL)
        if match:
            break
    else:
        raise ValueError('Unclosed quoted frontmatter scalar')
    parts = match.group(1).split('\n')
    folded, blanks, escaped_break = '', 0, False
    for position, part in enumerate(parts):
        if position:
            part = part.lstrip(' \t')
        if position < len(parts) - 1:
            trimmed = part.rstrip(' \t')
            # A double-quoted escaped trailing space is content, not folding.
            slashes = len(trimmed) - len(trimmed.rstrip('\\'))
            part = trimmed + (part[len(trimmed):len(trimmed) + 1]
                              if quote == '"' and slashes % 2 else '')
        if position and not part and position < len(parts) - 1:
            blanks += 1
            continue
        if position:
            folded += '\n' * blanks if blanks else ('' if escaped_break else ' ')
        folded += part
        blanks = 0
        slashes = len(part) - len(part.rstrip('\\'))
        escaped_break = quote == '"' and position < len(parts) - 1 and slashes % 2 == 1
        if escaped_break:
            folded = folded[:-1]
    if quote == "'":
        return folded.replace("''", "'")
    escapes = {'0': '\0', 'a': '\a', 'b': '\b', 't': '\t', 'n': '\n',
               'v': '\v', 'f': '\f', 'r': '\r', 'e': '\x1b', ' ': ' ',
               '"': '"', '/': '/', '\\': '\\', 'N': '\x85', '_': '\xa0',
               'L': '\u2028', 'P': '\u2029'}
    result, cursor = [], 0
    while cursor < len(folded):
        character = folded[cursor]
        if character != '\\':
            result.append(character); cursor += 1
            continue
        cursor += 1
        if cursor == len(folded):
            raise ValueError('Incomplete quoted frontmatter escape')
        escape = folded[cursor]
        if escape in escapes:
            result.append(escapes[escape]); cursor += 1
        elif escape in ('x', 'u', 'U'):
            width = {'x': 2, 'u': 4, 'U': 8}[escape]
            digits = folded[cursor + 1:cursor + 1 + width]
            if len(digits) != width or not re.fullmatch(r'[a-fA-F0-9]+', digits):
                raise ValueError('Invalid quoted frontmatter Unicode escape')
            codepoint = int(digits, 16)
            if codepoint > 0x10ffff:
                raise ValueError('Invalid quoted frontmatter Unicode codepoint')
            result.append(chr(codepoint)); cursor += width + 1
        else:
            raise ValueError('Unsupported quoted frontmatter escape')
    return ''.join(result)


def frontmatter(entry):
    """Read only the bounded YAML header. No YAML tags or code are evaluated."""
    with regular_file(entry) as stream:
        first = stream.readline(MAX_FRONTMATTER + 1)
        if first.removeprefix(b'\xef\xbb\xbf').rstrip(b'\r\n') != b'---':
            return {}, b''
        raw = first
        while len(raw) <= MAX_FRONTMATTER:
            line = stream.readline(MAX_FRONTMATTER - len(raw) + 1)
            if not line:
                break
            raw += line
            if line.rstrip(b'\r\n') == b'---':
                if len(raw) > MAX_FRONTMATTER:
                    break
                lines = raw.decode('utf-8').splitlines()[1:-1]
                values = {}
                for i, line in enumerate(lines):
                    if re.fullmatch(r'metadata:\s*(?:#.*)?', line):
                        children = []
                        for following in lines[i + 1:]:
                            if following.lstrip().startswith('#'):
                                continue
                            if following.strip() and not following[0].isspace():
                                break
                            if following.strip():
                                children.append(following)
                        indent = min((len(v) - len(v.lstrip()) for v in children), default=0)
                        for child in children:
                            if len(child) - len(child.lstrip()) == indent:
                                policy = re.fullmatch(r'opencode/autoinvoke:\s*(true|false)(?:\s+#.*)?', child.strip())
                                if policy:
                                    values['opencode/autoinvoke'] = policy.group(1)
                    match = re.match(r'^(name|description|disable-model-invocation):\s*(.*)$', line)
                    if not match:
                        continue
                    key, value = match.groups()
                    if re.fullmatch(r'[>|][1-9]?[+-]?(?:\s+#.*)?', value):
                        block = []
                        for following in lines[i + 1:]:
                            if following.strip() and not following[0].isspace():
                                break
                            block.append(following)
                        indent = min((len(v) - len(v.lstrip()) for v in block if v.strip()), default=0)
                        block = [v[indent:] if v.strip() else '' for v in block]
                        value = '\n'.join(block)
                        if value is not None and match.group(2).startswith('>'):
                            value = re.sub(r'(?<=\S)\n(?=\S)', ' ', value)
                        value = value.strip()
                    elif value.startswith(('"', "'")):
                        value = quoted_scalar(lines, i, value)
                    else:
                        # YAML also permits a plain scalar to start on the next
                        # indented line, without a > or | block marker.
                        plain = [re.split(r'\s+#', value, maxsplit=1)[0].strip()]
                        for following in lines[i + 1:]:
                            if following.strip() and not following[0].isspace():
                                break
                            if following.lstrip().startswith('#'):
                                continue
                            plain.append(re.split(r'\s+#', following.strip(), maxsplit=1)[0])
                        value = re.sub(r'(?<=\S)\n(?=\S)', ' ', '\n'.join(plain)).strip()
                    if isinstance(value, str):
                        values[key] = value
                return values, raw
    raise ValueError('Skill frontmatter exceeds the bound or has no closing delimiter')


def skill_record(entry, name, deployment, metadata=None):
    if not isinstance(deployment, str):
        deployment = 'recorded; malformed deployment omitted'
    record = {'kind': 'skill', 'name': name, 'path': str(entry),
              'instructions_present': metadata is not None, 'deployment': deployment}
    if metadata is not None:
        values, raw = metadata
        record['description'] = values.get('description', '')
        record['metadata_sha256'] = hashlib.sha256(raw).hexdigest()
        record['hash_scope'] = 'SKILL.md frontmatter only'
        if (values.get('disable-model-invocation', '').casefold() == 'true'
                or values.get('opencode/autoinvoke') == 'false'):
            record['manual_only'] = True
    return record


def bound_skill_metadata(record):
    """Omit oversized identity/prose fields intact, never truncate an identifier."""
    omitted = []
    for key in ('name', 'source_name', 'aliases', 'deployment', 'description'):
        value = record.get(key)
        oversized = (isinstance(value, str) and len(value) > MAX_RUNTIME_FIELD_CHARS
                     or isinstance(value, list) and
                     (len(value) > MAX_RUNTIME_LIST_ITEMS
                      or sum(map(len, value)) > MAX_RUNTIME_FIELD_CHARS))
        if oversized:
            omitted.append(key)
            del record[key]
    if omitted:
        record['oversized_fields_omitted'] = omitted
    return record


def active_host(host=None):
    if host is not None and host not in ('native', 'claude'):
        raise ValueError('Discovery host must be native or claude')
    return host or ('claude' if 'claude-releases' in Path(__file__).resolve().parts else 'native')


def inventory(state, skill_roots=None, host=None, body=False):
    state = Path(state).expanduser().resolve()
    host = active_host(host)
    release_root = state / ('claude-releases' if host == 'claude' else 'native-releases')
    skill_index = 'claude-skill-index.json' if host == 'claude' else 'native-skill-index.json'
    records, sources, seen = [], [], set()
    for filename, kind in ((skill_index, "skill"),
                           ("native-tools/index.json", "runtime")):
        source = state / filename
        resolved = source.resolve()
        if source.is_symlink() or resolved != source or not safe(resolved) or not resolved.is_relative_to(state):
            raise ValueError('Index must be a regular in-state path without redirects or private/cache trees')
        if not source.is_file():
            continue
        with regular_file(resolved) as stream:
            raw = stream.read(MAX_INDEX_BYTES + 1)
        if len(raw) > MAX_INDEX_BYTES:
            raise ValueError('Discovery index exceeds byte limit: ' + filename)
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("Expected an array in " + filename)
        source_info = {"file": str(source), "sha256": hashlib.sha256(raw).hexdigest()}
        sources.append(source_info)
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                continue
            if kind == 'skill':
                path_value = row.get('skill_path')
                if not isinstance(path_value, str) or not path_value.strip():
                    continue
                try:
                    entry = Path(path_value)
                    resolved = entry.resolve()
                    if (entry.name != 'SKILL.md' or resolved.name != 'SKILL.md'
                            or not safe(resolved)
                            or not resolved.is_relative_to(release_root.resolve())):
                        continue
                    if resolved in seen:
                        continue
                    metadata = frontmatter(resolved) if resolved.is_file() else None
                    record = skill_record(entry, row['name'], row.get('deployment', 'recorded'), metadata)
                    if body and metadata is not None:
                        record['_body_path'] = str(resolved)
                    if isinstance(row.get('source_name'), str):
                        record['source_name'] = row['source_name']
                    aliases = row.get('aliases')
                    if isinstance(aliases, list) and all(isinstance(alias, str) for alias in aliases):
                        record['aliases'] = aliases
                    bound_skill_metadata(record)
                    if 'name' not in record:
                        source_info['oversized_skill_records_omitted'] = source_info.get('oversized_skill_records_omitted', 0) + 1
                        continue
                    seen.add(resolved)
                except (OSError, ValueError, RuntimeError):
                    continue
            else:
                record = {'kind': 'runtime', 'name': row['name']}
                if len(row['name']) > MAX_RUNTIME_FIELD_CHARS:
                    continue
                for key in ('description', 'activation', 'readiness', 'limits', 'version', 'source_revision', 'native_mcp', 'binary', 'python', 'node', 'entrypoint', 'recipe', 'instructions', 'guide', 'documentation'):
                    if isinstance(row.get(key), str):
                        record[key] = row[key]
                # Runtime limits may be a prose string or separate constraints.
                # Keep their shape; never turn limitations into capability matches.
                for key in ('limits', 'readiness'):
                    value = row.get(key)
                    if isinstance(value, list) and all(isinstance(item, str) for item in value):
                        record[key] = list(value)
                if type(row.get('callable')) is bool:
                    record['callable'] = row['callable']
                if isinstance(row.get('state'), str):
                    record['state'] = row['state']
                aliases = row.get('aliases')
                if isinstance(aliases, list) and all(isinstance(alias, str) for alias in aliases):
                    record['aliases'] = aliases
                # These are inert invocation metadata, never executed here.
                for key in ('command', 'invoke'):
                    value = row.get(key)
                    if isinstance(value, str) or (isinstance(value, list)
                            and value and all(isinstance(part, str) for part in value)):
                        record[key] = value
                checks = row.get('checks')
                if isinstance(checks, str) or (isinstance(checks, list)
                        and all(isinstance(item, str) for item in checks)):
                    record['recorded_checks'] = list(checks) if isinstance(checks, list) else checks
                omitted = []
                for key, value in list(record.items()):
                    oversized = (isinstance(value, str) and len(value) > MAX_RUNTIME_FIELD_CHARS
                                 or isinstance(value, list) and
                                 (len(value) > MAX_RUNTIME_LIST_ITEMS
                                  or sum(map(len, value)) > MAX_RUNTIME_FIELD_CHARS))
                    if oversized:
                        omitted.append(key)
                        del record[key]
                if omitted:
                    record['oversized_fields_omitted'] = omitted
            records.append(record)
    roots = [Path(p).expanduser().absolute() for p in (skill_roots or [])]
    allowed = [release_root.resolve()]
    for root in roots:
        try:
            if safe(root) and safe(root.resolve()):
                allowed.append(root.resolve())
        except (OSError, RuntimeError):
            pass
    remaining = MAX_PATHS
    for root in roots:
        pairs, visited, skipped = [], set(), 0
        oversized_records = 0
        pending = [(root, 0)]
        while pending and remaining:
            path, depth = pending.pop()
            remaining -= 1
            try:
                resolved = path.resolve()
                if (not safe(path) or not safe(resolved) or resolved in visited
                        or not any(resolved.is_relative_to(base) for base in allowed)):
                    skipped += 1
                    continue
                visited.add(resolved)
                if not resolved.is_dir():
                    continue
                entry = path / 'SKILL.md'
                if entry.exists() or entry.is_symlink():
                    target = entry.resolve()
                    if (target.name != 'SKILL.md' or not safe(target)
                            or not any(target.is_relative_to(base) for base in allowed)):
                        skipped += 1
                        continue
                    values, raw = frontmatter(target)
                    pairs.append((str(target), hashlib.sha256(raw).hexdigest()))
                    if target not in seen:
                        record = skill_record(entry, values.get('name') or path.name,
                                              'current file; host enablement not established', (values, raw))
                        if body:
                            record['_body_path'] = str(target)
                        bound_skill_metadata(record)
                        if 'name' not in record:
                            oversized_records += 1
                            continue
                        records.append(record)
                        seen.add(target)
                    continue  # Support directories never become extra skills.
                if depth < MAX_DEPTH:
                    # A shared path budget also bounds directory enumeration.
                    children = []
                    if os.scandir not in os.supports_fd:
                        raise ValueError('Descriptor-relative directory enumeration is unavailable')
                    with directory_fd(resolved) as descriptor, os.scandir(descriptor) as entries:
                        for item in entries:
                            remaining -= 1
                            if remaining < 0:
                                remaining = 0
                                break
                            try:
                                if item.name.casefold() not in SKIP and (item.is_dir(follow_symlinks=False) or item.is_symlink()):
                                    children.append(path / item.name)
                            except OSError:
                                skipped += 1
                    pending.extend((child, depth + 1) for child in sorted(children, reverse=True))
            except (OSError, ValueError, RuntimeError):
                skipped += 1
        sources.append({'root': str(root), 'sha256': hashlib.sha256(json.dumps(sorted(pairs)).encode()).hexdigest(),
                        'hash_scope': 'resolved SKILL paths and frontmatter hashes', 'skills': len(pairs),
                        'skipped': skipped, 'path_budget_exhausted': remaining == 0,
                        'max_depth': MAX_DEPTH})
        if oversized_records:
            sources[-1]['oversized_skill_records_omitted'] = oversized_records
    return records, sources


def metadata_matches(terms, text):
    """Literal words/phrases and simple s-plurals, never arbitrary substrings."""
    text = text.casefold()
    matched = []
    for term in terms:
        forms = {term}
        if term.isalpha():
            forms.add(term + 's')
            if len(term) > 3 and term.endswith('s') and not term.endswith('ss'):
                forms.add(term[:-1])
        if any(re.search(r'(?<!\w)' + re.escape(form) + r'(?!\w)', text) for form in forms):
            matched.append(term)
    return matched


def functional_catalog():
    """Read this skill's inert, bounded navigation data; never trust stale cards."""
    path = Path(__file__).resolve().parents[1] / 'references/capability-cards.json'
    if not path.exists():
        return {}, {}, {'status': 'unavailable'}
    try:
        with regular_file(path) as stream:
            raw = stream.read(MAX_CATALOG_BYTES + 1)
        if len(raw) > MAX_CATALOG_BYTES:
            raise ValueError('Functional catalog exceeds byte limit')
        data = json.loads(raw)
        if data.get('version') != 1 or not isinstance(data.get('cards'), dict):
            raise ValueError('Invalid functional catalog schema')
        facets = data.get('facets', {})
        if not all(isinstance(facets.get(key), dict) and
                   all(isinstance(k, str) and isinstance(v, str) and len(k) <= 64 and len(v) <= 120
                       for k, v in facets[key].items()) and len(facets[key]) <= 64
                   for key in FACET_KEYS):
            raise ValueError('Invalid functional facets')
        cards = {}
        for identity, card in data['cards'].items():
            if (not isinstance(identity, str) or not isinstance(card, dict)
                    or not re.fullmatch(r'[a-f0-9]{64}', str(card.get('description_sha256', '')))):
                continue
            if (not isinstance(card.get('function'), str) or not 0 < len(card['function']) <= 180
                    or not isinstance(card.get('distinguish'), str) or len(card['distinguish']) > 260):
                continue
            if not all(isinstance(card.get(key), list) and 0 < len(card[key]) <= 8
                       and all(isinstance(v, str) and v in facets[key] for v in card[key])
                       for key in FACET_KEYS):
                continue
            cards[identity] = {key: card[key] for key in
                               ('description_sha256', 'function', 'distinguish', *FACET_KEYS)}
        return cards, facets, {'status': 'read', 'path': str(path),
                               'sha256': hashlib.sha256(raw).hexdigest(), 'cards': len(cards)}
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as error:
        return {}, {}, {'status': 'unavailable', 'reason': type(error).__name__}


def attach_function(record, cards):
    """A card describes function, not enablement, authority or execution readiness."""
    if record.get('kind') != 'skill':
        record['functional_status'] = 'runtime; use current invocation and readiness metadata'
        return record
    card = cards.get(record.get('source_name', record['name']))
    if not card:
        record['functional_status'] = 'unclassified; use current metadata'
    elif card['description_sha256'] != hashlib.sha256(record.get('description', '').encode()).hexdigest():
        record['functional_status'] = 'stale description; card ignored'
    else:
        record['functional_status'] = 'current description-bound navigation'
        record['function'] = dict(card)
    return record


def facet_match(record, filters):
    """OR within a facet, AND across facets; filters never establish completeness."""
    return all(set(values).intersection(record.get('function', {}).get(key, []))
               for key, values in (filters or {}).items() if values)


def browse(state, facet, skill_roots=None, host=None, filters=None, limit=8):
    records, sources = inventory(Path(state), skill_roots=skill_roots, host=host)
    cards, facets, provenance = functional_catalog()
    if facet not in FACET_KEYS:
        raise ValueError('Unknown functional facet')
    groups, unclassified = {}, []
    for record in records:
        attach_function(record, cards)
        if not record.get('function'):
            unclassified.append({'name': record['name'], 'status': record['functional_status']})
        if not facet_match(record, filters):
            continue
        for value in record.get('function', {}).get(facet, []):
            group = groups.setdefault(value, {'label': facets[facet][value], 'count': 0, 'members': [], 'examples': []})
            group['count'] += 1
            group['members'].append(record['name'])
            if len(group['examples']) < limit:
                group['examples'].append({k: record[k] for k in ('name', 'path', 'function')})
    return {'facet': facet, 'groups': groups, 'unclassified': unclassified,
            'sources': sources, 'functional_catalog': provenance,
            'scope': 'Overlapping navigation views, never exclusive routes or runtime readiness. '
                     'Examples are bounded, not best-method rankings. New/stale/unclassified capabilities '
                     'remain available through ordinary metadata/body and native host discovery.'}


def body_prefix(entry, metadata_sha256, budget):
    """Read only this admitted SKILL through the same no-follow boundary.

    The aggregate budget includes this additional header read. File-size and
    body hashes describe observations, not an atomic snapshot or instructions.
    """
    consumed, header = 0, b''
    with regular_file(entry) as stream:
        while consumed < budget and len(header) <= MAX_FRONTMATTER:
            line = stream.readline(min(MAX_FRONTMATTER + 1 - len(header), budget - consumed))
            consumed += len(line)
            if not line:
                break
            header += line
            if len(header) == len(line):
                if line.removeprefix(b'\xef\xbb\xbf').rstrip(b'\r\n') != b'---':
                    return '', {'status': 'no_frontmatter', 'read_bytes': consumed}
            elif line.rstrip(b'\r\n') == b'---':
                break
        else:
            return '', {'status': 'header_bound', 'read_bytes': consumed}
        if (not header.endswith((b'---\n', b'---\r\n', b'---'))
                or hashlib.sha256(header).hexdigest() != metadata_sha256):
            return '', {'status': 'metadata_changed', 'read_bytes': consumed}
        capacity = min(MAX_BODY_BYTES, budget - consumed)
        if capacity <= 0:
            return '', {'status': 'budget_exhausted', 'read_bytes': consumed}
        raw = stream.read(capacity)
        consumed += len(raw)
        size = max(0, os.fstat(stream.fileno()).st_size - len(header))
    truncated = size > len(raw)
    return raw.decode('utf-8', errors='replace'), {
        'status': 'read', 'sha256': hashlib.sha256(raw).hexdigest(),
        'hash_scope': 'SKILL.md body prefix bytes read' if truncated else 'SKILL.md complete body bytes read',
        'body_bytes': len(raw), 'read_bytes': consumed, 'truncated': truncated,
        'observed_body_size': size, 'header_sha256': hashlib.sha256(header).hexdigest(),
        'decoding': 'UTF-8; invalid bytes replaced in excerpts',
        'resolved_path': str(entry), 'first_line': header.count(b'\n') + 1,
    }


def excerpt(text, term, field, first_line=None):
    """A bounded literal-match lead, including negation and surrounding context."""
    forms = {term}
    if term.isalpha():
        forms.add(term + 's')
        if len(term) > 3 and term.endswith('s') and not term.endswith('ss'):
            forms.add(term[:-1])
    folded = text.casefold()
    match = re.search(r'(?<!\w)(?:' + '|'.join(re.escape(form) for form in sorted(forms))
                      + r')(?!\w)', folded)
    if not match:
        return None
    position = match.start()
    if len(folded) != len(text):
        # Preserve original source text/line coordinates when Unicode folding
        # expands a character, e.g. Straße -> strasse.
        offset = 0
        for original_position, character in enumerate(text):
            offset += len(character.casefold())
            if offset > match.start():
                position = original_position
                break
    start = max(0, position - MAX_SNIPPET_CHARS // 3)
    end = min(len(text), start + MAX_SNIPPET_CHARS)
    result = {'field': field, 'term': term, 'excerpt': text[start:end],
              'excerpt_truncated': start > 0 or end < len(text)}
    if first_line is not None:
        result['line'] = first_line + text.count('\n', 0, position)
    return result


def prepare_snapshot(state, skill_roots=None, host=None, body=False, facet_filters=None):
    """One fresh local observation shared only by the current search invocation."""
    records, sources = inventory(Path(state), skill_roots=skill_roots, host=host, body=body)
    cards, _, catalog_source = functional_catalog()
    prepared = []
    remaining, body_sources, body_counts = MAX_BODY_TOTAL_BYTES, [], {'read': 0, 'unavailable': 0, 'budget_exhausted': 0}
    for record in records:
        attach_function(record, cards)
        # Excluded methods must not consume the eligible body's byte allowance.
        if not facet_match(record, facet_filters):
            continue
        body_text, body_info = '', None
        admitted = record.pop('_body_path', None)
        if body and admitted:
            if remaining <= 0:
                body_info = {'status': 'budget_exhausted', 'read_bytes': 0}
            else:
                try:
                    body_text, body_info = body_prefix(Path(admitted), record['metadata_sha256'], remaining)
                except (OSError, ValueError, RuntimeError):
                    # A failed read may have consumed bytes before raising.
                    # Reserve its entire possible allowance rather than retry
                    # beyond the shared byte boundary or invent an exact count.
                    body_info = {'status': 'unavailable', 'read_bytes': min(
                        remaining, MAX_FRONTMATTER + 1 + MAX_BODY_BYTES),
                        'read_bytes_scope': 'conservative failed-read budget charge'}
            remaining -= body_info['read_bytes']
            status = body_info['status']
            body_counts[status if status in body_counts else 'unavailable'] += 1
            body_sources.append((admitted, body_info))
            record['body_source'] = body_info
        if body:
            record['_body_text'] = body_text
        prepared.append(record)
    return {'records': prepared, 'sources': sources, 'catalog_source': catalog_source,
            'body': body, 'body_sources': body_sources, 'body_counts': body_counts,
            'remaining': remaining, 'host': active_host(host)}


def search_snapshot(snapshot, terms, limit=8):
    """Rank one need without mutating or rereading its invocation's observation."""
    sources, catalog_source = snapshot['sources'], snapshot['catalog_source']
    body, host = snapshot['body'], snapshot['host']
    body_sources, body_counts, remaining = snapshot['body_sources'], snapshot['body_counts'], snapshot['remaining']
    words = list(dict.fromkeys(word.strip().casefold() for word in terms if word.strip()))
    ranked = []
    for original in snapshot['records']:
        record = dict(original)
        body_text = record.pop('_body_text', '')
        body_info = record.get('body_source')
        identities = [record.get('name', ''), record.get('source_name', ''), *record.get('aliases', [])]
        exact = [word for word in words if len(words) == 1
                 and word in [value.casefold() for value in identities]]
        function_text = ' '.join(record.get(key, '') for key in ('description', 'activation'))
        function_text += ' ' + record.get('function', {}).get('function', '')
        function = metadata_matches(words, function_text)
        identity = metadata_matches(words, ' '.join(identities))
        checks = record.get('recorded_checks', '')
        checks_text = ' '.join(checks) if isinstance(checks, list) else checks
        context = metadata_matches(words, ' '.join((record.get('native_mcp', ''), checks_text)))
        score = (bool(exact), len(function), len(identity) if not function else 0,
                 len(context) if not function and not identity else 0)
        expanded = None
        if body:
            body_terms = metadata_matches(words, body_text)
            coverage = [word for word in words if word in function or word in body_terms]
            score = (bool(exact), len(coverage), len(identity) if not coverage else 0,
                     len(context) if not coverage and not identity else 0)
            fields = {key: metadata_matches(words, record.get(key, '')) for key in ('description', 'activation')}
            fields['functional_summary'] = metadata_matches(words, record.get('function', {}).get('function', ''))
            evidence = []
            for field, text_value, matches, first_line in (
                    ('body', body_text, body_terms, (body_info or {}).get('first_line', 1)),
                    ('description', record.get('description', ''), fields['description'], None),
                    ('activation', record.get('activation', ''), fields['activation'], None),
                    ('functional_summary', record.get('function', {}).get('function', ''), fields['functional_summary'], None)):
                for term in matches:
                    snippet = excerpt(text_value, term, field, first_line)
                    if snippet and len(evidence) < MAX_BODY_SNIPPETS:
                        evidence.append(snippet)
            expanded = {'body': body_terms, 'concept_coverage': coverage, 'fields': fields,
                        'evidence': evidence}
        if any(score):
            ranked.append((score, {**record, 'match': {
                'exact_identity': exact, 'function': function, 'identity': identity, 'context': context,
                'rank': list(score),
                **(expanded or {}),
            }}))
    # Equal evidence keeps inventory order; a brand's alphabetic position is not relevance.
    ranked.sort(key=lambda item: item[0], reverse=True)
    result = {'matches': [row for _, row in ranked[:limit]], 'total_matches': len(ranked), 'host': active_host(host),
            'sources': sources, 'functional_catalog': catalog_source,
            'scope': 'Fresh local metadata discovery only. A record or current file does not prove host '
                     'enablement, callability, authorization or successful execution. '
                     'Whole-query exact identities rank first; functional matches tie on functional evidence. '
                     'Identity/check-only matches are fallback; '
                     'equal ranks do not establish a better method. Word/phrase and simple s-plural matches '
                     'are lexical, not semantic. '
                     'Runtime readiness and limits are recorded claims, not a current execution check. '
                     'Connected host tools and plugins require native discovery separately. '
                     'Function cards are description-bound navigation; facets and distinguishing boundaries '
                     'add no rank weight. Drop filters and search current metadata for unclassified or new capabilities.'}
    if body:
        result['body_discovery'] = {
            'per_file_body_limit_bytes': MAX_BODY_BYTES, 'aggregate_read_limit_bytes': MAX_BODY_TOTAL_BYTES,
            'read_bytes': MAX_BODY_TOTAL_BYTES - remaining, 'records': body_counts,
            'read_bytes_scope': 'additional header/body bytes; failed reads conservatively charge their maximum allowance',
            'sources_sha256': hashlib.sha256(json.dumps(body_sources, sort_keys=True).encode()).hexdigest(),
            'hash_scope': 'admitted resolved SKILL paths and observed body-source provenance',
        }
        result['scope'] = ('Fresh bounded SKILL-body and metadata lexical discovery. Whole-query exact identities rank first; '
                           'expanded ranks compare distinct query concepts found in description/activation, '
                           'current description-bound functional summary or body. '
                           'Matched fields and inert excerpts are retrieval leads, including negative or misleading text; '
                           'they do not establish suitability, best method, callability, enablement or authority. '
                           'No reference, script or linked file is traversed. Body hashes cover only observed body bytes, '
                           'with prefix truncation and aggregate exhaustion explicit. Runtime readiness/limits are not '
                           'positive function claims. Equal ranks do not establish a better method. '
                           'Connected tools/plugins still require native discovery and verification.')
    return result


def search(state, terms, limit=8, skill_roots=None, host=None, body=False, facet_filters=None):
    snapshot = prepare_snapshot(state, skill_roots, host, body, facet_filters)
    return search_snapshot(snapshot, terms, limit)


def search_many(state, queries, limit=8, skill_roots=None, host=None, body=False, facet_filters=None):
    """Independent ranked needs from one fresh, nonpersistent observation."""
    snapshot = prepare_snapshot(state, skill_roots, host, body, facet_filters)
    return [search_snapshot(snapshot, terms, limit) for terms in queries]


def default_skill_roots(home=None, cwd=None, host=None):
    home, cwd = Path(home or Path.home()), Path(cwd or Path.cwd())
    claude = active_host(host) == 'claude'
    current_user = home.resolve() == Path.home().resolve()
    configured = os.environ.get('CLAUDE_CONFIG_DIR') if claude and current_user else None
    claude_home = Path(configured).expanduser().absolute() if configured else home / '.claude'
    configured_codex = os.environ.get('CODEX_HOME') if not claude and current_user else None
    codex_home = Path(configured_codex).expanduser().absolute() if configured_codex else home / '.codex'
    roots = ([claude_home / 'skills'] if claude else
             [home / '.agents/skills', codex_home / 'skills', home / '.config/opencode/skills'])
    for folder in [cwd, *cwd.parents]:
        roots.extend([folder / '.claude/skills'] if claude else
                     [folder / '.agents/skills', folder / '.opencode/skills'])
        if (folder / '.git').exists() or folder == home:
            break
    return list(dict.fromkeys(roots))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('terms', nargs='*')
    parser.add_argument('--state', type=Path, help='Isolated index lookup unless --skills-root is also supplied')
    parser.add_argument('--skills-root', type=Path, action='append', help='Also enumerate this skill root; repeatable')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--host', choices=('native', 'claude'), help='Default follows this helper’s installed release; native covers Codex/OpenCode')
    parser.add_argument('--body', action='store_true', help='Expand an insufficient metadata search to bounded admitted SKILL bodies; excerpts are inert leads')
    parser.add_argument('--need', action='append', help='Independent contribution query; repeat to avoid one need crowding out another')
    parser.add_argument('--browse', choices=FACET_KEYS, help='Browse overlapping functional views; examples are not rankings')
    for facet in FACET_KEYS:
        parser.add_argument('--' + facet, action='append', help='Optional navigation filter; OR within, AND across facets')
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error('--limit must be between 1 and 30')
    if not args.terms and not args.need and not args.browse:
        parser.error('Supply query terms, --need or --browse')
    roots = args.skills_root if args.skills_root is not None else (None if args.state is not None else default_skill_roots(host=args.host))
    state = args.state or Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
    filters = {key: getattr(args, key) for key in FACET_KEYS if getattr(args, key)}
    try:
        if args.browse:
            result = browse(state, args.browse, roots, args.host, filters, args.limit)
        elif args.need:
            queries = args.need + ([' '.join(args.terms)] if args.terms else [])
            results = search_many(state, [q.split() for q in queries], args.limit, roots,
                                  args.host, args.body, filters)
            result = {'needs': [{'need': q, **found} for q, found in zip(queries, results)],
                      'scope': 'Independent candidate lists preserve contribution coverage. '
                               '01 decides and verifies the compatible combination; this helper does not choose it. '
                               'All needs share one fresh invocation snapshot; per-need provenance describes '
                               'shared observations, not additional physical reads.'}
        else:
            result = search(state, args.terms, args.limit, roots, args.host, args.body, filters)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
