"""Check A15 ideation B1 files without running a role, API, gate, or dry-run."""
import importlib.util
import json
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path

PREP = Path(__file__).resolve().parent
BASE = PREP.parent
SOURCE = BASE.parents[2]
P1 = BASE / '09b-a15-b1-ideation-p1-01'
STAGE_A = BASE / '09b-a15-stage-a-01'
PACKET = BASE / '09b-executable-materials-15'


def load(path):
    return json.loads(path.read_bytes())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def check():
    ready = load(STAGE_A / 'readiness.json')
    static = load(PACKET / 'static-check.json')
    inp = load(P1 / 'input.json')
    draft = load(P1 / 'stage-b-approval.json')
    material = load(P1 / 'approval.json')
    root = Path(ready['root'])
    role_root = root / 'roles/ideation'
    assert ready['status'] == 'READY_FOR_APPROVAL' and ready['roles_started'] == []
    assert load(STAGE_A / 'result.json')['attempt'] == ready['target_binding']
    assert all(ready['target_binding'].get(key) not in [None, ''] for key in
               ['task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace'])
    assert inp['root'] == ready['root'] and inp['task'] == ready['task']
    assert inp['code_revision'] == ready['source_revision'] == static['revision']
    assert inp['preset'] == 'ideation' and inp['turn_limit'] == 4
    assert inp['api_url'] == 'http://127.0.0.1:0'
    assert inp['role_file'] == str(role_root / 'role.md')
    assert inp == material['input']
    assert material['status'] == 'INCOMPLETE'
    assert material['phase'] == 'launch material only; no CLI started'
    for name in ['input.json', 'scenario.json', 'nonce.txt', 'approval.json', 'role.md']:
        assert (P1 / name).read_bytes() == (role_root / name).read_bytes(), name
    assert (P1 / 'isolated-settings.json').read_bytes() == (role_root / 'claude/settings.json').read_bytes()
    assert load(P1 / 'isolated-settings.json') == {'theme': 'dark'}
    assert (P1 / 'nonce.txt').read_text(encoding='utf-8').startswith('A15_ideation_')
    assert (P1 / 'sources.tar.gz').read_bytes() == (PACKET / 'sources.tar.gz').read_bytes()
    files = load(P1 / 'source-files.json')
    with tarfile.open(P1 / 'sources.tar.gz') as archive:
        assert archive.getnames() == files
        for name in files:
            assert (SOURCE / name).read_bytes() == archive.extractfile(name).read(), name
    assert draft['approved_by'] is None and draft['approval_ref'] is None
    assert draft['binding'] == ready['target_binding']
    assert draft['source_revision'] == inp['code_revision']
    assert draft['stage'] == 'B' and draft['phase'] == 'B1' and draft['role'] == 'ideation'
    assert draft['p1_materials'] == str(P1) and draft['p1_phase'] == 'launch'
    assert draft['p1_args'] == ['--reuse-stage-a', '--reuse-api-root', str(role_root),
                                '--reuse-readiness-file', str(STAGE_A / 'readiness.json')]
    assert draft['readiness_reference'] == str(STAGE_A / 'readiness.json')
    assert draft['allow_role_cli_spawn'] is True and draft['stop_after'] == 'first-screen'
    runner_b = module('stage_b_static', BASE / 'run-09b-stage-b.py')
    assert draft['screen_approvals'] == runner_b.expected_screen_plan()
    assert draft['tool_approval'] == {'key': 'Enter', 'purpose': 'one-time-tool-approval',
                                      'selected_label': '1. Yes', 'one_time': True}
    assert load(P1 / 'onboarding/s7-Enter.json')['purpose'] == 'onboarding-notice'
    assert all(load(path)['approved_by'] is None and load(path)['approval_ref'] is None
               for path in (P1 / 'onboarding').glob('*.json'))
    launch_env = material['launch']['env']
    for key, relative in [('HOME', 'home'), ('CLAUDE_CONFIG_DIR', 'claude'), ('TMPDIR', 'tmp'),
                          ('ZDOTDIR', 'shell'), ('A2A_REQUEST_DIR', 'requests'),
                          ('A2A_HOOK_TRACE_DIR', 'hooks'), ('A2A_USER_DATA', 'user-data')]:
        assert launch_env[key] == str(role_root / relative), key
        assert Path(launch_env[key]).is_dir(), key
    assert launch_env['A2A_PRESET'] == inp['preset'] and launch_env['A2A_LAUNCH'] == inp['launch']
    assert Path(inp['executable']).is_file()
    assert Path(material['launch']['node_executable']).is_file()
    api = next(item for item in ready['api_processes'] if item['role'] == 'ideation')
    assert load(role_root / 'api-ready.json') == api['ready']
    assert api['ready']['pid'] == api['pid'] and api['ready']['stage'] == 'A'
    assert api['ready']['host'] == '127.0.0.1' and 1 <= api['ready']['port'] <= 65535
    registry = load(role_root / 'protocol-registry.json')
    assert registry == {'phase_plan': str(root / 'protocol-plan.json'), 'dispatches': {}, 'message_budget': 6}
    plan = load(root / 'protocol-plan.json')
    assert plan['target_binding'] == ready['target_binding'] and plan['roles'] == {'ideation': inp}
    assert plan['i1_prompt'] == (BASE / '09b-a15-materials-01/i1-prompt.txt').read_text(encoding='utf-8')
    assert (root / 'target-baseline.bin').read_bytes() == (root / 'target/home/received.bin').read_bytes()
    command_checks = []
    for index, line in enumerate((P1 / 'B1-COMMANDS.txt').read_text(encoding='utf-8').splitlines()):
        if not line.strip():
            continue
        argv = shlex.split(line)
        assert argv[:3] == ['python3', '-B', str(BASE / 'run-09b-stage-b.py')]
        expected = {'--materials': PACKET, '--stage-a': STAGE_A, '--approval': P1 / 'stage-b-approval.json'}
        for flag, path in expected.items():
            assert Path(argv[argv.index(flag) + 1]) == path and path.exists(), flag
        assert argv[argv.index('--role') + 1] == 'ideation'
        assert argv[argv.index('--phase') + 1] == 'B1'
        output = Path(argv[argv.index('--output') + 1])
        expected_output = BASE / ('09b-a15-b1-ideation-01-dry-run' if index == 0 else '09b-a15-b1-ideation-01')
        assert output == expected_output and not output.exists()
        assert ('--dry-run' in argv) == (index == 0)
        command_checks.append({'command': line, 'input_paths': 'PASS', 'output_exists': False, 'executed': False})
    assert len(command_checks) == 2
    onboarding = (P1 / 'ONBOARD-COMMANDS.txt').read_text(encoding='utf-8')
    assert 'LAUNCH_LABEL' in onboarding
    for line in onboarding.splitlines():
        if line.startswith('python3 '):
            argv = shlex.split(line)
            assert Path(argv[2]) == SOURCE / 'workbench/tests/run_t078_p1.py'
            assert Path(argv[2]).is_file()
    lineage = module('stage_a_lineage_static', BASE / 'run-09b.py')
    lineage.validate_material_lineage(PACKET, static)
    generation = load(P1 / 'generation.json')
    assert generation['status'] == 'PASS' and generation['launch_status'] == 'NO_GO'
    report = {'status': 'PASS', 'scope': 'Static files only; no B1 runner/dry-run, process probe, API request, or gate call',
              'source_revision': static['revision'], 'checked_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
              'stage_a': str(STAGE_A), 'p1_materials': str(P1), 'root': str(root),
              'binding': ready['target_binding'], 'ideation_api_from_saved_readiness': api,
              'source_files_byte_compared': len(files), 'draft_unsigned': True,
              'screen_plan': 'matches stage-B runner exactly', 'b1_commands': command_checks,
              'live_process_identity': 'NOT_CHECKED; real B1 must verify PID and lstart',
              'dry_run_status': 'NOT_RUN', 'real_b1_status': 'NO_GO; unsigned',
              'role_cli_started': False, 'business_input_sent': False}
    with (PREP / 'static-check.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'source_files': len(files), 'b1_commands': len(command_checks),
                      'draft_unsigned': True, 'dry_run': 'NOT_RUN', 'real_b1': 'NOT_RUN'}))


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    check()
