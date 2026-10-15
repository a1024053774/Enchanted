"""Approve exactly one native Bash permission for protocol I1.

The dispatch phase must have stopped at ``READY_FOR_PERMISSION`` first.  This
script reads the bound permission screen, uses the real Electron window input
path for one Enter, and then delegates final Messages/Stop/inbox readback to
the shared protocol driver.  It is never run as part of material preparation.
"""
import argparse
import base64
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
TESTS = SOURCE / 'workbench/tests'
sys.path.insert(0, str(TESTS))
from electron_client import ElectronClient
from t078_09b_i1_driver import gate, protocol_i1_readback


def rows(state, table):
    with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        return [json.loads(row[0]) for row in db.execute(f'SELECT data FROM {table}')]


def events(state, launch):
    with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        return [{'seq': row[0], 'type': row[1], 'launch': row[2], 'data': json.loads(row[3])}
                for row in db.execute('SELECT seq,type,launch,data FROM orchestration_events WHERE launch=? ORDER BY seq', (launch,))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--materials', type=Path, required=True)
    parser.add_argument('--stage-a', type=Path, required=True)
    parser.add_argument('--dispatch-result', type=Path, required=True)
    parser.add_argument('--process-manifest', type=Path, required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    materials = args.materials.resolve(); stage_a = args.stage_a.resolve(); dispatch_result = json.loads(args.dispatch_result.read_bytes())
    approval = json.loads(args.approval.read_bytes()); manifest = json.loads(args.process_manifest.read_bytes())
    input_data = json.loads((materials / 'b1-input.json').read_bytes())
    readiness = json.loads((stage_a / 'readiness.json').read_bytes())
    root = Path(readiness['root']).resolve(); state = root / 'state'; launch = input_data['launch']; thread = input_data['thread']
    if dispatch_result.get('status') != 'READY_FOR_PERMISSION': raise RuntimeError('protocol_dispatch_phase_required')
    if approval.get('approved_by') != 'executor' or not approval.get('approval_ref'):
        raise RuntimeError('permission_approval_required')
    for key in ['launch', 'session']:
        if approval.get(key) != input_data[key] or manifest.get(key) != input_data[key]:
            raise RuntimeError('permission_binding_mismatch')
    dispatch = dispatch_result['dispatch']; permission_event = dispatch_result['permission_event']
    if approval.get('dispatch') != dispatch['id'] or approval.get('permission_seq') != permission_event['seq']:
        raise RuntimeError('permission_dispatch_binding_mismatch')
    screen_file = Path(approval.get('screen_file', ''))
    if screen_file.resolve() != Path(dispatch_result['permission_screen']).resolve() or not screen_file.is_file():
        raise RuntimeError('permission_screen_path_mismatch')
    if approval.get('key') != 'Enter' or approval.get('selected_label') != 'Yes' or approval.get('selected_line') != '❯ 1. Yes':
        raise RuntimeError('permission_yes_binding_required')
    command = permission_event.get('data', {}).get('tool_input', {}).get('command')
    if not command or approval.get('bash_command') != command:
        raise RuntimeError('permission_command_mismatch')
    observed = gate(root, 'pane_output', '--launch', launch, '--offset', '0')
    if base64.b64decode(observed['data_base64']) != screen_file.read_bytes():
        raise RuntimeError('permission_screen_changed')
    pane = gate(root, 'pane_status', '--thread', thread)
    if pane.get('state') != 'busy' or pane.get('active', {}).get('dispatch') != dispatch['id']:
        raise RuntimeError('permission_active_dispatch_mismatch')
    before = events(state, launch)
    if len([event for event in before if event['type'] == 'permission_wait' and event['seq'] == approval['permission_seq']]) != 1:
        raise RuntimeError('permission_event_missing')
    # Every permission attempt gets a distinct build slot. build.mjs refuses
    # to overwrite an existing slot, so derive it from the new output label.
    slot = 't078-a12-i1-' + args.output.name + '-' + launch
    build = subprocess.run(['node', str(SOURCE / 'workbench/app/build.mjs'), '--slot', slot], cwd=SOURCE,
                           capture_output=True, text=True, check=True)
    build_out = json.loads(build.stdout.strip().splitlines()[-1])['out']
    env = json.loads((materials / 'b1-input.json').read_bytes())
    client_env = {**os.environ, 'PATH': '/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                  'HOME': str(root / 'manager-home'), 'TMPDIR': str(root / 'tmp'),
                  'A2A_OPERATOR_CREDENTIAL': str(root / 'operator.json'),
                  'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    electron_output = args.output.parent / (args.output.name + '-electron')
    client = ElectronClient(SOURCE, Path(build_out), state, input_data['task'], root / 'electron-home', electron_output, client_env, launch=launch)
    try:
        view = client.wait(lambda value: value.get('launch') == launch and value.get('thread') == thread
                           and value.get('active_dispatch') == dispatch['id'] and value.get('input_enabled') is True
                           and approval['selected_line'] in value.get('terminal', ''))
        before_seq = max([event['seq'] for event in before], default=0)
        key_result = client.call('terminal-key', key='Enter', permission=True, launch=launch, thread=thread,
                                 dispatch=dispatch['id'], window_id=view['window_id'], source='test-simulated-user',
                                 approval_ref=approval['approval_ref'])
        after = events(state, launch)
        intents = [event for event in after if event['seq'] > before_seq and event['type'] == 'terminal_input_write_intent'
                   and event['data'].get('data') == '\r']
        if len(intents) != 1: raise RuntimeError('permission_enter_intent_mismatch')
        action_rows = [row for row in rows(state, 'user_inputs') if row.get('source_ref', {}).get('command_id') == intents[0]['data'].get('request_id')]
        if len(action_rows) != 1 or action_rows[0].get('form') != 'action' or action_rows[0].get('content', {}).get('data') != '\r':
            raise RuntimeError('permission_enter_not_control_action')
        result = protocol_i1_readback(root, root / 'roles' / 'ideation', launch, thread, readiness['target_binding'], dispatch,
                                      dispatch_result.get('release'), args.output.resolve(), dispatch_result['protocol_source'],
                                      Path(dispatch_result['test_simulated_user_action']))
        result.update({'permission_approval': approval, 'permission_view': view, 'permission_key_result': key_result,
                       'permission_control_action': action_rows[0], 'process_manifest': str(args.process_manifest.resolve())})
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'status': 'PASS', 'messages_sent': 2, 'permission_enter': 'control action'}, ensure_ascii=False))
    finally:
        client.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
