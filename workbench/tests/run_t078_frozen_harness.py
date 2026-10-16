"""Verify the approved reader archive before running an existing harness entry."""
import argparse
import json
import os
from pathlib import Path
import sys
import tarfile

SOURCE = Path(__file__).resolve().parents[2]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
CHANGED = {'workbench/tests/run_t078_p1.py', 'workbench/tests/t078_09b_phase_driver.py',
           'workbench/tests/t078_09b_i1_permission.py'}
ENTRIES = {'screen': 'workbench/tests/run_t078_p1.py', 'phase': 'workbench/tests/t078_09b_i1_driver.py',
           'permission': 'workbench/tests/t078_09b_i1_permission.py', 'recover': 'workbench/tests/recover_t078_permission_screen.py',
           'prepare-permission': 'evidence/2026-10-11-batch13/T-078/prepare-a14.py'}


def verify(freeze):
    manifest = json.loads((freeze / 'manifest.json').read_bytes())
    if manifest.get('status') != 'PASS' or not manifest.get('harness_revision') or manifest.get('scene_actions') != 0:
        raise ValueError('invalid_frozen_reader_manifest')
    names = json.loads((freeze / 'source-files.json').read_bytes())
    if manifest['changed_original_files'] != sorted(CHANGED):
        raise ValueError('unapproved_reader_delta')
    original_dir = Path(manifest['original_materials'])
    with tarfile.open(original_dir / 'sources.tar.gz') as old:
        original_names = old.getnames()
    old_revision = json.loads((original_dir / 'static-check.json').read_bytes())['revision']
    if manifest['business_revision'] != old_revision:
        raise ValueError('business_revision_changed')
    if set(names) - set(original_names) != set(manifest['added_files']):
        raise ValueError('unexpected_harness_file')
    if any(not name.startswith('workbench/tests/') for name in manifest['added_files']):
        raise ValueError('product_file_added')
    with tarfile.open(freeze / 'sources.tar.gz') as current, tarfile.open(original_dir / 'sources.tar.gz') as old:
        if current.getnames() != names or len(names) != len(set(names)) or old.getnames() != original_names:
            raise ValueError('archive_member_mismatch')
        differences = []
        for name in names:
            path = (SOURCE / name).resolve()
            if Path(name).is_absolute() or '..' in Path(name).parts or not path.is_relative_to(SOURCE) or not current.getmember(name).isfile():
                raise ValueError('invalid_source_member')
            raw = current.extractfile(name).read()
            if path.read_bytes() != raw:
                raise ValueError('frozen_harness_source_changed:' + name)
            if name in original_names and raw != old.extractfile(name).read():
                differences.append(name)
        if set(differences) != CHANGED or not set(original_names).issubset(names):
            raise ValueError('business_or_unapproved_source_changed')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--entry', choices=ENTRIES)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(); manifest = verify(args.freeze.resolve())
    print(json.dumps({'status': 'PASS', 'harness_revision': manifest['harness_revision'],
                      'business_revision': manifest['business_revision'], 'scope': 'Source byte verification only'}), flush=True)
    if args.check_only:
        return
    if not args.entry:
        parser.error('--entry is required for execution')
    arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
    os.execv(sys.executable, [sys.executable, '-B', str(SOURCE / ENTRIES[args.entry]), *arguments])


if __name__ == '__main__':
    main()
