"""静态材料核对：不调用 runner.main、gate、HTTP、ps、Electron 或时钟等待。"""
import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import traceback

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
SOURCE = BASE.parents[2]


def load(path):
    return json.loads(Path(path).read_bytes())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT / 'static-check.json')
    output = parser.parse_args().output.resolve()
    assert output.parent == OUT
    assert not output.exists()
    report = {'status': 'INCOMPLETE', 'scope': '只读材料与实际函数的纯校验；未执行 B1 dry-run/real 或场景操作',
              'scene_process_starts': 0, 'keys_sent': 0, 'HTTP_requests': 0, 'signature_files_written': False}
    try:
        stage_a = BASE / '09c-stage-a-01'
        packet = BASE / '09c-executable-materials-02'
        ready = load(stage_a / 'readiness.json')
        assert ready['status'] == load(stage_a / 'result.json')['status'] == 'READY_FOR_APPROVAL'
        static = load(packet / 'static-check.json'); root = Path(ready['root'])
        assert ready['scene'] == static['scene'] == '09C' and ready['source_revision'] == static['revision']
        a = load(BASE / '09c-materials-01/stage-a-approval.json')
        assert a['approved_by'] == 'executor' and a['approval_ref']
        preflight = module('C_material_stage_A', BASE / 'run-09b.py')
        preflight.validate_stage_a_inputs(packet, a, protocol=True)
        files = load(packet / 'source-files.json')
        assert len(files) == 312
        with tarfile.open(packet / 'sources.tar.gz') as frozen:
            original = {name: frozen.extractfile(name).read() for name in files}
        assert all(value == (SOURCE / name).read_bytes() for name, value in original.items())
        b1 = module('C_material_stage_B', BASE / 'run-09b-stage-b.py')
        binding = b1.read_stage_a_binding(stage_a, b1.static_process_probe(ready))
        p1s = {role: BASE / ('09c-c1-b1-' + role + '-p1-01') for role in ['ideation', 'executor']}
        plan = load(root / 'protocol-plan.json')
        assert plan['scene'] == '09C' and plan['target_binding'] == ready['target_binding']
        assert set(plan['roles']) == set(p1s) and plan['source_revision'] == static['revision']
        assert plan['i1_prompt'] == (BASE / '09c-materials-01/i1-prompt.txt').read_text(encoding='utf-8')
        assert (root / 'target-baseline.bin').read_bytes() == (root / 'target/home/received.bin').read_bytes()
        roles = []; future = {}; commands = []
        for role, p1 in p1s.items():
            inp = load(p1 / 'input.json'); draft = load(p1 / 'stage-b-approval.json')
            assert inp == plan['roles'][role] and inp['root'] == str(root) and inp['preset'] == role
            assert inp['api_url'] == 'http://127.0.0.1:0' and inp['turn_limit'] == (4 if role == 'ideation' else 1)
            assert inp['readiness_file'] == str(p1 / 'readiness.json')
            assert draft['approved_by'] is None and draft['approval_ref'] is None
            assert draft['binding'] == ready['target_binding']
            assert draft['screen_approvals'] == b1.expected_screen_plan()
            synthetic = copy.deepcopy(draft)
            synthetic.update(approved_by='executor', approval_ref='只读内存夹具；不是运行批准')
            b1.validate_role_approval(synthetic, binding, packet, role, 'B1')
            for name in ['input.json', 'nonce.txt', 'scenario.json']:
                assert (p1 / name).read_bytes() == (root / 'roles' / role / name).read_bytes()
            with tarfile.open(p1 / 'sources.tar.gz') as copied:
                assert set(copied.getnames()) == set(files)
                assert all(copied.extractfile(name).read() == data for name, data in original.items())
            launch = load(p1 / 'approval.json')['launch']
            for key, sub in [('HOME','home'),('CLAUDE_CONFIG_DIR','claude'),('TMPDIR','tmp'),('ZDOTDIR','shell'),
                             ('A2A_REQUEST_DIR','requests'),('A2A_HOOK_TRACE_DIR','hooks'),('A2A_USER_DATA','user-data')]:
                assert launch['env'][key] == str(root / 'roles' / role / sub)
                assert Path(launch['env'][key]).is_dir()
            for path in (p1 / 'onboarding').glob('*.json'):
                value = load(path)
                assert value['approved_by'] is None and value['approval_ref'] is None
                assert value['directory'] == str(root / 'repo') and value['launch'] == inp['launch']
                if value['screen_id'].endswith('s7'): assert value['purpose'] == 'onboarding-notice'
            assert len(list((p1 / 'onboarding').glob('*.json'))) == 6
            assert not (p1 / 'readiness.json').exists() and not (p1 / 'launch-binding.json').exists()
            api = next(item for item in ready['api_processes'] if item['role'] == role)
            assert load(root / 'roles' / role / 'api-ready.json') == api['ready']
            assert api['ready']['protocol'] == 'rev2-raw-c-profile-v1'
            registry = load(root / 'roles' / role / 'protocol-registry.json')
            assert registry['phase_plan'] == str(root / 'protocol-plan.json')
            assert registry['message_budget'] == (7 if role == 'ideation' else 1)
            assert not list((root / 'roles' / role / 'http-exchanges').glob('*.request.bin'))
            for folder in (p1 / 'phases').iterdir():
                approval = load(folder / 'approval.json')
                assert approval['approved_by'] is None and approval['approval_ref'] is None
                assert approval['launch'] == inp['launch'] and approval['target_binding'] == ready['target_binding']
                if folder.name in ['C-I4', 'C-E1']:
                    assert not (folder / 'OBSERVE-PERMISSION-COMMAND.txt').exists()
                    assert not (folder / 'PERMISSION-SCREEN-CMP-COMMAND.txt').exists()
                    assert not (folder / 'PERMISSION-ENTER-COMMAND.txt').exists()
            future[str(p1 / 'launch-binding.json')] = '实际 B1 bind-launch'
            future[str(p1 / 'readiness.json')] = '主控签 s13 readiness 后只读核对'
            roles.append({'role': role, 'p1': str(p1), 'launch': inp['launch'], 'session': inp['session'],
                          'turn_limit': inp['turn_limit'], 'API_PID': api['pid'], 'API_port': api['ready']['port'],
                          'B1_signature': 'empty', 'keys': 6, 'live_process_probe': 'NOT_RUN'})
        # 所有现有入口/路径必须存在；只对实际 B1/许可/阶段产生的路径登记为未来依赖。
        command_files = [*OUT.glob('*COMMAND*.txt')]
        for p1 in p1s.values(): command_files += list(p1.rglob('*COMMAND*.txt'))
        for path in command_files:
            text = path.read_text(encoding='utf-8')
            for code in re.findall(r"<<'PY'\n(.*?)\nPY", text, re.S): ast.parse(code)
            for line in text.splitlines():
                if not line.startswith(('python3 ', 'node ', 'cmp ')): continue
                if "<<'PY'" in line: continue
                argv = shlex.split(line)
                if argv[0] in ['python3','node']:
                    entry = Path(argv[2] if argv[1] == '-B' else argv[1])
                    assert entry.is_file(), (path, entry)
                deferred = []
                for option in ['--materials','--stage-a','--p1','--plan','--approval','--result','--dispatch-result',
                               '--screen-file','--approval-file','--process-manifest','--build']:
                    if option not in argv: continue
                    value = argv[argv.index(option)+1]
                    if value == 'LAUNCH_MANIFEST':
                        deferred.append({'option': option, 'path': value, 'reason': '实际 B1 的 bind-launch，不复制 manifest'}); continue
                    target = Path(value)
                    if target.exists(): continue
                    permission_output = (option == '--approval' and target.name == 'permission-approval-01.json'
                                         and (target.parent / 'PREPARE-PERMISSION-COMMAND.txt').is_file())
                    allowed = option in ['--result','--dispatch-result','--screen-file','--build'] or str(target) in future or permission_output
                    assert allowed, (path, option, target)
                    deferred.append({'option': option, 'path': value, 'reason': '前序实际运行生成；当前未运行'})
                if '--output' in argv: assert not Path(argv[argv.index('--output')+1]).exists(), (path, 'output exists')
                if '--slot' in argv: assert not (Path('/Volumes/WD-Elements/a2a-workbench')/argv[argv.index('--slot')+1]).exists()
                commands.append({'file': str(path.relative_to(BASE)), 'argv': argv, 'deferred': deferred, 'executed': False})
        assert len(roles) == 2
        keys = ['HOME','CLAUDE_CONFIG_DIR','TMPDIR','ZDOTDIR','A2A_REQUEST_DIR','A2A_HOOK_TRACE_DIR','A2A_USER_DATA']
        environments = [load(p1 / 'approval.json')['launch']['env'] for p1 in p1s.values()]
        assert not set(environments[0][k] for k in keys) & set(environments[1][k] for k in keys)
        for path in OUT.glob('*.py'): ast.parse(path.read_text(encoding='utf-8'))
        report.update(status='PASS', source_revision=static['revision'], frozen_members=len(files),
                      regression_validation=preflight.validate_regression_readbacks(static,a), roles=roles,
                      commands=commands, command_files=len(command_files), command_count=len(commands),
                      future_dependencies=future, budget=load(BASE / '09c-materials-01/BUDGET.json'),
                      runtime_ids='only actual Stage A/B1 inputs; permission/stop IDs remain uncreated',
                      screen_reader='frozen p1_output.read_complete_output; fixed total/continuous offsets/full EOF',
                      actual_09C='INCOMPLETE: not run')
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['status','command_files','command_count'] if key in report} |
                     ({'error': report['error']} if 'error' in report else {}), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
