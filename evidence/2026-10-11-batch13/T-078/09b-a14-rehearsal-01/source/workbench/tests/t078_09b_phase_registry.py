"""Bind approved fake responses to actual gate dispatches. Never write gate state."""
import json
import sqlite3
import shlex
import time
import uuid
from contextlib import closing
from pathlib import Path

from t078_09b_protocol_core import ProtocolRefusal, _text_blocks

ORDER = {'ideation': ['I1', 'I2', 'I3', 'I4'], 'executor': ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']}
NEXT = {'I1': 'I2', 'I3': 'I4', 'E1': 'E2', 'E2': 'E3', 'E3': 'E4', 'E4': 'E5', 'E5': 'E6'}


def rows(root, table):
    if table not in ['inbox_records', 'relay_requests', 'relay_results', 'orchestration_events', 'events', 'launch_records']:
        raise ValueError('invalid_table')
    with closing(sqlite3.connect((Path(root) / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute('SELECT * FROM ' + table)]


def accepted(root, role):
    path = Path(root) / 'roles' / role / 'requests.ndjson'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line] if path.exists() else []


def feedback_receipts(text):
    body = text.partition('\n')[2]
    index = body.find('\n[')
    if index < 0:
        raise ProtocolRefusal('gate_feedback_json_required')
    return json.loads(body[index + 1:])


def stop_entry(plan):
    target = plan['target_binding']
    refs = {f"thread:{target['thread_id']}", f"attempt:{target['attempt_id']}", f"input:{plan['synthetic_input_id']}"}
    candidates = [json.loads(row['data']) for row in rows(plan['root'], 'inbox_records')]
    candidates = [entry for entry in candidates if entry.get('kind') == 'stop' and entry.get('from') == 'ideation'
                  and entry.get('to') == 'executor' and refs.issubset(set(entry.get('refs', [])))]
    if len(candidates) != 1:
        raise ProtocolRefusal('actual_stop_entry_required')
    return candidates[0]


def phase_for_dispatch(plan, role, dispatch):
    if role == 'ideation' and dispatch['source'] == 'executor':
        if dispatch['text'].partition('\n')[2] != plan['i1_prompt'].rstrip('\r\n'):
            raise ProtocolRefusal('i1_prompt_mismatch')
        return 'I1'
    entry = stop_entry(plan)
    if dispatch['source'] == 'inbox':
        if role == 'executor' and dispatch.get('inbox_entry') == entry['id']:
            return 'E1'
        entries = [json.loads(row['data']) for row in rows(plan['root'], 'inbox_records')]
        ack = next((item for item in entries if item['id'] == dispatch.get('inbox_entry')), None)
        if role == 'ideation' and ack and ack['kind'] == 'ack' and ack['from'] == 'executor' and ack['reply_to'] == entry['id']:
            return 'I3'
    if dispatch['source'] == 'gate':
        receipts = feedback_receipts(dispatch['text'])
        if len(receipts) != 1:
            raise ProtocolRefusal('one_actual_execution_receipt_required')
        request_id = receipts[0]['request_id']
        prior = [row for row in accepted(plan['root'], role) if not row.get('error') and row.get('message_kind') == 'tool_result'
                 and row.get('tool_result_payload', {}).get('request_id') == request_id]
        if len(prior) != 1 or prior[0].get('phase') not in NEXT:
            raise ProtocolRefusal('feedback_request_binding_required')
        stage = NEXT[prior[0]['phase']]
        if stage == 'I2' and (receipts[0]['result'].get('delivery', {}).get('state') != 'delivered'
                              or receipts[0]['result'].get('entry', {}).get('id') != entry['id']):
            raise ProtocolRefusal('i2_actual_delivery_required')
        return stage
    raise ProtocolRefusal('unexpected_actual_dispatch')


def tool_for(plan, stage):
    protocol = json.loads(Path(plan['protocol_source']).read_bytes())
    phase = next(item for item in protocol['phases'] if item['id'] == stage)
    if phase['tool'] is None:
        return None
    values = {'target.thread_id': plan['target_binding']['thread_id'],
              'target.attempt_id': plan['target_binding']['attempt_id'],
              'synthetic_user_input.id': plan['synthetic_input_id']}
    if stage != 'I1':
        values['stop.id'] = stop_entry(plan)['id']
    argv = []
    for token in protocol['commands'][phase['tool']]['argv']:
        for key, value in values.items():
            token = token.replace('{' + key + '}', value)
        if token.endswith('/roles/ideation/stop-body.txt'):
            token = str(Path(plan['root']) / 'roles/ideation/stop-body.txt')
        if '{' in token or '}' in token:
            raise ProtocolRefusal('unresolved_command_placeholder')
        argv.append(token)
    return {'id': str(uuid.uuid4()), 'name': 'Bash', 'input': {'command': shlex.join(argv)}, 'command_argv': argv}


def validate_phase_approval(approval, plan, role, stage):
    if role not in ORDER or stage not in ORDER[role]:
        raise ProtocolRefusal('phase_role_mismatch')
    inp = plan['roles'][role]
    if (approval.get('approved_by') != 'executor' or not approval.get('approval_ref') or approval.get('stage') != stage
            or approval.get('role') != role or approval.get('launch') != inp['launch']
            or approval.get('session') != inp['session'] or approval.get('target_binding') != plan['target_binding']
            or approval.get('source_revision') != inp['code_revision']):
        raise ProtocolRefusal('phase_approval_binding_mismatch')


def resolve_request(request, registry, api_root, role):
    """The explicit phase-plan profile reads actual gate rows before responding."""
    plan = json.loads(Path(registry['phase_plan']).read_bytes())
    inp = plan['roles'][role]
    if Path(api_root).resolve() != Path(plan['root']) / 'roles' / role:
        raise ProtocolRefusal('phase_api_root_mismatch')
    launches = [json.loads(row['data']) for row in rows(plan['root'], 'launch_records') if row['id'] == inp['launch']]
    if len(launches) != 1 or any(launches[0].get(key) != value for key, value in
                               [('session', inp['session']), ('preset', role), ('thread', inp['thread']), ('task', inp['task'])]):
        raise ProtocolRefusal('actual_controller_launch_required')
    texts = [text for msg in request.get('messages', []) if msg.get('role') == 'user' for text in _text_blocks(msg)]
    dispatches = [json.loads(row['data']) for row in rows(plan['root'], 'orchestration_events')
                  if row['type'] == 'dispatch_queued' and row['launch'] == inp['launch']]
    candidates = [item for item in dispatches if item['text'] in texts]
    if not candidates:
        raise ProtocolRefusal('registered_text_mismatch')
    dispatch = max(candidates, key=lambda item: item['seq'])
    submitted = [row for row in rows(plan['root'], 'orchestration_events') if row['type'] == 'turn_submitted'
                 and row['launch'] == inp['launch'] and json.loads(row['data']).get('dispatch') == dispatch['id']]
    if len(submitted) != 1:
        raise ProtocolRefusal('actual_submission_required')
    stage = phase_for_dispatch(plan, role, dispatch)
    bound_file = Path(api_root) / ('bound-' + dispatch['id'] + '.json')
    if bound_file.exists():
        bound = json.loads(bound_file.read_bytes())
        if bound['text'] != dispatch['text'] or bound['seq'] != dispatch['seq'] or bound['phase'] != stage:
            raise ProtocolRefusal('bound_dispatch_changed')
    else:
        bound = {**dispatch, 'phase': stage, 'role': role, 'attempt': plan['target_binding']['attempt_id'],
                 'session': inp['session'], 'fence': plan['target_binding']['fence']}
        tool = tool_for(plan, stage)
        if tool:
            bound.update(tool_use=tool, tool_result={'request_root': str(Path(api_root) / 'requests')})
        with bound_file.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(bound, ensure_ascii=False, indent=2) + '\n')
    # Explicit fixture response barrier. It holds this single HTTP call, not
    # a retry or another model request. The controller arms one stage at a time.
    approval_file = Path(api_root) / 'stage-approvals' / (stage + '.json')
    waiting = Path(api_root) / 'waiting-phase.json'
    waiting.write_text(json.dumps({'stage': stage, 'dispatch': dispatch, 'approval_file': str(approval_file)}) + '\n', encoding='utf-8')
    deadline = time.monotonic() + 180
    while not approval_file.is_file():
        if time.monotonic() >= deadline:
            raise ProtocolRefusal('phase_approval_deadline')
        time.sleep(.05)
    validate_phase_approval(json.loads(approval_file.read_bytes()), plan, role, stage)
    return {**registry, 'dispatches': {bound['id']: bound}, 'ack_text': stage + '_ACK'}, stage
