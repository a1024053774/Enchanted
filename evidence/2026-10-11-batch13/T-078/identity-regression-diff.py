#!/usr/bin/env python3
"""Diff only the identity repair against the preserved failed candidate."""
import argparse
import difflib
from pathlib import Path
import tarfile

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[3]
archive=Path(__file__).parent/'outside-inbox-01/coop/sources.tar.gz'
paths=['workbench/src/daemon.ts','workbench/src/gates/core.ts','workbench/tests/daemon_acceptance_host.ts']
with tarfile.open(archive) as old, args.output.open('x',encoding='utf-8',newline='\n') as out:
    for name in paths:
        before=old.extractfile(name).read().decode('utf-8').splitlines(keepends=True)
        after=(root/name).read_text(encoding='utf-8').splitlines(keepends=True)
        out.writelines(difflib.unified_diff(before,after,fromfile='a/'+name,tofile='b/'+name))
