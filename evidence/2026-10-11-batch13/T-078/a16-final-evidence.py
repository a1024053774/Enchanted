"""Recount A16 HTTP/hook originals and correlate real gate receipts; no runtime actions."""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_output import validate_capture


def need(ok, label, **context):
    if not ok: raise AssertionError({'check': label, **context})


def load(path):
    return json.loads(Path(path).read_bytes())


def one(values, label):
    need(len(values) == 1, label, count=len(values))
    return values[0]


def raw_role(directory, inp, phases):
    expected = [(p['id'], kind) for p in phases for kind in (['tool_use', 'tool_result'] if p['tool'] else ['text'])]
    requests = sorted((directory / 'http-exchanges').glob('*.request.bin'))
    need(len(requests) == len(expected), 'actual_POST_count', role=inp['preset'], actual=len(requests), expected=len(expected))
    need(len(list((directory / 'http-exchanges').glob('*.meta.json'))) == len(requests) ==
         len(list((directory / 'http-exchanges').glob('*.response.bin'))), 'HTTP_triplets')
    exchanges = []
    for index, (path, (stage, kind)) in enumerate(zip(requests, expected), 1):
        need(path.stem == f'{index:04d}.request', 'HTTP_sequence')
        meta = load(path.with_name(f'{index:04d}.meta.json'))
        response_path = path.with_name(f'{index:04d}.response.bin')
        body, response = path.read_bytes(), response_path.read_bytes()
        need(meta['method'] == 'POST' and meta['path'].split('?')[0] == '/v1/messages' and
             meta['role'] == inp['preset'] and meta['phase'] == stage, 'HTTP_role_stage', sequence=index)
        need(meta['status'] == 200 and meta['complete'] is True and len(body) == meta['request_bytes'] and
             len(response) == meta['response_bytes'] == meta['wire_bytes_confirmed'], 'HTTP_complete_bytes', sequence=index)
        events = [json.loads(line[6:]) for line in response.decode('utf-8').splitlines() if line.startswith('data: ')]
        need([x['type'] for x in events] == ['message_start', 'content_block_start', 'content_block_delta',
             'content_block_stop', 'message_delta', 'message_stop'], 'complete_SSE', sequence=index)
        need(events[0]['message']['id'] == meta['request_id'], 'response_request_id')
        exchange = {'phase': stage, 'kind': kind, 'sequence': index, 'meta': meta, 'body': json.loads(body),
                    'request_file': str(path), 'response_file': str(response_path),
                    'meta_file': str(path.with_name(f'{index:04d}.meta.json'))}
        block = events[1]['content_block']
        if kind == 'tool_use':
            need(block['type'] == 'tool_use' and block['name'] == 'Bash' and
                 events[2]['delta']['type'] == 'input_json_delta' and events[4]['delta']['stop_reason'] == 'tool_use',
                 'actual_Bash_tool_use', stage=stage)
            tool_input = json.loads(events[2]['delta']['partial_json'])
            need(set(tool_input) == {'command'}, 'native_Bash_command_schema', stage=stage)
            exchange.update(tool_id=block['id'], command=tool_input['command'])
        else:
            need(block['type'] == 'text' and events[4]['delta']['stop_reason'] == 'end_turn', 'neutral_final_response')
            exchange['assistant_text'] = events[2]['delta']['text']
        exchanges.append(exchange)
    hooks = []
    for directory_item in sorted((directory / 'hooks').iterdir()):
        if not directory_item.is_dir(): continue
        need({p.name for p in directory_item.iterdir()} == {'stdin.bin', 'started.json', 'finished.json', 'stdout.bin', 'stderr.bin'},
             'hook_five_originals', path=str(directory_item))
        payload, started, finished = load(directory_item / 'stdin.bin'), load(directory_item / 'started.json'), load(directory_item / 'finished.json')
        need(finished['exit_code'] == 0 and finished['launch'] == inp['launch'] and
             payload['session_id'] == inp['session'], 'hook_identity_exit', path=str(directory_item))
        hooks.append({'directory': str(directory_item), 'payload': payload, 'started': started, 'finished': finished})
    counts = Counter(h['payload']['hook_event_name'] for h in hooks)
    need(counts == {'UserPromptSubmit': len(phases), 'Stop': len(phases),
                   'PermissionRequest': sum(bool(p['tool']) for p in phases)}, 'hook_counts', actual=dict(counts))
    ups = [h for h in hooks if h['payload']['hook_event_name'] == 'UserPromptSubmit']
    need(len({h['payload']['prompt_id'] for h in ups}) == len(phases), 'unique_raw_UPS_roots')
    return exchanges, hooks, dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(exist_ok=False)
    record = {'status': 'INCOMPLETE', 'scope': 'Worker read-only original recount; not a fresh independent acceptance review',
              'runtime_actions': 0, 'archive_executed': False, 'shutdown_executed': False}
    try:
        ready = load(BASE / '09b-a16-stage-a-01/readiness.json'); root = Path(ready['root'])
        protocol = load(BASE / '09b-materials-01/protocol.json')
        with closing(sqlite3.connect((root / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row; db.execute('BEGIN')
            tables = {name: [dict(x) for x in db.execute('SELECT * FROM ' + name)] for name in
                      ['dispatch_records', 'orchestration_events', 'inbox_records', 'inbox_deliveries',
                       'relay_requests', 'relay_results', 'user_inputs', 'events']}
        events = [{**row, 'data': json.loads(row['data'])} for row in tables['orchestration_events']]
        dispatches = {row['id']: {**row, 'data': json.loads(row['data'])} for row in tables['dispatch_records']}
        entries = [json.loads(row['data']) for row in tables['inbox_records']]
        plan = load(root / 'protocol-plan.json')
        stop = one([e for e in entries if e['kind'] == 'stop' and f"input:{plan['synthetic_input_id']}" in e['refs']], 'one_stop')
        need(stop['from'] == 'ideation' and stop['to'] == 'executor', 'actual_stop_sender')
        all_http, phases_out, roles_out, self_checks = [], [], {}, []
        requests_by_stage = {}
        for role in ['ideation', 'executor']:
            p1 = BASE / ('09b-a16-b1-' + role + '-p1-01'); inp = load(p1 / 'input.json')
            phases = [p for p in protocol['phases'] if p['role'] == role]
            raw_directory = root / 'roles' / role
            exchanges, hooks, counts = raw_role(raw_directory, inp, phases)
            role_runtime = load(Path(load(p1 / 'launch-binding.json')['process_manifest']).parent / 'runtime-manifest.json')
            api = one([a for a in ready['api_processes'] if a['role'] == role], 'one_original_API')
            need(role_runtime['input']['api_url'] == api['ready']['api_url'] and
                 api['ready']['host'] == '127.0.0.1' and api['ready']['model_turns'] == 0 and
                 api['ready']['protocol'] == 'rev2-raw-c-profile-v1', 'loopback_fake_model_boundary')
            with tarfile.open(p1 / 'sources.tar.gz') as archive:
                for name in archive.getnames():
                    need(archive.extractfile(name).read() == (SOURCE / name).read_bytes(), 'frozen_source_member', path=name)
            role_summary = {'POST': len(exchanges), 'roots': counts['UserPromptSubmit'], 'hooks': counts,
                            'hook_files': len(hooks) * 5, 'runtime_manifest': str(Path(load(p1 / 'launch-binding.json')['process_manifest']).parent / 'runtime-manifest.json'),
                            'api_url': api['ready']['api_url'], 'fake_API_ready': str(raw_directory / 'api-ready.json')}
            roles_out[role] = role_summary
            for phase in phases:
                stage = phase['id']; calls = [x for x in exchanges if x['phase'] == stage]
                first, last = calls[0], calls[-1]; dispatch = dispatches[first['meta']['dispatch_id']]
                queued = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'dispatch_queued'
                              and e['data'].get('id') == dispatch['id']], 'one_registered_dispatch')
                need(dispatch['seq'] == queued['data']['seq'], 'actual_global_seq', stage=stage)
                need(all(c['meta']['dispatch_id'] == dispatch['id'] for c in calls),
                     'one_phase_dispatch', stage=stage)
                text = queued['data']['text']
                marker = re.match(r'^⟦(?:主控|门禁) #([0-9]+)⟧\n', text)
                need(marker is not None and int(marker.group(1)) == dispatch['seq'], 'raw_registered_global_marker', stage=stage)
                for call in calls:
                    texts = [block['text'] for message in call['body']['messages'] if message['role'] == 'user'
                             for block in (message['content'] if isinstance(message['content'], list) else [{'type': 'text', 'text': message['content']}])
                             if block.get('type') == 'text']
                    registered = [e for e in events if e['launch'] == inp['launch'] and e['type'] == 'dispatch_queued' and e['data']['text'] in texts]
                    need(text in texts and max(registered, key=lambda e: e['data']['seq'])['data']['id'] == dispatch['id'],
                         'latest_exact_registered_text', stage=stage)
                ups = one([h for h in hooks if h['payload']['hook_event_name'] == 'UserPromptSubmit' and h['payload']['prompt'] == text], 'one_raw_UPS')
                prompt = ups['payload']['prompt_id']
                stop_hook = one([h for h in hooks if h['payload']['hook_event_name'] == 'Stop' and h['payload']['prompt_id'] == prompt], 'one_raw_Stop')
                need(stop_hook['payload']['last_assistant_message'] == last['assistant_text'], 'actual_Stop_assistant_text')
                submitted = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'turn_submitted'
                                 and e['data'].get('dispatch') == dispatch['id']], 'one_actual_submission')
                intent = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'turn_submit_intent'
                              and e['data'].get('dispatch') == dispatch['id']], 'one_phase_root_intent')
                start_event = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'turn_start_signal'
                                   and e['data'].get('prompt_id') == prompt], 'one_actual_UPS_signal')
                end_event = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'turn_end_signal'
                                 and e['data'].get('prompt_id') == prompt], 'one_actual_Stop_signal')
                idle = one([e for e in events if e['launch'] == inp['launch'] and e['type'] == 'pane_idle'
                            and e['data'].get('submission') == intent['data']['id']], 'one_phase_idle')
                need(intent['seq'] < submitted['seq'] < start_event['seq'] < end_event['seq'] and idle['seq'] > submitted['seq'], 'phase_completion_order')
                completion = p1 / 'phases' / stage / ('execute-02/result.json' if stage == 'I1' else 'collect-01/result.json' if stage == 'I2' else 'readback-03/result.json')
                need(load(completion)['status'] == ('READY_FOR_EXECUTOR' if stage == 'I1' else 'PASS'), 'saved_phase_completion', stage=stage)
                row = {'stage': stage, 'role': role, 'POST': len(calls), 'dispatch_id': dispatch['id'], 'dispatch_seq': dispatch['seq'],
                       'source': dispatch['data']['source'], 'prompt_id': prompt, 'UPS_original': ups['directory'] + '/stdin.bin',
                       'Stop_original': stop_hook['directory'] + '/stdin.bin', 'submission_seq': submitted['seq'],
                       'intent_seq': intent['seq'], 'UPS_signal_seq': start_event['seq'], 'Stop_signal_seq': end_event['seq'],
                       'idle_seq': idle['seq'], 'completion_receipt': str(completion)}
                if phase['tool']:
                    values = {'target.thread_id': ready['target_binding']['thread_id'],
                              'target.attempt_id': ready['target_binding']['attempt_id'],
                              'synthetic_user_input.id': plan['synthetic_input_id'], 'stop.id': stop['id']}
                    expected_argv = []
                    for token in protocol['commands'][phase['tool']]['argv']:
                        for key, value in values.items(): token = token.replace('{' + key + '}', value)
                        if token.endswith('/roles/ideation/stop-body.txt'): token = str(root / 'roles/ideation/stop-body.txt')
                        expected_argv.append(token)
                    need(shlex.split(first['command']) == expected_argv, 'approved_protocol_command', stage=stage)
                    results = [block for message in last['body']['messages'] if message['role'] == 'user' and isinstance(message['content'], list)
                               for block in message['content'] if block.get('type') == 'tool_result' and block.get('tool_use_id') == first['tool_id']]
                    tool_result = one(results, 'matching_actual_tool_result')
                    need(tool_result.get('is_error') is False, 'native_tool_not_validation_error')
                    queued_result = json.loads(tool_result['content'])
                    need(queued_result.get('ok') is True and queued_result.get('queued') is True and queued_result.get('delivered') is False,
                         'actual_async_queued_tool_result')
                    request = one([r for r in tables['relay_requests'] if r['launch'] == inp['launch'] and r['request_id'] == queued_result['request_id']], 'one_actual_relay_request')
                    need(json.loads(request['input'])['prompt_id'] == prompt, 'Stop_request_prompt')
                    receipt = json.loads(one([r for r in tables['relay_results'] if r['key'] == request['key']], 'one_actual_relay_result')['data'])
                    requests_by_stage[stage] = queued_result['request_id']
                    permission = one([h for h in hooks if h['payload']['hook_event_name'] == 'PermissionRequest' and h['payload']['prompt_id'] == prompt], 'one_raw_permission')
                    need(permission['payload']['tool_name'] == 'Bash' and permission['payload']['tool_input']['command'] == first['command'], 'hook_tool_command')
                    folder = p1 / 'phases' / stage
                    dispatch_result, execution, consent = load(folder / 'dispatch-01/result.json'), load(folder / 'execute-02/result.json'), load(folder / 'permission-approval-01.json')
                    screen_file = Path(dispatch_result['permission_screen']); screen = screen_file.read_bytes()
                    validate_capture(screen, dispatch_result['permission_screen_capture'])
                    validate_capture(screen, execution['permission_screen_verified_capture'])
                    need(consent['approved_by'] == 'executor' and bool(consent['approval_ref']) and consent['bash_command'] == first['command'] and
                         consent['dispatch'] == dispatch['id'], 'signed_permission_bound_to_actual_command')
                    action = execution['permission_control_action']; key_receipt = execution['permission_key_result']['delivered']
                    need(action['form'] == 'action' and action['content']['data'] == '\r' and key_receipt['written'] is True and
                         action['source_ref']['command_id'] == key_receipt['request_id'], 'Enter_control_action')
                    need(any(load_input['id'] == action['id'] for load_input in map(lambda r: json.loads(r['data']), tables['user_inputs'])), 'actual_persisted_action')
                    written = [e for e in events if e['launch'] == inp['launch'] and e['type'] == 'terminal_input_written'
                               and e['data'].get('request_id') == key_receipt['request_id'] and e['data'].get('byte_length') == 1]
                    need(len(written) == 1, 'one_written_Enter')
                    if stage != 'I1':
                        fresh = p1 / f'a16-{role}-{stage}-permission-screen-01/screen.bin'
                        need(fresh.read_bytes() == screen and load(folder / 'permission-check-01/result.json')['status'] == 'PASS', 'fresh_complete_screen_and_check')
                    row.update(tool_use_id=first['tool_id'], tool_command=first['command'], request_id=queued_result['request_id'],
                               permission_original=permission['directory'] + '/stdin.bin', permission_screen=str(screen_file),
                               permission_screen_bytes=len(screen), permission_capture=dispatch_result['permission_screen_capture'],
                               control_action_id=action['id'], Enter_written_seq=written[0]['seq'],
                               relay_result=receipt)
                phases_out.append(row)
            for call in exchanges:
                all_http.append({k: call[k] for k in ['phase', 'kind', 'sequence', 'request_file', 'response_file', 'meta_file']})
            if role == 'ideation':
                # Deliberately corrupt copies only, through the same original reader.
                with tempfile.TemporaryDirectory(prefix='t078-a16-raw-counterexamples-', dir='/private/tmp') as temporary:
                    for name in ['missing-response', 'truncated-SSE', 'extra-UPS']:
                        clone = Path(temporary) / name
                        shutil.copytree(raw_directory / 'http-exchanges', clone / 'http-exchanges')
                        shutil.copytree(raw_directory / 'hooks', clone / 'hooks')
                        if name == 'missing-response': (clone / 'http-exchanges/0001.response.bin').unlink()
                        elif name == 'truncated-SSE':
                            path = clone / 'http-exchanges/0001.response.bin'; path.write_bytes(path.read_bytes()[:-20])
                        else:
                            extra = next(d for d in (clone / 'hooks').iterdir() if load(d / 'stdin.bin')['hook_event_name'] == 'UserPromptSubmit')
                            shutil.copytree(extra, clone / 'hooks/duplicated-UPS')
                        try:
                            raw_role(clone, inp, phases)
                        except (AssertionError, FileNotFoundError, ValueError) as error:
                            self_checks.append({'case': name, 'rejected': True, 'error': str(error)})
                        else: raise AssertionError({'check': 'raw_counterexample_survived', 'case': name})
        phase_map = {p['stage']: p for p in phases_out}
        i1, e1, i2 = phase_map['I1'], phase_map['E1'], phase_map['I2']
        history = [json.loads(r['data']) for r in tables['inbox_deliveries'] if r['entry'] == stop['id']]
        delivered = one([r for r in history if r['state'] == 'delivered'], 'one_delivered_receipt')
        need(any(r['state'] == 'pending' and r.get('reason') == 'role_session_missing' for r in history) and
             any(r['state'] == 'queued' for r in history), 'pending_then_queued_history')
        feedback = one([e for e in events if e['type'] == 'relay_feedback_registered' and e['data'].get('request_id') == requests_by_stage['I1']], 'original_I2_once')
        submitted = one([e for e in events if e['type'] == 'turn_submitted' and e['data'].get('dispatch') == e1['dispatch_id']], 'actual_E1_written')
        need(delivered['message'] == e1['dispatch_id'] and delivered['created_at'] == submitted['time'] and
             feedback['seq'] > submitted['seq'] and feedback['data']['dispatch'] == i2['dispatch_id'] and
             feedback['data']['entry_id'] == stop['id'], 'delivered_before_original_I2')
        need(i1['relay_result']['delivery']['state'] == 'pending' and i1['relay_result']['entry'] == stop, 'I1_visible_pending_original_entry')
        i2_registered = [e for e in events if e['type'] == 'dispatch_queued' and e['data'].get('id') == i2['dispatch_id']]
        i2_intents = [e for e in events if e['type'] == 'turn_submit_intent' and e['data'].get('dispatch') == i2['dispatch_id']]
        need(len(i2_registered) == len(i2_intents) == 1, 'I2_registration_submission_once')
        baseline = (root / 'target-baseline.bin').read_bytes(); target = (root / 'target/home/received.bin').read_bytes()
        need(target == baseline + b'\x1b', 'exactly_one_target_Esc')
        interrupts = [r for r in tables['events'] if r['type'] == 'emergency_interrupt_requested']
        need(len(interrupts) == 1 and json.loads(interrupts[0]['details'])['actor'] == 'executor' and
             json.loads(interrupts[0]['details'])['thread'] == ready['target_binding']['thread_id'], 'one_actual_executor_interrupt')
        for stage, error in [('E1', 'worker_target_required'), ('I3', 'recipient_required'), ('E5', 'stop_already_acknowledged')]:
            need(phase_map[stage]['relay_result'].get('ok') is False and phase_map[stage]['relay_result'].get('error') == error, 'real_denial', stage=stage)
        acks = [entry for entry in entries if entry['kind'] == 'ack' and entry['reply_to'] == stop['id']]
        ack = one(acks, 'one_actual_ack')
        need(ack['from'] == 'executor' and phase_map['E3']['relay_result']['entry']['id'] == phase_map['E4']['relay_result']['entry']['id'] == ack['id'], 'same_idempotent_ack')
        wakes = [e for e in events if e['type'] == 'dispatch_queued' and e['data'].get('inbox_entry') == ack['id']]
        need(len(wakes) == 1 and wakes[0]['data']['id'] == phase_map['I3']['dispatch_id'] and
             dispatches[e1['dispatch_id']]['data']['inbox_entry'] == stop['id'], 'one_ack_wake_and_original_stop_delivery')
        actual_model_sources = {'boundary': 'Both actual runtime inputs point to the original loopback APIs; frozen source has no provider forwarding; SSE originals are deterministic',
                                'runtime_manifests': [v['runtime_manifest'] for v in roles_out.values()], 'vendor_model_turns': 0}
        record.update(status='PASS', root=str(root), source_revision=ready['source_revision'], roles=roles_out,
                      totals={'POST': len(all_http), 'roots': sum(v['roots'] for v in roles_out.values()),
                              'permissions': sum(v['hooks']['PermissionRequest'] for v in roles_out.values()),
                              'hook_files': sum(v['hook_files'] for v in roles_out.values()), 'vendor_model_turns': 0},
                      phases=sorted(phases_out, key=lambda p: p['dispatch_seq']), HTTP_originals=all_http,
                      target={'baseline_file': str(root / 'target-baseline.bin'), 'received_file': str(root / 'target/home/received.bin'),
                              'baseline_bytes': len(baseline), 'received_bytes': len(target), 'delta_hex': '1b', 'interrupt_event_seq': interrupts[0]['seq']},
                      delivery={'entry_id': stop['id'], 'original_created_at': stop['created_at'], 'original_request_id': requests_by_stage['I1'],
                                'history': history, 'turn_submitted_seq': submitted['seq'], 'feedback_seq': feedback['seq'],
                                'feedback_count': 1, 'I2_registration_count': 1, 'I2_submission_count': 1},
                      model_evidence=actual_model_sources, counterexamples=self_checks,
                      archive_status='INCOMPLETE: originals still live; capture/byte readback/independent tar recount must precede stop')
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: record[k] for k in ['status', 'totals', 'error'] if k in record}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
