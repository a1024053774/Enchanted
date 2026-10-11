#!/usr/bin/env python3
"""Collect only completed, version-bound rebase-01 receipts; no test execution."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077'
HEAD = '446f25c3de00925dfcc2f1c3f1375713676e166b'


def archive_large_outputs():
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External evidence volume is not mounted')
    records = []
    for top in sorted(EVIDENCE.glob('outside-rebase-01-*')):
        paths = sorted(top.rglob('*')) if top.is_dir() else [top]
        for path in paths:
            if not path.is_file() or path.stat().st_size <= 5 * 1024 * 1024:
                continue
            destination = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077') / path.relative_to(EVIDENCE)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with path.open('rb') as source, destination.open('xb') as target:
                shutil.copyfileobj(source, target)
                target.flush(); os.fsync(target.fileno())
            with path.open('rb') as source, destination.open('rb') as target:
                while True:
                    left, right = source.read(1024 * 1024), target.read(1024 * 1024)
                    if left != right:
                        raise ValueError('Archive bytes differ: ' + str(path))
                    if not left:
                        break
            pointer = path.with_name(path.name + '.archive.json')
            record = {'original': str(path), 'archive': str(destination), 'pointer': str(pointer),
                      'bytes': path.stat().st_size,
                      'replay': ['bash', str(EVIDENCE / 'outside-sandbox.sh'), 'rebase-01']}
            with pointer.open('x', encoding='utf-8') as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2); handle.write('\n')
            path.unlink()  # Only this batch's verified output is relocated.
            records.append(record)
    return records


def main():
    out = EVIDENCE / 'outside-rebase-01-summary.json'
    if out.exists():
        raise FileExistsError(out)
    stages = []

    def read(stage, filename='run.json'):
        path = EVIDENCE / ('outside-rebase-01-' + stage) / filename
        return path, json.loads(path.read_text(encoding='utf-8'))

    path, v = read('contracts')
    provenance = json.loads((path.parent / 'preflight.json').read_text(encoding='utf-8'))
    passed = v['status'] == 'PASS' and len(v['cases']) == 25 and all(
        (c['tests_run'], c['failures'], c['errors'], c['skipped'], c['exit_code']) == (1, 0, 0, 0, 0) for c in v['cases'])
    stages.append({'stage': 'contracts-including-seven-conflicts', 'tests': 25, 'path': str(path),
                   'pass': passed and provenance['head']['stdout'].strip() == HEAD})
    for name, count in [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1), ('cards', 15), ('identity', 4)]:
        path, v = read(name)
        passed = (v['status'], v['tests_run'], v['failures'], v['errors'], v['skipped']) == ('PASS', count, 0, 0, 0)
        if name != 'identity':
            passed = passed and not v['collection_errors'] and v['exit_code'] == 0 and v['source_commit'] == HEAD
        stages.append({'stage': name, 'tests': count, 'path': str(path), 'pass': passed})
    path, v = read('shutdown')
    stages.append({'stage': 'shutdown', 'tests': 4, 'path': str(path),
                   'pass': v['status'] == 'PASS' and v['tests_run'] == 4 and not v['failures'] and not v['errors'] and not v['skipped']})
    path, v = read('native-final', 'results.json')
    stages.append({'stage': 'native-final', 'tests': 9, 'path': str(path),
                   'pass': len(v['results']) == 9 and all(r['failure'] is None for r in v['results'])})
    path, v = read('dispatch-state', 'results.json')
    stages.append({'stage': 'dispatch-state', 'tests': 1, 'path': str(path), 'pass': v['failure'] is None})
    path = EVIDENCE / 'outside-rebase-01-panes.json'
    panes = json.loads(path.read_text(encoding='utf-8'))
    stages.append({'stage': 'panes', 'tests': 4, 'path': str(path),
                   'pass': panes['status'] == 'PASS' and len(panes['tests']) == 4 and all(t['pass'] for t in panes['tests'])})
    fixture = Path(panes['root']).resolve(strict=True)
    if fixture.parent != Path('/tmp').resolve() or not fixture.name.startswith('s3-pane-'):
        raise ValueError('The Panes fixture is not owned by this probe')
    with tarfile.open(EVIDENCE / 'outside-rebase-01-panes-fixtures.tar.gz', 'x:gz') as archive:
        archive.add(fixture, arcname=fixture.name)
    commands = []
    for argv in (['git', 'rev-parse', 'HEAD'],
                 ['git', 'diff', '--exit-code', HEAD, '--', 'workbench', 'acceptance', 'fixtures/pagination'],
                 ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        commands.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    archives = archive_large_outputs()
    for stage in stages:
        for archived in archives:
            if stage['path'] == archived['original']:
                stage.update(path=archived['archive'], repository_pointer=archived['pointer'])
    passed = (all(s['pass'] for s in stages) and all(c['exit'] == 0 for c in commands)
              and commands[0]['stdout'].strip() == HEAD)
    report = {'status': 'PASS' if passed else 'INCOMPLETE', 'scope': 'Rebased scripted acceptance only; real Codex and independent review remain pending',
              'candidate': HEAD, 'parent': '457e02a867bfdc5d8b06a9d14214eb7a429c48c2', 'stages': stages,
              'final_checks': commands, 'external_archives': archives, 'real_codex_turns': 0,
              'replay': ['bash', str(EVIDENCE / 'outside-sandbox.sh'), 'rebase-01']}
    with out.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'stages': len(stages), 'real_codex_turns': 0}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
