"""Archive only T-110-referenced fixtures; no hashes, links or source deletion."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

p = argparse.ArgumentParser()
p.add_argument('--summary', type=Path, action='append', required=True)
p.add_argument('--label', required=True)
p.add_argument('--manifest', type=Path, required=True)
args = p.parse_args()
assert not args.manifest.exists(), 'Use a new manifest'
assert args.label and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label)
volume = Path('/Volumes/WD-Elements')
archive = volume / 'a2a-evidence/2026-10-20-batch18/T-110' / args.label
report = dict(status='INCOMPLETE', files=[], source_summaries=list(map(str, args.summary)), original_directories_retained=True,
              replay=['zsh', 'evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh', '/private/tmp/NEW-T110-SUMMARY.json'])
roots = set()

def collect(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ['fixture', 'retained_fixture'] and isinstance(item, str):
                roots.add(Path(item).resolve())
            collect(item)
    elif isinstance(value, list):
        for item in value:
            collect(item)


def inventory(root):
    return {str(path.relative_to(root)): path.stat().st_size for path in root.rglob('*') if not path.is_symlink() and path.is_file()}


try:
    assert os.path.ismount(volume) and volume.resolve() == volume, 'External disk absent; no internal fallback'
    assert not archive.exists(), 'Preserve previous archive; use a new label'
    for summary in args.summary:
        collect(json.loads(summary.read_text(encoding='utf-8')))
    assert roots, 'No referenced fixtures'
    roots = {root for root in roots if not any(parent in roots for parent in root.parents)}
    allowed = ('t110-native-', 't078-2-t108-', 't078-2-t110-', 't108-hook-failure-', 't108-answer-lifecycle-', 't108-question-contract-')
    for root in sorted(roots):
        assert root.parent == Path('/private/tmp') and root.name.startswith(allowed) and root.is_dir(), str(root)
        # Native CLI-created links are evidence, never instructions to copy
        # their external targets. Save each original link target as plain text.
        links = {str(path.relative_to(root)): os.readlink(path) for path in root.rglob('*') if path.is_symlink()}
        before = inventory(root)
        destination = archive / root.name
        destination.mkdir(parents=True, exist_ok=False)
        for name in before:
            src, dst = root / name, destination / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            assert dst.parent.resolve() == dst.parent, 'Archive parent is linked'
            shutil.copy2(src, dst, follow_symlinks=False)
        after = inventory(destination)
        assert before == after and before == inventory(root), 'File count or bytes changed; preserve originals'
        report['files'].append(dict(original=str(root), archive=str(destination), files=len(before), bytes=sum(before.values()),
                                    count_and_bytes='PASS', original_symlinks=links, symlink_targets_copied=False))
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = str(error)
finally:
    with args.manifest.open('x', encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(json.dumps(dict(status=report['status'], manifest=str(args.manifest), error=report.get('error')), ensure_ascii=False))
sys.exit(0 if report['status'] == 'PASS' else 1)
