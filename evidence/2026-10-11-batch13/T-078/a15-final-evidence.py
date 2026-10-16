"""Read A15 files and retain only counts, approved tools and bounded receipts."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import traceback

BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-yp09xosq')
EXPECTED = {'I1': 2, 'I2': 1, 'I3': 2, 'I4': 1,
            'E1': 2, 'E2': 2, 'E3': 2, 'E4': 2, 'E5': 2, 'E6': 1}


def load(path):
    return json.loads(Path(path).read_bytes())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def approved_tool(row, approval, expected_argv, root, role):
    # The complete HTTP body is inspected in memory, never retained or printed.
    body = json.loads(row['body_raw'])
    blocks = [block for message in body['messages'] if isinstance(message.get('content'), list)
              for block in message['content'] if isinstance(block, dict)]
    identity = row['tool_use_id']
    uses = [item for item in blocks if item.get('type') == 'tool_use' and item.get('id') == identity]
    results = [item for item in blocks if item.get('type') == 'tool_result' and item.get('tool_use_id') == identity]
    assert len(uses) == len(results) == 1
    use, result = uses[0], results[0]
    assert use['name'] == 'Bash' and set(use['input']) == {'command'}
    assert use['input']['command'] == approval['bash_command']
    assert shlex.split(use['input']['command']) == expected_argv
    content = result['content']
    if isinstance(content, list):
        assert all(item.get('type') == 'text' and set(item) == {'type', 'text'} for item in content)
        content = ''.join(item['text'] for item in content)
    payload = json.loads(content)
    assert payload['ok'] is True and payload['queued'] is True and payload['delivered'] is False
    assert not result.get('is_error', False)
    assert Path(payload['path']) == root / 'roles' / role / 'requests' / (payload['request_id'] + '.json')
    return {'tool_use': {'id': identity, 'name': 'Bash', 'input': {'command': use['input']['command']}},
            'tool_result': {'tool_use_id': identity, 'is_error': False,
                            'content': {key: payload[key] for key in ['ok', 'queued', 'delivered', 'request_id', 'path']}}}


def collect(owner):
    assert Path(owner['root']) == ROOT and ROOT.is_dir() and not ROOT.is_symlink()
    protocol = load(BASE / '09b-materials-01/protocol.json')
    plan = load(ROOT / 'protocol-plan.json')
    ready = load(Path(owner['stage_a']) / 'readiness.json')
    assert plan['root'] == ready['root'] == str(ROOT)
    assert plan['target_binding'] == ready['target_binding']
    original = load(owner['I1_result'])
    old_redactor = module('a14_archive_helpers', BASE / 'redact-a14-scene.py')
    pending = old_redactor.safe_pending(original['request_id'], original['relay_receipt'])
    entry = pending['entry']['id']
    sources, roles, phases, permits = {}, {}, [], []
    for role, budget in [('ideation', 6), ('executor', 11)]:
        api = ROOT / 'roles' / role
        p1 = Path(owner['roles'][role]['input']).parent
        inp = load(p1 / 'input.json')
        assert inp['launch'] == owner['roles'][role]['launch'] and inp['session'] == owner['roles'][role]['session']
        runtime = load(owner['roles'][role]['runtime_manifest'])
        env = runtime['launch']['env']
        api_ready = load(api / 'api-ready.json')
        frozen_api = next(item for item in ready['api_processes'] if item['role'] == role)
        assert api_ready == frozen_api['ready'] and api_ready['pid'] == owner['pids'][role + '_api']
        assert env['ANTHROPIC_BASE_URL'] == 'http://127.0.0.1:' + str(api_ready['port'])
        assert runtime['launch']['authentication'] == 'isolated fake API only'
        assert runtime['launch']['code_revision'] == owner['original_source_revision']
        assert all(Path(env[key]) == ROOT / 'roles' / role / suffix for key, suffix in
                   [('HOME', 'home'), ('CLAUDE_CONFIG_DIR', 'claude'), ('TMPDIR', 'tmp'),
                    ('ZDOTDIR', 'shell'), ('A2A_REQUEST_DIR', 'requests'), ('A2A_HOOK_TRACE_DIR', 'hooks'), ('A2A_USER_DATA', 'user-data')])
        requests, responses = rows(api / 'requests.ndjson'), rows(api / 'responses.ndjson')
        assert len(requests) == len(responses) == budget
        http = api / 'http-exchanges'
        assert len(list(http.glob('*.request.bin'))) == len(list(http.glob('*.response.raw'))) == budget
        assert len(list(http.glob('*.meta.json'))) == budget
        safe_calls = []
        for index, call in enumerate(requests, 1):
            assert not call.get('error') and call['path'].split('?')[0] == '/v1/messages'
            assert call['session'] == inp['session'] and call['attempt'] == ready['target_binding']['attempt_id']
            assert call['fence'] == ready['target_binding']['fence'] and call['anthropic'] is True
            meta = load(http / f'{index:04d}.meta.json')
            assert meta['status'] == 200 and meta['role'] == role
            assert meta['dispatch_id'] == call['dispatch_id'] and meta['request_id'] == call['request_id']
            assert responses[index - 1]['request_id'] == call['request_id']
            assert responses[index - 1]['dispatch_id'] == call['dispatch_id']
            raw = (http / f'{index:04d}.response.raw').read_bytes()
            assert raw.count(b'event: ') == responses[index - 1]['events'] == 6
            assert b'event: message_stop\n' in raw
            safe_calls.append({key: call[key] for key in ['phase', 'dispatch_id', 'dispatch_seq', 'request_id', 'message_kind']})
        sources[role] = {'requests': str(api / 'requests.ndjson'), 'responses': str(api / 'responses.ndjson'),
                         'http_exchanges': str(http), 'hooks': str(api / 'hooks')}
        role_phases = [item for item in protocol['phases'] if item['role'] == role]
        role_stops = []; prompt_texts = {}; permission_commands = {}
        for phase in role_phases:
            stage = phase['id']; directory = p1 / 'phases' / stage
            path = directory / ('execute-02/result.json' if stage == 'I1' else 'collect-01/result.json' if stage == 'I2' else 'readback-03/result.json')
            result = load(path)
            assert result['status'] == ('READY_FOR_EXECUTOR' if stage == 'I1' else 'PASS')
            calls = [call for call in requests if call['phase'] == stage]
            assert len(calls) == result['messages'] == EXPECTED[stage] == phase['messages']
            assert {call['dispatch_id'] for call in calls} == {result['dispatch_id']}
            assert {call['dispatch_seq'] for call in calls} == {result['dispatch_seq']}
            stop = result['stop_event']; role_stops.append(stop['data']['prompt_id'])
            assert stop['launch'] == inp['launch'] and stop['data']['session_id'] == inp['session']
            assert stop['data']['prompt_id'] == result['prompt_id']
            bound = load(api / ('bound-' + result['dispatch_id'] + '.json'))
            assert bound['id'] == result['dispatch_id'] and bound['seq'] == result['dispatch_seq']
            assert bound['phase'] == stage and bound['role'] == role
            prompt_texts[result['prompt_id']] = bound['text']
            assert result['created_at'] == pending['entry']['created_at']
            safe_phase = {'phase': stage, 'role': role, 'dispatch_id': result['dispatch_id'], 'dispatch_seq': result['dispatch_seq'],
                          'messages': len(calls), 'roots': 1, 'prompt_id': result['prompt_id'], 'stop_event_seq': stop['seq'],
                          'target_byte_count': result['target_byte_count'], 'source': str(path)}
            receipt = result['relay_receipt']
            if receipt is not None:
                safe_phase['relay'] = {'ok': receipt['ok']}
                if receipt.get('error'):
                    assert receipt['error'] == {'E1': 'worker_target_required', 'I3': 'recipient_required',
                                                'E5': 'stop_already_acknowledged'}[stage]
                    safe_phase['relay']['error_code'] = receipt['error']
                if stage == 'E2':
                    assert receipt['interruptRequested'] is True
                    safe_phase['relay']['interruptRequested'] = True
                if stage in ['E3', 'E4']:
                    ack = result['ack_entry']
                    assert ack['from'] == 'executor' and ack['reply_to'] == entry
                    assert receipt['entry']['id'] == ack['id']
                    safe_phase['relay']['ack_id'] = ack['id']
            if stage == 'I2':
                assert result['original_request_id'] == pending['request_id']
            if phase['tool']:
                executed = load(directory / 'execute-02/result.json')
                approval = executed['permission_approval']; action = executed['permission_control_action']
                assert approval['approved_by'] == 'executor' and approval['approval_ref'].strip()
                assert action['form'] == 'action' and action['text'] == '\r'
                assert action['content'] == {'action': 'terminal-key', 'data': '\r'}
                assert action['target']['thread'] == inp['thread']
                delivered = executed['permission_key_result']['delivered']
                assert delivered['ok'] is True and delivered['written'] is True
                assert action['source_ref']['command_id'] == delivered['request_id']
                assert [call['message_kind'] for call in calls] == ['tool_use', 'tool_result']
                argv = protocol['commands'][phase['tool']]['argv']
                values = {'{target.thread_id}': ready['target_binding']['thread_id'],
                          '{target.attempt_id}': ready['target_binding']['attempt_id'],
                          '{synthetic_user_input.id}': plan['synthetic_input_id'], '{stop.id}': entry}
                expected = []
                for token in argv:
                    for placeholder, value in values.items(): token = token.replace(placeholder, value)
                    if token.endswith('/roles/ideation/stop-body.txt'): token = str(ROOT / 'roles/ideation/stop-body.txt')
                    expected.append(token)
                projected = approved_tool(calls[1], approval, expected, ROOT, role)
                permission_commands[result['prompt_id']] = approval['bash_command']
                safe_phase['tools'] = projected
                permits.append({'phase': stage, 'action_id': action['id'], 'command_id': delivered['request_id'],
                                'form': 'action', 'text_hex': '0d', 'source': str(directory / 'execute-02/result.json')})
            phases.append(safe_phase)
        hooks = []
        for directory in sorted((api / 'hooks').iterdir()):
            if not directory.is_dir(): continue
            request = load(directory / 'stdin.bin'); finished = load(directory / 'finished.json')
            assert finished['exit_code'] == 0 and finished['launch'] == inp['launch']
            assert request['session_id'] == inp['session']
            if request['hook_event_name'] == 'UserPromptSubmit':
                assert request['prompt'] == prompt_texts[request['prompt_id']]
            if request['hook_event_name'] == 'PermissionRequest':
                assert request['tool_name'] == 'Bash'
                assert request['tool_input']['command'] == permission_commands[request['prompt_id']]
            if request['hook_event_name'] in ['UserPromptSubmit', 'Stop']:
                hooks.append({'event': request['hook_event_name'], 'prompt_id': request['prompt_id'], 'exit_code': 0})
            elif request['hook_event_name'] == 'PermissionRequest':
                hooks.append({'event': 'PermissionRequest', 'prompt_id': request['prompt_id'], 'exit_code': 0})
        for event in ['UserPromptSubmit', 'Stop']:
            assert sorted(item['prompt_id'] for item in hooks if item['event'] == event) == sorted(role_stops)
        assert sorted(item['prompt_id'] for item in hooks if item['event'] == 'PermissionRequest') == sorted(permission_commands)
        roles[role] = {'POST': budget, 'responses_200': budget, 'http_409': 0,
                       'roots': len(role_stops), 'requests': safe_calls, 'hooks': hooks}
    assert len({item['action_id'] for item in permits}) == len(permits) == 7
    assert len({item['tools']['tool_result']['content']['request_id'] for item in phases if 'tools' in item}) == 7
    assert len({item['relay']['ack_id'] for item in phases if 'ack_id' in item.get('relay', {})}) == 1
    assert sorted(item['dispatch_seq'] for item in phases) == list(range(2, 12))
    target = (ROOT / 'target/home/received.bin').read_bytes(); baseline = (ROOT / 'target-baseline.bin').read_bytes()
    assert target == baseline + b'\x1b' and not baseline
    delivered = load(BASE / '09b-a15-e1-preparation-01/delivery-i2-readback-01.json')
    assert delivered['status'] == 'PASS' and delivered['original_request_id'] == pending['request_id']
    assert delivered['original_entry_id'] == entry and delivered['original_created_at'] == pending['entry']['created_at']
    assert delivered['turn_submitted_seq'] < delivered['feedback_seq']
    assert delivered['feedback_count'] == delivered['i2_registration_count'] == delivered['i2_submission_count'] == 1
    assert delivered['delivery']['state'] == 'delivered'
    return {'schema': 1, 'status': 'PASS', 'root': str(ROOT), 'business_revision': owner['original_source_revision'],
            'reader_harness_revision': 'c0c5caee3e70e58abadbd55efa4eade72a44370b',
            'roles': roles, 'phases': sorted(phases, key=lambda item: item['dispatch_seq']), 'tool_permissions': permits,
            'POST_total': 17, 'roots_total': 10, 'real_vendor_model_turns': 0,
            'model_basis': 'launch manifests and reused loopback API identities; all 17 Messages accounted for locally',
            'target_delta_hex': '1b', 'target_byte_count': 1,
            'original_I1_pending_receipt': pending, 'delivered_I2_readback': delivered, 'sources': sources,
            'raw_messages_retained': False, 'headers_metadata_system_auth_retained': False,
            'collection_actions': 'file reads only; no gate/API/process/SQLite/window/key operations'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    try:
        result = collect(load(args.owner))
    except Exception as error:
        result = {'status': 'INCOMPLETE', 'error_type': type(error).__name__, 'traceback': traceback.format_exc()}
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result.get(key) for key in ['status', 'POST_total', 'roots_total', 'target_delta_hex', 'error_type']}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
