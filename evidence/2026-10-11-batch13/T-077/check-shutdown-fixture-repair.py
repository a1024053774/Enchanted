#!/usr/bin/env python3
"""Bind the metadata-only repair and collect its three requested reruns."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077'
HEAD = '446f25c3de00925dfcc2f1c3f1375713676e166b'
BASE = '457e02a867bfdc5d8b06a9d14214eb7a429c48c2'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import audit_s3_assertions as audit


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2); handle.write('\n')


def binding():
    commands = []
    for argv in (['git', 'rev-parse', 'HEAD'],
                 ['git', 'diff', '--exit-code', HEAD, '--', 'workbench/src', 'workbench/hooks', 'workbench/README.md', 'acceptance', 'fixtures/pagination'],
                 ['git', 'diff', '--name-only', HEAD, '--', 'workbench/tests'],
                 ['git', 'diff', '--exit-code', HEAD, '--', 'workbench/tests/test_startup_shutdown_e2e.py', 'workbench/tests/test_multiturn_identity_e2e.py', 'workbench/tests/test_conflict_panes.ts']):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        commands.append({'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    scope = audit.audit_checkout(BASE)
    scope['self_check'] = audit.self_check()
    expected = {'workbench/tests/startup_shutdown_host.ts', 'workbench/tests/audit_s3_assertions.py'}
    proof = json.loads((EVIDENCE / 'rollout-cwd-proof-01.json').read_text(encoding='utf-8'))
    passed = (all(c['exit'] == 0 for c in commands) and commands[0]['stdout'].strip() == HEAD and
              set(commands[2]['stdout'].splitlines()) == expected and scope['status'] == 'PASS' and
              scope['self_check']['status'] == 'PASS' and proof['status'] == 'PASS' and all(proof['checks'].values()))
    return {'status': 'PASS' if passed else 'NO_GO', 'commands': commands, 'assertion_scope': scope,
            'proof': str(EVIDENCE / 'rollout-cwd-proof-01.json'), 'product_candidate': HEAD}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('prepare', 'collect'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != EVIDENCE or not out.name.startswith('outside-rebase-fix-'):
        raise ValueError('Output must be a fresh T-077 rebase-fix directory')
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External evidence volume is not mounted')
    if args.mode == 'prepare':
        out.mkdir(exist_ok=False)
        record = binding()
        record.update(real_codex_turns=0, business_checks='INCOMPLETE: three outside reruns pending', argv=sys.argv)
        save(out / 'preparation.json', record)
        names = ['workbench/tests/startup_shutdown_host.ts', 'workbench/tests/audit_s3_assertions.py',
                 'workbench/tests/test_startup_shutdown_e2e.py', 'workbench/tests/test_multiturn_identity_e2e.py',
                 'workbench/tests/test_conflict_panes.ts', 'evidence/2026-10-11-batch13/T-077/check-shutdown-fixture-repair.py']
        names += [str(p.relative_to(ROOT)) for p in (ROOT / 'workbench/src').rglob('*.ts')]
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            for name in names:
                archive.add(ROOT / name, arcname=name, recursive=False)
        patch = subprocess.run(['git', 'diff', HEAD, '--', 'workbench/tests/startup_shutdown_host.ts',
                                'workbench/tests/audit_s3_assertions.py'], cwd=ROOT, capture_output=True, check=True).stdout
        (out / 'fixture-repair.patch').write_bytes(patch)
        save(out / 'source-files.json', names)
    else:
        original = json.loads((out / 'preparation.json').read_text(encoding='utf-8'))
        record = binding()
        changed = []
        with tarfile.open(out / 'candidate-source.tar.gz', 'r:gz') as archive:
            for member in archive:
                with archive.extractfile(member) as saved:
                    if (ROOT / member.name).read_bytes() != saved.read():
                        changed.append(member.name)
        shutdown = json.loads((out / 'shutdown/run.json').read_text(encoding='utf-8'))
        identity = json.loads((out / 'identity/run.json').read_text(encoding='utf-8'))
        panes = json.loads((out / 'panes.json').read_text(encoding='utf-8'))
        results = [
            {'stage': 'shutdown', 'tests': 4, 'pass': shutdown['status'] == 'PASS' and shutdown['tests_run'] == 4 and
             not shutdown['failures'] and not shutdown['errors'] and not shutdown['skipped']},
            {'stage': 'identity', 'tests': 4, 'pass': (identity['status'], identity['tests_run'], identity['failures'], identity['errors'], identity['skipped']) == ('PASS', 4, 0, 0, 0)},
            {'stage': 'panes', 'tests': 4, 'pass': panes['status'] == 'PASS' and len(panes['tests']) == 4 and all(t['pass'] for t in panes['tests'])},
        ]
        fixture = Path(panes['root']).resolve(strict=True)
        if fixture.parent != Path('/tmp').resolve() or not fixture.name.startswith('s3-pane-'):
            raise ValueError('Panes fixture is not owned by this probe')
        with tarfile.open(out / 'panes-fixtures.tar.gz', 'x:gz') as archive:
            archive.add(fixture, arcname=fixture.name)
        status = record['status'] == original['status'] == 'PASS' and not changed and all(r['pass'] for r in results)
        record.update(status='PASS' if status else 'INCOMPLETE', scope='Shutdown metadata repair and identity/Panes reruns only',
                      stages=results, changed_source_files=changed, real_codex_turns=0, argv=sys.argv,
                      preserved_failure=str(EVIDENCE / 'outside-rebase-01-shutdown/run.json'))
        save(out / 'run.json', record)
    print(json.dumps({'status': record['status'], 'mode': args.mode, 'real_codex_turns': 0}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
