#!/usr/bin/env python3
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[3]
EXPECTED = '8933ee0f4e4667a6f927e18975fe2cb8cc58729b'
EVIDENCE = Path(__file__).resolve().parent


def main():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if revision != EXPECTED:
        raise RuntimeError('Source revision changed; do not run the baseline against another revision.')
    out = Path(tempfile.mkdtemp(prefix='outside-01-', dir=EVIDENCE))
    scratch = Path(tempfile.mkdtemp(prefix='t156-baseline-', dir='/private/tmp'))
    record = {'status': 'INCOMPLETE', 'task': 'T-156-1', 'attempt': 'a1',
              'source_revision': revision, 'source': str(ROOT), 'raw_artifact_root': str(scratch),
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
              'python_version': sys.version, 'real_model_turns': 0, 'runs': []}
    env = {**os.environ, 'A2A_TEST_ARTIFACT_PARENT': '/private/tmp', 'PYTHONDONTWRITEBYTECODE': '1'}
    entries = [
        ('legacy-runner', 'run_t082_boundary.py', ['--source', str(ROOT)], 'run.json'),
        ('quality-bootstrap', 'test_t078_quality_host_bootstrap.py', [], 'results.json'),
    ]
    for label, name, options, report_name in entries:
        target = scratch / label
        argv = [sys.executable, '-B', str(ROOT / 'workbench/tests' / name),
                *options, '--output', str(target)]
        row = {'name': label, 'command': argv, 'output': str(target)}
        with (scratch / (label + '.stdout.txt')).open('xb') as stdout, (scratch / (label + '.stderr.txt')).open('xb') as stderr:
            try:
                result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=600)
                row['exit_code'] = result.returncode
            except subprocess.TimeoutExpired as error:
                row['timeout'] = str(error)
        report_path = target / report_name
        row['report_path'] = str(report_path)
        if report_path.exists():
            row['report'] = json.loads(report_path.read_text(encoding='utf-8'))
        else:
            row['report_missing'] = True
        row['stdout'] = (scratch / (label + '.stdout.txt')).read_text(encoding='utf-8', errors='replace')
        row['stderr'] = (scratch / (label + '.stderr.txt')).read_text(encoding='utf-8', errors='replace')
        record['runs'].append(row)
    record['ending_revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['status'] = ('PASS' if record['ending_revision'] == EXPECTED
                        and all('exit_code' in row for row in record['runs']) else 'INCOMPLETE')
    record['status_scope'] = 'Both baseline commands executed and their outcomes were captured; this is not a product or test pass.'
    record['archive_pending'] = 'Controller archives raw_artifact_root and any fixture roots under T-088; do not remove anomalous evidence.'
    with (out / 'SUMMARY.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': record['status'], 'summary': str(out / 'SUMMARY.json'),
                      'raw_artifact_root': str(scratch)}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
