#!/usr/bin/env python3
"""Check registered inputs against archived native records. Do not call a model."""
import collections
import datetime as dt
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def instant(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def native(directory, cli):
    if cli == 'claude':
        return rows(directory / 'native-transcript-final.jsonl')
    return [r for f in (directory / 'native-rollouts').glob('*.jsonl') for r in rows(f)]


def texts(records, cli):
    result = []
    for r in records:
        if cli == 'codex':
            p = r.get('payload', {})
            kinds = p.get('internal_chat_message_metadata_passthrough', {}).get('content_item_kinds', [])
            if r['type'] == 'response_item' and p.get('role') == 'user' and 'user.text' in kinds:
                result.append(''.join(c['text'] for c in p['content'] if c['type'] == 'input_text'))
        elif r.get('type') == 'user' and not r.get('isMeta'):
            c = r['message']['content']
            if isinstance(c, str):
                result.append(c)
            elif not any(x['type'] == 'tool_result' for x in c):
                result.append(''.join(x['text'] for x in c if x['type'] == 'text'))
    return result


all_injections = rows(BASE / 'r7-injections.jsonl')
injections = [r for r in all_injections if r.get('ready_rev') == 3]
assert len({(r['label'], r['id']) for r in injections}) == len(injections)
sessions = []
races = []
for label in sorted({r['label'] for r in injections}):
    directory = BASE / label
    manifest = json.loads((directory / 'launch.json').read_text())
    cli = manifest['cli']
    records = native(directory, cli)
    actual = texts(records, cli)
    hooks = rows(directory / 'turn-hooks.jsonl')
    group = [r for r in injections if r['label'] == label]
    writes = rows(directory / 'writes.jsonl')
    registrations = rows(directory / 'registrations.jsonl')
    for r in group:
        registered = [x for x in registrations if x['id'] == r['id']]
        assert len(registered) == 1 and registered[0]['registered_text'] == r['registered_text']
        parts = [x for x in writes if x.get('id') == r['id']]
        if not r['written']:
            assert parts == [] and r['registered_text'] not in actual
            assert r['outcome'] == 'other' and r['observed_text'] is None
            continue
        assert [p['part'] for p in parts] == [1, 2]
        assert instant(r['registered_at']) <= instant(parts[0]['written_at'])
        assert parts[0]['bytes'] == '\x1b[200~' + r['registered_text'] + '\x1b[201~'
        assert parts[1]['bytes'] == '\r'
        assert (instant(parts[1]['written_at']) - instant(parts[0]['written_at'])).total_seconds() >= .3
        assert r['observed_text'] == r['registered_text']
        if r['state'] == 'running':
            attachments = [x for x in records if x.get('type') == 'attachment'
                           and x.get('attachment', {}).get('type') == 'queued_command'
                           and x['attachment'].get('prompt') == r['registered_text']]
            assert len(attachments) == 1 and r['registered_text'] not in actual
            assert r['outcome'] == 'other' and r['native_record_type'] == 'attachment.queued_command'
        else:
            assert actual.count(r['registered_text']) == 1 and r['outcome'] == 'ok'
        if r['state'] == 'idle_gated':
            assert r['gate_last_event']['payload']['hook_event_name'] == 'Stop'
            assert r['gate_last_event'] in hooks

    if cli == 'codex':
        session_id = next(x['payload']['id'] for x in records if x['type'] == 'session_meta' and x['payload']['source'] == 'cli')
        turns = [x['payload'] for x in records if x['type'] == 'event_msg' and x['payload']['type'] == 'task_started']
        turn_ids = {x['turn_id'] for x in turns}
        model = sorted({x['payload']['model'] for x in records if x['type'] == 'turn_context'})
        usage = [x['payload']['info']['total_token_usage'] for x in records if x['type'] == 'event_msg' and x['payload']['type'] == 'token_count']
        usage = usage[-1] if usage else None
        assert model == ['gpt-6-astra']
        assert '-c' in manifest['cli_argv'] and 'service_tier="fast"' in manifest['cli_argv']
        assert json.loads((directory / 'cleanup.json').read_text())['entire_created_root_removed']
    else:
        session_id = manifest['native_session']
        turn_ids = {x['promptId'] for x in records if x.get('type') == 'user' and x.get('promptId')}
        responses = {x['message']['id']: x['message'] for x in records if x.get('type') == 'assistant'}
        model = sorted({x['model'] for x in responses.values()})
        usage = [dict(id=k, model=v['model'], usage=v.get('usage')) for k, v in responses.items()]
        assert model == ['claude-haiku-5-5']
        assert json.loads((directory / 'archive-final.json').read_text())['owned_processes_present'] == []
    assert all(x['payload']['session_id'] == session_id for x in hooks)
    identity = 'turn_id' if cli == 'codex' else 'prompt_id'
    starts = [x for x in hooks if x['payload']['hook_event_name'] == 'UserPromptSubmit']
    stops = [x for x in hooks if x['payload']['hook_event_name'] == 'Stop']
    starts_by_id = collections.Counter(x['payload'][identity] for x in starts)
    stopped_ids = {x['payload'][identity] for x in stops}
    assert set(starts_by_id).issubset(turn_ids)
    prompt_id_comparisons = []
    if cli == 'claude':
        for start in starts:
            matching = [x for x in records if x.get('type') == 'user'
                        and x.get('message', {}).get('content') == start['payload']['prompt']]
            if matching:
                assert len(matching) == 1
                prompt_id_comparisons.append(dict(prompt=start['payload']['prompt'],
                    start_prompt_id=start['payload']['prompt_id'], native_prompt_id=matching[0]['promptId'],
                    same=start['payload']['prompt_id'] == matching[0]['promptId']))
    timeline = rows(directory / 'race-timeline.jsonl')
    final = next(x for x in timeline if x['stage'] == 'final')
    assert all(x.get('marker_exists') is not True for x in timeline)
    a = next(r for r in group if r['race_role'] == 'A')
    b = next(r for r in group if r['race_role'] == 'B')
    a_start = next(x for x in starts if x['payload'].get('prompt') == a['registered_text'])
    permission = [x for x in hooks if x['payload']['hook_event_name'] == 'PermissionRequest']
    assert len(permission) == 1
    assert not any(x['payload'][identity] == a_start['payload'][identity] for x in stops)
    escapes = [x for x in writes if x.get('kind') == 'harness-control' and x['bytes'] == '\x1b']
    assert len(escapes) == 1
    assert instant(permission[0]['received_at']) < instant(escapes[0]['written_at'])
    if cli == 'codex':
        assert any(x['type'] == 'event_msg' and x['payload']['type'] == 'turn_aborted'
                   and x['payload']['turn_id'] == a_start['payload'][identity] for x in records)
        close = 'native turn_aborted / interrupted'
    else:
        calls = [x for rec in records if rec.get('type') == 'assistant' for x in rec['message']['content']
                 if x.get('type') == 'tool_use' and x.get('name') == 'Bash' and 'race-' in x['input']['command']]
        assert len(calls) == 1
        results = [x for rec in records if rec.get('type') == 'user' and isinstance(rec['message']['content'], list)
                   for x in rec['message']['content'] if x.get('type') == 'tool_result' and x.get('tool_use_id') == calls[0]['id']]
        assert len(results) == 1 and results[0]['is_error'] is True
        close = 'native Bash tool_result is_error=true after Esc'
    race = dict(label=label, cli=cli, case=b['race_case'], a_submitted_at=a['submitted_at'],
                a_start_received_at=a_start['received_at'], b_registered_at=b['registered_at'],
                b_written=b['written'], b_outcome=b['outcome'], b_queued_seconds=b['queued_seconds'],
                b_first_written_at=b.get('first_written_at'), b_submitted_at=b.get('submitted_at'),
                permission_received_at=permission[0]['received_at'], esc_at=escapes[0]['written_at'],
                observation_cutoff=final['at'], marker_exists=False, close=close,
                a_stop_received=False, gate_missed=final['gate_missed'])
    if b['race_case'] == 'before_start':
        assert instant(a['submitted_at']) <= instant(b['first_written_at']) < instant(a_start['received_at'])
        assert b['written'] and b['gate_last_event']['payload']['hook_event_name'] == 'Stop'
        race['gap_from_a_cr_to_start_ms'] = (instant(a_start['received_at']) - instant(a['submitted_at'])).total_seconds() * 1000
        race['b_gate_at_cr'] = b['gate_at_submit']['last_event']['payload']['hook_event_name']
    else:
        assert not b['written'] and b['gate_attempt']['last_event']['payload']['hook_event_name'] == 'UserPromptSubmit'
        assert b['queued_seconds'] >= 60
    assert final['gate_missed'] == b['written']
    races.append(race)
    sessions.append(dict(label=label, cli=cli, session_id=session_id, model=model, native_turns=len(turn_ids),
                         starts=len(starts), stops=len(stops), permission_events=len(permission),
                         repeated_start_ids={k:v for k,v in starts_by_id.items() if v > 1},
                         prompt_id_comparisons=prompt_id_comparisons,
                         native_turn_ids_without_stop=sorted(turn_ids-stopped_ids),
                         hook_identifier=identity, hook_payload_keys=sorted(set().union(*(set(x['payload']) for x in hooks))), usage=usage))

for cli in ('codex', 'claude'):
    idle = [r for r in injections if r['cli'] == cli and r['state'] == 'idle_gated']
    assert len(idle) >= 5 and all(r['outcome'] == 'ok' for r in idle)
    assert {r['case'] for r in races if r['cli'] == cli} == {'before_start', 'after_start'}
assert sum(r['cli'] == 'claude' and r['state'] == 'running' for r in injections) >= 2
codex_new = sum(s['native_turns'] for s in sessions if s['cli'] == 'codex')
claude_new = sum(s['native_turns'] for s in sessions if s['cli'] == 'claude')
assert 23 + codex_new <= 40 and 11 + claude_new <= 25
counts = collections.Counter((r['cli'], r['state'], r['outcome'], r['written']) for r in injections)
summary = dict(ready_rev=3, status='BLOCKED', reason='Both before_start races wrote B using a previous Stop event',
               sessions=sessions, races=races, registration_count=len(injections),
               actual_injections=sum(r['written'] for r in injections),
               counts=[dict(cli=k[0], state=k[1], outcome=k[2], written=k[3], count=v) for k,v in sorted(counts.items())],
               cumulative_claude_actual_injections=sum(r['cli']=='claude' and r.get('written',True) for r in all_injections),
               codex_main_turns=dict(prior=23, new=codex_new, total=23+codex_new, limit=40),
               claude_turns=dict(prior_conservative=11, new_native_prompt_ids=claude_new, total=11+claude_new, limit=25),
               independent_review='Not performed: task card assigns raw-evidence review to controller')
destination = BASE / 'analysis-rev3.json'
if destination.exists():
    assert json.loads(destination.read_text()) == summary, 'Changed archive; preserve previous result'
else:
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('sessions','races')}, ensure_ascii=False, indent=2))
