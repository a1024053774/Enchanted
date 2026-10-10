#!/usr/bin/env python3
"""Compare registered text to native user.text content; no screen oracle."""
import argparse
import collections
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'codex-02'
parser = argparse.ArgumentParser()
parser.add_argument('--label', default='')
args = parser.parse_args()
if args.label and not all(c.isalnum() or c in '-_' for c in args.label):
    raise SystemExit('Invalid output label')
suffix = '-' + args.label if args.label else ''
destination = BASE / ('r7-injections' + suffix + '.jsonl')
if destination.exists():
    raise SystemExit('Existing result retained; refuse overwrite')
registered = [json.loads(line) for line in (OUT / 'registrations.jsonl').read_text(encoding='utf-8').splitlines()]
messages = []
events = []
for file in (OUT / 'native-rollouts').glob('*.jsonl'):
    for number, line in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
        record = json.loads(line)
        payload = record.get('payload', {})
        if record['type'] == 'event_msg':
            events.append(payload)
        if record['type'] != 'response_item' or payload.get('role') != 'user':
            continue
        kinds = payload.get('internal_chat_message_metadata_passthrough', {}).get('content_item_kinds')
        if kinds != ['user.text']:
            continue
        text = ''.join(item['text'] for item in payload['content'] if item['type'] == 'input_text')
        messages.append(dict(text=text, source=str(file.relative_to(BASE)), line=number,
                             message_id=payload.get('id'), timestamp=record['timestamp']))
cutoff = json.loads((OUT / 'cutoff.json').read_text(encoding='utf-8'))
writes = [json.loads(line) for line in (OUT / 'writes.jsonl').read_text(encoding='utf-8').splitlines()]
ordering = all(any(write.get('id') == r['id'] and write['registered_text'] == r['registered_text']
                   and write['registered_at'] == r['registered_at']
                   and write['written_at'] >= r['registered_at']
                   for write in writes) for r in registered)
if not ordering:
    raise SystemExit('Missing write record or registration ordering mismatch')
results = []
for registration in registered:
    matches = [message for message in messages if message['text'] == registration['registered_text']]
    embedded = [message for message in messages if registration['registered_text'] in message['text']]
    if len(matches) == 1:
        outcome, observed, reason = 'ok', matches[0]['text'], 'One exact native user.text message'
    elif embedded:
        outcome, observed, reason = 'merged', embedded[0]['text'], 'Registered text is embedded in a larger native message'
    else:
        outcome, observed, reason = 'other', None, 'No matching native user.text by cutoff; lost versus draft versus other input interception is unknown'
    results.append(dict(**registration, observed_text=observed, outcome=outcome,
                        reason=reason, observed_sources=matches or embedded,
                        cutoff_at=cutoff['cutoff_at'], observation_seconds=cutoff['elapsed_seconds']))
with destination.open('x', encoding='utf-8') as stream:
    for result in results:
        stream.write(json.dumps(result, ensure_ascii=False) + '\n')
    stream.flush()
    os.fsync(stream.fileno())
counts = collections.Counter((r['cli'], r['state'], r['outcome']) for r in results)
summary = dict(status='BLOCKED', r7_counts=[dict(cli=k[0], state=k[1], outcome=k[2], count=v) for k, v in sorted(counts.items())],
               r7_count=len(results), required_codex_count=10,
               measured_states=sorted({r['state'] for r in results}),
               missing_states=sorted({'idle', 'running', 'awaiting_approval'} - {r['state'] for r in results}),
               native_primary_started_turns=sum(e['type'] == 'task_started' for e in events),
               native_primary_completed_turns=sum(e['type'] == 'task_complete' for e in events),
               usage_records=[e for e in events if e['type'] == 'token_count'],
               r6_actual_approval_triggered=False, claude_real_launches=0,
               registration_precedes_write=ordering)
(BASE / ('analysis' + suffix + '.json')).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
