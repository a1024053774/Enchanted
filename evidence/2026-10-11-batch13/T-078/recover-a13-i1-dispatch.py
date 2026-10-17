"""Recover an existing A-13 I1 dispatch/permission pause without dispatching again."""
import argparse, base64, json, os, shutil, subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
NODE = shutil.which('node') or '/opt/homebrew/bin/node'

def gate(root: Path, *args):
    clean = {k: v for k, v in os.environ.items() if not k.startswith('A2A_')}
    clean.update({'A2A_OPERATOR_CREDENTIAL': str(root / 'operator.json'), 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
    command = [NODE, str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', str(root / 'state'), *map(str, args)]
    result = subprocess.run(command, cwd=SOURCE, env=clean, capture_output=True, text=True, check=True)
    return json.loads(result.stdout.strip().splitlines()[-1])

def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage-a', type=Path, required=True); p.add_argument('--materials', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); stage = a.stage_a.resolve(); materials = a.materials.resolve(); out = a.output.resolve(); assert not out.exists(), 'output_exists'
    readiness = json.loads((stage / 'readiness.json').read_bytes()); approval = json.loads((materials / 'approval.json').read_bytes()); inp = json.loads((materials / 'b1-input.json').read_bytes())
    assert readiness['status'] == 'READY_FOR_APPROVAL' and readiness['root'] == inp['root'] and approval['launch'] == inp['launch'] and approval['session'] == inp['session']
    root = Path(readiness['root']).resolve(); task = readiness['task']; launch = inp['launch']; expected_prompt = (materials / 'i1-prompt.txt').read_text(encoding='utf-8').rstrip('\r\n')
    events_result = gate(root, 'orchestration_events', '--task', task); events = events_result.get('events', [])
    dispatch_events = [event for event in events if event.get('type') == 'dispatch_queued' and event.get('launch') == launch and event.get('data', {}).get('source') == 'executor' and event.get('data', {}).get('text', '').endswith(expected_prompt)]
    assert len(dispatch_events) == 1, {'dispatch_candidates': len(dispatch_events), 'launch': launch}
    dispatch_event = dispatch_events[0]; data = dispatch_event['data']; dispatch = {'id': data['id'], 'seq': data['seq'], 'source': data['source'], 'text': data['text'], 'registered_at': data.get('registered_at')}
    permission_events = [event for event in events if event.get('type') == 'permission_wait' and event.get('launch') == launch]
    assert len(permission_events) == 1, {'permission_events': len(permission_events), 'launch': launch}
    permission_event = permission_events[0]
    assert permission_event['data'].get('hook_event_name') == 'PermissionRequest' and permission_event['data'].get('tool_name') == 'Bash'
    screen = gate(root, 'pane_output', '--launch', launch, '--offset', '0'); assert screen.get('ok') is True and isinstance(screen.get('data_base64'), str)
    screen_bytes = base64.b64decode(screen['data_base64'], validate=True); assert screen_bytes
    out.mkdir(parents=True); (out / 'permission-screen.bin').write_bytes(screen_bytes)
    (out / 'permission-screen.json').write_text(json.dumps({'launch': launch, 'session': inp['session'], 'dispatch': dispatch, 'permission_event': permission_event, 'pane_output': screen, 'recovered_without_dispatch': True}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {'status': 'READY_FOR_PERMISSION', 'stage': 'I1', 'role': 'ideation', 'dispatch': dispatch, 'permission_event': permission_event, 'permission_screen': str((out / 'permission-screen.bin').resolve()), 'messages_sent': 1, 'roots_used': 1, 'stop_condition': 'pause before permission Enter; no tool_result, Stop or executor wake yet', 'recovered_without_dispatch': True, 'source_events': str((out / 'events-readback.json').resolve())}
    (out / 'events-readback.json').write_text(json.dumps({'status': 'PASS', 'event_count': len(events), 'dispatch_event_seq': dispatch_event['seq'], 'permission_event_seq': permission_event['seq']}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'recovered_dispatch': dispatch['id'], 'seq': dispatch['seq'], 'permission_seq': permission_event['seq'], 'dispatch_called': False}, ensure_ascii=False))

if __name__ == '__main__': raise SystemExit(main())
