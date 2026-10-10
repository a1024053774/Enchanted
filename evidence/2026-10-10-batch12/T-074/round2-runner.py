#!/usr/bin/env python3
"""Controller-decided real PTY experiments, with a bounded native-record oracle."""
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('probe', BASE / 'probe.py')
probe = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(probe)

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def append(path, record):
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())

def wait_state(label, state, deadline=60):
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        status = probe.control(label, {'op': 'status'})
        if status['state'] == state:
            return status
        time.sleep(0.25)
    raise SystemExit('State not reached in bounded observation: ' + state)

def user_messages(label):
    path = BASE / label / 'native-events.jsonl'
    if not path.exists():
        return []
    messages = []
    for line in path.read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        record = entry['record']
        payload = record.get('payload', {})
        if record['type'] != 'response_item' or payload.get('role') != 'user':
            continue
        metadata = payload.get('internal_chat_message_metadata_passthrough', {})
        if metadata.get('content_item_kinds') != ['user.text']:
            continue
        text = ''.join(item['text'] for item in payload['content'] if item['type'] == 'input_text')
        messages.append(dict(text=text, source=label + '/' + entry['file'], line=entry['line'],
                             message_id=payload.get('id'), timestamp=record['timestamp'],
                             received_at=entry['received_at']))
    return messages

def inject(label, method, state, text, experiment, marker_file=None):
    wait_state(label, state)
    request = dict(op='inject', method=method, state=state, text=text, experiment=experiment,
                   marker_file=marker_file)
    registration = probe.control(label, request)
    if 'error' in registration:
        raise SystemExit(json.dumps(registration))
    start = time.monotonic()
    deadline = start + 60
    exact, embedded = [], []
    while time.monotonic() < deadline:
        exact = [m for m in user_messages(label) if m['text'] == text]
        embedded = [m for m in user_messages(label) if text in m['text']]
        if exact or embedded:
            break
        time.sleep(0.25)
    observed = (exact or embedded)[0]['text'] if exact or embedded else None
    outcome = 'ok' if len(exact) == 1 else 'merged' if embedded else 'other'
    marker = Path(marker_file) if marker_file else None
    marker_observation = dict(path=marker_file, exists=marker.exists(), text=marker.read_text(encoding='utf-8') if marker.exists() else None) if marker else None
    if state == 'awaiting_approval' and not exact and marker_observation and marker_observation['exists']:
        outcome = 'taken_as_approval'
    result = dict(**registration, label=label, observed_text=observed, outcome=outcome,
                  observed_sources=exact or embedded, cutoff_at=stamp(),
                  observation_seconds=time.monotonic() - start, marker_observation=marker_observation,
                  outcome_reason='Exact native user.text' if exact else 'Embedded native user.text' if embedded else 'No native user.text before 60s; approval effect tracked separately')
    append(BASE / label / 'observations.jsonl', result)
    append(BASE / 'r7-injections.jsonl', result)
    print(json.dumps(dict(label=label, method=method, state=state, outcome=outcome,
                          seconds=result['observation_seconds']), ensure_ascii=False), flush=True)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['wait', 'inject'])
    parser.add_argument('label')
    parser.add_argument('--state', default='idle')
    parser.add_argument('--method')
    parser.add_argument('--text')
    parser.add_argument('--experiment', default='pilot')
    parser.add_argument('--marker-file')
    args = parser.parse_args()
    if args.operation == 'wait':
        print(json.dumps(wait_state(args.label, args.state), ensure_ascii=False))
    else:
        inject(args.label, args.method, args.state, args.text, args.experiment, args.marker_file)
