#!/bin/zsh
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
OUT=$(mktemp -d "$ROOT/evidence/2026-10-23-batch23/T-152/outside-04-XXXXXXXX") || exit 2
REV=$(git rev-parse HEAD) || exit 2
TOTAL=0
python3 -B evidence/2026-10-23-batch23/T-152/run_suite.py --revision "$REV" --case tracer_review_copy --summary "$OUT/tracer.json" || TOTAL=1
python3 - "$OUT" "$REV" "$TOTAL" <<'PY'
import json
from pathlib import Path
import sys

out = Path(sys.argv[1])
record = {'status': 'INCOMPLETE', 'source_revision': sys.argv[2], 'case': 'tracer_review_copy',
          'real_model_turns': 0, 'checks': [], 'scope': 'one fresh controlled CLI/daemon/gate flow; no mutant/full-suite claim'}
def check(name, condition, proof):
    record['checks'].append({'name': name, 'passed': bool(condition), 'proof': proof})
def exactly(rows, description):
    if len(rows) != 1:
        raise RuntimeError(description + ': expected exactly one, got ' + str(len(rows)))
    return rows[0]
try:
    summary = json.loads((out / 'tracer.json').read_text(encoding='utf-8'))
    record.update(run_report=summary.get('run_report'), artifact_root=summary['artifact_root'], fixture_root=summary.get('fixture_root'))
    check('normal_tracer_passed', sys.argv[3] == '0' and summary['status'] == 'PASS', summary.get('cases'))
    run = Path(summary['run_report']).parent / 'tracer_review_copy'
    case = json.loads((run / 'case.json').read_text(encoding='utf-8'))
    tables = json.loads((run / 'database-readback.json').read_text(encoding='utf-8'))['tables']
    launches = [json.loads(row['data']) for row in tables['launch_records']]
    worker = exactly([row for row in launches if row['role'] == 'worker'], 'worker launch')
    native = json.loads((Path(case['fixture']) / 'control' / (worker['id'] + '.json')).read_text(encoding='utf-8'))
    orchestration = [{**row, 'data': json.loads(row['data'])} for row in tables['orchestration_events']]
    events = [{**row, 'details': json.loads(row['details'])} for row in tables['events']]
    queued = json.loads((run / 'requests' / worker['id'] / 'delivery-1.json').read_text(encoding='utf-8'))
    queue_command = exactly([cmd for cmd in case['commands'] if 'submit' in cmd['argv']], 'worker submit command')
    queue_reply = json.loads(Path(queue_command['stdout']).read_text(encoding='utf-8'))
    check('queued_file_bound_to_worker', queue_reply.get('ok') and queue_reply.get('queued')
          and not queue_reply.get('delivered') and queued['request_id'] == 'delivery-1'
          and queued['command'] == 'submit' and queued['task'] == worker['task']
          and queued['attempt'] == worker['attempt'] and queued['session'] == worker['session']
          and queued['fence'] == worker['fence'] and queued['spec_rev'] == worker['spec_rev'],
          {'captured_file': str(run / 'requests' / worker['id'] / 'delivery-1.json'), 'queue_reply': queue_reply})
    idle = [e for e in orchestration if e['type'] == 'pane_idle' and e['launch'] == worker['id']]
    first = exactly([e for e in idle if e['data'].get('stop', {}).get('turn_id') == 'fixture-turn-1'], 'worker matched Stop')
    check('matched_worker_stop', first['data']['stop']['session_id'] == native['native']
          and first['data']['stop']['cwd'] == worker['worktree']
          and first['data']['stop']['transcript_path'] == native['log'],
          {'seq': first['seq'], 'stop': first['data']['stop']})
    request = exactly([q for q in tables['relay_requests'] if q['launch'] == worker['id'] and q['request_id'] == 'delivery-1'], 'relay request')
    result_row = exactly([r for r in tables['relay_results'] if r['key'] == request['key']], 'relay result')
    result = json.loads(result_row['data'])
    check('relay_result_submitted_candidate', json.loads(request['input']) == queued and result.get('ok')
          and result['task']['state'] == 'submitted' and result['task']['candidate_commit'] == queued['commit'],
          {'key': request['key'], 'candidate': queued['commit'], 'result_state': result.get('task', {}).get('state')})
    gate_dispatch = exactly([json.loads(d['data']) for d in tables['dispatch_records']
                            if d['launch'] == worker['id'] and json.loads(d['data'])['source'] == 'gate'], 'source=gate feedback')
    submitted = exactly([e for e in orchestration if e['type'] == 'turn_submitted' and e['launch'] == worker['id']
                         and e['data']['dispatch'] == gate_dispatch['id']], 'feedback turn submission')
    check('one_gate_receipt_dispatch', 'delivery-1' in gate_dispatch['text'] and first['seq'] < submitted['seq'],
          {'dispatch': gate_dispatch['id'], 'turn_submitted_seq': submitted['seq']})
    ack = exactly([e for e in idle if e['data'].get('stop', {}).get('turn_id') == 'fixture-turn-2'], 'ACK unique pane_idle')
    check('ack_unique_matching_completion', ack['data']['submission'] == submitted['data']['id']
          and ack['data']['stop']['session_id'] == first['data']['stop']['session_id']
          and ack['data']['stop']['cwd'] == worker['worktree']
          and ack['data']['stop']['transcript_path'] == native['log'] and submitted['seq'] < ack['seq'],
          {'submission': ack['data']['submission'], 'idle_seq': ack['seq'], 'stop': ack['data']['stop']})
    reviewer = exactly([row for row in launches if row['role'] == 'reviewer'], 'reviewer launch')
    review_event = exactly([e for e in events if e['type'] == 'review_result'], 'review_result')
    review = review_event['details']['review']
    check('independent_review_result', review['candidate_commit'] == queued['commit'] and review['result']['verdict'] == '可合并'
          and review['thread_id'] == reviewer['thread'] and review['session_id'] != worker['session']
          and review['launch_id'] != worker['id'], {'review_id': review['review_id'], 'result_seq': review_event['seq']})
    reclaimed = exactly([e for e in events if e['type'] == 'review_reclaimed' and e['details']['review_id'] == review['review_id']], 'review_reclaimed')
    removed = exactly([e for e in events if e['type'] == 'review_candidate_copy_removed' and e['details']['review_id'] == review['review_id']], 'copy removed event')
    check('review_reclaimed_after_copy_cleanup', review_event['seq'] < removed['seq'] < reclaimed['seq'],
          {'result_seq': review_event['seq'], 'removed_seq': removed['seq'], 'reclaimed_seq': reclaimed['seq']})
    check('candidate_copy_physically_absent', not Path(review['candidate_workspace']).exists(), review['candidate_workspace'])
    record['status'] = 'PASS' if all(c['passed'] for c in record['checks']) else 'INCOMPLETE'
except Exception as error:
    record['error'] = repr(error)
with (out / 'SUMMARY.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': record['status'], 'summary': str(out / 'SUMMARY.json')}))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
if [[ $? -ne 0 ]]; then TOTAL=1; fi
exit "$TOTAL"
