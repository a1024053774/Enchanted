"""Check reader archive scope with a private source copy, never the live scene."""
import argparse
import json
from pathlib import Path
import shutil
import tarfile
import tempfile

import run_t078_frozen_harness as frozen


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = frozen.SOURCE; original = frozen.BASE / '09b-executable-materials-15'
    with tarfile.open(original / 'sources.tar.gz') as archive:
        old_names = archive.getnames()
    added = ['workbench/tests/p1_output.py', 'workbench/tests/recover_t078_permission_screen.py',
             'workbench/tests/run_t078_frozen_harness.py']
    names = old_names + added
    rows = []
    with tempfile.TemporaryDirectory(prefix='t078-frozen-reader-', dir='/tmp') as tmp:
        root = Path(tmp).resolve(); copied = root / 'source'; copied.mkdir(); packet = root / 'packet'; packet.mkdir()
        for name in names:
            path = copied / name; path.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source / name, path)
        manifest = {'status': 'PASS', 'harness_revision': 'private-fixture-only', 'scene_actions': 0,
                    'original_materials': str(original), 'business_revision': json.loads((original / 'static-check.json').read_bytes())['revision'],
                    'changed_original_files': sorted(frozen.CHANGED), 'added_files': added}
        (packet / 'manifest.json').write_text(json.dumps(manifest)); (packet / 'source-files.json').write_text(json.dumps(names))
        def archive_sources():
            with tarfile.open(packet / 'sources.tar.gz', 'w:gz') as archive:
                for name in names: archive.add(copied / name, arcname=name)
        archive_sources(); frozen.SOURCE = copied
        try:
            frozen.verify(packet); rows.append({'case': 'approved-read-only-delta', 'status': 'PASS'})
            changed = copied / 'workbench/src/panes.ts'; before = changed.read_bytes(); changed.write_bytes(before + b'\n')
            try:
                frozen.verify(packet)
            except ValueError as error:
                rows.append({'case': 'workspace-changed-after-freeze', 'status': 'PASS' if str(error).startswith('frozen_harness_source_changed:') else 'INCOMPLETE', 'error': str(error)})
            else:
                rows.append({'case': 'workspace-changed-after-freeze', 'status': 'INCOMPLETE'})
            archive_sources()
            try:
                frozen.verify(packet)
            except ValueError as error:
                rows.append({'case': 'product-change-hidden-in-new-archive', 'status': 'PASS' if str(error) == 'business_or_unapproved_source_changed' else 'INCOMPLETE', 'error': str(error)})
            else:
                rows.append({'case': 'product-change-hidden-in-new-archive', 'status': 'INCOMPLETE'})
        finally:
            frozen.SOURCE = source
    assert not root.exists()
    report = {'status': 'PASS' if len(rows) == 3 and all(x['status'] == 'PASS' for x in rows) else 'INCOMPLETE',
              'checks': rows, 'scope': 'Private source/archive copy only; no product worktree edits or scene actions'}
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report)); return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
