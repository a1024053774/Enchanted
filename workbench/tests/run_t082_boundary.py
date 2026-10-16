"""Run the T-082 controlled tracer and four launch-policy mutants.

No provider or Codex model is started. Each child uses the real daemon/CLI,
Git, SQLite, and controlled PTY host; the four mutants alter only reviewer
launch facts and must be refused by the gate.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = Path('/private/tmp') if Path('/private/tmp').is_dir() else Path('/tmp').resolve()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def materialize(source, target, before, after):
    shutil.copytree(source / 'workbench', target / 'workbench', symlinks=True,
                    ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
    (target / 'workbench/node_modules').symlink_to((source / 'workbench/node_modules').resolve(), target_is_directory=True)
    path = target / 'workbench/src/panes.ts'
    text = path.read_text(encoding='utf-8')
    if text.count(before) != 1:
        raise RuntimeError(f'mutation target is not unique: {before}')
    path.write_text(text.replace(before, after), encoding='utf-8')


def run_case(source, output, case, output_name=None):
    target = output / (output_name or case)
    argv = [sys.executable, '-B', source / 'workbench/tests/test_t082_review_boundary_e2e.py',
            '--source', source, '--output', target, '--case', case]
    result = subprocess.run(list(map(str, argv)), cwd=source, env=os.environ.copy(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=300)
    report = json.loads((target / 'run.json').read_text(encoding='utf-8')) if (target / 'run.json').exists() else None
    return {'argv': list(map(str, argv)), 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr,
            'report': report, 'report_path': str(target / 'run.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(); output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'real_codex_turns': 0,
              'source': str(source), 'output': str(output), 'steps': [],
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    fixture_root = Path(tempfile.mkdtemp(prefix='t082-boundary-',
                        dir=os.environ.get('A2A_TEST_ARTIFACT_PARENT', '/Volumes/WD-Elements'))).resolve()
    fixture_parent = Path(os.environ.get('A2A_TEST_ARTIFACT_PARENT', str(TMP_ROOT))).resolve()
    cleanup_confirmed = False
    try:
        green = run_case(source, output, 'tracer_review_copy')
        result['steps'].append({'name': 'green-tracer', **green})
        failures = []
        if green['returncode'] != 0 or not green['report'] or green['report'].get('status') != 'PASS':
            failures.append('green-tracer')
        mutations = [
            ('readonly-argv',
             'const sandboxMode = "workspace-write";',
             'const sandboxMode = review ? "read-only" : "workspace-write";'),
            ('wrong-workspace',
             'const launchWorkspace = review ? review.candidate_workspace : attempt.workspace;',
             'const launchWorkspace = review ? review.workspace : attempt.workspace;'),
            ('network-enabled',
             'const networkAccess = "false";',
             'const networkAccess = review ? "true" : "false";'),
            ('tmp-writable',
             'const excludeSlashTmp = review ? "true" : "false";',
             'const excludeSlashTmp = review ? "false" : "false"'),
        ]
        for name, before, after in mutations:
            variant = fixture_root / name
            materialize(source, variant, before, after)
            row = run_case(variant, output, 'launch_boundary_refused', 'launch-boundary-refused-' + name)
            result['steps'].append({'name': name, 'mutation': {'before': before, 'after': after}, **row})
            if row['returncode'] != 0 or not row['report'] or row['report'].get('status') != 'PASS':
                failures.append(name)
        result['failures'] = failures
        result['status'] = result['product_status'] = 'PASS' if not failures else 'INCOMPLETE'
        cleanup_confirmed = True
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        result['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        owned = []
        for index, step in enumerate(result['steps']):
            report = step.get('report')
            if not report or any(case.get('cleanup_failures') for case in report['cases']):
                cleanup_confirmed = False
                continue
            artifact = Path(report['artifact_root']).resolve()
            try:
                if artifact.parent != fixture_parent or not artifact.name.startswith('q76-'):
                    raise RuntimeError('Unexpected child fixture ownership: ' + str(artifact))
                owned.append(artifact)
                archive = output / ('owned-fixture-%d.tar.gz' % index)
                with tarfile.open(archive, 'x:gz') as stream:
                    stream.add(artifact, arcname=artifact.name)
                step['fixture_archive'] = str(archive)
                shutil.rmtree(artifact)
            except Exception as error:
                cleanup_confirmed = False
                result.update(status='INCOMPLETE', product_status='INCOMPLETE', cleanup_error=repr(error))
        result['q76_created'] = list(map(str, owned))
        result['q76_remaining'] = [str(path) for path in owned if path.exists()]
        if cleanup_confirmed:
            try:
                shutil.rmtree(fixture_root)
            except Exception as error:
                result.update(status='INCOMPLETE', product_status='INCOMPLETE', cleanup_error=repr(error))
        result.update(mutation_fixture_root=str(fixture_root), mutation_fixture_removed=not fixture_root.exists())
        save(output / 'run.json', result)
        print(json.dumps({'status': result['status'], 'product_status': result['product_status'],
                          'real_codex_turns': result['real_codex_turns']}), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
