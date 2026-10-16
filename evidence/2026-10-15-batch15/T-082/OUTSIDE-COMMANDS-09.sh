#!/usr/bin/env bash
# Controlled product-path replay of the recorded report. No real Codex.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [[ -e "$SCRIPT_DIR/outside-command-09-$(printf '%02d' "$sequence")" ]]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-09-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ROOT" "$OUTPUT" <<'PY'
import json, os, shutil, subprocess, sys, tarfile
from pathlib import Path

root, out = map(Path, sys.argv[1:])
steps = []
env = {key: value for key, value in os.environ.items()
       if not key.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_', 'ELECTRON_'))}
env['PYTHONDONTWRITEBYTECODE'] = '1'
plan = [
    ('report-roundtrip', 'test_t082_review_boundary_e2e.py', ['--case', 'real_payload_report_roundtrip']),
    ('t076-properties', 'test_quality_tracer_e2e.py', ['--case', 'tracer_wrong_candidate', '--case',
         'tracer_reused_native', '--case', 'tracer_writer_cannot_review', '--case', 'tracer_malformed_review']),
    ('t077-review-lifecycle', 'test_review_worktree_lifecycle_e2e.py', []),
]
for name, script, options in plan:
    target = out / name
    argv = [sys.executable, '-B', str(root / 'workbench/tests' / script), '--source', str(root),
            '--output', str(target), *options]
    row = {'name': name, 'argv': argv, 'cwd': str(root), 'status': 'INCOMPLETE'}
    steps.append(row)
    with (out / (name + '.stdout.txt')).open('xb') as stdout, (out / (name + '.stderr.txt')).open('xb') as stderr:
        try:
            result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=600)
            row['exit_code'] = result.returncode
        except subprocess.TimeoutExpired:
            row['error'] = 'suite timeout; preserve fixture for controller'
    report_path = target / 'run.json'
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding='utf-8'))
        row['report'] = str(report_path)
        row['status'] = 'PASS' if row.get('exit_code') == 0 and report['status'] == 'PASS' else 'INCOMPLETE'
        # Archive only the exact fixture root owned by this child's receipt.
        artifact = Path(report['artifact_root']).resolve()
        if artifact.parent != Path('/private/tmp') or not artifact.name.startswith('q76-'):
            raise RuntimeError('Unexpected artifact ownership: ' + str(artifact))
        if any(case.get('cleanup_failures') for case in report['cases']):
            row['fixture_preserved'] = str(artifact)
        else:
            archive = out / (name + '.fixtures.tar.gz')
            with tarfile.open(archive, 'x:gz') as stream:
                stream.add(artifact, arcname=artifact.name)
            row['fixture_archive'] = str(archive)
            shutil.rmtree(artifact)
status = 'PASS' if all(row['status'] == 'PASS' for row in steps) else 'INCOMPLETE'
(out / 'run.json').write_text(json.dumps({'status': status, 'steps': steps, 'real_codex_turns': 0},
                                       ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': status, 'real_codex_turns': 0}))
raise SystemExit(0 if status == 'PASS' else 1)
PY
exit_code=$?
printf 'output=%s\nexit_code=%s\n' "$OUTPUT" "$exit_code"
exit "$exit_code"
