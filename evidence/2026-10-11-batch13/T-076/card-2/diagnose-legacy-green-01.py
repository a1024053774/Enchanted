"""Read saved evidence only; do not repeat the failed backend run."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
card = Path(__file__).resolve().parent
source = card / 'outside-legacy-green-01'
if args.output.exists(): raise RuntimeError('Choose a new evidence path.')
overall = json.loads((source / 'run.json').read_text(encoding='utf-8'))
w07 = json.loads((source / 'w07-red/run.json').read_text(encoding='utf-8'))
snapshots = json.loads((source / 'w07-red/state-readback.json').read_text(encoding='utf-8'))
if len(snapshots) != 1: raise RuntimeError('Expected the one W07 fixture readback.')
tables = snapshots[0]['tables']
task = json.loads(tables['tasks'][0]['data'])
events = [{**row, 'details': json.loads(row['details'])} for row in tables['events']]
failures = [row for row in events if row['type'] == 'review_lifecycle_failed']
issues = [row for row in events if row['type'] == 'issue_issue']
verify_rejections = [row for row in events if row['type'] == 'rejected' and row['details'].get('input', {}).get('command') == 'verify']
f10 = json.loads((source / 'f10-red/run.json').read_text(encoding='utf-8'))['cases'][0]
expected = task['card']['executor'] == {'cli': 'Codex', 'model': 'fixture', 'effort': 'xhigh'}
expected = expected and task['state'] == 'paused' and task['review']['state'] == 'unknown' and task['verification']['state'] == 'passed'
expected = expected and len(failures) == len(issues) == len(verify_rejections) == 1
expected = expected and failures[0]['details']['phase'] == 'create' and issues[0]['details']['blocking'] is True
expected = expected and verify_rejections[0]['details']['error'] == 'gate_failure'
expected = expected and verify_rejections[0]['details']['details'] == 'Error: worker_executor_mismatch'
expected = expected and f10['outcome'] == 'contract_failure' and f10['failure_id'] == 'MANUAL-CLAIM-SOURCE'
expected = expected and [row['name'] for row in overall['steps']] == ['f10-red', 'w07-red']
record = {'status': 'PASS' if expected else 'INCOMPLETE', 'product_status': 'INCOMPLETE',
          'scope': 'saved failure classification only; no new dynamic run', 'real_codex_turns': 0,
          'source': str(source), 'task_id': task['task_id'], 'attempt_id': task['current_attempt']['attempt_id'],
          'candidate': task['candidate_commit'], 'executor': task['card']['executor'],
          'task_state': task['state'], 'review_state': task['review']['state'], 'verification_state': task['verification']['state'],
          'lifecycle_failures': failures, 'issues': issues, 'verify_rejections': verify_rejections,
          'w07_result': {key: w07[key] for key in ('status', 'tests_run', 'failures', 'errors', 'exit_code')},
          'f10_result': {key: f10[key] for key in ('case', 'outcome', 'failure_id', 'cleanup_failures')},
          'outer_exit': {'controller_reported': 0, 'raw_exit_receipt_in_card': None,
                         'scope': 'child exit codes and report status are preserved; the top-level shell exit cannot be independently verified here'},
          'classification': 'fixture executor precondition; existing reviewer creation-failure contract was satisfied',
          'pending': ['F14 approval before changing fixture model', 'W07 intended red and remaining legacy checks']}
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({key: record[key] for key in ('status', 'product_status', 'classification')}))
raise SystemExit(0 if expected else 1)
