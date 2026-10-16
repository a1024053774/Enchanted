"""Generate protocol I1's three-step A-13 packet from real Stage-A and B1 inputs."""
import argparse, json, shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
PROTOCOL = SOURCE / 'evidence/2026-10-11-batch13/T-078/09b-materials-01/protocol.json'

def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def actual_b1_output(p1: Path):
    candidates = []
    for result_file in p1.glob('*/result.json'):
        try:
            result = json.loads(result_file.read_bytes())
        except Exception:
            continue
        manifest = result_file.parent / 'process-manifest.json'
        if result.get('started', {}).get('ok') is True and manifest.is_file():
            candidates.append((result_file.stat().st_mtime_ns, result_file.parent, manifest))
    if not candidates:
        raise FileNotFoundError(f'actual B1 process-manifest missing under {p1}')
    _, label_dir, manifest = max(candidates, key=lambda item: item[0])
    return label_dir, manifest

def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage-a', type=Path, required=True); p.add_argument('--p1', type=Path, required=True); p.add_argument('--prompt-file', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); stage, p1, prompt, out = a.stage_a.resolve(), a.p1.resolve(), a.prompt_file.resolve(), a.output.resolve(); assert not out.exists(), 'output_exists'
    ready = json.loads((stage / 'readiness.json').read_bytes()); inp = json.loads((p1 / 'input.json').read_bytes()); p1_approval = json.loads((p1 / 'approval.json').read_bytes())
    assert ready['status'] == 'READY_FOR_APPROVAL' and ready['stage'] == 'A' and ready['roles_started'] == [] and p1_approval['input'] == inp
    assert inp['root'] == ready['root'] and inp['preset'] == 'ideation' and inp['launch'] == p1_approval['launch']['id'] and inp['session'] == p1_approval['launch']['session'] and prompt.is_file()
    api = next(item for item in ready['api_processes'] if item['role'] == 'ideation'); assert api['ready'].get('protocol')
    out.mkdir(parents=False)
    for source, name in [(stage / 'readiness.json', 'stage-a-readiness.json'), (p1 / 'input.json', 'b1-input.json'), (p1 / 'approval.json', 'b1-approval.json'), (prompt, 'i1-prompt.txt')]: shutil.copyfile(source, out / name)
    binding = ready['target_binding']; protocol_source = str(PROTOCOL.resolve())
    b1_label_dir, p1_manifest = actual_b1_output(p1)
    b1_manifest = json.loads(p1_manifest.read_bytes())
    assert b1_manifest.get('launch') == inp['launch'] and b1_manifest.get('session') == inp['session']
    write(out / 'static-check.json', {'status': 'PASS', 'launch_status': 'NO_GO', 'stage': 'I1', 'role': 'ideation', 'root': inp['root'], 'task': inp['task'], 'launch': inp['launch'], 'session': inp['session'], 'api_pid': api['pid'], 'api_port': api['ready']['port'], 'api_protocol_tag': api['ready']['protocol'], 'messages_expected': 2, 'permission_screens_expected': 1, 'roots_expected': 1, 'messages_budget': 6, 'real_vendor_model_turns': 0, 'real_process_starts': 0})
    approval = {'approved_by': None, 'approval_ref': None, 'stage': 'I1', 'phase': 'I1', 'role': 'ideation', 'source_revision': ready['source_revision'], 'launch': inp['launch'], 'session': inp['session'], 'thread': inp['thread'], 'target_binding': binding, 'p1_materials': str(p1), 'readiness_reference': str((stage / 'readiness.json').resolve()), 'api_root': str(Path(ready['root']) / 'roles' / 'ideation'), 'api_protocol_tag': api['ready']['protocol'], 'protocol_source': protocol_source, 'dispatch_text_file': str((out / 'i1-prompt.txt').resolve()), 'messages_expected': 2, 'roots_expected': 1, 'messages_budget': 6, 'permission_screens_expected': 1, 'tool': 'I_SEND_STOP', 'real_vendor_model_turns': 0, 'actions': ['pane_dispatch exact approved text', 'record actual dispatch id/seq', 'record actual permission request', 'pane_release once', 'one PermissionRequest approval', 'verify tool_result then actual Stop/relay wake and idle'], 'stop_condition': 'one tool_use + one tool_result, actual Stop/relay wake, idle; no retry'}
    write(out / 'approval-template.json', approval)
    write(out / 'permission-approval-template.json', {'approved_by': None, 'approval_ref': None, 'phase': 'I1-permission', 'source': 'test-simulated-user', 'launch': inp['launch'], 'session': inp['session'], 'thread': inp['thread'], 'directory': str(Path(ready['root']) / 'repo'), 'dispatch': None, 'permission_seq': None, 'bash_command': None, 'key': 'Enter', 'selected_label': 'Yes', 'selected_line': '❯ 1. Yes', 'screen_file': None, 'basis': None, 'stop_condition': 'one bound control Enter, then tool_result/actual Stop-relay readback; no retry', 'slot_rule': 't078-i1-<output-label>-<launch>; output and slot must be new'})
    dispatch_dir = out / 'execute-01' / 'dispatch-01'; execute_dir = out / 'execute-02'
    command = f'''# 1. Dispatch only: pause at PermissionRequest; no Enter.\nPYTHONPATH={SOURCE / 'workbench/tests'} python3 -B {SOURCE / 'workbench/tests/t078_09b_i1_driver.py'} --mode execute --protocol --protocol-phase dispatch --materials {out} --stage-a {stage} --approval {out / 'approval.json'} --output {dispatch_dir}\n\n# 2. Read the exact permission screen through the gate; if the screen is not the expected Bash command, stop.\n{Path(shutil.which('node') or '/opt/homebrew/bin/node')} {SOURCE / 'workbench/src/gates/cli.ts'} --state {ready['root']}/state pane_output --launch {inp['launch']} --offset 0\n\n# 3. After a signed permission approval, send exactly one Electron control Enter. The helper derives a unique slot from execute-02 and launch; no retry.\nPYTHONPATH={SOURCE / 'workbench/tests'} python3 -B {SOURCE / 'workbench/tests/t078_09b_i1_permission.py'} --materials {out} --stage-a {stage} --dispatch-result {dispatch_dir / 'result.json'} --process-manifest {p1_manifest} --approval {out / 'permission-approval-01.json'} --output {execute_dir}\n'''
    (out / 'I1-COMMAND.txt').write_text(command, encoding='utf-8')
    write(out / 'generation.json', {'status': 'PASS', 'stage': 'I1', 'role': 'ideation', 'launch_status': 'NO_GO', 'real_process_starts': 0, 'stage_a': str(stage), 'p1': str(p1), 'b1_launch_label': b1_label_dir.name, 'b1_process_manifest': str(p1_manifest), 'protocol_source': protocol_source, 'unique_output': str(execute_dir), 'unique_slot_rule': 't078-i1-<output-label>-<launch>'})
    print(json.dumps({'status': 'PASS', 'output': str(out), 'launch': 'NO_GO'}, ensure_ascii=False))

if __name__ == '__main__': main()
