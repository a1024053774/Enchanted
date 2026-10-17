"""Approved 09B phase control and independent persistent-state readback."""
import json
import os
import time
from pathlib import Path

from t078_09b_phase_registry import rows, accepted, validate_phase_approval
from p1_output import read_complete_output


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def context(stage_a, approval):
    ready = json.loads((Path(stage_a) / 'readiness.json').read_bytes())
    plan = json.loads((Path(ready['root']) / 'protocol-plan.json').read_bytes())
    if ready['target_binding'] != plan['target_binding'] or ready['root'] != plan['root']:
        raise RuntimeError('phase_readiness_mismatch')
    validate_phase_approval(approval, plan, approval['role'], approval['stage'])
    if ready['status'] != 'READY_FOR_APPROVAL':
        raise RuntimeError('stage_a_readiness_required')
    return plan, plan['roles'][approval['role']]


def phase_events(plan, inp, dispatch_id):
    events = [{**row, 'data': json.loads(row['data'])} for row in rows(plan['root'], 'orchestration_events') if row['launch'] == inp['launch']]
    submissions = [event for event in events if event['type'] == 'turn_submit_intent' and event['data'].get('dispatch') == dispatch_id]
    if len(submissions) != 1:
        raise RuntimeError('one_actual_phase_submission_required')
    later = [event['seq'] for event in events if event['type'] == 'turn_submit_intent' and event['seq'] > submissions[0]['seq']]
    boundary = min(later) if later else float('inf')
    starts = [event for event in events if event['type'] == 'turn_start_signal' and submissions[0]['seq'] < event['seq'] < boundary]
    if not starts:
        return events, submissions[0], None
    return events, submissions[0], starts[0]['data']['prompt_id']


