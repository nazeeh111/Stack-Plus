"""Canonical exposure names; source coordinates and workflow routing stay separate."""
import re

RENAMES = {
    'frontend-design': 'web-ui-design',
    'unslop': 'ui-polish',
    'impeccable-audit': 'ui-quality-audit',
    'impeccable-harden': 'ui-reliability',
    'taste-skill': 'ui-art-direction',
    'core': 'browser-cli-guide',
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
    return {'version': 1, 'renames': dict(RENAMES)}


def entry_name(raw, name):
    text, count = re.subn(r'(?m)^name:.*$', 'name: ' + name, raw.decode(), count=1)
    if count != 1:
        raise ValueError('Selected entry lacks a unique name')
    return text.encode()
