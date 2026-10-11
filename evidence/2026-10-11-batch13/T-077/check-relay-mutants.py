#!/usr/bin/env python3
"""Mutate isolated source copies; count assertion failures, never setup errors."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
original = (ROOT / 'workbench/src/relay.ts').read_text(encoding='utf-8')
lookup = 'this.store.db.prepare("SELECT * FROM relay_requests WHERE launch=? AND request_id=?").get(binding.id, requestId)'
mutations = [
    ('global-lookup', lookup, 'this.store.db.prepare("SELECT * FROM relay_requests WHERE request_id=?").get(requestId)',
     {'new_attempt_same_id_is_new_delivery', 'another_task_same_id_is_independent'}),
    ('duplicate-effect', 'this.store.event("relay_replayed", { key, file: file.name, result }, binding);',
     'if (row) { const { schema: _schema, request_id: _id, ...command } = input; await perform(command); }\n'
     '      this.store.event("relay_replayed", { key, file: file.name, result }, binding);',
     {'same_launch_duplicate_change_and_pending_are_fenced'}),
    ('forget-persisted-intent', lookup,
     'this.store.db.prepare("SELECT * FROM relay_requests WHERE key=?").get(`id:${binding.id}:${requestId}`)',
     {'legacy_result_and_pending_intent_remain_authoritative'}),
]
records = []
for name, before, after, expected in mutations:
    assert original.count(before) == 1, name
    source = Path(tempfile.mkdtemp(prefix='t077-relay-mutant-', dir='/tmp'))
    shutil.copytree(ROOT / 'workbench/src', source / 'src')
    shutil.copyfile(ROOT / 'workbench/package.json', source / 'package.json')
    (source / 'node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    (source / 'src/relay.ts').write_text(original.replace(before, after), encoding='utf-8')
    output = args.output / name
    argv = ['node', str(ROOT / 'workbench/tests/test_relay_scope.ts'), str(source / 'src/relay.ts'), str(output.resolve())]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=30)
    (output / 'console.txt').write_text(p.stdout + p.stderr, encoding='utf-8')
    result = json.loads((output / 'run.json').read_text(encoding='utf-8'))
    failed = {row['name'] for row in result['tests'] if not row['pass']}
    errors = [row for row in result['tests'] if row['failure'] and not row['failure']['assertion']]
    record = {'mutant': name, 'argv': argv, 'exit': p.returncode, 'source': str(source),
              'expected_failures': sorted(expected), 'actual_failures': sorted(failed),
              'errors': errors, 'detected': p.returncode == 1 and expected <= failed and not errors}
    records.append(record)
    with tarfile.open(output / 'source.tar.gz', 'x:gz') as archive:
        archive.add(source / 'src', arcname='src')
        archive.add(source / 'package.json', arcname='package.json')
        archive.add(ROOT / 'workbench/tests/test_relay_scope.ts', arcname='test_relay_scope.ts')
report = {'status': 'PASS' if all(row['detected'] for row in records) else 'INCOMPLETE',
          'scope': 'Boundary mutants only; no native process, socket or provider', 'real_codex_turns': 0, 'mutants': records}
(args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
