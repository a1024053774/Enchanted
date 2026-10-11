#!/usr/bin/env python3
"""Materialize the recorded T-077 product baseline without changing a checkout."""
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
BASE = '14b57d22a84bcaebfa91c5051b9909b53a570fac'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    source = ROOT / 'evidence/2026-10-11-batch13/T-077/outside-red-01'
    receipt = json.loads((source / 'run.json').read_text(encoding='utf-8'))
    if receipt['phase'] != 'baseline' or receipt['red_confirmed'] is not True:
        raise RuntimeError('A confirmed baseline receipt is required')
    product = Path(tempfile.mkdtemp(prefix='s3-base-', dir='/tmp')).resolve()
    copied = []
    with tarfile.open(source / 'sources.tar.gz', 'r:gz') as archive:
        for member in archive.getmembers():
            name = member.name
            if not member.isfile() or not (name.startswith(('workbench/src/', 'acceptance/entry/')) or name in (
                    'workbench/package.json', 'workbench/package-lock.json', 'workbench/tests/daemon_acceptance_host.ts')):
                continue
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise RuntimeError('Archive path is outside the product snapshot')
            with archive.extractfile(member) as handle:
                data = handle.read()
            original = subprocess.run(['git', 'show', BASE + ':' + name], cwd=ROOT, capture_output=True, check=True).stdout
            if data != original:
                raise RuntimeError('Recorded source differs from the assigned baseline commit: ' + name)
            target = product / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(data)
            copied.append(name)
    if not copied:
        raise RuntimeError('No baseline product files were found')
    # The snapshot is a test source directory, not a build output. No dependency
    # is moved, replaced, installed or written through this read-only use.
    dependencies = ROOT / 'workbench/node_modules'
    if not dependencies.is_dir():
        raise RuntimeError('Existing dependencies are unavailable')
    (product / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump({'source_commit': BASE, 'source_archive': str(source / 'sources.tar.gz'),
                   'product_root': str(product), 'dependencies': str(dependencies),
                   'byte_equal_to_git_show': copied}, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(product)


if __name__ == '__main__':
    main()
