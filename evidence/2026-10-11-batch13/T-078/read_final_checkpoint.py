#!/usr/bin/env python3
"""Read final receipts and archived originals without importing product code."""
import argparse
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
base = Path('/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078')
root = base / 'outside-final-01'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
checkpoint = read(root / 'checkpoint.json')
archive = read(base / 'external-archive-26fbebf6628b47c99f307a1fd2f480f1.json')
archived = {row['source']: row for row in archive['files']}
checks = []


def check(name, passed, **details):
    checks.append({'name': name, 'pass': bool(passed), **details})


check('candidate', checkpoint['head'] == 'b3fb998cf48574821c39440ece3f9ff897f26cf9' and checkpoint['checkpoint_status'] == 'PASS')
for name, count in [('domain', 11), ('inbox-entry', 8), ('pane-state', 11), ('controller-plan', 2),
                    ('runtime-entry', 12), ('input-entry', 11), ('worker-inbox', 14)]:
    data = read(root / name / 'results.json')
    check(name, data['status'] == 'PASS' and len(data['checks']) == count and all(row['status'] == 'PASS' for row in data['checks'])
          and not data.get('setup_or_probe_error') and not data.get('cleanup_error') and not data.get('error'), count=len(data['checks']))
for name, count in [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1)]:
    original = root / name / 'run.json'
    location = Path(archived[str(original)]['archive']) if str(original) in archived else original
    data = read(location)
    check(name, data['status'] == 'PASS' and data['tests_run'] == count and data['exit_code'] == 0
          and all(data[key] == 0 for key in ['failures', 'errors', 'skipped']) and data['changed_source_paths'] == [],
          tests=data['tests_run'], source=str(location))
for name in ['assign', 'ready', 'foreign-ack', 'revoked']:
    data = read(root / ('worker-rule-' + name) / 'results.json')
    verdict = read(root / 'worker-rule-verdicts.json')[name]
    failed = [row['name'] for row in data['checks'] if row['status'] != 'PASS']
    entries = [json.loads(row['data']) for row in read(root / ('worker-rule-' + name) / 'readback-inbox_records.json')]
    stored = verdict['stored_forbidden_entry']
    persisted = stored in entries if stored else name == 'ready' and verdict['gate_response'].get('ok') is True and [row['id'] for row in verdict['gate_response']['ready']] == ['W-READY']
    check('worker-rule-' + name, len(data['checks']) == 14 and failed == [verdict['contract']] and verdict['pass']
          and verdict['mutated_backend_loaded'] and verdict['forbidden_outcome_observed'] and persisted
          and data['setup_complete'] and data['cleanup_complete'] and not data.get('setup_or_probe_error') and not data.get('cleanup_error'), failed=failed)
for name in ['fence', 'cas', 'lock']:
    data = read(root / ('mutant-' + name) / 'run.json')
    verdict = checkpoint['counterexamples'][name]
    check('mutant-' + name, data['exit_code'] == 1 and data['tests_run'] == 1 and data['failures'] > 0
          and data['errors'] == 0 and data['skipped'] == 0 and data['changed_source_paths'] == []
          and verdict['pass'] and verdict['classification'] == 'business-counterfactual'
          and verdict['loaded_core'] and verdict['business_evidence'], failures=data['failures'], errors=data['errors'])
for row in archive['files']:
    check('archive:' + row['source'], not Path(row['source']).exists() and Path(row['archive']).stat().st_size == row['bytes']
          and row['byte_readback'] == 'PASS' and row['local_original_removed'], archive=row['archive'], bytes=row['bytes'])
check('no_large_local_files', not [path for path in base.rglob('*') if path.is_file() and path.stat().st_size > 5 * 1024 * 1024])
check('no_model_execution_claim', checkpoint['real_model_turns'] == 0 and not checkpoint['claude_started'] and not checkpoint['claude_fixture_started'])
result = {'status': 'PASS' if all(row['pass'] for row in checks) else 'INCOMPLETE', 'argv': sys.argv,
          'candidate': checkpoint['head'], 'checks': checks, 'independent_review': False,
          'scope': 'Worker readback of raw group results, archived originals and persisted worker-rule outcomes; not a new runtime test or reviewer verdict.'}
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps({'status': result['status'], 'checks': len(checks), 'failed': [row['name'] for row in checks if not row['pass']]}))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