def settle_stage(plan, inp, stage, output):
    """Read actual HTTP, Stop, relay, entry, delivery and target bytes; no sends."""
    if plan.get('scene') == '09C':
        from t078_09c_driver import settle_stage as settle_c
        return settle_c(plan, inp, stage, output)
    deadline = time.monotonic() + 45
    expected = next(item for item in json.loads(Path(plan['protocol_source']).read_bytes())['phases'] if item['id'] == stage)
    while time.monotonic() < deadline:
        calls = accepted(plan['root'], inp['preset'])
        errors = [call for call in calls if call.get('error')]
        if errors:
            raise RuntimeError({'api_error_no_retry': [item['error'] for item in errors]})
        calls = [call for call in calls if call.get('phase') == stage]
        if len(calls) > expected['messages']:
            raise RuntimeError('phase_messages_exceeded')
        response_file = Path(plan['root']) / 'roles' / inp['preset'] / 'responses.ndjson'
        responses = [json.loads(line) for line in response_file.read_text(encoding='utf-8').splitlines() if line] if response_file.exists() else []
        if len(calls) == expected['messages'] and len([row for row in responses if row['dispatch_id'] == calls[0]['dispatch_id']]) == expected['messages']:
            dispatch_id = calls[0]['dispatch_id']
            events, submission, prompt = phase_events(plan, inp, dispatch_id)
            stops = [event for event in events if event['type'] == 'turn_end_signal' and event['data'].get('prompt_id') == prompt]
            ended = [event for event in events if event['type'] == 'pane_idle' and event['data'].get('submission') == submission['data']['id']]
            if stops and ended:
                if expected['tool']:
                    queued = calls[1]['tool_result_payload']
                    requests = [row for row in rows(plan['root'], 'relay_requests') if row['launch'] == inp['launch'] and row['request_id'] == queued['request_id']]
                    receipts = [json.loads(row['data']) for row in rows(plan['root'], 'relay_results') if requests and row['key'] == requests[0]['key']]
                    if not requests or not receipts:
                        time.sleep(.05)
                        continue
                break
        time.sleep(.05)
    else:
        raise RuntimeError('phase_stop_deadline')
    if expected['tool']:
        if [call['message_kind'] for call in calls] != ['tool_use', 'tool_result']:
            raise RuntimeError('actual_tool_exchange_required')
        queued = calls[1]['tool_result_payload']
        requests = [row for row in rows(plan['root'], 'relay_requests') if row['launch'] == inp['launch'] and row['request_id'] == queued['request_id']]
        receipts = [json.loads(row['data']) for row in rows(plan['root'], 'relay_results') if requests and row['key'] == requests[0]['key']]
        if len(requests) != 1 or len(receipts) != 1:
            raise RuntimeError('actual_stop_relay_receipt_required')
        if json.loads(requests[0]['input'])['prompt_id'] != prompt:
            raise RuntimeError('actual_stop_prompt_binding_mismatch')
        receipt = receipts[0]
    else:
        receipt = None
    inbox = [json.loads(row['data']) for row in rows(plan['root'], 'inbox_records')]
    stops_inbox = [item for item in inbox if item['kind'] == 'stop' and f"input:{plan['synthetic_input_id']}" in item['refs']]
    if len(stops_inbox) != 1:
        raise RuntimeError('one_actual_stop_entry_required')
    stop = stops_inbox[0]
    result = {'status': 'PASS', 'stage': stage, 'role': inp['preset'], 'dispatch_id': dispatch_id,
              'dispatch_seq': calls[0]['dispatch_seq'], 'prompt_id': prompt, 'stop_event': stops[0],
              'messages': len(calls), 'relay_receipt': receipt, 'stop_entry': stop}
    if stage == 'I1':
        if receipt.get('ok') is not True or receipt.get('delivery', {}).get('state') != 'pending':
            raise RuntimeError('i1_visible_pending_required')
        if receipt['entry']['id'] != stop['id'] or stop['from'] != 'ideation' or stop['to'] != 'executor':
            raise RuntimeError('i1_stop_sender_mismatch')
        feedback = [event for event in events if event['type'] == 'dispatch_queued' and event['data']['source'] == 'gate']
        if feedback:
            raise RuntimeError('pending_feedback_forbidden')
        result.update(status='READY_FOR_EXECUTOR', request_id=queued['request_id'], pending=True, feedback_count=0)
    elif stage == 'I2':
        bound = json.loads((Path(plan['root']) / 'roles/ideation' / ('bound-' + dispatch_id + '.json')).read_bytes())
        from t078_09b_phase_registry import feedback_receipts
        original = feedback_receipts(bound['text'])[0]
        if original['result']['entry']['id'] != stop['id'] or original['result']['delivery']['state'] != 'delivered':
            raise RuntimeError('i2_actual_delivered_receipt_required')
        delivery = original['result']['delivery']
        written = [json.loads(row['data']) for row in rows(plan['root'], 'orchestration_events')
                   if row['type'] == 'turn_submitted' and json.loads(row['data']).get('dispatch') == delivery['message']]
        if len(written) != 1:
            raise RuntimeError('i2_target_write_receipt_required')
        result['original_request_id'] = original['request_id']
    elif stage in ['E1', 'I3', 'E5']:
        error = {'E1': 'worker_target_required', 'I3': 'recipient_required', 'E5': 'stop_already_acknowledged'}[stage]
        if receipt.get('ok') is not False or receipt.get('error') != error:
            raise RuntimeError('real_gate_denial_required_' + stage)
    elif stage == 'E2':
        if receipt.get('ok') is not True or receipt.get('interruptRequested') is not True:
            raise RuntimeError('real_target_interrupt_required')
        interrupts = [json.loads(row['details']) for row in rows(plan['root'], 'events') if row['type'] == 'emergency_interrupt_requested']
        if len(interrupts) != 1 or interrupts[0]['actor'] != 'executor' or interrupts[0]['thread'] != plan['target_binding']['thread_id']:
            raise RuntimeError('actual_executor_interrupt_event_required')
    elif stage in ['E3', 'E4']:
        acks = [item for item in inbox if item['kind'] == 'ack' and item['reply_to'] == stop['id']]
        if len(acks) != 1 or acks[0]['from'] != 'executor' or receipt.get('entry', {}).get('id') != acks[0]['id']:
            raise RuntimeError('one_real_executor_ack_required')
        result['ack_entry'] = acks[0]
        wakes = [row for row in rows(plan['root'], 'orchestration_events') if row['type'] == 'dispatch_queued'
                 and json.loads(row['data']).get('inbox_entry') == acks[0]['id']]
        if len(wakes) != 1:
            raise RuntimeError('one_ack_wake_required')
    baseline = (Path(plan['root']) / 'target-baseline.bin').read_bytes()
    expect_esc = stage in ['E2', 'E3', 'E4', 'E5', 'E6', 'I3', 'I4']
    byte_deadline = time.monotonic() + 5
    target_bytes = (Path(plan['root']) / 'target/home/received.bin').read_bytes()
    while expect_esc and target_bytes == baseline and time.monotonic() < byte_deadline:
        time.sleep(.05)
        target_bytes = (Path(plan['root']) / 'target/home/received.bin').read_bytes()
    if target_bytes != baseline + (b'\x1b' if expect_esc else b''):
        raise RuntimeError('target_bytes_outside_expected_one_esc')
    result.update(target_byte_count=len(target_bytes), target_delta_hex='1b' if expect_esc else '', created_at=stop['created_at'])
    write_new(Path(output) / 'result.json', result)
    return result


