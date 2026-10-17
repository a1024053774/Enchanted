"""Generate only files for an explicit 09B instance; bind actual Stage A/P1."""
import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import tarfile
import uuid
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def screen_plan():
    # Frozen successful A12 B1 evidence, not the key-stage purpose spelling.
    value = json.loads((BASE / 'stage-b-a12-ideation-approval-01.json').read_bytes())
    return value['screen_approvals'], value['tool_approval']


def phase_commands(stage_a, p1, stage):
    driver = SOURCE / 'workbench/tests/t078_09b_i1_driver.py'
    folder = p1 / 'phases' / stage
    action = 'release' if stage == 'E1' else 'dispatch'
    head = f"python3 -B {driver} --mode execute --protocol --stage {stage} --materials {p1} --stage-a {stage_a} --approval {folder/'approval.json'}"
    text = f'# 单独签字后只执行这一阶段；自动阶段不重新 pane_dispatch。\n{head} --protocol-phase {action} --output {folder/"dispatch-01"}\n'
    if stage == 'I2':
        text = f'# executor 初始放行前，只预批准原有 I2 响应，不发送任何输入。\n{head} --protocol-phase arm --output {folder/"armed-01"}\n\n# executor 放行且 I2 实际完成后只读结算，不再 arm 或派发。\n{head} --protocol-phase collect --output {folder/"collect-01"}\n'
    if stage not in ['I2', 'I4', 'E6']:
        text += (f'\n# 读到 READY_FOR_PERMISSION 后，根据实际事件/屏幕生成未签批准（不发键）。\n'
                 f'python3 -B {BASE/"prepare-a14.py"} --mode permission --p1 {p1} --result {folder/"dispatch-01/result.json"} --output {folder/"permission-approval-01.json"}\n'
                 f'\n# 主控核对完整命令和 ❯ 1. Yes、签字后，一次 awaited Electron Enter。\n'
                 f'python3 -B {SOURCE/"workbench/tests/t078_09b_i1_permission.py"} --materials {p1} --p1 {p1} --stage {stage} --stage-a {stage_a} --dispatch-result {folder/"dispatch-01/result.json"} --process-manifest LAUNCH_MANIFEST --approval {folder/"permission-approval-01.json"} --output {folder/"execute-02"}\n')
    return text


