#!/usr/bin/env python3
"""Prepare the exact reviewed Linux Docker CLI from supplied inert artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
HERE=Path(__file__).resolve().parent
PIN=json.loads((HERE/'CONTROLLER-CLIENT.json').read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def prepare(archive,source,state):
    if state.exists() or state.is_symlink():raise ValueError('Select fresh durable private state')
    if (archive.is_symlink() or source.is_symlink() or digest(archive)!=PIN['archive_sha256']
            or archive.stat().st_size!=PIN['archive_bytes'] or digest(source)!=PIN['source_archive_sha256']):
        raise ValueError('Exact reviewed CLI/source archives required; no download/build fallback')
    with tarfile.open(archive) as bundle:
        members=[m for m in bundle.getmembers() if m.name==PIN['archive_member']]
        if len(members)!=1 or not members[0].isfile() or members[0].size!=PIN['binary_bytes']:
            raise ValueError('CLI archive member differs')
        raw=bundle.extractfile(members[0]).read()
    if hashlib.sha256(raw).hexdigest()!=PIN['binary_sha256']:raise ValueError('CLI binary differs')
    state.mkdir(mode=0o700)
    (state/'docker').write_bytes(raw);(state/'docker').chmod(0o500)
    shutil.copyfile(source,state/'source.tar')
    for name in ['DockerCLI-LICENSE','DockerCLI-NOTICE']:shutil.copyfile(HERE/'licenses'/name,state/name)
    (state/'ACQUISITION.json').write_text(json.dumps(PIN,indent=2)+'\n')
    for path in state.iterdir():path.chmod(0o500 if path.name=='docker' else 0o400)
    return state/'docker'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--source-archive',type=Path,required=True);parser.add_argument('--state',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps({'controller_cli':str(prepare(args.archive,args.source_archive,args.state)),'executed':False}))
    except (OSError,ValueError) as error:parser.error(str(error))
if __name__=='__main__':main()