def execute(materials, stage_a, approval_path, output, stage, action):
    from t078_09b_i1_driver import gate
    approval = json.loads(Path(approval_path).read_bytes())
    plan, inp = context(stage_a, approval)
    Path(output).mkdir(parents=True, exist_ok=False)
    root = Path(plan['root']); role = inp['preset']
    if Path(approval.get('p1_materials', '')).resolve() != Path(materials).resolve():
        raise RuntimeError('approved_p1_path_mismatch')
    if json.loads((Path(materials) / 'input.json').read_bytes()) != inp:
        raise RuntimeError('approved_p1_input_mismatch')
    if approval['stage'] != stage:
        raise RuntimeError('phase_stage_mismatch')
    if action == 'collect':
        return settle_stage(plan, inp, stage, output)
    if action in ['release', 'dispatch'] and stage in ['I1', 'E1']:
        ready = json.loads(Path(approval['startup_readiness_file']).read_bytes())
        if ready.get('confirmed_by') != 'executor' or ready.get('readiness') != 'confirmed' or not ready.get('basis') or ready.get('launch') != inp['launch'] or ready.get('session') != inp['session']:
            raise RuntimeError('onboarding_readiness_required')
    if action == 'release':
        if stage != 'E1' or not (root / 'roles/ideation/stage-approvals/I2.json').is_file():
            raise RuntimeError('executor_release_requires_preapproved_I2')
    armed = root / 'roles' / role / 'stage-approvals' / (stage + '.json')
    if action != 'observe':
        write_new(armed, approval)
    if action == 'arm':
        value = {'status': 'ARMED', 'stage': stage, 'approval_file': str(armed), 'business_input_sent': False}
        write_new(Path(output) / 'result.json', value); return value
    if action == 'release':
        gate(root, 'pane_release', '--thread', inp['thread'], '--reason', approval['approval_ref'])
    elif stage == 'I1' and action != 'observe':
        prompt = Path(materials) / 'i1-prompt.txt'
        if prompt.read_text(encoding='utf-8') != plan['i1_prompt']:
            raise RuntimeError('approved_i1_prompt_changed')
        (root / 'roles/ideation/stop-body.txt').write_text(json.dumps({'source': 'test-simulated-user', 'action_id': plan['synthetic_input_id'], 'approval_ref': approval['approval_ref']}) + '\n', encoding='utf-8')
        queued = gate(root, 'pane_dispatch', '--thread', inp['thread'], '--body-file', prompt)
        write_new(Path(output) / 'dispatch.json', queued)
        action = {'id': plan['synthetic_input_id'], 'source': 'test-simulated-user', 'action': 'window-stop-request',
                  'approval_ref': approval['approval_ref'], 'launch': inp['launch'], 'thread': inp['thread'], 'dispatch': queued['dispatch']['id']}
        write_new(root / 'roles/ideation' / ('window-stop-action-' + queued['dispatch']['id'] + '.json'), action)
        gate(root, 'pane_release', '--thread', inp['thread'], '--reason', approval['approval_ref'])
    # All other roots are actual gate feedback or inbox wake; no pane_dispatch.
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        observed = accepted(root, role)
        if any(call.get('error') for call in observed):
            raise RuntimeError({'api_error_no_retry': [call['error'] for call in observed if call.get('error')]})
        calls = [call for call in observed if call.get('phase') == stage]
        if calls:
            dispatch_id = calls[0]['dispatch_id']
            events, _, prompt = phase_events(plan, inp, dispatch_id)
            permission = [event for event in events if event['type'] == 'permission_wait' and event['data']['prompt_id'] == prompt]
            if permission:
                screen = read_complete_output(lambda offset: gate(root, 'pane_output', '--launch', inp['launch'], '--offset', str(offset)), inp['launch'])
                Path(output).mkdir(parents=True, exist_ok=True)
                path = Path(output) / 'permission-screen.bin'
                with path.open('xb') as stream:
                    stream.write(screen['raw'])
                bound = json.loads((root / 'roles' / role / ('bound-' + dispatch_id + '.json')).read_bytes())
                result = {'status': 'READY_FOR_PERMISSION', 'stage': stage, 'role': role, 'dispatch': bound,
                          'permission_event': permission[0], 'permission_screen': str(path.resolve()),
                          'permission_screen_capture': screen['capture'], 'phase_plan': str(root / 'protocol-plan.json')}
                write_new(Path(output) / 'result.json', result); return result
            if stage in ['I2', 'I4', 'E6']:
                return settle_stage(plan, inp, stage, output)
        time.sleep(.05)
    raise RuntimeError('phase_permission_deadline')