def prepare_role(args):
    assert isinstance(args.instance, str) and re.fullmatch(r'a[1-9][0-9]*', args.instance), 'explicit_instance_required'
    assert args.prompt_file and args.prompt_file.is_file(), 'explicit_prompt_file_required'
    stage_a, packet, out = args.stage_a.resolve(), args.packet.resolve(), args.output.resolve()
    ready = json.loads((stage_a / 'readiness.json').read_bytes())
    static = json.loads((packet / 'static-check.json').read_bytes())
    assert ready['status'] == 'READY_FOR_APPROVAL' and static['revision'] == ready['source_revision'] and static['protocol'] is True
    root = Path(ready['root']); role = args.role; role_root = root / 'roles' / role
    if role == 'executor':
        pending = json.loads(args.result.read_bytes())
        assert pending['status'] == 'READY_FOR_EXECUTOR' and pending['pending'] is True and pending['feedback_count'] == 0
        import sys
        sys.path.insert(0, str(SOURCE / 'workbench/tests'))
        from t078_09b_phase_registry import rows
        actual = [json.loads(row['data']) for row in rows(root, 'relay_results')]
        assert any(value.get('entry', {}).get('id') == pending['stop_entry']['id']
                   and value.get('delivery', {}).get('state') == 'pending' for value in actual)
    api = next(item for item in ready['api_processes'] if item['role'] == role)
    assert api['ready']['fixture_profile'] == 'a14-approved-gate-history-v1'
    assert not out.exists()
    for name in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']:
        (role_root / name).mkdir(parents=True, exist_ok=True)
    role_text = f'09B {role} deterministic role. Use only approved phase input and exact registered tool commands. No retry or extra role.\n'
    (role_root / 'role.md').write_text(role_text, encoding='utf-8')
    (role_root / 'claude/settings.json').write_text('{"theme":"dark"}\n', encoding='utf-8')
    inp = {'schema': 1, 'root': str(root), 'state': str(root / 'state'), 'task': ready['task'], 'preset': role,
           'launch': str(uuid.uuid4()), 'session': str(uuid.uuid4()), 'thread': str(uuid.uuid4()),
           'executable': '/Users/luckye/.local/share/claude/versions/2.1.296', 'role_file': str(role_root / 'role.md'),
           'code_revision': static['revision'], 'source_snapshot': str(packet / 'sources.tar.gz'),
           'api_url': 'http://127.0.0.1:0', 'turn_limit': 4 if role == 'ideation' else 6}
    nonce = args.instance.upper() + '_' + role + '_' + uuid.uuid4().hex
    save(role_root / 'input.json', inp)
    save(role_root / 'scenario.json', {'schema': 1, 'name': args.instance + '-' + role, 'nonce': nonce})
    (role_root / 'nonce.txt').write_text(nonce, encoding='utf-8')
    subprocess.run(['node', str(SOURCE / 'workbench/tests/prepare_t078_p1.ts'), str(role_root / 'input.json'), str(role_root / 'approval.json')], cwd=SOURCE, check=True)
    out.mkdir()
    for name in ['input.json', 'scenario.json', 'nonce.txt', 'approval.json', 'role.md']:
        shutil.copyfile(role_root / name, out / name)
    shutil.copyfile(role_root / 'claude/settings.json', out / 'isolated-settings.json')
    shutil.copyfile(packet / 'sources.tar.gz', out / 'sources.tar.gz')
    with tarfile.open(out / 'sources.tar.gz') as arc:
        save(out / 'source-files.json', arc.getnames())
    plan_path = root / 'protocol-plan.json'
    if role == 'ideation':
        prompt = args.prompt_file.read_text(encoding='utf-8')
        plan = {'schema': 1, 'root': str(root), 'target_binding': ready['target_binding'], 'roles': {},
                'protocol_source': str(BASE / '09b-materials-01/protocol.json'), 'synthetic_input_id': str(uuid.uuid4()), 'i1_prompt': prompt}
        baseline = root / 'target/home/received.bin'; before = baseline.read_bytes()
        assert baseline.read_bytes() == before
        with (root / 'target-baseline.bin').open('xb') as stream:
            stream.write(before)
        save(plan_path, plan)
    plan = json.loads(plan_path.read_bytes())
    assert role not in plan['roles'] and plan['target_binding'] == ready['target_binding']
    plan['roles'][role] = inp
    temporary = root / 'protocol-plan.tmp'; save(temporary, plan); temporary.replace(plan_path)
    save(role_root / 'protocol-registry.json', {'phase_plan': str(plan_path), 'dispatches': {}, 'message_budget': 6 if role == 'ideation' else 11})
    if role == 'ideation':
        (out / 'i1-prompt.txt').write_text(plan['i1_prompt'], encoding='utf-8')
    launch_label = '09b-' + args.instance + '-b1-' + role + '-01'
    screens, tool = screen_plan()
    approval = {'approved_by': None, 'approval_ref': None, 'stage': 'B', 'phase': 'B1', 'role': role,
                'source_revision': static['revision'], 'binding': ready['target_binding'], 'p1_materials': str(out),
                'p1_phase': 'launch', 'p1_args': ['--reuse-stage-a', '--reuse-api-root', str(role_root), '--reuse-readiness-file', str(stage_a / 'readiness.json')],
                'readiness_reference': str(stage_a / 'readiness.json'), 'allow_role_cli_spawn': True, 'stop_after': 'first-screen',
                'screen_approvals': screens, 'tool_approval': tool}
    save(out / 'stage-b-approval.json', approval)
    save(out / 'readiness-template.json', {'launch': inp['launch'], 'session': inp['session'], 'confirmed_by': None, 'readiness': 'unconfirmed', 'basis': None})
    commands = []
    for dry in [True, False]:
        label = launch_label + '-dry-run' if dry else launch_label
        commands.append(f'python3 -B {BASE/"run-09b-stage-b.py"} --materials {packet} --stage-a {stage_a} --role {role} --phase B1 --approval {out/"stage-b-approval.json"} --output {BASE/label}' + (' --dry-run' if dry else ''))
    (out / 'B1-COMMANDS.txt').write_text('\n\n'.join(commands) + '\n', encoding='utf-8')
    # The real launch result chooses the manifest; bind-launch is file-only.
    (out / 'BIND-LAUNCH.txt').write_text(f'python3 -B {BASE/"prepare-a14.py"} --mode bind-launch --p1 {out} --result {BASE/launch_label/"result.json"} --output {out/"launch-binding.json"}\n', encoding='utf-8')
    keys = [('s1', 'ArrowUp', 'onboarding-theme', 'Auto (match terminal)'), ('s3', 'ArrowDown', 'onboarding-theme', 'Dark mode'),
            ('s5', 'Enter', 'onboarding-theme', 'Dark mode'), ('s7', 'Enter', 'onboarding-notice', 'Continue'),
            ('s9', 'ArrowDown', 'workspace-trust', 'Yes, I trust this folder'), ('s11', 'Enter', 'workspace-trust', 'Yes, I trust this folder')]
    lines = ['# 每次只运行一条批准的命令，读屏不符时换新 -02 label 重读，不发键。LAUNCH_LABEL 在 bind-launch 后从实际结果替换。']
    for index, (screen, key, purpose, selected) in enumerate(keys):
        read_label = args.instance + '-' + role + '-' + screen + '-screen'
        for suffix in ['', '-02']:
            lines += [f'# {screen}: ' + ('仅在初读不符时重读；仍不符继续停下。' if suffix else '只读。'),
                      f'python3 -B {SOURCE/"workbench/tests/run_t078_p1.py"} --materials {out} --reuse-stage-a --launch-label LAUNCH_LABEL --phase screen --label {read_label+suffix} --screen-id {role}-{screen}']
        draft = {'launch': inp['launch'], 'session': inp['session'], 'directory': str(root / 'repo'), 'approved_by': None,
                 'approval_ref': None, 'basis': '主控逐字核对当前 screen.bin 后签字；一次一个键', 'screen_id': role + '-' + screen,
                 'purpose': purpose, 'key': key, 'selected_label': selected, 'screen_file': str(out / read_label / 'screen.bin')}
        save(out / 'onboarding' / (screen + '-' + key + '.json'), draft)
        next_screen = role + '-' + (keys[index + 1][0] if index < len(keys) - 1 else 's13')
        lines += ['# 若实际采用 -02，批准和本条 --screen-file 同时绑定该 -02 原件。',
                  f'python3 -B {SOURCE/"workbench/tests/run_t078_p1.py"} --materials {out} --reuse-stage-a --launch-label LAUNCH_LABEL --phase key --label {args.instance}-{role}-{screen}-{key} --screen-id {role}-{screen} --key {key} --purpose {purpose} --approval-file {out/"onboarding"/(screen+"-"+key+".json")} --screen-file {out/read_label/"screen.bin"} --next-screen-id {next_screen}']
        if role == 'executor':
            lines += ['# 每个键后、下一键与初始 release 前，刷新原 stop 收据；不是 delivered/不是 I2。失败立即停。',
                      f'python3 -B {BASE/"observe-startup-queued.py"} --p1 {out} --i1-result {args.result.resolve()} --expected-keys {index+1} --output {out/"onboarding"/(screen+"-queued-readback.json")}']
    for suffix in ['', '-02']:
        lines += [f'# s13{suffix}: 只读最终空提示符/manual；不符就停。', f'python3 -B {SOURCE/"workbench/tests/run_t078_p1.py"} --materials {out} --reuse-stage-a --launch-label LAUNCH_LABEL --phase screen --label {args.instance}-{role}-s13-screen{suffix} --screen-id {role}-s13']
    (out / 'ONBOARD-COMMANDS.txt').write_text('\n\n'.join(lines) + '\n', encoding='utf-8')
    protocol = json.loads((BASE / '09b-materials-01/protocol.json').read_bytes())
    for phase in protocol['phases']:
        if phase['role'] != role:
            continue
        stage = phase['id']; folder = out / 'phases' / stage
        save(folder / 'approval.json', {'approved_by': None, 'approval_ref': None, 'stage': stage, 'phase': stage, 'role': role,
             'launch': inp['launch'], 'session': inp['session'], 'target_binding': ready['target_binding'],
             'p1_materials': str(out), 'source_revision': static['revision'],
             'startup_readiness_file': str(out / 'readiness.json'), 'messages_expected': phase['messages'], 'tool': phase['tool']})
        (folder / 'COMMANDS.txt').write_text(phase_commands(stage_a, out, stage), encoding='utf-8')
    save(out / 'generation.json', {'status': 'PASS', 'instance': args.instance, 'role': role, 'launch_status': 'NO_GO', 'stage_a': str(stage_a), 'prompt_file': str(args.prompt_file.resolve()), 'real_process_starts': 0})


