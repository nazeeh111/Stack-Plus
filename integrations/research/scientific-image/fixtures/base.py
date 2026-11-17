"""Verify frozen public Debian metadata using the base's ordinary signature policy."""
from pathlib import Path
import hashlib
import json
import lzma
import subprocess

metadata = Path('/metadata')
subprocess.run(['/usr/bin/sqv', '--keyring', '/usr/share/keyrings/debian-archive-keyring.pgp',
    '--cleartext', '--output', '/tmp/verified.Release', str(metadata/'InRelease')], check=True)
pins = json.loads(Path('/input/metadata-expected.json').read_text())
for filename, record in pins.items():
    assert hashlib.sha256((metadata/filename).read_bytes()).hexdigest() == record['sha256']
release = Path('/tmp/verified.Release').read_text().split('SHA256:\n', 1)[1].split('\n\n', 1)[0]
lines = [line.split() for line in release.splitlines() if line.startswith(' ')]
assert [pins['Packages.xz']['sha256'], str((metadata/'Packages.xz').stat().st_size),
        'main/binary-arm64/Packages.xz'] in lines
expected = json.loads(Path('/input/debian-artifacts.json').read_text())
packages = lzma.decompress((metadata/'Packages.xz').read_bytes()).decode()
found = {}
for paragraph in packages.split('\n\n'):
    fields = dict(line.split(': ', 1) for line in paragraph.splitlines()
                  if line and not line.startswith(' ') and ': ' in line)
    name = fields.get('Package')
    if name in expected and fields.get('Version') == expected[name]['version']:
        row = expected[name]
        assert fields['SHA256'] == row['sha256']
        assert fields['Size'] == str(row['size'])
        assert fields['Filename'] == row['url'].split('https://deb.debian.org/debian/', 1)[1]
        found[name] = fields['Version']
assert found == {k: v['version'] for k, v in expected.items()}
print('Normal-policy signed frozen metadata and all115 package records verified')
