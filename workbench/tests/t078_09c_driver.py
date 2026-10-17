"""09C test driver: real clocks, registered tool phases and one bound Enter.

This module does not start a role CLI or send a business stop as operator.
The native role tool/Stop path performs the business operation.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
import traceback
import uuid

from p1_output import read_complete_output, validate_capture
from t078_raw_retention import require, save, read_json

STAGES = {'C-I1': ('ideation', 2, True), 'C-E1': ('executor', 1, False),
          'C-I2': ('ideation', 2, True), 'C-I3': ('ideation', 2, True),
          'C-I4': ('ideation', 1, False)}
TARGET_KEYS = ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id',
               'workspace', 'launch', 'shell_pid', 'leader_pid', 'native_session', 'lstart')
BINDING_KEYS = ('source_revision', 'package', 'launch', 'session', 'thread', 'dispatch',
                'global_seq', 'prompt_id', 'tool_use_id', 'permission_seq', 'stop',
                'target', 'command', 'argv', 'window_id', 'input_generation')
ENTRY_OUTPUT = None


def created_ms(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000


class Clock:
    """System clocks in operational use. Unit tests label injected clocks."""
    def wall(self): return time.time() * 1000
    # Python 3.9 on macOS subtracts a process-local t0 in time.monotonic().
    # Origins are read by later processes, so use the shared POSIX clock directly.
    def mono(self): return time.clock_gettime_ns(time.CLOCK_MONOTONIC) / 1000000
    def sleep(self, seconds): time.sleep(seconds)


def origin(stop, clock):
    wall, mono = clock.wall(), clock.mono()
    age = wall - created_ms(stop['created_at'])
    require(0 <= age < 10000, 'observe_stop_within_first_ten_seconds')
    return {'stop': stop, 'wall_ms': wall, 'mono_ms': mono, 'initial_age_ms': age,
            'observer_pid': os.getpid(), 'clock_type': type(clock).__module__ + '.' + type(clock).__qualname__}


def timing(start, clock):
    wall, mono = clock.wall(), clock.mono()
    elapsed = mono - start['mono_ms']; wall_elapsed = wall - start['wall_ms']
    require(elapsed >= 0 and abs(wall_elapsed - elapsed) <= 1000,
            {'reason': 'clock_discontinuity', 'start': start, 'wall_ms': wall, 'mono_ms': mono,
             'wall_elapsed_ms': wall_elapsed, 'monotonic_elapsed_ms': elapsed,
             'difference_ms': wall_elapsed - elapsed, 'observer_pid': os.getpid(),
             'clock_type': type(clock).__module__ + '.' + type(clock).__qualname__})
    age = wall - created_ms(start['stop']['created_at'])
    require(age <= 150000, 'scenario_deadline_150_seconds')
    return {'wall_ms': wall, 'monotonic_ms': mono, 'wall_age_ms': age, 'observed_elapsed_ms': elapsed}


def validate_binding(binding):
    require(set(binding) == set(BINDING_KEYS), 'permission_binding_fields')
    require(all(value is not None and value != '' for value in binding.values()), 'empty_permission_binding')
    require(type(binding['global_seq']) is int and binding['global_seq'] > 0 and
            type(binding['permission_seq']) is int and binding['permission_seq'] > 0, 'permission_event_numbers')
    require(set(binding['target']) == set(TARGET_KEYS) and all(binding['target'].values()), 'complete_target_binding_required')
    require(set(binding['stop']) == {'id', 'created_at', 'request_id'} and all(binding['stop'].values()), 'stop_binding_required')
    require(binding['argv'] and shlex.join(binding['argv']) == binding['command'], 'exact_command_argv_required')


def validate_permission(template, actual, original, capture):
    require(template.get('approved_by') == 'executor' and bool(template.get('approval_ref')), 'permission_signature_required')
    require(template.get('stage') in ('C-I1', 'C-I2', 'C-I3') and template.get('source') == 'test-simulated-user', 'permission_stage_source')
    require(template.get('key') == 'Enter' and template.get('selected_line') == '❯ 1. Yes' and
            template.get('selected_label') == 'Yes' and template.get('max_writes') == 1, 'one_time_Yes_required')
    validate_binding(template['binding']); validate_binding(actual['binding'])
    require(template['binding'] == actual['binding'], 'actual_permission_template_mismatch')
    require(actual.get('active') is True and actual.get('ack') is False and actual.get('demand_valid') is True,
            'stop_demand_or_active_changed')
    require(actual.get('selected_line') == '❯ 1. Yes', 'permission_selection_changed')
    require(actual.get('visible_command') == template['binding']['command'], 'visible_permission_command_mismatch')
    validate_capture(original, capture)


def visible_command(terminal):
    """Read the native Bash command box, preserving command characters."""
    tail = terminal.rsplit('Run shell command', 1)
    require(len(tail) == 2 and 'This command requires approval' in tail[1], 'native_Bash_command_box_required')
    box = tail[1].split('This command requires approval', 1)[0]
    lines = [line.strip()[1:].strip() for line in box.splitlines() if line.strip().startswith('│')]
    require(bool(lines), 'native_Bash_command_lines_required')
    return ' '.join(lines)


def conditional_enter(template, runtime, start, output, clock=None):
    """Validate repeatedly; exactly one durable intent precedes the one write.

    runtime uses the existing Electron terminal-key permission route. The unit
    runtime is an explicit deterministic spy, never a claim of native CLI use.
    """
    clock = clock or Clock(); output = Path(output); output.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'key_attempts': 0, 'samples': [], 'stage': template.get('stage')}
    intent = Path(template['intent_file'])
    try:
        require(not intent.exists(), 'permission_intent_already_consumed')
        original = Path(template['screen_file']).read_bytes()
        validate_permission(template, runtime.actual(), original, template['screen_capture'])
        require(start['stop'] == template['binding']['stop'], 'clock_stop_binding_mismatch')
        while True:
            sample = timing(start, clock); actual = runtime.actual()
            validate_permission(template, actual, original, template['screen_capture'])
            record['samples'].append(sample)
            save(output / f'sample-{len(record["samples"]):03d}.json', {**sample, 'actual': actual})
            if template['stage'] != 'C-I3':
                require(sample['wall_age_ms'] < 120000, 'early_permission_deadline')
                break
            require(sample['wall_age_ms'] <= 130000, 'conditional_enter_start_deadline')
            if sample['wall_age_ms'] > 120000 and sample['observed_elapsed_ms'] >= 120100: break
            clock.sleep(min(10, max(.01, (120100 - sample['observed_elapsed_ms']) / 1000)))
        # Re-read every page and confirm EOF immediately before the write.
        observed = read_complete_output(runtime.fetch_page, template['binding']['launch'])
        (output / 'current-screen.bin').write_bytes(observed['raw'])
        save(output / 'current-screen-capture.json', observed['capture'])
        require(observed['raw'] == original, 'permission_original_bytes_changed')
        validate_permission(template, runtime.actual(), original, template['screen_capture'])
        sample = timing(start, clock)
        if template['stage'] == 'C-I3':
            require(sample['wall_age_ms'] > 120000 and sample['observed_elapsed_ms'] >= 120100 and
                    sample['wall_age_ms'] <= 130000, 'late_permission_time_mismatch')
        else:
            require(sample['wall_age_ms'] < 120000, 'early_permission_deadline')
        # O_EXCL + fsync survives an uncertain write. Different output labels
        # still refer to this same per-dispatch intent path.
        intent.parent.mkdir(parents=True, exist_ok=True)
        with intent.open('x', encoding='utf-8') as stream:
            json.dump({'binding': template['binding'], 'approval_ref': template['approval_ref'],
                       'write_may_have_happened': True, 'at': sample}, stream, ensure_ascii=False)
            stream.flush(); os.fsync(stream.fileno())
        record['key_attempts'] = 1
        receipt = runtime.enter(template)
        require(receipt.get('form') == 'action' and receipt.get('data') == '\r' and
                receipt.get('intent_count') == 1 and receipt.get('written_count') == 1 and
                receipt.get('new_turn_intents') == 0, 'permission_control_action_unconfirmed_no_retry')
        record.update(status='PASS', control_action=receipt, enter_at=sample, screen_capture=observed['capture'])
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    save(output / 'result.json', record)
    return record


def phase_for_dispatch(plan, role, dispatch):
    from t078_09b_phase_registry import stop_entry, feedback_receipts, accepted
    if role == 'ideation' and dispatch['source'] == 'executor':
        require(dispatch['text'].partition('\n')[2] == plan['i1_prompt'].rstrip('\r\n'), 'C_I1_prompt_mismatch')
        return 'C-I1'
    stop = stop_entry(plan)
    if role == 'executor' and dispatch['source'] == 'inbox' and dispatch.get('inbox_entry') == stop['id']:
        return 'C-E1'
    require(role == 'ideation' and dispatch['source'] == 'gate', 'C_actual_feedback_required')
    receipts = feedback_receipts(dispatch['text']); require(len(receipts) == 1, 'C_one_feedback_required')
    request_id = receipts[0]['request_id']
    previous = [item for item in accepted(plan['root'], role) if not item.get('error') and
                item.get('message_kind') == 'tool_result' and item.get('tool_result_payload', {}).get('request_id') == request_id]
    require(len(previous) == 1, 'C_original_request_required')
    prior = previous[0]['phase']; result = receipts[0].get('result')
    require(isinstance(result, dict), 'C_feedback_envelope_result_required')
    if prior == 'C-I1':
        require(result.get('ok') is True and result.get('entry', {}).get('id') == stop['id'] and
                result.get('delivery', {}).get('state') == 'delivered', 'C_actual_delivery_required')
        return 'C-I2'
    if prior == 'C-I2':
        require(result.get('ok') is False and result.get('error') == 'stop_too_early', 'C_actual_early_denial_required')
        return 'C-I3'
    require(prior == 'C-I3' and result.get('ok') is True and result.get('interruptRequested') is True,
            'C_actual_late_interrupt_receipt_required')
    return 'C-I4'


def tool_for(plan, stage):
    from t078_09b_phase_registry import tool_for as b_tool, stop_entry
    if stage == 'C-I1': return b_tool(plan, 'I1')
    if stage not in ('C-I2', 'C-I3'): return None
    argv = [plan['node'], str(Path(plan['source']) / 'workbench/src/gates/cli.ts'), 'stop',
            '--thread', plan['target_binding']['thread_id'], '--stop-id', stop_entry(plan)['id']]
    return {'id': str(uuid.uuid4()), 'name': 'Bash', 'input': {'command': shlex.join(argv)}, 'command_argv': argv}


def start_first_turn(plan, approval, gate):
    """One approved window request; all later roots come from actual feedback."""
    root = Path(plan['root']); inp = plan['roles']['ideation']
    require(Path(plan['prompt_file']).read_text(encoding='utf-8') == plan['i1_prompt'], 'C_approved_prompt_file_changed')
    for role in ('ideation', 'executor'):
        pane = gate(root, 'pane_status', '--thread', plan['roles'][role]['thread'])
        require(pane['state'] == 'idle' and pane.get('active') is None and not pane.get('queued'), 'C_both_roles_must_be_initialized_idle')
        require(not list((root / 'roles' / role / 'http-exchanges').glob('*.request.bin')), 'C_start_requires_zero_POSTs')
    # Exclusive body creation prevents a second dispatch on an uncertain run.
    save(root / 'roles/ideation/stop-body.txt', {'source': 'test-simulated-user',
         'action_id': plan['synthetic_input_id'], 'approval_ref': approval['approval_ref']})
    queued = gate(root, 'pane_dispatch', '--thread', inp['thread'], '--body-file', plan['prompt_file'])
    dispatch = queued['dispatch']
    require(dispatch['text'] == f'⟦主控 #{dispatch["seq"]}⟧\n' + plan['i1_prompt'].rstrip('\r\n'), 'C_actual_dispatch_prompt')
    save(root / 'roles/ideation' / ('window-stop-action-' + dispatch['id'] + '.json'),
         {'source': 'test-simulated-user', 'action': 'window-stop-request', 'action_id': plan['synthetic_input_id'],
          'approval_ref': approval['approval_ref'], 'launch': inp['launch'], 'thread': inp['thread'], 'dispatch': dispatch})
    return {'status': 'DISPATCHED', 'dispatch': dispatch}


def original_send(plan):
    """Bind the original queued receipt to the real request row and result key."""
    from t078_09b_phase_registry import accepted, rows, stop_entry
    from t078_09b_phase_driver import phase_events
    inp = plan['roles']['ideation']; stop = stop_entry(plan)
    calls = [item for item in accepted(plan['root'], 'ideation') if item.get('phase') == 'C-I1' and
             item.get('message_kind') == 'tool_result' and not item.get('error')]
    require(len(calls) == 1, 'C_one_original_send_tool_result_required')
    request_id = calls[0]['tool_result_payload']['request_id']
    requests = [row for row in rows(plan['root'], 'relay_requests') if row['launch'] == inp['launch'] and row['request_id'] == request_id]
    require(len(requests) == 1, 'C_one_original_send_request_required')
    request = requests[0]; native = json.loads(request['input'])
    _, _, prompt = phase_events(plan, inp, calls[0]['dispatch_id'])
    require(all(native.get(key) == value for key, value in [('command','inbox_send'),('launch',inp['launch']),
        ('session',inp['session']),('native_session',inp['session']),('preset','ideation'),('task',inp['task']),
        ('request_id',request_id),('prompt_id',prompt)]), 'C_original_send_caller_or_prompt_changed')
    results = [json.loads(row['data']) for row in rows(plan['root'], 'relay_results') if row['key'] == request['key']]
    require(len(results) == 1 and results[0].get('ok') is True and results[0].get('entry', {}).get('id') == stop['id'],
            'C_original_send_result_key_or_entry_changed')
    return stop, request, results[0]


class NativePermission:
    """Live readback plus the already validated Electron permission transport."""
    def __init__(self, plan, stage, client):
        self.plan, self.stage, self.client = plan, stage, client
        self.root = Path(plan['root']); self.inp = plan['roles']['ideation']

    def fetch_page(self, offset):
        from t078_09b_i1_driver import gate
        return gate(self.root, 'pane_output', '--launch', self.inp['launch'], '--offset', str(offset))

    def actual(self):
        from t078_09b_i1_driver import gate
        from t078_09b_phase_registry import rows, stop_entry
        from t078_09b_phase_driver import phase_events
        from t078_raw_retention import NativeRuntime, check_identities
        # The signed owner freezes full argv/lstart for all nine processes.
        owner = read_json(self.plan['owner_file'])
        require(owner['scene']==self.plan['scene']=='09C','C_nine_process_scene_required')
        check_identities(owner, NativeRuntime(owner))
        require(self.plan['source_revision'] == owner['source_revision'] and self.plan['target_binding'] == owner['claim_binding'],
                'C_plan_source_or_claim_not_owned')
        require(read_json(Path(self.plan['package']) / 'static-check.json')['revision'] == owner['source_revision'],
                'C_original_source_package_required')
        for key in ('launch', 'session'):
            require(self.inp[key] == owner['roles']['ideation'][key], 'C_original_role_changed:' + key)
        for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace', 'launch'):
            require(self.plan['target_identity'][key] == owner['target_binding'][key], 'C_plan_target_not_owned:' + key)
        require(self.plan['target_identity']['lstart'] == owner['processes']['target_leader']['started'], 'C_target_lstart_not_owned')
        require(self.plan['target_identity']['shell_pid'] == owner['processes']['target_shell']['pid'] and
                self.plan['target_identity']['leader_pid'] == owner['processes']['target_leader']['pid'] and
                self.plan['target_identity']['native_session'] == owner['claim_binding']['runtime_identity']['native_session'],
                'C_original_target_process_binding_required')
        stop = stop_entry(self.plan); inp = self.inp
        pane = gate(self.root, 'pane_status', '--thread', inp['thread'])
        active = pane.get('active') or {}; dispatch_id = active.get('dispatch')
        bound = read_json(self.root / 'roles/ideation' / ('bound-' + str(dispatch_id) + '.json'))
        require(bound['phase'] == self.stage, 'C_active_stage_mismatch')
        events, _, prompt = phase_events(self.plan, inp, dispatch_id)
        waits = [item for item in events if item['type'] == 'permission_wait' and item['data'].get('prompt_id') == prompt]
        require(len(waits) == 1, 'C_one_active_permission_event_required')
        event = waits[0]; command = event['data']['tool_input']['command']
        require(bound['tool_use']['input'] == {'command': command}, 'C_actual_Bash_binding_mismatch')
        view = self.client.call('inspect')
        require(view['launch'] == inp['launch'] and view['thread'] == inp['thread'] and
                view['active_dispatch'] == dispatch_id and view['input_enabled'], 'C_actual_window_binding_mismatch')
        require(re.search(r'^\s*❯\s+1\. Yes\s*$', view['terminal'], re.M) is not None, 'C_one_time_Yes_not_selected')
        entries = [json.loads(row['data']) for row in rows(self.root, 'inbox_records')]
        demand = read_json(self.plan['continued_demand_file'])
        target = gate(self.root, 'pane_process_info', '--thread', self.plan['target_binding']['thread_id'])
        require(target['shell_pid'] == self.plan['target_identity']['shell_pid'] and
                target['leader'] == self.plan['target_identity']['leader_pid'] and
                target['native_session'] == self.plan['target_identity']['native_session'], 'C_target_process_changed')
        live = gate(self.root, 'status', '--task', self.plan['target_binding']['task_id'])['task']['current_attempt']
        require(isinstance(live, dict), 'C_original_attempt_missing')
        for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace'):
            require(live.get(key) == self.plan['target_binding'][key], 'C_current_attempt_changed:' + key)
        original_stop, send_request, _ = original_send(self.plan)
        require(original_stop == stop, 'C_original_stop_changed')
        binding = {'source_revision': self.plan['source_revision'], 'package': self.plan['package'],
            'launch': inp['launch'], 'session': inp['session'], 'thread': inp['thread'], 'dispatch': bound['id'],
            'global_seq': bound['seq'], 'prompt_id': prompt, 'tool_use_id': bound['tool_use']['id'],
            'permission_seq': event['seq'], 'stop': {'id': stop['id'], 'created_at': stop['created_at'], 'request_id': send_request['request_id']},
            'target': self.plan['target_identity'], 'command': command, 'argv': bound['tool_use']['command_argv'],
            'window_id': view['window_id'], 'input_generation': view['input_generation']}
        return {'binding': binding, 'active': pane['state'] == 'busy', 'selected_line': '❯ 1. Yes',
                'visible_command': visible_command(view['terminal']),
                'ack': any(item.get('kind') == 'ack' and item.get('from') == 'executor' and item.get('reply_to') == stop['id'] for item in entries),
                'demand_valid': demand.get('still_required') is True and demand.get('stop_id') == stop['id']}

    def enter(self, template):
        from t078_09b_i1_permission import events, rows
        state = self.root / 'state'; launch = self.inp['launch']; before = events(state, launch)
        high = max([item['seq'] for item in before], default=0)
        binding = template['binding']
        receipt = self.client.call('terminal-key', key='Enter', permission=True, launch=launch, thread=self.inp['thread'],
            dispatch=binding['dispatch'], window_id=binding['window_id'], source='test-simulated-user', approval_ref=template['approval_ref'])
        after = [item for item in events(state, launch) if item['seq'] > high]
        intents = [item for item in after if item['type'] == 'terminal_input_write_intent' and item['data'].get('data') == '\r']
        written = [item for item in after if item['type'] == 'terminal_input_written' and len(intents) == 1 and
                   item['data'].get('request_id') == intents[0]['data'].get('request_id')]
        actions = [row for row in rows(state, 'user_inputs') if len(intents) == 1 and
                   row.get('source_ref', {}).get('command_id') == intents[0]['data'].get('request_id')]
        require(len(actions) == 1, 'C_permission_action_missing')
        return {'form': actions[0]['form'], 'data': actions[0].get('content', {}).get('data'),
                'intent_count': len(intents), 'written_count': len(written),
                'new_turn_intents': len([item for item in after if item['type'] == 'turn_submit_intent' and len(intents) == 1 and
                                        item['data'].get('request_id') == intents[0]['data'].get('request_id')]),
                'window_receipt': receipt, 'action': actions[0], 'events': after}


def settle_stage(plan, inp, stage, output):
    """Use actual POSTs, relay receipts, Stop events and target bytes as oracle."""
    from t078_09b_phase_registry import accepted, rows, stop_entry
    from t078_09b_phase_driver import phase_events
    role, expected_posts, has_tool = STAGES[stage]
    require(inp['preset'] == role, 'C_stage_role_mismatch')
    deadline = time.monotonic() + 20
    while True:
        calls = accepted(plan['root'], role)
        require(not any(item.get('error') for item in calls), 'C_HTTP_error_no_retry')
        raw_posts = list((Path(plan['root']) / 'roles' / role / 'http-exchanges').glob('*.request.bin'))
        require(len(raw_posts) <= (7 if role == 'ideation' else 1), 'C_actual_POST_budget_exceeded')
        phase_calls = [item for item in calls if item.get('phase') == stage]
        require(len(phase_calls) <= expected_posts, 'C_phase_POST_budget_exceeded')
        if len(phase_calls) == expected_posts:
            dispatch_id = phase_calls[0]['dispatch_id']
            events, submission, prompt = phase_events(plan, inp, dispatch_id)
            ends = [item for item in events if item['type'] == 'turn_end_signal' and item['data'].get('prompt_id') == prompt]
            idle = [item for item in events if item['type'] == 'pane_idle' and item['data'].get('submission') == submission['data']['id']]
            if ends and idle: break
        require(time.monotonic() < deadline, 'C_actual_Stop_idle_deadline')
        if Path(plan['clock_origin_file']).exists(): timing(read_json(plan['clock_origin_file']), Clock())
        time.sleep(.05)
    stop = stop_entry(plan)
    inbox = [json.loads(row['data']) for row in rows(plan['root'], 'inbox_records')]
    require(not any(item.get('kind') == 'ack' and item.get('reply_to') == stop['id'] for item in inbox), 'C_unexpected_ack')
    receipt = None
    if has_tool:
        require([item['message_kind'] for item in phase_calls] == ['tool_use', 'tool_result'], 'C_actual_tool_exchange_required')
        request_id = phase_calls[1]['tool_result_payload']['request_id']
        requests = [row for row in rows(plan['root'], 'relay_requests') if row['launch'] == inp['launch'] and row['request_id'] == request_id]
        require(len(requests) == 1 and json.loads(requests[0]['input'])['prompt_id'] == prompt, 'C_actual_relay_request_required')
        receipts = [json.loads(row['data']) for row in rows(plan['root'], 'relay_results') if row['key'] == requests[0]['key']]
        require(len(receipts) == 1, 'C_actual_relay_result_required'); receipt = receipts[0]
    root = Path(plan['root']); target_bytes = (root / plan['target_bytes']).read_bytes()
    baseline = bytes.fromhex(plan['target_baseline_hex'])
    if stage == 'C-I1':
        require(receipt.get('ok') is True and receipt.get('entry', {}).get('id') == stop['id'] and
                receipt.get('delivery', {}).get('state') == 'delivered', 'C_send_must_be_delivered')
        save(plan['clock_origin_file'], origin({'id': stop['id'], 'created_at': stop['created_at'], 'request_id': request_id}, Clock()))
    if stage == 'C-I2':
        require(receipt.get('ok') is False and receipt.get('error') == 'stop_too_early', 'C_early_guard_failed')
        require(target_bytes == baseline, 'C_early_interrupt_forbidden')
        require(timing(read_json(plan['clock_origin_file']), Clock())['wall_age_ms'] < 120000, 'C_early_receipt_not_before_threshold')
    if stage in ('C-I3', 'C-I4', 'C-E1'):
        require(target_bytes == baseline + b'\x1b', 'C_exactly_one_target_Esc_required')
        emergencies = [row for row in rows(root, 'events') if row['type'] == 'emergency_interrupt_requested' and
                       json.loads(row['details']).get('stop_id') == stop['id']]
        require(len(emergencies) == 1 and json.loads(emergencies[0]['details']).get('actor') == 'ideation' and
                json.loads(emergencies[0]['details']).get('thread') == plan['target_binding']['thread_id'], 'C_actual_ideation_interrupt_required')
        require(created_ms(emergencies[0]['time']) - created_ms(stop['created_at']) > 120000, 'C_actual_interrupt_time_must_exceed_120_seconds')
    from t078_09b_i1_driver import gate
    current = gate(root, 'status', '--task', plan['target_binding']['task_id'])['task']['current_attempt']
    require(isinstance(current, dict), 'C_target_must_not_be_reclaimed')
    for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace'):
        require(current.get(key) == plan['target_binding'][key], 'C_target_binding_changed_after_Stop:' + key)
    live = gate(root, 'pane_process_info', '--thread', plan['target_binding']['thread_id'])
    require(live.get('shell_pid') == plan['target_identity']['shell_pid'] and live.get('leader') == plan['target_identity']['leader_pid'] and
            live.get('native_session') == plan['target_identity']['native_session'] and not live.get('session_ended') and not live.get('failed'),
            'C_target_must_remain_alive')
    if stage == 'C-I3':
        require(receipt.get('ok') is True and receipt.get('interruptRequested') is True, 'C_late_gate_interrupt_required')
        save(root / 'roles/executor/hold-release.json', {'stop_id': stop['id'], 'source_revision': plan['source_revision']})
    sample = timing(read_json(plan['clock_origin_file']), Clock())
    result = {'status': 'PASS', 'stage': stage, 'calls': phase_calls, 'stop': stop, 'relay_receipt': receipt,
              'submission': submission, 'Stop': ends, 'idle': idle, 'target_bytes_hex': target_bytes.hex(),
              'observed_time': sample, 'actual_POSTs': len(raw_posts), 'no_ack': True, 'real_vendor_model_turns': 0}
    save(Path(output) / 'settlement.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--stage', choices=list(STAGES), required=True)
    parser.add_argument('--mode', choices=['initialize', 'arm', 'start', 'observe', 'permission', 'collect'], required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    require(not args.output.exists(), 'output_exists_no_action')
    global ENTRY_OUTPUT
    ENTRY_OUTPUT = args.output
    plan = read_json(args.plan); approval = read_json(args.approval)
    require(plan['scene'] == '09C', 'C_plan_required')
    require(plan['roles']['ideation']['turn_limit'] == 4 and plan['roles']['executor']['turn_limit'] == 1,
            'C_native_root_budget_must_be_4_and_1')
    role, _, _ = STAGES[args.stage]; inp = plan['roles'][role]
    from t078_09b_phase_registry import validate_phase_approval, rows
    from t078_09b_i1_driver import gate
    validate_phase_approval(approval, plan, role, args.stage)
    if args.mode == 'permission':
        from electron_client import ElectronClient
        require(args.stage == 'C-I3' and args.build and args.build.is_dir(), 'C_I3_existing_Electron_build_required')
        # Keep the window alive while the executive signs its actual identity.
        # The input transport is the same terminal-key route used for 09B.
        env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
        root = Path(plan['root']); env.update(HOME=str(root / 'manager-home'), TMPDIR=str(root / 'tmp'),
                                             A2A_OPERATOR_CREDENTIAL=str(root / 'operator.json'))
        with_output = args.output.parent / (args.output.name + '-electron')
        client = ElectronClient(Path(plan['source']), args.build, root / 'state', inp['task'], root / 'electron-home', with_output, env, launch=inp['launch'])
        try:
            client.wait(lambda view: view.get('launch') == inp['launch'] and view.get('thread') == inp['thread'] and
                        view.get('active_dispatch') and view.get('input_enabled') is True and
                        re.search(r'^\s*❯\s+1\. Yes\s*$', view.get('terminal', ''), re.M) is not None)
            runtime = NativePermission(plan, args.stage, client)
            observed = read_complete_output(runtime.fetch_page, inp['launch'])
            review = args.output.parent / (args.output.name + '-review'); review.mkdir(parents=True, exist_ok=False)
            (review / 'screen.bin').write_bytes(observed['raw'])
            actual = runtime.actual()
            template = {'stage': args.stage, 'source': 'test-simulated-user', 'key': 'Enter', 'selected_line': '❯ 1. Yes',
                'selected_label': 'Yes', 'max_writes': 1, 'binding': actual['binding'], 'screen_file': str(review / 'screen.bin'),
                'screen_capture': observed['capture'], 'intent_file': str(root / 'permission-intents' / (actual['binding']['dispatch'] + '.json')),
                'approved_by': None, 'approval_ref': None}
            save(review / 'template.json', template)
            start = read_json(plan['clock_origin_file'])
            signed = review / 'approved.json'
            while not signed.is_file():
                sample = timing(start, Clock()); require(sample['wall_age_ms'] < 130000, 'C_permission_signature_deadline')
                time.sleep(.2)
            signed_value = read_json(signed)
            require({key: value for key, value in signed_value.items() if key not in ('approved_by', 'approval_ref')} ==
                    {key: value for key, value in template.items() if key not in ('approved_by', 'approval_ref')}, 'signed_template_content_changed')
            result = conditional_enter(signed_value, runtime, start, args.output / 'control')
            if result['status'] == 'PASS':
                result['settlement'] = settle_stage(plan, inp, args.stage, args.output)
            save(args.output / 'result.json', result)
        finally: client.close()
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        root = Path(plan['root'])
        if args.mode == 'initialize':
            require(args.stage == 'C-I1', 'C_initialize_only_before_I1')
            for r in ('ideation', 'executor'):
                value = plan['roles'][r]; ready = read_json(value['readiness_file'])
                require(ready.get('launch') == value['launch'] and ready.get('session') == value['session'] and
                        ready.get('confirmed_by') == 'executor' and ready.get('readiness') == 'confirmed', 'C_signed_role_readiness_required')
                pane = gate(root, 'pane_status', '--thread', value['thread'])
                require(pane['state'] == 'unknown' and pane.get('active') is None and not pane.get('queued'), 'C_empty_startup_required')
                require(not list((root / 'roles' / r / 'http-exchanges').glob('*.request.bin')), 'C_B1_must_use_zero_POSTs')
            for r in ('ideation', 'executor'):
                gate(root, 'pane_release', '--thread', plan['roles'][r]['thread'], '--reason', approval['approval_ref'])
            result = {'status': 'INITIALIZED', 'business_input_sent': False}
        elif args.mode == 'collect':
            result = settle_stage(plan, inp, args.stage, args.output)
        elif args.mode == 'arm':
            save(root / 'roles' / role / 'stage-approvals' / (args.stage + '.json'), approval)
            result = {'status': 'ARMED', 'input_sent': False}
        elif args.mode == 'start':
            require(args.stage == 'C-I1', 'C_automatic_roots_must_not_be_dispatched')
            from t078_raw_retention import NativeRuntime, check_identities
            owner = read_json(plan['owner_file']); check_identities(owner, NativeRuntime(owner))
            result = start_first_turn(plan, approval, gate)
        else:
            # Observation cannot submit a queued root or press a key.
            events = [{**row, 'data': json.loads(row['data'])} for row in rows(root, 'orchestration_events')]
            result = {'status': 'OBSERVED', 'events': events,
                      'panes': {r: gate(root, 'pane_status', '--thread', plan['roles'][r]['thread']) for r in ('ideation', 'executor')}}
            bound_files = list((root / 'roles' / role).glob('bound-*.json'))
            bound = [read_json(path) for path in bound_files if read_json(path).get('phase') == args.stage]
            require(len(bound) == 1, 'C_one_bound_dispatch_required')
            if STAGES[args.stage][2]:
                from t078_09b_phase_driver import phase_events
                phase, _, prompt = phase_events(plan, inp, bound[0]['id'])
                waits = [item for item in phase if item['type'] == 'permission_wait' and item['data'].get('prompt_id') == prompt]
                require(len(waits) == 1, 'C_permission_event_required')
                screen = read_complete_output(lambda offset: gate(root, 'pane_output', '--launch', inp['launch'], '--offset', str(offset)), inp['launch'])
                (args.output / 'permission-screen.bin').write_bytes(screen['raw'])
                result.update(status='READY_FOR_PERMISSION', stage=args.stage, dispatch=bound[0], permission_event=waits[0],
                              phase_plan=str(args.plan.resolve()), permission_screen=str((args.output / 'permission-screen.bin').resolve()),
                              permission_screen_capture=screen['capture'])
                save(args.output / 'result.json', result)
                print(json.dumps(result, ensure_ascii=False)); return 0
            from t078_09b_phase_registry import stop_entry
            stop = stop_entry(plan)
            if not Path(plan['clock_origin_file']).exists():
                original_stop, send_request, _ = original_send(plan)
                require(original_stop == stop, 'C_original_stop_changed')
                save(plan['clock_origin_file'], origin({'id': stop['id'], 'created_at': stop['created_at'], 'request_id': send_request['request_id']}, Clock()))
        save(args.output / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] != 'INCOMPLETE' else 1


def run_cli():
    global ENTRY_OUTPUT
    ENTRY_OUTPUT = None
    try:
        return main()
    except Exception as error:
        # Retain an entry failure even if it happened before a key attempt.
        # Never overwrite an earlier output/result when a label is repeated.
        failure = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc()}
        if ENTRY_OUTPUT is not None:
            ENTRY_OUTPUT.mkdir(parents=True, exist_ok=True)
            current = ENTRY_OUTPUT / 'result.json'
            if current.exists():
                # This label was created by this attempt (the entry rejects
                # existing outputs). Preserve any intermediate success bytes.
                with (ENTRY_OUTPUT / 'partial-result.json').open('xb') as stream:
                    stream.write(current.read_bytes())
                current.unlink()
            save(ENTRY_OUTPUT / 'result.json', failure)
        print(json.dumps(failure, ensure_ascii=False))
        return 1


if __name__ == '__main__': raise SystemExit(run_cli())
