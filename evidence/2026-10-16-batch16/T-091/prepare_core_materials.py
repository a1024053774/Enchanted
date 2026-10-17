#!/usr/bin/env python3
"""Check the four sparse-checkout materials required by the original core runner.

CONTROLLER ONLY with --restore: materialize absent tracked files from HEAD.
Never overwrite an existing file, edit an assertion, change sparse configuration,
start a service, or write outside these four paths. Default is read-only.
"""
import argparse
import json
from pathlib import Path
import subprocess

PATHS = [
    'fixtures/pagination/CONTRACT.md',
    'fixtures/pagination/pager.py',
    'evidence/2026-10-11-batch13/T-076/card-2/controller-decision-03.md',
    'evidence/2026-10-11-batch13/T-076/card-2/legacy-acceptance-hunks.diff',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    pending, rows = [], []
    for name in PATHS:
        original = subprocess.check_output(['git', 'show', revision + ':' + name], cwd=source)
        target = source / name
        # Check each existing parent without following a link out of the checkout.
        parent = target.parent
        while parent != source:
            if parent.is_symlink():
                raise RuntimeError('Refuse symlink material parent: ' + name)
            parent = parent.parent
        if target.exists() or target.is_symlink():
            if not target.is_file() or target.is_symlink() or target.read_bytes() != original:
                raise RuntimeError('Existing material differs; preserve it: ' + name)
            rows.append({'path': name, 'state': 'present', 'bytes': len(original)})
        else:
            pending.append((target, original))
            rows.append({'path': name, 'state': 'missing', 'bytes': len(original)})
    if args.restore:
        for target, original in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(original)
        for row in rows:
            if row['state'] == 'missing':
                row['state'] = 'restored_from_HEAD'
    print(json.dumps({'status': 'PASS' if args.restore or not pending else 'INCOMPLETE',
        'source_revision': revision, 'restore': args.restore, 'materials': rows}, ensure_ascii=False))
    return 0 if args.restore or not pending else 1


if __name__ == '__main__':
    raise SystemExit(main())
