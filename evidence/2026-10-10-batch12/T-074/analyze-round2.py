#!/usr/bin/env python3
"""Verify the controller's protocol against archived native records, read-only."""
import collections
import datetime as dt
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
labels = ['codex-01', 'codex-02', 'round2-M1-pilot', 'round2-M2-pilot', 'round2-M3-pilot']

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

def native_messages(label):
    result = []
    for file in (BASE / label / 'native-rollouts').glob('*.jsonl'):
        for number, record in enumerate(rows(file), 1):
            payload = record.get('payload', {})
            if record['type'] != 'response_item' or payload.get('role') != 'user':
                continue
            metadata = payload.get('internal_chat_message_metadata_passthrough', {})
            if 'user.text' not in metadata.get('content_item_kinds', []):
                continue
            text = ''.join(item['text'] for item in payload['content'] if item['type'] == 'input_text')
            result.append(dict(text=text, file=str(file.relative_to(BASE)), line=number))
    return result

injections = rows(BASE / 'r7-injections.jsonl')
injections = [r for r in injections if r.get('label','codex-02') in labels]
verification = []
for row in injections:
    label = row.get('label', 'codex-02')
    messages = native_messages(label)
    exact = [m for m in messages if m['text'] == row['registered_text']]
    if row['outcome'] == 'ok':
        assert len(exact) == 1 and row['observed_text'] == exact[0]['text'], (label, row['id'])
    elif row['outcome'] in ('other', 'taken_as_approval'):
        assert not exact and row['observed_text'] is None, (label, row['id'])
    else:
        raise AssertionError('Unexpected observed outcome; inspect raw evidence')
    writes = [w for w in rows(BASE / label / 'writes.jsonl') if w.get('id') == row['id']]
    actual = [w['bytes'] for w in writes]
    text = row['registered_text']
    method = row['method']
    expected = [text + '\r'] if method == 'M1' else [text, '\r'] if method == 'M2' else ['\x1b[200~' + text + '\x1b[201~', '\r']
    assert actual == expected, (label, row['id'], 'controller protocol bytes')
    assert writes[0]['written_at'] >= row['registered_at']
    delay = None
    if method in ('M2', 'M3'):
        times = [dt.datetime.fromisoformat(w['written_at'].replace('Z', '+00:00')) for w in writes]
        delay = (times[1] - times[0]).total_seconds()
        assert delay >= 0.300, (label, row['id'], delay)
    verification.append(dict(label=label, id=row['id'], method=method, state=row['state'],
                             outcome=row['outcome'], archived_matches=exact, write_delay_seconds=delay))

counts = collections.Counter((r['cli'], r['method'], r['state'], r['outcome']) for r in injections)
primary = {}
auxiliary = []
last_usage = {}
for label in labels:
    events = [record for file in (BASE / label / 'native-rollouts').glob('*.jsonl') for record in rows(file)]
    started = [r['payload']['turn_id'] for r in events if r['type']=='event_msg' and r['payload']['type']=='task_started']
    completed = [r['payload']['turn_id'] for r in events if r['type']=='event_msg' and r['payload']['type']=='task_complete']
    primary[label] = dict(started=len(started), completed=len(completed), turn_ids=started)
    notify = BASE / label / 'notify.jsonl'
    if notify.exists():
        auxiliary.extend(dict(label=label, payload=n['payload'], received_at=n['received_at']) for n in rows(notify) if n['payload']['turn-id'] not in started)
    usage = [r['payload']['info']['total_token_usage'] for r in events if r['type']=='event_msg' and r['payload']['type']=='token_count']
    last_usage[label] = usage[-1] if usage else None
assert sum(r['started'] for r in primary.values()) <= 30
snapshots = rows(BASE / 'round2-M3-pilot/r6-snapshots.jsonl')
before, after = snapshots
assert before['marker_exists'] is False and after['marker_exists'] is True
danger = [r for r in injections if r['outcome']=='taken_as_approval']
assert len(danger)==1 and danger[0]['marker_observation']['text']==after['marker_text']
summary = dict(status='BLOCKED', reason='Codex fact collection complete; Claude authentication and real probes pending; PTY approval injection requires a design decision',
               r7_count=len(injections),
               counts=[dict(cli=k[0], method=k[1], state=k[2], outcome=k[3], count=v) for k,v in sorted(counts.items())],
               pilot_counts=collections.Counter(r['method'] for r in injections if r.get('experiment','pilot')=='pilot'),
               selected_method='M3', selected_post_pilot_count=sum(r['method']=='M3' and r.get('experiment')!='pilot' for r in injections),
               selected_states=sorted({r['state'] for r in injections if r['method']=='M3'}),
               primary_turns=primary, primary_started_total=sum(r['started'] for r in primary.values()), primary_turn_cap=30,
               auxiliary_turns=auxiliary, usage_by_native_thread=last_usage,
               r6=dict(osc9=before['osc9'], marker_before=False, marker_after=True, marker_text=after['marker_text'],
                       before_capture=before['captured_at'], after_capture=after['captured_at'],
                       notify_types_before=dict(collections.Counter(n['payload']['type'] for n in before['notify'])),
                       notify_types_after=dict(collections.Counter(n['payload']['type'] for n in after['notify']))),
               verification=verification, claude_real_launches=0)
destination=BASE/'analysis-round2.json'
if destination.exists():
    old=json.loads(destination.read_text(encoding='utf-8'))
    assert old==summary, 'Evidence differs; preserve the original and inspect'
else:
    destination.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k,v in sorted(counts.items()):
    print(*k,v)
print('main turns',summary['primary_started_total'],'cap',30,'auxiliary completions',len(auxiliary))
print('M3 after pilot',summary['selected_post_pilot_count'],summary['selected_states'])
