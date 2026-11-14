"""Explicit, reviewed English instruction ports. No translation at build time."""
import difflib
import hashlib
import json
import pathlib
import re

P = pathlib.Path
ROOT = P(__file__).resolve().parents[1]
ASSETS = ROOT / 'ports/english'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(repository, revision):
    manifest = json.loads((ASSETS / 'manifest.json').read_text())
    return [row for row in manifest['files']
            if (row['repository'], row['revision']) == (repository, revision)]


def normalized(raw):
    # The final native adapter changes only the discovered entry name.
    return re.sub(rb'(?m)^name: (?:p\d+|x-creative-archify)-', b'name: ', raw, count=1)


def adapted(row, original, prior):
    if sha(original) != row['source_sha256']:
        raise ValueError('English port pinned source changed: ' + row['source_path'])
    if sha(normalized(prior)) not in row['input_sha256']:
        raise ValueError('English port operative input changed: ' + row['target'])
    asset = ASSETS / row['english']
    if row.get('kind') == 'spans':
        text = prior.decode()
        for edit in json.loads(asset.read_text())['replacements']:
            if text.count(edit['old']) != 1:
                raise ValueError('English port span changed: ' + row['target'])
            text = text.replace(edit['old'], edit['new'], 1)
        english = text.encode()
    else:
        english = asset.read_bytes()
    # Keep the source-owned build name; native_setup owns natural naming later.
    name = re.search(rb'(?m)^name: ([^\n]+)$', prior)
    if prior.startswith(b'---\n') and name:
        english, count = re.subn(rb'(?m)^name: [^\n]+$', lambda _: name[0], english, count=1)
        if count != 1:
            raise ValueError('English entry lacks its discovery name: ' + row['english'])
    return english


def changes(source_bytes, prior_bytes, selected):
    """Return adapted bytes and source-fidelity records for explicit known files."""
    output = {}
    receipts = []
    for row in selected:
        original = source_bytes(row['source_path'])
        prior = prior_bytes(row['target'])
        english = adapted(row, original, prior)
        target = row['target']
        upstream = 'ENGLISH-PORT/upstream/' + row['source_path'] + '.reference.txt'
        previous = 'ENGLISH-PORT/native-before/' + target + '.reference.txt'
        difference = 'ENGLISH-PORT/diffs/' + target + '.patch'
        output.update({target: english, upstream: original, previous: prior,
                       difference: ''.join(difflib.unified_diff(
                           prior.decode().splitlines(True), english.decode().splitlines(True),
                           fromfile='native-before/' + target, tofile='english/' + target)).encode()})
        support = []
        for item in row.get('additional', []):
            raw = (ASSETS / item['english']).read_bytes()
            output[item['target']] = raw
            support.append({**item, 'sha256': sha(raw)})
        receipts.append({'repository': row['repository'], 'revision': row['revision'],
                         'source_path': row['source_path'], 'source_sha256': sha(original),
                         'archival_upstream': upstream, 'target': target,
                         'native_before_sha256': sha(prior), 'archival_native_before': previous,
                         'english_asset': row['english'],
                         'english_asset_sha256': sha((ASSETS / row['english']).read_bytes()),
                         'active_sha256': sha(english), 'diff': difference,
                         'additional_english_support': support})
    if receipts:
        output['ENGLISH-PORT/SOURCE-FIDELITY.json'] = (json.dumps({
            'adaptation': 'Reviewed English operative prose; original libraries, source pins and notices retained.',
            'active_hash_stage': 'Before final native discovery-name normalization; host adapters may change entry metadata.',
            'files': receipts}, sort_keys=True, indent=2) + '\n').encode()
    return output


def apply(source, out, spec):
    selected = rows(spec['source_repository'], spec['revision'])
    # One repository can expose several leaves; do not translate another leaf.
    selected = [row for row in selected if row['entry_source'] == spec['source_path']]
    output = changes(lambda rel: (source / rel).read_bytes(),
                     lambda rel: (out / rel).read_bytes(), selected)
    for rel, raw in output.items():
        file = out / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    if output:
        from closure import validate
        validate(out)


def academic_overrides(frozen, overrides, repository, revision):
    # Each optional academic bundle retains the same full source tree.
    return changes(lambda rel: frozen[rel][0],
                   lambda rel: overrides.get(rel, frozen[rel][0]), rows(repository, revision))
