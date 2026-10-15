"""Generate A-13 ideation P1 material from a real Stage-A readiness; no spawn."""
import argparse, json, shutil, subprocess, tarfile, uuid
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage-a', type=Path, required=True)
    p.add_argument('--packet', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); stage = a.stage_a.resolve(); packet = a.packet.resolve(); out = a.output.resolve()
    assert not out.exists(), 'output_exists'
    readiness = json.loads((stage / 'readiness.json').read_bytes())
    static = json.loads((packet / 'static-check.json').read_bytes())
    assert readiness['status'] == 'READY_FOR_APPROVAL' and readiness['stage'] == 'A' and readiness['roles_started'] == []
    assert static['status'] == 'PASS' and static['protocol'] is True and static['revision'] == readiness['source_revision']
    root = Path(readiness['root']).resolve(); assert root.is_dir()
    role_root = root / 'roles' / 'ideation'
    for name in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']:
        (role_root / name).mkdir(parents=True, exist_ok=True)
    role_text = '09B ideation deterministic role. Use only approved phase input and exact registered text; no retry or extra role.\n'
    (role_root / 'role.md').write_text(role_text, encoding='utf-8')
    write(role_root / 'claude/settings.json', {'theme': 'dark'})
    launch, session, thread = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    nonce = 'A13_B1_IDEATION_' + uuid.uuid4().hex
    inp = {'schema': 1, 'root': str(root), 'state': str(root / 'state'), 'task': readiness['task'],
           'preset': 'ideation', 'launch': launch, 'session': session, 'thread': thread,
           'executable': '/Users/luckye/.local/share/claude/versions/2.1.296',
           'role_file': str(role_root / 'role.md'), 'code_revision': readiness['source_revision'],
           'source_snapshot': str((packet / 'sources.tar.gz').resolve()), 'api_url': 'http://127.0.0.1:0', 'turn_limit': 4}
    scenario = {'schema': 1, 'name': 'a13-stage-b-ideation', 'nonce': nonce}
    (root / 'nonce.txt').write_text(nonce, encoding='utf-8'); write(root / 'scenario.json', scenario); write(root / 'input.json', inp)
    approval_path = root / 'approval.json'
    subprocess.run([shutil.which('node') or '/opt/homebrew/bin/node', str(SOURCE / 'workbench/tests/prepare_t078_p1.ts'), str(root / 'input.json'), str(approval_path)], cwd=SOURCE, check=True)
    approval = json.loads(approval_path.read_bytes()); assert approval['input'] == inp
    out.mkdir(parents=False); write(out / 'input.json', inp); shutil.copyfile(approval_path, out / 'approval.json'); shutil.copyfile(root / 'nonce.txt', out / 'nonce.txt'); write(out / 'scenario.json', scenario)
    (out / 'role.md').write_text(role_text, encoding='utf-8'); shutil.copyfile(role_root / 'claude/settings.json', out / 'isolated-settings.json'); shutil.copyfile(packet / 'sources.tar.gz', out / 'sources.tar.gz')
    with tarfile.open(out / 'sources.tar.gz') as archive: write(out / 'source-files.json', archive.getnames())
    write(out / 'readiness-template.json', {'launch': launch, 'session': session, 'confirmed_by': None, 'readiness': 'unconfirmed', 'basis': None})
    write(out / 'screen-key-approval-template.json', {'launch': launch, 'session': session, 'directory': str(root / 'repo'), 'approved_by': None, 'approval_ref': None, 'basis': None, 'screen_id': None, 'purpose': None, 'key': None, 'selected_label': None, 'screen_file': None, 'selected_label_semantics': 'Target item after this key', 'trust_sequence': ['ArrowDown', 'Enter'], 'trust_target': 'Yes, I trust this folder'})
    p1_args = ['--reuse-stage-a', '--reuse-api-root', str(role_root), '--reuse-readiness-file', str((stage / 'readiness.json').resolve())]
    approval_template = json.loads((BASE / 'stage-b-a13-ideation-approval-template.json').read_bytes())
    approval_template.update({'source_revision': readiness['source_revision'], 'binding': readiness['target_binding'],
                              'p1_materials': str(out), 'p1_phase': 'launch', 'p1_args': p1_args,
                              'readiness_reference': str((stage / 'readiness.json').resolve()),
                              'api_protocol_tag': 'a07-registered-anthropic-v1'})
    write(BASE / 'stage-b-a13-ideation-approval-01.json', approval_template)
    write(out / 'control-plane.json', {'environment': {'HOME': str(root / 'manager-home'), 'TMPDIR': str(root / 'tmp'), 'A2A_STATE': str(root / 'state'), 'A2A_PROJECT': 't078-09b-runtime-project', 'A2A_TASK': readiness['task'], 'A2A_PRESET': 'ideation'}, 'api_reuse': {'root': str(role_root), 'readiness_file': str((stage / 'readiness.json').resolve()), 'template_url': 'http://127.0.0.1:0', 'protocol': True}, 'driver_argv': [str(SOURCE / 'workbench/tests/run_t078_p1.py'), '--materials', str(out), '--phase', 'launch', '--label', 'a13-b1-launch', *p1_args], 'launch_input_budget': 0, 'real_vendor_model_budget': 0, 'messages_request_budget': 6, 'cli_starts': 0})
    write(out / 'generation.json', {'status': 'PASS', 'scope': 'A-13 B1 ideation launch material only', 'launch': launch, 'session': session, 'task': readiness['task'], 'stage_a_readiness': str((stage / 'readiness.json').resolve()), 'api_root': str(role_root), 'api_url_template': 'http://127.0.0.1:0', 'protocol': True, 'real_cli_starts': 0, 'api_starts': 0, 'daemon_starts': 0, 'target_starts': 0})
    print(json.dumps({'status': 'PASS', 'output': str(out), 'real_cli_starts': 0}, ensure_ascii=False))

if __name__ == '__main__': main()
