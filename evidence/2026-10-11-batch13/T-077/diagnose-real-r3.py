#!/usr/bin/env python3
"""Read the failed C2 receipt and stopped archive without changing the run."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tarfile

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'real-conflict-03/attempt-2'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
launch = json.loads((SOURCE / 'launch-record.json').read_text(encoding='utf-8'))
run = json.loads((SOURCE / 'run.json').read_text(encoding='utf-8'))
commands = [json.loads(line) for line in (SOURCE / 'commands.jsonl').read_text(encoding='utf-8').splitlines()]
show = next(row for row in commands if row.get('phase') == 'finished' and
            row['argv'][:4] == ['git', 'show', '-s', '--format=%B'])
message = Path(show['stdout_file']).read_bytes()
assert message.decode('utf-8') == show['stdout']
(args.output / 'C2-message.txt').write_bytes(message)
with closing(sqlite3.connect((SOURCE / 'databases-after-stop/state.sqlite3').resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
    db.row_factory = sqlite3.Row
    task = json.loads(db.execute('SELECT data FROM tasks').fetchone()[0])
    gate_events = [{**dict(r), 'details': json.loads(r['details'])} for r in db.execute(
        "SELECT seq,time,attempt,type,details FROM events WHERE type IN ('submitted','dispatched','conflict_rework_intent','conflict_worker_replaced','verified','integrated','trailer_check','completion_check') ORDER BY seq")]
    verifications = [json.loads(row['data']) for row in db.execute('SELECT data FROM verifications')]
events = json.loads((SOURCE / 'events-after-stop.json').read_text(encoding='utf-8'))
binding = task['current_attempt']
expected = {'A2A-Task': launch['task'], 'A2A-Attempt': launch['attempt'], 'A2A-Session': launch['session'],
    'A2A-Role': 'worker', 'A2A-Tool': 'codex-cli 0.162.1', 'A2A-Model': 'gpt-6.1-sol', 'A2A-Effort': 'xhigh',
    'A2A-Native-Session': binding['runtime_identity']['native_session'], 'A2A-Launch': launch['id']}
fields = [line for line in message.decode('utf-8').splitlines() if line.startswith('A2A-')]
actual = {}
for line in fields:
    key, value = line.split(': ', 1); actual.setdefault(key, []).append(value)
diff = {'missing': [key for key in expected if key not in actual],
        'extra': {key: value for key, value in actual.items() if key not in expected},
        'different': {key: {'expected': value, 'actual': actual[key]} for key, value in expected.items()
                      if key in actual and actual[key] != [value]}}
with tarfile.open(SOURCE / 'fixture-artifacts.tar.gz') as archive:
    members = [m for m in archive if m.isfile() and m.name.startswith('codex-home/sessions/') and m.name.endswith('.jsonl')]
    logs = []
    commit_calls = []
    old_preserved = False
    for member in members:
        raw = archive.extractfile(member).read()
        rows = [json.loads(line) for line in raw.splitlines()]
        meta = rows[0]['payload']
        logs.append({'member': member.name, 'native': meta['id'], 'cwd': meta['cwd'],
                     'root_turns': [r['payload']['turn_id'] for r in rows if r['type'] == 'event_msg' and r['payload'].get('type') == 'task_started']})
        if meta['cwd'].endswith('-a1'):
            old_preserved = raw == (BASE / 'real-conflict-03/attempt-1/original-rollout.jsonl').read_bytes()
        if meta['id'] != expected['A2A-Native-Session']:
            continue
        for row in rows:
            p = row['payload']
            if row['type'] == 'response_item' and p.get('type') == 'custom_tool_call' and 'A2A-Fence' in p.get('input', ''):
                commit_calls.append({'member': member.name, 'ordinal': row.get('ordinal'), 'timestamp': row.get('timestamp'),
                                     'turn': p.get('internal_chat_message_metadata_passthrough', {}).get('turn_id'), 'input': p['input']})
conflict = json.loads((SOURCE / 'conflict-reply.json').read_text(encoding='utf-8'))
selected = [e for e in events if e['type'] in ('native_session_ended', 'pane_archived', 'fixture_launch_approved', 'relay_processed', 'relay_rejected', 'turn_end_signal', 'pane_idle')]
timeline = [{'seq': e['seq'], 'time': e['time'], 'launch': e['launch'], 'type': e['type'],
             'key': e['data'].get('key'), 'ok': e['data'].get('result', {}).get('ok'), 'error': e['data'].get('result', {}).get('error')} for e in selected]
result = {'status': 'INCOMPLETE', 'scope': 'Retrospective diagnosis only; original failure retained',
    'product_revision': run['product_revision'], 'C2': task['candidate_commit'], 'show_command': show,
    'expected': expected, 'actual': actual, 'field_count': len(fields), 'field_diff': diff,
    'classification': 'worker supplied two unsupported trailer fields; no observed attempt/native identity mismatch',
    'worker_commit_calls': commit_calls, 'task_state': task['state'], 'current_attempt': binding,
    'conflict': {'verification': conflict['details']['verification_id'], 'state': conflict['details']['state'],
                 'G': conflict['details']['G'], 'C1': conflict['details']['C'], 'files': conflict['details']['conflict']['files']},
    'verification_rows': [{'id': v['verification_id'], 'C': v['C'], 'state': v['state']} for v in verifications],
    'gate_events': gate_events, 'timeline': timeline, 'archived_logs': logs,
    'old_rollout_bytes_preserved': old_preserved,
    'C2_verify_or_integrate_reached': any(e['type'] in ('verified','integrated') and e['attempt'] == binding['attempt_id'] for e in gate_events),
    'budget': {'r3_observed': run['observed_total_root_turns'], 'r3_limit': 4, 'new_turns_in_diagnosis': 0},
    'isolated_home_removed': run['isolated_home_removed'],
    'sources': [str(SOURCE / name) for name in ('run.json','commands.jsonl','conflict-reply.json','launch-record.json','events-after-stop.json','fixture-artifacts.tar.gz','databases-after-stop/state.sqlite3')]}
assert task['candidate_commit'] == show['argv'][-1]
assert diff['missing'] == [] and diff['different'] == {}
assert diff['extra'] == {'A2A-Fence': ['2'], 'A2A-Spec-Rev': ['1']}
assert len(commit_calls) == 1 and len(logs) == 2
with (args.output / 'diagnosis.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'status': 'INCOMPLETE', 'field_count': len(fields), 'field_diff': diff,
                  'task_state': task['state'], 'C2_verify_or_integrate_reached': result['C2_verify_or_integrate_reached'], 'new_real_turns': 0}, ensure_ascii=False))
