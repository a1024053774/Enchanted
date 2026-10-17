"""File/schema/transcript preflight only. No daemon, HTTP server, CLI, or model."""
import argparse
import ast
import copy
import importlib.util
import json
import shlex
import sqlite3
import subprocess
import sys
import traceback
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE / 'workbench/tests'))


def recorded_feedback(module):
    """Replay saved gate bytes only; this does not execute relay or HTTP."""
    snapshot = BASE / '09b-pending-local-03/pending/state.sqlite3'
    with sqlite3.connect(snapshot.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        inbox = [json.loads(row[0]) for row in db.execute('SELECT data FROM inbox_records')]
        dispatches = [json.loads(row[0]) for row in db.execute("SELECT data FROM orchestration_events WHERE type='dispatch_queued'")]
    feedback = next(item for item in dispatches if item['source'] == 'gate')
    receipt = module.feedback_receipts(feedback['text'])[0]
    stop = next(item for item in inbox if item['id'] == receipt['result']['entry']['id'])
    assert receipt['result']['delivery']['state'] == 'delivered'
    target = {key: next(ref.split(':', 1)[1] for ref in stop['refs'] if ref.startswith(prefix))
              for key, prefix in [('thread_id', 'thread:'), ('attempt_id', 'attempt:')]}
    plan = {'root': '/recorded-only', 'target_binding': target,
            'synthetic_input_id': next(ref.split(':', 1)[1] for ref in stop['refs'] if ref.startswith('input:'))}
    previous_rows, previous_accepted = module.rows, module.accepted
    module.rows = lambda root, table: [{'data': json.dumps(item)} for item in inbox]
    module.accepted = lambda root, role: [{'message_kind': 'tool_result', 'phase': 'I1', 'tool_result_payload': {'request_id': receipt['request_id']}}]
    try:
        assert module.phase_for_dispatch(plan, 'ideation', feedback) == 'I2'
        bad = copy.deepcopy(feedback)
        receipts = module.feedback_receipts(bad['text']); receipts[0]['result']['delivery']['state'] = 'pending'
        bad['text'] = bad['text'].split('\n[')[0] + '\n' + json.dumps(receipts)
        try:
            module.phase_for_dispatch(plan, 'ideation', bad)
        except module.ProtocolRefusal as error:
            assert str(error) == 'i2_actual_delivery_required'
        else:
            raise AssertionError('pending accepted as I2')
        wake = next(item for item in dispatches if item.get('inbox_entry') == stop['id'])
        assert module.phase_for_dispatch(plan, 'executor', wake) == 'E1'
        ack = next(item for item in inbox if item.get('kind') == 'ack' and item.get('reply_to') == stop['id'])
        wake = next(item for item in dispatches if item.get('inbox_entry') == ack['id'])
        assert module.phase_for_dispatch(plan, 'ideation', wake) == 'I3'
    finally:
        module.rows, module.accepted = previous_rows, previous_accepted
    return {'status': 'PASS', 'source': str(snapshot), 'cases': ['delivered feedback I2', 'pending I2 denied', 'stop wake E1', 'ack wake I3'],
            'scope': 'saved event parser plus synthetic API-log association; no new relay execution'}


def transcripts(core):
    protocol = json.loads((BASE / '09b-materials-01/protocol.json').read_bytes())
    totals = {}
    last_tool = None
    for role, limit in [('ideation', 6), ('executor', 11)]:
        history = []; number = 0
        for index, phase in enumerate(item for item in protocol['phases'] if item['role'] == role):
            dispatch = {'id': phase['id'], 'seq': 101 + index, 'role': role, 'text': f"⟦主控 #{101+index}⟧\n{phase['id']} 中文  两行\n保留空白",
                        'attempt': 'fixture-attempt', 'session': 'fixture-native', 'fence': 1}
            if phase['tool']:
                dispatch['tool_use'] = {'id': 'tool-' + phase['id'], 'name': 'Bash', 'input': {'command': 'node /fixture/inbox'}}
                dispatch['tool_result'] = {'request_root': '/fixture/requests'}
            registry = {'dispatches': {dispatch['id']: dispatch}, 'message_budget': limit, 'ack_text': phase['id'] + '_ACK'}
            history.append({'role': 'user', 'content': dispatch['text']})
            number += 1; registry['messages_used'] = number
            body = {'messages': copy.deepcopy(history), 'model': 'claude-haiku-5-5', 'stream': True}
            normalized, _ = core.normalize_anthropic_request(body, registry, role)
            response = core.validate_request(normalized, registry)
            assert bool(response.get('tool_use')) == bool(phase['tool'])
            if phase['tool']:
                history.append({'role': 'assistant', 'content': [{'type': 'tool_use', **dispatch['tool_use']}]})
                payload = {'ok': True, 'queued': True, 'delivered': False, 'request_id': 'request-' + phase['id'],
                           'path': '/fixture/requests/request-' + phase['id'] + '.json'}
                history.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': dispatch['tool_use']['id'], 'content': json.dumps(payload)}]})
                # The recorded 2.1.296 sequence may append a system message.
                history.append({'role': 'system', 'content': 'fixture trailing system message'})
                number += 1; registry['messages_used'] = number
                body['messages'] = copy.deepcopy(history)
                normalized, _ = core.normalize_anthropic_request(body, registry, role)
                assert core.validate_request(normalized, registry)['settlement'] is True
                last_tool = (copy.deepcopy(body), copy.deepcopy(registry), role)
            history.append({'role': 'assistant', 'content': phase['id'] + '_ACK'})
        assert number == limit
        totals[role] = number
    return totals, last_tool


def check():
    import t078_09b_protocol_core as core
    import t078_09b_phase_registry as registry_module
    files = [SOURCE / 'workbench/tests' / name for name in ['t078_09b_protocol_core.py', 't078_09b_fake_api.py', 't078_09b_phase_registry.py',
             't078_09b_phase_driver.py', 't078_09b_i1_driver.py', 't078_09b_i1_permission.py', 'run_t078_p1.py']]
    files += [BASE / name for name in ['prepare-a14.py', 'prepare-09b-executable.py', 'run-09b.py', 'run-09b-stage-b.py']]
    for path in files:
        assert path.is_file(); ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    protocol = json.loads((BASE / '09b-materials-01/protocol.json').read_bytes())
    assert {role: (sum(item['role'] == role for item in protocol['phases']), sum(item['messages'] for item in protocol['phases'] if item['role'] == role))
            for role in ['ideation', 'executor']} == {'ideation': (4, 6), 'executor': (6, 11)}
    original_source = subprocess.check_output(['git', 'show', 'cc96540efe5b1841a76fbd132fe3155705dc2cc0:workbench/tests/t078_09b_protocol_core.py'], cwd=SOURCE, text=True)
    parent = {}; exec(compile(original_source, '<parent-protocol-core>', 'exec'), parent)
    parent_module = type('Parent', (), parent)
    try:
        transcripts(parent_module)
    except ValueError as error:
        old_error = str(error)
        assert old_error in ['tool_use_id_mismatch', 'tool_result_multiplicity', 'message_budget_exhausted']
    else:
        raise AssertionError('known-bad transcript checker was accepted')
    totals, last_tool = transcripts(core)
    body, registry, role = last_tool
    negatives = []
    for kind in ['tool_id', 'duplicate', 'text', 'seq', 'identity', 'role', 'budget']:
        bad = copy.deepcopy(body); reg = copy.deepcopy(registry)
        block = next(block for msg in reversed(bad['messages']) for block in (msg.get('content') if isinstance(msg.get('content'), list) else []) if block.get('type') == 'tool_result')
        if kind == 'tool_id': block['tool_use_id'] = 'foreign-current-tool'
        if kind == 'duplicate': bad['messages'].append({'role': 'user', 'content': [copy.deepcopy(block)]})
        if kind == 'text':
            dispatch = next(iter(reg['dispatches'].values()))
            bad['messages'] = [{**message, 'content': message['content'].replace('中文', '正文中间差异')} if isinstance(message.get('content'), str) else message for message in bad['messages']]
        if kind == 'budget': reg['messages_used'] = reg['message_budget'] + 1
        try:
            normalized, _ = core.normalize_anthropic_request(bad, reg, role)
            if kind == 'seq': normalized['dispatch_seq'] += 1
            if kind == 'identity': normalized['attempt'] = 'foreign'
            if kind == 'role': normalized['role'] = 'ideation' if role == 'executor' else 'executor'
            core.validate_request(normalized, reg)
        except core.ProtocolRefusal as error:
            negatives.append({'case': kind, 'error': str(error)})
        else:
            raise AssertionError('counterexample accepted: ' + kind)
    scene = BASE / '09b-a11-i1-scene-01/requests.ndjson'
    first = json.loads(scene.read_text(encoding='utf-8').splitlines()[0]); tools = json.loads(first['body_raw'])['tools']
    bash = next(item for item in tools if item['name'] == 'Bash')['input_schema']
    assert 'command' in bash['properties'] and 'command' in bash['required'] and 'argv' not in bash['properties']
    # Static command substitution only. No synthetic ID reaches a live command.
    actual_stop = registry_module.stop_entry
    registry_module.stop_entry = lambda plan: {'id': 'fixture-stop'}
    try:
        for phase in protocol['phases']:
            tool = registry_module.tool_for({'root': '/fixture', 'protocol_source': str(BASE / '09b-materials-01/protocol.json'),
                'target_binding': {'thread_id': 'fixture-thread', 'attempt_id': 'fixture-attempt'}, 'synthetic_input_id': 'fixture-input'}, phase['id'])
            if phase['tool']:
                assert set(tool['input']) == {'command'} and shlex.split(tool['input']['command']) == tool['command_argv']
    finally:
        registry_module.stop_entry = actual_stop
    draft = json.loads((BASE / '09b-a14-materials-01/stage-a-approval.json').read_bytes())
    assert draft['allow_role_cli_spawn'] is False and draft['approved_by'] is None and draft['approval_ref'] is None
    stage_template = json.loads((BASE / '09b-a14-materials-01/b1-approval-template.json').read_bytes())
    frozen = json.loads((BASE / 'stage-b-a12-ideation-approval-01.json').read_bytes())
    assert stage_template['screen_approvals'] == frozen['screen_approvals'] and stage_template['tool_approval'] == frozen['tool_approval']
    assert stage_template['screen_approvals'][3]['purpose'] == 'security-notice' and stage_template['screen_approvals'][3]['screen_text']
    assert 'onboarding-notice' in (BASE / 'prepare-a14.py').read_text(encoding='utf-8')
    assert 'window.a2a.input' in (SOURCE / 'workbench/tests/electron_driver.mjs').read_text(encoding='utf-8')
    p1 = (SOURCE / 'workbench/tests/run_t078_p1.py').read_text(encoding='utf-8')
    assert "if args.reuse_stage_a else root" in p1
    generation = (BASE / 'prepare-a14.py').read_text(encoding='utf-8')
    assert '--reuse-stage-a --launch-label LAUNCH_LABEL --phase' in generation
    assert (BASE / '09b-a14-materials-01/protocol.json').read_bytes() == (BASE / '09b-materials-01/protocol.json').read_bytes()
    command_paths = [SOURCE / path for path in ['workbench/bin/inbox', 'workbench/src/gates/cli.ts', 'workbench/app/build.mjs', 'workbench/tests/electron_driver.mjs']]
    command_paths += [Path(command['argv'][0]) for command in protocol['commands'].values()]
    command_paths += [Path('/Users/luckye/.local/share/claude/versions/2.1.296')]
    for path in command_paths:
        assert path.is_file(), ('command path missing', str(path))
    for file in ['STAGE-A-COMMAND.txt', 'ROLE-MATERIAL-COMMANDS.txt']:
        for line in (BASE / '09b-a14-materials-01' / file).read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#'):
                argv = shlex.split(line); assert argv[:2] == ['python3', '-B'] and Path(argv[2]).is_file(), argv
    spec = importlib.util.spec_from_file_location('a14_file_generator', BASE / 'prepare-a14.py')
    generator = importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)
    assert generator.screen_plan() == (frozen['screen_approvals'], frozen['tool_approval'])
    generated_commands = []
    for phase in protocol['phases']:
        future_p1 = BASE / ('09b-a14-b1-' + phase['role'] + '-p1-01')
        lines = generator.phase_commands(BASE / '09b-a14-stage-a-01', future_p1, phase['id']).splitlines()
        commands = [shlex.split(line) for line in lines if line and not line.startswith('#')]
        assert len(commands) == (3 if phase['tool'] else (2 if phase['id'] == 'I2' else 1))
        for argv in commands:
            assert Path(argv[2]).is_file(), argv
            generated_commands.append({'stage': phase['id'], 'argv': argv, 'input_bindings': 'deferred until actual Stage A/B1/PermissionRequest'})
    return {'status': 'PASS', 'scope': 'static files plus pure-data transcript/schema validation only; no runtime acceptance',
            'parent_red': old_error, 'current_transcript_messages': totals, 'counterexamples': negatives,
            'recorded_feedback': recorded_feedback(registry_module), 'command_paths': [str(path) for path in files + command_paths],
            'generated_phase_commands': generated_commands,
            'deferred_paths': {'09b-executable-materials-14': 'commit script unified prepare', '09b-a14-stage-a-01': 'separately approved Stage A',
                               '09b-a14-b1-ideation-p1-01': 'prepare-a14 --mode role', '09b-a14-b1-executor-p1-01': 'prepare-a14 after I1 pending'},
            'real_process_starts': 0, 'http_checks': 'NOT_RUN', 'launch': 'NO_GO'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    try:
        value = check()
    except Exception as error:
        value = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc(), 'real_process_starts': 0, 'launch': 'NO_GO'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(value, ensure_ascii=False))
    return 0 if value['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
