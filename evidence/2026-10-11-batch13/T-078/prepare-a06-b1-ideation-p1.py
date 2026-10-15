"""Create A-06 ideation P1 launch materials bound to the retained Stage-A root."""
import argparse
import json
import shutil
import subprocess
import tarfile
import uuid
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
STAGE_A = BASE / '09b-a06-stage-a-02'
PACKET = BASE / '09b-executable-materials-06'


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE / '09b-a06-b1-ideation-p1-01')
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'output_exists'
    readiness_file = STAGE_A / 'readiness.json'
    readiness = json.loads(readiness_file.read_bytes())
    assert readiness['status'] == 'READY_FOR_APPROVAL' and readiness['stage'] == 'A'
    root = Path(readiness['root']).resolve()
    assert root.is_dir() and readiness['roles_started'] == []
    static = json.loads((PACKET / 'static-check.json').read_bytes())
    assert static['status'] == 'PASS' and static['protocol'] is True
    assert static['revision'] == readiness['source_revision']
    assert (PACKET / 'sources.tar.gz').is_file()

    out.mkdir(parents=False)
    role_root = root / 'roles' / 'ideation'
    for name in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']:
        (role_root / name).mkdir(parents=True, exist_ok=True)
    role_text = '09B ideation deterministic role. Use only approved phase input and exact registered text; no retry or extra role.\n'
    (role_root / 'role.md').write_text(role_text, encoding='utf-8')
    write_json(role_root / 'claude/settings.json', {'theme': 'dark'})

    nonce = 'A06_B1_IDEATION_' + uuid.uuid4().hex
    launch = str(uuid.uuid4())
    session = str(uuid.uuid4())
    thread = str(uuid.uuid4())
    input_data = {
        'schema': 1,
        'root': str(root),
        'state': str(root / 'state'),
        'task': readiness['task'],
        'preset': 'ideation',
        'launch': launch,
        'session': session,
        'thread': thread,
        'executable': '/Users/luckye/.local/share/claude/versions/2.1.296',
        'role_file': str(role_root / 'role.md'),
        'code_revision': readiness['source_revision'],
        'source_snapshot': str((PACKET / 'sources.tar.gz').resolve()),
        'api_url': 'http://127.0.0.1:0',
        'turn_limit': 4,
    }
    scenario = {'schema': 1, 'name': 'stage-b-ideation', 'nonce': nonce}
    (root / 'nonce.txt').write_text(nonce, encoding='utf-8')
    write_json(root / 'scenario.json', scenario)
    write_json(root / 'input.json', input_data)
    approval_path = root / 'approval.json'
    subprocess.run([
        shutil.which('node') or '/opt/homebrew/bin/node',
        str(SOURCE / 'workbench/tests/prepare_t078_p1.ts'),
        str(root / 'input.json'),
        str(approval_path),
    ], cwd=SOURCE, check=True)
    approval = json.loads(approval_path.read_bytes())
    assert approval['input'] == input_data

    write_json(out / 'input.json', input_data)
    shutil.copyfile(approval_path, out / 'approval.json')
    shutil.copyfile(root / 'nonce.txt', out / 'nonce.txt')
    write_json(out / 'scenario.json', scenario)
    (out / 'role.md').write_text(role_text, encoding='utf-8')
    shutil.copyfile(role_root / 'claude/settings.json', out / 'isolated-settings.json')
    shutil.copyfile(PACKET / 'sources.tar.gz', out / 'sources.tar.gz')
    with tarfile.open(out / 'sources.tar.gz') as archive:
        source_files = archive.getnames()
    write_json(out / 'source-files.json', source_files)
    write_json(out / 'readiness-template.json', {
        'launch': launch, 'session': session, 'confirmed_by': None,
        'readiness': 'unconfirmed', 'basis': None,
    })
    write_json(out / 'screen-key-approval-template.json', {
        'launch': launch, 'session': session, 'directory': str(root / 'repo'),
        'approved_by': None, 'approval_ref': None, 'basis': None,
        'screen_id': None, 'purpose': None, 'key': None, 'selected_label': None,
        'screen_file': None, 'selected_label_semantics': 'Target item after this key',
        'trust_sequence': ['ArrowDown', 'Enter'],
        'trust_target': 'Yes, I trust this folder',
        'template_origin': 'A-06 generator; approval fields deliberately empty',
    })
    api_root = root / 'roles' / 'ideation'
    p1_args = [
        '--reuse-stage-a', '--reuse-api-root', str(api_root),
        '--reuse-readiness-file', str(readiness_file.resolve()),
    ]
    write_json(out / 'control-plane.json', {
        'environment': {
            'PATH': '/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
            'HOME': str(root / 'manager-home'), 'TMPDIR': str(root / 'tmp'),
            'A2A_STATE': str(root / 'state'), 'A2A_PROJECT': 't078-09b-runtime-project',
            'A2A_TASK': readiness['task'], 'A2A_PRESET': 'ideation',
        },
        'api_reuse': {
            'root': str(api_root), 'readiness_file': str(readiness_file.resolve()),
            'template_url': 'http://127.0.0.1:0', 'protocol': True,
        },
        'api_argv': [
            '/Library/Developer/CommandLineTools/usr/bin/python3', '-B',
            str(SOURCE / 'workbench/tests/t078_09b_fake_api.py'), '--root',
            str(api_root), '--role', 'ideation', '--port', '0', '--protocol',
        ],
        'driver_argv': [
            '/usr/bin/python3', '-B', str(SOURCE / 'workbench/tests/run_t078_p1.py'),
            '--materials', str(out), '--phase', 'launch', '--label', 'b1-launch',
            *p1_args,
        ],
        'launch_input_budget': 0, 'real_vendor_model_budget': 0,
        'messages_request_budget': 6, 'cli_starts': 0,
    })
    write_json(out / 'generation.json', {
        'status': 'PASS', 'scope': 'A-06 B1 ideation launch materials only',
        'launch': launch, 'session': session, 'task': readiness['task'],
        'stage_a_readiness': str(readiness_file.resolve()),
        'api_root': str(api_root), 'api_url_template': 'http://127.0.0.1:0',
        'protocol': True, 'real_cli_starts': 0, 'api_starts': 0,
        'daemon_starts': 0, 'target_starts': 0,
    })
    print(json.dumps({'status': 'PASS', 'output': str(out), 'real_cli_starts': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
