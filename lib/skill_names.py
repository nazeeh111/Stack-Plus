"""Canonical exposure names; source coordinates and workflow routing stay separate."""
import hashlib
import json
import re

RENAMES = {
    'frontend-design': 'web-ui-design',
    'unslop': 'ui-polish',
    'impeccable-audit': 'ui-quality-audit',
    'impeccable-harden': 'ui-reliability',
    'taste-skill': 'ui-art-direction',
    'core': 'browser-cli-guide',
    'codex-skill': 'cli-anything-harnesses',
    'composition-patterns': 'react-composition-patterns',
    'fp-check': 'security-finding-verification',
    'differential-review': 'security-change-review',
    'media-use': 'hyperframes-media',
    'product-marketing': 'product-marketing-context',
    'launch': 'product-launch-strategy',
    'emails': 'email-sequences',
    'interview-script': 'customer-interview-script',
    'synthesize-research': 'user-research-synthesis',
    'cloudflare-security-audit': 'code-security-review',
    'finance-audit-xls': 'spreadsheet-formula-audit',
}

# Reviewed host invocations only: source leaf -> exact operative path -> literal
# token/phrase -> referenced source skill. CLI catalogs, code paths and archives
# are intentionally absent. Some host usage examples live in plain code fences.
HOST_INVOCATIONS = {
    'hyperframes': {path: {'`/media-use`': 'media-use'} for path in (
        'skills/hyperframes/SKILL.md',
        'skills/hyperframes/references/captions.md',
        'skills/hyperframes/references/sound.md',
        'skills/hyperframes/references/format.md',
        'skills/hyperframes/references/types/launch.md',
    )},
    'hyperframes-cli': {
        **{path: {'`/media-use`': 'media-use'} for path in (
            'skills/hyperframes-cli/SKILL.md',
            'skills/hyperframes-cli/references/compare-and-batch.md',
            'skills/hyperframes/references/format.md',
        )},
        'skills/hyperframes-cli/references/init-and-scaffold.md': {
            'see the `media-use` skill': 'media-use',
        },
        'skills/hyperframes-cli/references/upgrade-info-misc.md': {
            'invoke the `media-use` skill': 'media-use',
        },
    },
    'product-marketing': {'SKILL.md': {'`/product-marketing`': 'product-marketing'}},
    'synthesize-research': {'product-management/skills/synthesize-research/SKILL.md': {
        '\n/synthesize-research $ARGUMENTS': 'synthesize-research',
    }},
    'unslop': {'README.md': {
        '`/unslop`': 'unslop', '`$unslop`': 'unslop', '\n/unslop ': 'unslop',
    }},
}
PORT_RECEIPT = 'EXPOSURE-PORT.json'
ORIGINALS = 'EXPOSURE-ORIGINALS'
HOST_NOTES = {'unslop': {'README.md': (
    '> nstack profile: the host invocation examples below use `{exposed}`. '
    'The unchanged upstream source/install paths install the upstream name, '
    'rather than this nstack exposure.\n\n'
)}}
DESCRIPTIONS = {
    'gstack-office-hours': {
        'source': 'YC Office Hours — two modes. (gstack)',
        'exposed': 'Diagnose a startup or product idea, or explore a builder project as a design partner, using gstack Office Hours. Use for problem framing, alternatives and a practical design before implementation.',
    },
    'gstack-plan-eng-review': {
        'source': 'Eng manager-mode plan review. (gstack)',
        'exposed': 'Review an engineering plan for architecture, scope, failure modes, test coverage and rollout using gstack engineering review.',
    },
}


def canonical(name):
    return RENAMES.get(name, name)


def source_name(name):
    return next((source for source, exposed in RENAMES.items() if exposed == name), name)


def metadata(name):
    source = source_name(name)
    return {'source_name': source, 'aliases': [source] if source != name else []}


def policy():
    """Seal the full naming policy so changed exposure rules invalidate releases."""
    return {'version': 2, 'renames': dict(RENAMES), 'host_invocations': HOST_INVOCATIONS,
            'host_notes': HOST_NOTES, 'descriptions': DESCRIPTIONS}


def description(raw):
    header = raw.decode().split('---', 2)[1]
    matches = re.findall(r'(?m)^description:\s*(.*)$', header)
    if len(matches) != 1:
        raise ValueError('Exposure description requires one inline metadata field')
    value = matches[0].strip()
    return json.loads(value) if value.startswith('"') else value


def entry_name(raw, name):
    text, count = re.subn(r'(?m)^name:.*$', 'name: ' + name, raw.decode(), count=1)
    if count != 1:
        raise ValueError('Selected entry lacks a unique name')
    if name in DESCRIPTIONS:
        override = DESCRIPTIONS[name]
        if description(raw) not in (override['source'], override['exposed']):
            raise ValueError('Reviewed exposure description changed: ' + name)
        text = re.sub(r'(?m)^description:.*$', 'description: ' + json.dumps(override['exposed']), text, count=1)
    return text.encode()


def expose_files(source, files, entry=None, name=None):
    """Pure closed-map adaptation, retaining changed originals and an exact receipt."""
    result, changes = dict(files), {}
    for relative, (raw, mode) in files.items():
        metadata_changed = (relative == entry and name in DESCRIPTIONS
                            and description(raw) != DESCRIPTIONS[name]['exposed'])
        data = entry_name(raw, name) if name is not None and relative == entry else raw
        rendered = data
        replacements = {}
        for literal, referenced in HOST_INVOCATIONS.get(source, {}).get(relative, {}).items():
            exposed = canonical(referenced)
            if exposed == referenced:
                continue
            before, after = literal.encode(), literal.replace(referenced, exposed).encode()
            count = rendered.count(before)
            if not count:
                raise ValueError('Reviewed host invocation anchor missing: ' + source + '/' + relative)
            rendered = rendered.replace(before, after)
            replacements[literal] = {'rendered': after.decode(), 'occurrences': count}
        if replacements and relative in HOST_NOTES.get(source, {}):
            rendered = HOST_NOTES[source][relative].format(exposed=canonical(source)).encode() + rendered
        result[relative] = (rendered, mode)
        if rendered != data or metadata_changed:
            original = ORIGINALS + '/' + relative + '.original'
            if original in files or PORT_RECEIPT in files:
                raise ValueError('Exposure provenance collision: ' + source + '/' + relative)
            result[original] = (raw, mode)
            changes[relative] = {'before_sha256': hashlib.sha256(raw).hexdigest(),
                                 'after_sha256': hashlib.sha256(rendered).hexdigest(),
                                 'original': original, 'replacements': replacements}
            if metadata_changed:
                changes[relative]['description'] = DESCRIPTIONS[name]['exposed']
    if changes:
        receipt = {'policy_version': policy()['version'], 'source_name': source,
                   'scope': 'Reviewed host invocations, exposure bindings and entry metadata; pre-exposure bytes retained.',
                   'files': changes}
        result[PORT_RECEIPT] = ((json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode(), 0o444)
    return result