def bind_launch(args):
    p1 = args.p1.resolve(); result = json.loads(args.result.read_bytes()); inp = json.loads((p1 / 'input.json').read_bytes())
    assert result['status'] == 'PASS' and result['cli_spawned'] is True
    actual = Path(result['p1_result']).resolve()
    assert actual.parent.parent == p1
    manifest = actual.parent / 'process-manifest.json'
    value = json.loads(manifest.read_bytes())
    assert value['launch'] == inp['launch'] and value['session'] == inp['session']
    save(args.output, {'launch_label': actual.parent.name, 'process_manifest': str(manifest)})
    for command_file in [p1 / 'ONBOARD-COMMANDS.txt', *p1.glob('phases/*/COMMANDS.txt')]:
        text = command_file.read_text(encoding='utf-8').replace('LAUNCH_LABEL', actual.parent.name).replace('LAUNCH_MANIFEST', str(manifest))
        command_file.write_text(text, encoding='utf-8')


def permission(args):
    result = json.loads(args.result.read_bytes()); inp = json.loads((args.p1 / 'input.json').read_bytes())
    assert result['status'] == 'READY_FOR_PERMISSION'
    screen = Path(result['permission_screen']); assert screen.is_file()
    event = result['permission_event']; command = event['data']['tool_input']['command']
    save(args.output, {'approved_by': None, 'approval_ref': None, 'phase': result['stage'] + '-permission',
         'source': 'test-simulated-user', 'launch': inp['launch'], 'session': inp['session'], 'thread': inp['thread'],
         'directory': str(Path(inp['root']) / 'repo'), 'dispatch': result['dispatch']['id'], 'permission_seq': event['seq'],
         'bash_command': command, 'key': 'Enter', 'selected_label': 'Yes', 'selected_line': '❯ 1. Yes',
         'screen_file': str(screen), 'basis': '主控核对该原屏完整命令和一次性 Yes 后签字'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['role', 'bind-launch', 'permission'], required=True)
    parser.add_argument('--role', choices=['ideation', 'executor'])
    parser.add_argument('--instance')
    parser.add_argument('--prompt-file', type=Path)
    for key in ['stage-a', 'packet', 'p1', 'result', 'output']:
        parser.add_argument('--' + key, type=Path, required=key == 'output')
    args = parser.parse_args()
    if args.mode == 'role': prepare_role(args)
    elif args.mode == 'bind-launch': bind_launch(args)
    else: permission(args)
    print(json.dumps({'status': 'PASS', 'mode': args.mode, 'output': str(args.output), 'real_process_starts': 0}))


if __name__ == '__main__': main()
